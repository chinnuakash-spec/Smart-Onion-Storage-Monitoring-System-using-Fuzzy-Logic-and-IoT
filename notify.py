"""
notify.py — Notification Service
==================================
Polls the Django GET API for the latest sensor reading.
If estimated shelf life < 1 month → sends Email (Gmail) and SMS (Twilio).

Run alongside sensor.py, or as a cron job:
  python notify.py

Authors: Rahul Prasad, Suman Raj, Akash Machireddy, Harshith Shahshni
IEEE Conference — IIT Mandi
"""

import time
import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── CONFIG ────────────────────────────────────────────────────────────────────
API_URL            = "http://127.0.0.1:8000/data/"    # Django GET endpoint

SHELF_LIFE_ALERT   = 1.0                              # months — trigger threshold

# Email (Gmail SMTP)
GMAIL_USER         = os.getenv("GMAIL_USER",     "your_email@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_PASSWORD", "your_app_password")
ALERT_TO_EMAIL     = os.getenv("ALERT_TO",       "farmer@gmail.com")

# Twilio SMS
TWILIO_SID         = os.getenv("TWILIO_ACCOUNT_SID",  "")
TWILIO_AUTH        = os.getenv("TWILIO_AUTH_TOKEN",    "")
TWILIO_FROM        = os.getenv("TWILIO_FROM_NUMBER",   "")
TWILIO_TO          = os.getenv("TWILIO_TO_NUMBER",     "")

CHECK_INTERVAL     = 60  # seconds between API polls


# ═══════════════════════════════════════════════════════════════════════════════
#  EMAIL ALERT
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(shelf_life_days: int):
    """Send Gmail alert when shelf life is critically low."""
    subject = "⚠️ E-Smart Storage: Estimated lifetime of onion is less than a month!"
    body = f"""Dear User,

Estimated shelf-life of stored onion is only {shelf_life_days} days.
Thus it requires immediate actions.

Please check the dashboard and take corrective action.

Thanks,
E-Smart Storage System
"""
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = ALERT_TO_EMAIL
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, ALERT_TO_EMAIL, msg.as_string())

        print("[Notify] Email sent.")
    except Exception as e:
        print(f"[Notify] Email failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SMS ALERT  (Twilio)
# ═══════════════════════════════════════════════════════════════════════════════

def send_sms(shelf_life_days: int):
    """Send Twilio SMS alert when shelf life is critically low."""
    try:
        from twilio.rest import Client
        body = (
            f"Dear User,\n"
            f"  Estimated shelf-life of stored onion is only {shelf_life_days} days.\n"
            f"Thus it requires immediate actions.\n"
            f"Thanks."
        )
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(body=body, from_=TWILIO_FROM, to=TWILIO_TO)
        print("[Notify] SMS sent.")
    except Exception as e:
        print(f"[Notify] SMS failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN POLLING LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("[Notify] Starting notification monitor...")
    alerted = False   # prevent repeat alerts for same reading

    while True:
        try:
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                data       = response.json()
                # The GET API returns latest reading including shelf_life (months)
                shelf_life = float(data.get("shelf_life", 999))

                print(f"[Notify] Latest shelf life: {shelf_life:.2f} months")

                if shelf_life < SHELF_LIFE_ALERT and not alerted:
                    shelf_days = int(shelf_life * 30)
                    print(f"[Notify] ALERT! Shelf life critically low: {shelf_days} days")
                    send_email(shelf_days)
                    send_sms(shelf_days)
                    alerted = True
                elif shelf_life >= SHELF_LIFE_ALERT:
                    alerted = False   # reset if conditions improve

        except Exception as e:
            print(f"[Notify] API poll error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
