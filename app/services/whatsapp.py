import requests
import os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

def send_whatsapp_message(to_number: str, message: str):
    """
    Generic Whatsapp Sender
    """

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print("Whatsapp Error:", e)

# Admin Alert

def send_admin_new_order(order_id, amount):
    message=f"""
📚 New Order Received

Order ID: {order_id}
Amount: ₹{amount}

Check admin dashboard.
"""
    send_whatsapp_message(ADMIN_PHONE, message)

def send_user_order_confirmed(phone, order_id):
    message=f"""
    ✅ Order Confirmed

Order ID: {order_id}

Your order has been confirmed.
We will pack it shortly.
"""
    send_whatsapp_message(phone, message)

def send_user_order_packed(phone, order_id):
    message=f"""
📦 Order Packed

Order ID: {order_id}

Your order has been packed.
Will be shipped soon.
"""
    
def send_user_order_shipped(phone, order_id):
    message=f"""
🚚 Order Shipped

Order ID: {order_id}

Your order is on the way.
"""
    send_whatsapp_message(phone, message)

def send_user_order_delivered(phone, order_id):
    message=f"""
🎉 Order Delivered

Order ID: {order_id}

Thank you for shopping with Picasso Publications.
"""
    send_whatsapp_message(phone, message)