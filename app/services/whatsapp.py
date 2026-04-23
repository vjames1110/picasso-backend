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
        "to": str(to_number),
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

    res = requests.post(url, headers=headers, json=payload)

    print("WhatsApp Status:", res.status_code)
    print("WhatsApp Response:", res.text)


# ---------------- ADMIN NEW ORDER ----------------
def send_admin_new_order(order_id, amount, books):

    send_whatsapp_template(
        ADMIN_PHONE,
        "admin_new_order",
        [order_id, amount, books]
    )


# ---------------- USER CONFIRMED ----------------
try:
    send_user_order_confirmed(
        user_phone,
        order.id,
        order.total_amount,
        book_titles
    )
except Exception as e:
    print("WhatsApp Error (ignored):", str(e))


# ---------------- USER PACKED ----------------
def send_user_order_packed(phone, order_id, books):

    send_whatsapp_template(
        phone,
        "order_packed",
        [order_id, books]
    )


# ---------------- USER SHIPPED ----------------
def send_user_order_shipped(phone, order_id, books):

    send_whatsapp_template(
        phone,
        "order_shipped",
        [order_id, books]
    )


# ---------------- USER DELIVERED ----------------
def send_user_order_delivered(phone, order_id, books):

    send_whatsapp_template(
        phone,
        "order_delivered",
        [order_id, books]
    )