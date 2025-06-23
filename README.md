# 📬 Gmail AI Assistant with Twilio Voice Alerts

This Python script automatically scans your unread Gmail inbox for emails related to coding challenges, meetings, contests, and more — and schedules Twilio voice calls to remind you at the event time, 1 hour before, and 3 hours before.

---

## 🔧 Features

- 📥 Scans latest 25 unread emails
- 🧠 Detects keywords like `coding challenge`, `meeting`, `contest`, etc.
- 🕒 Extracts event time (supports natural language like "23 June at 3:00 PM")
- ☎️ Schedules automated Twilio voice calls at:
  - At the time of event
  - 1 hour before
  - 3 hours before

---

## 📌 Technologies Used

- Python
- Gmail API (Google OAuth 2.0)
- Twilio Voice API
- `dateparser`, `google-api-python-client`, `twilio`

---

## ⚙️ Setup Instructions

> This project uses local environment variables. No `.env` file is required.

1. Clone the repo:
   ```bash
   git clone https://github.com/Pradeep68-star/gmail-ai-assistant
   cd gmail-ai-assistant
