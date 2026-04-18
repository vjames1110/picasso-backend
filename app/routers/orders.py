from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from app.core.database import get_db
from app.services.payment import create_razorpay_order, verify_payment_signature
from app.services.deps import get_current_user, get_current_admin_user
from app.models.order import Order, OrderItem
from app.models.book import Book
from app.schemas.order import OrderCreate
from app.models.user import User

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
                book_id=book.id,          # ✅ FIXED
                title=book.title,         # ✅ from DB
                quantity=item.quantity,   # ✅ multi qty supported
                price=book.price          # ✅ correct price
            )
        )

    db.add_all(items)
    db.commit()
    db.refresh(order)

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

    order = db.query(Order).filter(
        Order.razorpay_order_id == payload["razorpay_order_id"]
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "confirmed"
    order.payment_id = payload["razorpay_payment_id"]

    if not order.confirmed_at:
        order.confirmed_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return {
        "message": "Payment successful",
        "order_id": order.id
    }


# ---------------- MY ORDERS ----------------
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
            "items": [
                {
                    "book_id": item.book_id,
                    "title": item.title,
                    "price": item.price,
                    "quantity": item.quantity
                }
                for item in order.items
            ]
        })

    return result

@router.get("/admin/all")
def get_all_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    orders = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            joinedload(Order.user))
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:
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

            "items": [
                {
                    "book_id": item.book_id,
                    "title": item.title,
                    "price": item.price,
                    "quantity": item.quantity
                }
                for item in order.items
            ]
        })

    return result


# ---------------- GET SINGLE ORDER ----------------
@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))   # IMPORTANT FIX
        .filter(
            Order.id == order_id,
            Order.user_id == user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

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
        "items": [
            {
                "book_id": item.book_id,
                "title": item.title,
                "price": item.price,
                "quantity": item.quantity
            }
            for item in order.items
        ]
    }


# ---------------- UPDATE ORDER STATUS ----------------
@router.put("/update-status/{order_id}")
def update_order_status(
    order_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = payload.get("status")

    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")

    valid_statuses = ["pending", "confirmed", "packed", "shipped", "delivered"]

    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    order.status = new_status
    now = datetime.utcnow()

    if new_status == "confirmed" and not order.confirmed_at:
        order.confirmed_at = now

    elif new_status == "packed" and not order.packed_at:
        order.packed_at = now

    elif new_status == "shipped" and not order.shipped_at:
        order.shipped_at = now

    elif new_status == "delivered" and not order.delivered_at:
        order.delivered_at = now

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status,
        "confirmed_at": order.confirmed_at,
        "packed_at": order.packed_at,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at
    }