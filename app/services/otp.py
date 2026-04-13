import random
import smtplib
from email.mime.text import MIMEText

# temporary in-memory store (upgrade to Redis later)
OTP_STORE = {}

EMAIL_SENDER = "vikashjames8@gmail.com"
EMAIL_PASSWORD = "mjpa wtns rfxd mbps"  # Gmail App Password only


def send_email_otp(email: str, otp: str):
    msg = MIMEText(f"Your OTP for Picasso Bookstore is: {otp}")
    msg["Subject"] = "Picasso OTP Verification"
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, email, msg.as_string())


def generate_otp(email: str):
    otp = str(random.randint(100000, 999999))

    OTP_STORE[email] = otp

    send_email_otp(email, otp)

    return True


def verify_otp(email: str, otp: str):
    stored = OTP_STORE.get(email)

    if stored and stored == otp:
        del OTP_STORE[email]
        return True

    return False