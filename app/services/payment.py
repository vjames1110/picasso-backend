import razorpay
import os
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

def create_razorpay_order(amount, receipt):
    order = client.order.create({
        "amount": int(amount * 100),
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1        
    })

    return order

def verify_payment_signature(data):
    try:
        client.utility.verify_payment_signature(data)
        return True
    except:
        return False