import requests
import os

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
ADMIN_EMAIL = "picasso.india10@gmail.com"


def send_email(to_email, subject, html):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "Picasso Publications",
            "email": "picasso.india10@gmail.com"
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "htmlContent": html
    }

    res = requests.post(url, headers=headers, json=payload)

    print("Email Status:", res.status_code)
    print("Email Response:", res.text)


# ---------------- ADMIN NEW ORDER ----------------
def send_admin_new_order_email(order_id, amount, books):

    html = f"""
    <h2>📦 New Order Received</h2>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Amount:</b> ₹{amount}</p>
    <p><b>Books:</b> {books}</p>
    """

    send_email(
        ADMIN_EMAIL,
        f"New Order #{order_id}",
        html
    )


# ---------------- USER CONFIRMED ----------------
def send_user_confirmed_email(email, order_id, amount, books):

    html = f"""
    <h2>✅ Order Confirmed</h2>
    <p>Your order has been confirmed.</p>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Amount:</b> ₹{amount}</p>
    <p><b>Books:</b> {books}</p>
    """

    send_email(email, f"Order Confirmed #{order_id}", html)


# ---------------- USER PACKED ----------------
def send_user_packed_email(email, order_id, books):

    html = f"""
    <h2>📦 Order Packed</h2>
    <p>Your order is packed.</p>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Books:</b> {books}</p>
    """

    send_email(email, f"Order Packed #{order_id}", html)


# ---------------- USER SHIPPED ----------------
def send_user_shipped_email(email, order_id, books):

    html = f"""
    <h2>🚚 Order Shipped</h2>
    <p>Your order has been shipped.</p>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Books:</b> {books}</p>
    """

    send_email(email, f"Order Shipped #{order_id}", html)


# ---------------- USER DELIVERED ----------------
def send_user_delivered_email(email, order_id, books):

    html = f"""
    <h2>✅ Order Delivered</h2>
    <p>Your order has been delivered.</p>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Books:</b> {books}</p>
    """

    send_email(email, f"Order Delivered #{order_id}", html)