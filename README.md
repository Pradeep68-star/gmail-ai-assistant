# Gmail AI Assistant

The **Gmail AI Assistant** is an intelligent automation tool that integrates **Gmail** with **Twilio** to detect event-related emails — such as meetings, hackathons, coding contests, or other time-based events — and automatically schedule **Twilio voice call reminders** at the event time, one hour before, and three hours before.

This project leverages **Google Gmail API**, **Twilio API**, and **DateParser** to accurately detect events and automate reminders.

---

## Features:

- Automatically scans the latest Gmail messages once per day  
- Detects event-related emails using intelligent keyword matching  
- Extracts and parses dates/times in any format using `dateparser`  
- Makes **automated Twilio calls** at:
  - **At the event time**
  - **1 hour before the event**
  - **3 hours before the event**
- Includes robust logging and error handling  

---

## Project Structure :

gmail-ai-assistant/  
│  
├── app.py # Main script integrating Gmail and Twilio  
├── requirements.txt # Dependencies  
├── credentials.json # Gmail API credentials (not included)  
├── .env # Environment variables for Twilio & Gmail  
├── logs/ # Log files for monitoring  
└── README.md # Project documentation  


##  Prerequisites:

Before running this project, ensure you have:

- A **Google Cloud Project** with Gmail API enabled  
- A **Twilio Account** with a verified phone number  
- **Python 3.8+** installed  

---

## Installation:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pradeep68-star/gmail-ai-assistant.git
   cd gmail-ai-assistant
   
Install dependencies

pip install -r requirements.txt
Set up environment variables
Create a .env file in the project root:  

TWILIO_ACCOUNT_SID=your_account_sid  
TWILIO_AUTH_TOKEN=your_auth_token  
TWILIO_PHONE_NUMBER=your_twilio_number  
USER_PHONE_NUMBER=your_verified_number  
GMAIL_TOKEN_FILE=token.json  
Add Gmail credentials  
Download your credentials.json from Google Cloud and place it in the root directory.  

Usage:  
Run the assistant manually:  
python app.py  
When executed, it will:  

Read the 25 most recent Gmail messages  

Identify event-related emails  

Extract event date/time  

Schedule Twilio voice call reminders  

Automation (Optional):  
To automate the script to run daily:  

Windows (Task Scheduler):  

Trigger: Daily at a specific time  

## Technologies Used:
- Python  

- Gmail API (Google)  

- Twilio API  

- DateParser  

- dotenv  

- pytz  

## Future Enhancements:  
- Add a web dashboard for monitoring call logs and event analytics  

- Integrate voice customization in Twilio calls  

- Implement AI-based email classification using NLP models  

## Author:  
P.S.S.S.P. Pradeep  
AI-ML Student | Chandigarh University  
LinkedIn
