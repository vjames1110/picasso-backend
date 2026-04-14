import random
import os
import requests
import threading

# temporary in-memory store (upgrade to Redis later)
OTP_STORE = {}

RESEND_API_KEY = os.getenv("re_AMNpx8uc_JN7oDvsYZJ58B933i8XS2St6")


def send_email_otp(email: str, otp: str):

    def send():
        requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Picasso Publications <picasso.india10@gmail.com>",
                "to": [email],
                "subject": "Picasso OTP Verification",
                "html": f"""
                    <h2>Picasso Publications</h2>
                    <h1>{otp}</h1>
                    <p>Valid for 5 minutes</p>
                """,
            },
        )

    threading.Thread(target=send).start()

    requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "Picasso <onboarding@resend.dev>",
            "to": [email],
            "subject": "Picasso OTP Verification",
            "html": f"""
                <h2>Picasso Publications</h2>
                <p>Your OTP is:</p>
                <h1>{otp}</h1>
                <p>This OTP is valid for 5 minutes.</p>
            """,
        },
    )


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