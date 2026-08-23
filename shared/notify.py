"""
Shared notifications: Telegram, Discord webhook, Teams webhook, Email, or console.

Configure via .env:
    TELEGRAM_BOT_TOKEN=...   (from @BotFather)
    TELEGRAM_CHAT_ID=...
    DISCORD_WEBHOOK_URL=...
    TEAMS_WEBHOOK_URL=...    (Power Automate "Post to a channel when a webhook request is received")
    EMAIL_TO=you@example.com
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=you@gmail.com
    SMTP_PASS=app-password    (Gmail: account settings -> Security -> App passwords)

If none are set, messages print to console.
"""

import os
import smtplib
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

load_dotenv()


def _send_email(message: str, parse_mode: str = "HTML") -> bool:
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    to = os.getenv("EMAIL_TO") or user
    port = int(os.getenv("SMTP_PORT", "587"))
    if not (host and user and password and to):
        return False
    subtype = "html" if parse_mode.upper() == "HTML" else "plain"
    msg = MIMEText(message, subtype, "utf-8")
    msg["Subject"] = message.split("\n")[0].strip()[:120] or "Notification"
    msg["From"] = user
    msg["To"] = to
    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False


def notify(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message via the first configured channel. Returns success."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": parse_mode},
                timeout=15,
            )
            if not r.ok:
                print(f"Telegram HTTP {r.status_code}: {r.text}")
            return r.ok
        except requests.RequestException as e:
            print(f"Telegram failed: {e}")

    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook:
        try:
            r = requests.post(webhook, json={"content": message}, timeout=15)
            return r.ok
        except requests.RequestException as e:
            print(f"Discord failed: {e}")

    teams_url = os.getenv("TEAMS_WEBHOOK_URL")
    if teams_url:
        try:
            # Power Automate Teams workflow payload (adaptive-card style)
            r = requests.post(
                teams_url,
                json={
                    "type": "message",
                    "attachments": [
                        {
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": {
                                "type": "AdaptiveCard",
                                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                "version": "1.4",
                                "body": [
                                    {
                                        "type": "TextBlock",
                                        "text": message,
                                        "wrap": True,
                                    }
                                ],
                            },
                        }
                    ],
                },
                timeout=15,
            )
            return r.ok
        except requests.RequestException as e:
            print(f"Teams failed: {e}")

    if _send_email(message, parse_mode):
        return True

    print(f"[notify] {message}")
    return True
