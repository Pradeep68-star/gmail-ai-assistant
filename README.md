# 📬 Gmail AI Assistant with Twilio Voice Reminders

An AI-powered assistant that **automatically scans your Gmail inbox daily**, detects important event-related emails (like coding contests, hackathons, or meetings), extracts event date/time using NLP, and schedules **Twilio voice call reminders** at:

* 🕒 The exact event time
* ⏰ 1 hour before
* ⏳ 3 hours before

## 🌟 Project Aim

> **To run every day and automatically remind you of upcoming events via voice call — so you never miss a coding challenge, meeting, or contest.**

---

## ⚒ How It Works

* Connects to your **Gmail API** (reads latest 25 unread emails).
* Uses keyword detection + NLP (`dateparser`) to extract event time.
* Schedules 3 **Twilio calls** per event using Windows Task Scheduler or `schtasks`.
* Fully automatic — no manual email checking or script running required.

---

## 🗕 Why Task Scheduler?

This script is meant to be run **automatically every day**.

Using **Windows Task Scheduler**:

* Runs this script each morning.
* Detects new emails/events.
* Schedules calls without user interaction.

> 🔁 This turns your script into a hands-free, AI-powered reminder system.

### ⏳ How to Schedule the Script (Windows)

1. Open **Task Scheduler**.
2. Click **Create Basic Task**.
3. Name it: `Gmail Reminder`.
4. Trigger: **Daily** at a preferred time (e.g., `09:00 AM`).
5. Action: **Start a Program**.
6. Program/script:

   ```
   python
   ```
7. Add arguments:

   ```
   "C:\path\to\your\gmail_event.py"
   ```
8. Finish ✅

---

## 🧪 Prerequisites

* Python 3.8+
* Gmail API credentials (`credentials.json`)
* Twilio account with verified phone number
* Installed libraries:

```bash
pip install --upgrade google-api-python-client google-auth google-auth-oauthlib twilio dateparser
```

---

## 🔐 Security

* No real credentials are stored in the GitHub repo.
* For local use, store sensitive values directly in your own file.
* If you prefer using `.env`, create a file like:

```env
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
USER_PHONE_NUMBER=your_verified_phone
```

> 🔒 `.env` and `token.json` should be listed in `.gitignore`.

---

## 📁 File Structure

```
📆 gmail-ai-assistant
 ├️ 📜 gmail_event.py             # Main script
 ├️ 📜 .gitignore                 # Ignore secrets
 ├️ 📜 .env.example (optional)   # Template for secrets
 └️ 📜 README.md                  # This file
```

---

## 🚀 One-Liner Description

> **An AI-powered daily email assistant that auto-detects events and schedules Twilio voice call reminders.**

---

## 🙌 Credits

Built by **P.S.S.S.P. Pradeep**
Mentored via ChatGPT (AI Assistant)
University: **Chandigarh University**
Specialization: **AI & ML (B.Tech)**

---

## 📢 Example Output

```
🚀 Script started.
📬 Found 25 unread emails.
🔍 Found: "A Coding Challenge"
✅ Keyword matched.
🕒 Event time: 2025-06-23 15:00:00
📞 Scheduled call 3h before, 1h before, and at the time.
```

---

## 📣 Contact

Feel free to raise an issue or fork the repo!
