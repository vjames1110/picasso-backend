import logging
import os
import random
import threading
from datetime import datetime, timedelta

import requests
from sqlalchemy.orm import Session

from app.models.otp import OtpCode

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
OTP_TTL_SECONDS = 600
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
                        "<p>This OTP is valid for 10 minutes.</p>"
                    ),
                },
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Unable to send OTP email: %s", exc)

    threading.Thread(target=send, daemon=True).start()


def generate_otp(db: Session, email: str):
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)

    record = db.query(OtpCode).filter(OtpCode.email == email).first()
    if record:
        record.otp = otp
        record.expires_at = expires_at
    else:
        db.add(OtpCode(email=email, otp=otp, expires_at=expires_at))
    db.commit()

    send_email_otp(email, otp)


def verify_otp(db: Session, email: str, otp: str):
    record = db.query(OtpCode).filter(OtpCode.email == email).first()
    if not record:
        return False

    if datetime.utcnow() > record.expires_at:
        db.delete(record)
        db.commit()
        return False

    if record.otp == otp:
        db.delete(record)
        db.commit()
        return True

    return False
