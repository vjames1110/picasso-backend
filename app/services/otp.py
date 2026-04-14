import random
import os
import requests
import threading

OTP_STORE = {}

RESEND_API_KEY = os.getenv("RESEND_API_KEY")


def send_email_otp(email: str, otp: str):

    def send():
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Picasso Publications <onboarding@resend.dev>",
                "to": [email],
                "subject": "Picasso OTP Verification",
                "html": f"""
                    <h2>Picasso Publications</h2>
                    <h1>{otp}</h1>
                    <p>This OTP is valid for 5 minutes.</p>
                """,
            },
        )

        print("EMAIL STATUS:", response.status_code)
        print("EMAIL RESPONSE:", response.text)

    threading.Thread(target=send).start()


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