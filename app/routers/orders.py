from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload, joinedload
from datetime import datetime

from app.core.database import get_db
from app.services.payment import create_razorpay_order, verify_payment_signature
from app.services.deps import get_current_user, get_current_admin_user
from app.models.order import Order, OrderItem
from app.models.book import Book
from app.schemas.order import OrderCreate

from app.services.whatsapp import (
    send_admin_new_order,
    send_user_order_confirmed,
    send_user_order_shipped,
    send_user_order_packed,
    send_user_order_delivered
)

from app.services.email import (
    send_admin_new_order_email,
    send_user_confirmed_email,
    send_user_packed_email,
    send_user_shipped_email,
    send_user_delivered_email
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------- CREATE ORDER ----------------
@router.post("/create")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    order = Order(
        user_id=user.id,
        total_amount=data.amount,
        status="pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    items = []

    for item in data.items:

        book = db.query(Book).filter(Book.id == item.book_id).first()

        if not book:
            raise HTTPException(
                status_code=400,
                detail=f"Book with id {item.book_id} not found"
            )

        items.append(
            OrderItem(
                order_id=order.id,
                book_id=book.id,
                title=book.title,
                quantity=item.quantity,
                price=book.price
            )
        )

    db.add_all(items)
    db.commit()
    db.refresh(order)

    # Create Razorpay Order ONLY
    razorpay_order = create_razorpay_order(
        amount=int(data.amount),
        receipt_id=str(order.id)
    )

    order.razorpay_order_id = razorpay_order["id"]
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": data.amount,
        "currency": "INR"
    }


# ---------------- VERIFY PAYMENT ----------------
@router.post("/verify")
def verify_payment(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    valid = verify_payment_signature(
        payload["razorpay_order_id"],
        payload["razorpay_payment_id"],
        payload["razorpay_signature"]
    )

    if not valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    order = db.query(Order).options(
        joinedload(Order.user),
        selectinload(Order.items)
    ).filter(
        Order.razorpay_order_id == payload["razorpay_order_id"]
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # mark confirmed
    order.status = "confirmed"
    order.payment_id = payload["razorpay_payment_id"]

    if not order.confirmed_at:
        order.confirmed_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    # Prepare data
    user_phone = order.user.phone
    user_email = order.user.email
    book_titles = ", ".join([item.title for item in order.items])

    # ---------- ADMIN NOTIFICATION ----------
    send_admin_new_order(
        order.id,
        order.total_amount,
        book_titles
    )

    send_admin_new_order_email(
        order.id,
        order.total_amount,
        book_titles
    )

    # ---------- USER CONFIRMATION ----------
    send_user_order_confirmed(
        user_phone,
        order.id,
        order.total_amount,
        book_titles
    )

    send_user_confirmed_email(
        user_email,
        order.id,
        order.total_amount,
        book_titles
    )

    return {
        "message": "Payment successful",
        "order_id": order.id
    }


# ---------------- MY ORDERS ----------------
@router.get("/my-orders")
def get_my_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:

        items = [
            {
                "book_id": item.book_id,
                "title": item.title,
                "price": item.price,
                "quantity": item.quantity
            }
            for item in order.items
        ]

        result.append({
            "id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "payment_id": order.payment_id,
            "created_at": order.created_at,
            "confirmed_at": order.confirmed_at,
            "packed_at": order.packed_at,
            "shipped_at": order.shipped_at,
            "delivered_at": order.delivered_at,
            "items": items
        })

    return result


# ---------------- ADMIN ALL ORDERS ----------------
@router.get("/admin/all")
def get_all_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    orders = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            joinedload(Order.user)
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:

        items = [
            {
                "book_id": item.book_id,
                "title": item.title,
                "price": item.price,
                "quantity": item.quantity
            }
            for item in order.items
        ]

        result.append({
            "id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "payment_id": order.payment_id,
            "created_at": order.created_at,
            "confirmed_at": order.confirmed_at,
            "packed_at": order.packed_at,
            "shipped_at": order.shipped_at,
            "delivered_at": order.delivered_at,
            "user": {
                "name": order.user.name,
                "email": order.user.email,
                "phone": order.user.phone,
                "pincode": order.user.pincode,
                "house": order.user.house,
                "area": order.user.area,
                "city": order.user.city,
                "state": order.user.state
            },
            "items": items
        })

    return result


# ---------------- UPDATE STATUS ----------------
@router.put("/update-status/{order_id}")
def update_order_status(
    order_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):

    order = db.query(Order).options(
        joinedload(Order.user),
        selectinload(Order.items)
    ).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    status = payload.get("status")
    order.status = status

    if status == "packed":
        order.packed_at = datetime.utcnow()

    elif status == "shipped":
        order.shipped_at = datetime.utcnow()

    elif status == "delivered":
        order.delivered_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    user_phone = order.user.phone
    user_email = order.user.email
    book_titles = ", ".join([item.title for item in order.items])

    if status == "packed":
        send_user_order_packed(user_phone, order.id, book_titles)
        send_user_packed_email(user_email, order.id, book_titles)

    elif status == "shipped":
        send_user_order_shipped(user_phone, order.id, book_titles)
        send_user_shipped_email(user_email, order.id, book_titles)

    elif status == "delivered":
        send_user_order_delivered(user_phone, order.id, book_titles)
        send_user_delivered_email(user_email, order.id, book_titles)

    return {"message": "Status updated"}


# ---------------- GET SINGLE ORDER ----------------
@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(
            Order.id == order_id,
            Order.user_id == user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [
        {
            "book_id": item.book_id,
            "title": item.title,
            "price": item.price,
            "quantity": item.quantity
        }
        for item in order.items
    ]

    return {
        "id": order.id,
        "status": order.status,
        "total_amount": order.total_amount,
        "payment_id": order.payment_id,
        "created_at": order.created_at,
        "confirmed_at": order.confirmed_at,
        "packed_at": order.packed_at,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
        "items": items
    }