import requests
import os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")


def send_whatsapp_template(to_number: str, template_name: str, params=[]):

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)}
                        for p in params
                    ]
                }
            ]
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        print("WhatsApp Status:", res.status_code)
        print("WhatsApp Response:", res.text)

    except Exception as e:
        print("Whatsapp Error:", e)


# Admin Alert
def send_admin_new_order(order_id, amount):

    send_whatsapp_template(
        ADMIN_PHONE,
        "admin_new_order",
        [order_id, amount]
    )


# User Order Confirmed
def send_user_order_confirmed(phone, order_id):

    send_whatsapp_template(
        phone,
        "order_confirmed",
        [order_id]
    )


# Packed
def send_user_order_packed(phone, order_id):

    send_whatsapp_template(
        phone,
        "order_packed",
        [order_id]
    )


# Shipped
def send_user_order_shipped(phone, order_id):

    send_whatsapp_template(
        phone,
        "order_shipped",
        [order_id]
    )


# Delivered
def send_user_order_delivered(phone, order_id):

    send_whatsapp_template(
        phone,
        "order_delivered",
        [order_id]
    )