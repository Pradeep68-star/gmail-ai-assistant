import time
import base64
import os
import re
import warnings
from datetime import datetime, timedelta
import dateparser
from dateparser.search import search_dates
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from twilio.rest import Client

warnings.filterwarnings("ignore", category=DeprecationWarning)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")




SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[!] Token refresh failed: {e}")
                creds = None
        if not creds:
            print("[*] Opening browser to re-authenticate...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

service = get_gmail_service()

KEYWORDS = ['competition', 'hackathon', 'meeting', 'coding challenge', 'contest', 'event', 'invitation']

def get_email_subject(msg):
    headers = msg['payload']['headers']
    for header in headers:
        if header['name'] == 'Subject':
            return header['value']
    return "(No Subject)"

def get_email_body(msg):
    try:
        parts = msg['payload'].get('parts', [])
        if parts:
            data = parts[0]['body'].get('data')
        else:
            data = msg['payload']['body'].get('data')
        if data:
            decoded = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8')
            return decoded
    except Exception as e:
        print(f"⚠️ Error decoding body: {e}")
    return ""

def contains_keyword(text):
    return any(keyword.lower() in text.lower() for keyword in KEYWORDS)

def extract_event_time(text):
    try:
        # Normalize AM/PM
        text = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', lambda m: m.group().replace('.', '').upper(), text, flags=re.IGNORECASE)

        # Remove duplicate years or garbage like "2025e"
        text = re.sub(r'\b(\d{4})[^\d\s]\b', r'\1', text)

        # Inject current year if missing
        current_year = datetime.now().year
        text = re.sub(
            r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
            r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|'
            r'Nov(?:ember)?|Dec(?:ember)?))(?!\s+\d{4})',
            rf'\1 {current_year}', text, flags=re.IGNORECASE
        )

        print(f"[DEBUG] Parsing text for dates:\n{text}\n")

        results = search_dates(text, settings={
            'PREFER_DATES_FROM': 'future',
            'DATE_ORDER': 'DMY'
        })

        if results:
            for match_text, dt in results:
                if dt.year < 2100 and dt.time() != datetime.min.time():
                    print(f"[DEBUG] Matched date text: '{match_text}' -> {dt}")
                    return dt
    except Exception as e:
        print(f"⚠️ Date parsing error: {e}")
    return None

def make_call(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        to=USER_PHONE_NUMBER,
        from_=TWILIO_PHONE_NUMBER
    )
    print(f"📞 Call scheduled with SID: {call.sid}")

def schedule_calls(event_time, subject):
    now = datetime.now()
    if event_time < now:
        print(f"⏩ Skipping past event: {event_time}")
        return

    time_diffs = {
        "at the time of": event_time,
        "1 hour before": event_time - timedelta(hours=1),
        "3 hours before": event_time - timedelta(hours=3)
    }

    for desc, t in time_diffs.items():
        if t > now:
            delay = (t - now).total_seconds()
            print(f"⏳ Will call in {int(delay)} seconds — {desc}")
            os.system(f'schtasks /create /tn "TwilioCall_{int(time.time())}" /tr "python -c \\"from twilio.rest import Client; Client(\'{TWILIO_ACCOUNT_SID}\', \'{TWILIO_AUTH_TOKEN}\').calls.create(twiml=\'<Response><Say>Reminder: {subject} is scheduled {desc}</Say></Response>\', to=\'{USER_PHONE_NUMBER}\', from_=\'{TWILIO_PHONE_NUMBER}\')\\"" /sc once /st {t.strftime("%H:%M")}')
            # You can also use subprocess or other scheduling if needed

def check_emails():
    print(f"[{datetime.now()}] 🚀 Script started.")
    try:
        results = service.users().messages().list(userId='me', maxResults=25, labelIds=['INBOX'], q='is:unread').execute()
        messages = results.get('messages', [])
        print(f"[{datetime.now()}] 📨 Found {len(messages)} emails to analyze.")

        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            subject = get_email_subject(msg_data)
            body = get_email_body(msg_data)
            combined_text = f"{subject}\n{body}"

            print(f"[{datetime.now()}] 🔍 Checking email: {subject}")
            if contains_keyword(combined_text):
                print(f"[{datetime.now()}] ✅ Keyword matched.")
                event_time = extract_event_time(combined_text)
                if event_time:
                    print(f"[{datetime.now()}] 🕒 Event time detected: {event_time}")
                    schedule_calls(event_time, subject)
                else:
                    print(f"[{datetime.now()}] ❌ No valid event time found.")
            else:
                print(f"[{datetime.now()}] ❌ No matching keyword.")
    except Exception as e:
        print(f"[!] Gmail fetch error: {e}")

if __name__ == "__main__":
    check_emails()
