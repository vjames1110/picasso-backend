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

    # ⚠️ FIX: removed admin notification before payment

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

    if order.status != "confirmed":
        order.status = "confirmed"
    
    order.payment_id = payload["razorpay_payment_id"]

    if not order.confirmed_at:
        order.confirmed_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    user_phone = order.user.phone
    book_titles = ", ".join([item.title for item in order.items])

    # ✅ ADMIN NOTIFICATION AFTER PAYMENT SUCCESS
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

    # ✅ USER CONFIRMATION
    send_user_order_confirmed(
        user_phone,
        order.id,
        order.total_amount,
        book_titles
    )

    send_user_confirmed_email(
        order.user.email,
        order.id,
        order.total_amount,
        book_titles
    )

    return {
        "message": "Payment successful",
        "order_id": order.id
    }