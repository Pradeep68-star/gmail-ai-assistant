import base64
import os
import re
import warnings
from datetime import datetime, timedelta
import pytz
from dateparser.search import search_dates
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from twilio.rest import Client
from bs4 import BeautifulSoup
import threading
import json
import logging
from flask import Flask, render_template, Response, request, jsonify

# --- Basic Setup & Configuration ---
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(level=logging.INFO)

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Global In-memory Storage (for simplicity) ---
# In a production environment, use a database or a more persistent store.
from dotenv import load_dotenv
load_dotenv()

# Replace hardcoded values with environment variables
app_config = {
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
    'USER_PHONE_NUMBER': os.getenv('USER_PHONE_NUMBER'),
    'SCOPES': ['https://www.googleapis.com/auth/gmail.readonly'],
    'KEYWORDS': ['competition', 'hackathon', 'meeting', 'coding challenge', 'contest', 'event', 'invitation', 'challange']
}

scheduled_reminders = []
gmail_service = None
IST = pytz.timezone("Asia/Kolkata")

# ---------------------- Gmail Authentication ----------------------
def get_gmail_service():
    global gmail_service
    if gmail_service:
        return gmail_service

    creds = None
    token_path = 'token.json'
# NEW Line 48 (Correct)
    credentials_path = os.getenv('CREDENTIALS_PATH')

    if not os.path.exists(credentials_path):
        raise FileNotFoundError("Error: 'credentials.json' not found. Please place it in the same directory as app.py.")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, app_config['SCOPES'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Token refresh failed: {e}")
                creds = None # Force re-authentication
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, app_config['SCOPES'])
            # Note: run_local_server will open a browser tab for authentication
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    gmail_service = build('gmail', 'v1', credentials=creds)
    return gmail_service

# ---------------------- Email Parsing Logic ----------------------
def get_email_subject(msg):
    for header in msg['payload']['headers']:
        if header['name'] == 'Subject':
            return header['value']
    return "(No Subject)"

def get_clean_email_body(msg):
    parts = []
    def extract_parts(payload):
        if 'parts' in payload:
            for part in payload['parts']:
                extract_parts(part)
        else:
            mime_type = payload.get('mimeType', '')
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode(errors="ignore")
                parts.append((mime_type, decoded))
    extract_parts(msg['payload'])

    for mime, content in parts:
        if 'text/plain' in mime:
            return clean_text(content)
    for mime, content in parts:
        if 'text/html' in mime:
            soup = BeautifulSoup(content, "html.parser")
            return clean_text(soup.get_text(separator="\n"))
    return ""

def clean_text(text):
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def contains_keyword(text):
    return any(keyword.lower() in text.lower() for keyword in app_config['KEYWORDS'])

# ---------------------- Date/Time Extraction ----------------------
def extract_event_times(text):
    try:
        text = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', lambda m: m.group().replace('.', '').upper(), text, flags=re.IGNORECASE)
        
        current_year = datetime.now().year
        text_with_year = re.sub(
            r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?))(?!\s+\d{4})',
            rf'\1 {current_year}', text, flags=re.IGNORECASE
        )

        results = search_dates(text_with_year, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True})

        found_times = []
        if results:
            now_ist = datetime.now(IST)
            for _, dt in results:
                dt_ist = dt.astimezone(IST) if dt.tzinfo else IST.localize(dt)
                
                if dt_ist > now_ist and dt_ist.time() != datetime.min.time():
                    found_times.append(dt_ist)
        
        return sorted(list(set(found_times)))
    except Exception as e:
        logging.error(f"Date parsing error: {e}")
        return []

# ---------------------- Twilio Call & Scheduling Logic ----------------------
def place_call(desc, subject, event_time_str):
    global scheduled_reminders
    try:
        client = Client(app_config['TWILIO_ACCOUNT_SID'], app_config['TWILIO_AUTH_TOKEN'])
        call = client.calls.create(
            to=app_config['USER_PHONE_NUMBER'],
            from_=app_config['TWILIO_PHONE_NUMBER'],
            twiml=f'<Response><Say>Reminder: {subject} scheduled {desc}</Say></Response>'
        )
        logging.info(f"Call placed for '{subject}' ({desc}) — SID: {call.sid}")
        for reminder in scheduled_reminders:
            if reminder['subject'] == subject and reminder['event_time'] == event_time_str and reminder['description'] == desc:
                reminder['status'] = 'Called'
                break
    except Exception as e:
        logging.error(f"Twilio call error: {e}")
        for reminder in scheduled_reminders:
            if reminder['subject'] == subject and reminder['event_time'] == event_time_str and reminder['description'] == desc:
                reminder['status'] = 'Failed'
                break

def schedule_calls(event_time_ist, subject):
    reminders = {
        "3 hours before": event_time_ist - timedelta(hours=3),
        "1 hour before": event_time_ist - timedelta(hours=1),
        "At the time of event": event_time_ist
    }
    now = datetime.now(IST)
    event_time_str = event_time_ist.strftime('%Y-%m-%d %I:%M %p %Z')

    scheduled_count = 0
    for desc, t in reminders.items():
        delay = (t - now).total_seconds()
        if delay > 0:
            logging.info(f"Scheduling call for '{subject}' {desc} in {int(delay)} seconds")
            threading.Timer(delay, place_call, args=(desc, subject, event_time_str)).start()
            
            scheduled_reminders.append({
                'subject': subject,
                'event_time': event_time_str,
                'description': desc,
                'scheduled_at': t.strftime('%Y-%m-%d %I:%M %p %Z'),
                'status': 'Scheduled'
            })
            scheduled_count += 1
        else:
            logging.warning(f"Skipping past reminder for '{subject}': {desc}")
    
    return scheduled_count > 0

# ---------------------- Main Email Checking Function ----------------------
def check_emails_and_stream_logs():
    def generate():
        def log_message(msg_type, text):
            timestamp = datetime.now(IST).strftime('%I:%M:%S %p')
            message = f"[{timestamp}] {text}"
            return f"data: {json.dumps({'type': msg_type, 'message': message})}\n\n"

        yield log_message("info", "🚀 Script started, attempting to authenticate with Gmail...")
        try:
            service = get_gmail_service()
            yield log_message("success", "✅ Successfully connected to Gmail API.")
        except Exception as e:
            yield log_message("error", f"❌ Gmail Authentication Failed: {e}. Please check credentials.json and ensure you authenticate in the browser.")
            yield log_message("info", "⏹️ Process stopped.")
            return

        try:
            results = service.users().messages().list(userId='me', maxResults=25, labelIds=['INBOX']).execute()
            messages = results.get('messages', [])
            yield log_message("info", f"📨 Found {len(messages)} recent emails in INBOX.")

            if not messages:
                yield log_message("info", "No emails found to process.")
            
            processed_count = 0
            for msg_summary in messages:
                processed_count += 1
                yield log_message("info", f"Processing email {processed_count}/{len(messages)}...")
                msg_data = service.users().messages().get(userId='me', id=msg_summary['id']).execute()
                subject = get_email_subject(msg_data)
                
                yield log_message("info", f"🔍 Checking email: \"{subject}\"")

                body = get_clean_email_body(msg_data)
                combined_text = f"{subject}\n{body}"

                if contains_keyword(combined_text):
                    yield log_message("success", f"🔑 Keyword matched in \"{subject}\".")
                    event_times = extract_event_times(combined_text)
                    if event_times:
                        for et in event_times:
                            yield log_message("success", f"🕒 Event time detected (IST): {et.strftime('%Y-%m-%d %I:%M %p')}")
                            if schedule_calls(et, subject):
                                yield log_message("success", f"📞 Reminders scheduled successfully for \"{subject}\".")
                            else:
                                yield log_message("warn", "All reminder times are in the past. No new calls scheduled.")
                    else:
                        yield log_message("warn", "Keyword matched, but no valid future event time was found.")
                else:
                    yield log_message("neutral", "No matching keyword found.")

            yield log_message("info", f"⏹️ Finished processing {len(messages)} emails.")

        except Exception as e:
            yield log_message("error", f"An error occurred: {e}")

    return Response(generate(), mimetype='text/event-stream')


# ---------------------- Flask Web Routes ----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    global app_config
    if request.method == 'GET':
        masked_config = app_config.copy()
        masked_config['TWILIO_ACCOUNT_SID'] = 'AC' + '*' * (len(app_config['TWILIO_ACCOUNT_SID']) - 4) + app_config['TWILIO_ACCOUNT_SID'][-2:]
        masked_config['TWILIO_AUTH_TOKEN'] = '*' * len(app_config['TWILIO_AUTH_TOKEN'])
        return jsonify(masked_config)
    
    if request.method == 'POST':
        data = request.json
        if data.get('TWILIO_ACCOUNT_SID') and 'AC*' not in data['TWILIO_ACCOUNT_SID']:
            app_config['TWILIO_ACCOUNT_SID'] = data['TWILIO_ACCOUNT_SID']
        if data.get('TWILIO_AUTH_TOKEN') and '****' not in data['TWILIO_AUTH_TOKEN']:
            app_config['TWILIO_AUTH_TOKEN'] = data['TWILIO_AUTH_TOKEN']

        app_config['TWILIO_PHONE_NUMBER'] = data.get('TWILIO_PHONE_NUMBER', app_config['TWILIO_PHONE_NUMBER'])
        app_config['USER_PHONE_NUMBER'] = data.get('USER_PHONE_NUMBER', app_config['USER_PHONE_NUMBER'])
        
        keywords_str = data.get('KEYWORDS', "")
        app_config['KEYWORDS'] = [k.strip() for k in keywords_str.split(',') if k.strip()]

        return jsonify({"status": "success", "message": "Configuration updated."})


@app.route('/check-emails')
def check_emails_endpoint():
    return check_emails_and_stream_logs()

@app.route('/reminders')
def get_reminders():
    return jsonify(sorted(scheduled_reminders, key=lambda x: x['scheduled_at'], reverse=True))


# ---------------------- Run the Application ----------------------
if __name__ == '__main__':
    print("Attempting to authenticate with Google...")
    print("A new tab may open in your browser for you to log in and grant permissions.")
    try:
        get_gmail_service()
        print("Gmail authentication successful.")
    except Exception as e:
        print(f"Could not authenticate with Gmail on startup: {e}")
        print("Authentication will be re-attempted when you click 'Check Emails Now'.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)