import logging
import os
import random
import threading
import time

import requests

OTP_STORE = {}
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
logger = logging.getLogger(__name__)


def send_email_otp(email: str, otp: str):
    """Send one OTP email without blocking the login request."""
    if not BREVO_API_KEY:
        logger.warning("OTP email skipped because BREVO_API_KEY is not configured")
        return

    def send():
        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={
                    "sender": {
                        "name": "Picasso Publications",
                        "email": "picasso.india10@gmail.com",
                    },
                    "to": [{"email": email}],
                    "subject": "Your OTP - Picasso Publications",
                    "htmlContent": (
                        "<h2>Picasso Publications</h2>"
                        f"<h1>{otp}</h1>"
                        "<p>This OTP is valid for 5 minutes.</p>"
                    ),
                },
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Unable to send OTP email: %s", exc)

    threading.Thread(target=send, daemon=True).start()


def generate_otp(email: str):
    otp = str(random.randint(100000, 999999))
    OTP_STORE[email] = {"otp": otp, "time": time.time()}
    send_email_otp(email, otp)


def verify_otp(email: str, otp: str):
    data = OTP_STORE.get(email)
    if not data:
        return False

    if time.time() - data["time"] > 300:
        del OTP_STORE[email]
        return False

    if data["otp"] == otp:
        del OTP_STORE[email]
        return True

    return False
