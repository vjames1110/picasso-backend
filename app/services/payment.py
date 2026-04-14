import razorpay
import os
import hmac
import hashlib

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ---------------- CREATE ORDER ----------------
def create_razorpay_order(amount: int, receipt_id: str):

    order = client.order.create({
        "amount": amount * 100,  # paise
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1
    })

    return order


# ---------------- VERIFY SIGNATURE ----------------
def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):

    body = f"{razorpay_order_id}|{razorpay_payment_id}"

    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    return expected_signature == razorpay_signature