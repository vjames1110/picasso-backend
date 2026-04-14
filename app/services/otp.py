import random
import os
import requests
import threading
import time

OTP_STORE = {}

BREVO_API_KEY = os.getenv("BREVO_API_KEY")


def send_email_otp(email: str, otp: str):

    def send():
        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": BREVO_API_KEY,
                    "content-type": "application/json"
                },
                json={
                    "sender": {
                        "name": "Picasso Publications",
                        "email": "picasso.india10@gmail.com"
                    },
                    "to": [
                        {
                            "email": email
                        }
                    ],
                    "subject": "Your OTP - Picasso Publications",
                    "htmlContent": f"""
                        <h2>Picasso Publications</h2>
                        <h1>{otp}</h1>
                        <p>This OTP is valid for 5 minutes.</p>
                    """
                }
            )

            print("BREVO STATUS:", response.status_code)
            print("BREVO RESPONSE:", response.text)

        except Exception as e:
            print("BREVO ERROR:", e)

    threading.Thread(target=send).start()


def generate_otp(email: str):
    otp = str(random.randint(100000, 999999))

    OTP_STORE[email] = {
        "otp": otp,
        "time": time.time()
    }

    send_email_otp(email, otp)

    return True


def verify_otp(email: str, otp: str):
    data = OTP_STORE.get(email)

    if not data:
        return False

    # expire after 5 min
    if time.time() - data["time"] > 300:
        del OTP_STORE[email]
        return False

    if data["otp"] == otp:
        del OTP_STORE[email]
        return True

    return False