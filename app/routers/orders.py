from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.services.payment import create_razorpay_order, verify_payment_signature
from app.services.deps import get_current_user
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------- CREATE ORDER ----------------
@router.post("/create")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    # 1. Save order in DB
    order = Order(
        user_id=user.id,
        total_amount=data.amount,
        status="pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Save items
    for item in data.items:
        db.add(OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            title=item.title,
            quantity=item.quantity,
            price=item.price
        ))

    db.commit()

    # 3. Create Razorpay order
    razorpay_order = create_razorpay_order(
        amount=int(data.amount),
        receipt_id=str(order.id)
    )

    # 4. Save razorpay order id in DB
    order.razorpay_order_id = razorpay_order["id"]
    db.commit()

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

    # find using razorpay_order_id
    order = db.query(Order).filter(
        Order.razorpay_order_id == payload["razorpay_order_id"]
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "completed"
    order.payment_id = payload["razorpay_payment_id"]

    db.commit()

    return {
        "message": "Payment successful",
        "order_id": order.id
    }

# Order history

# ---------------- MY ORDERS ----------------
@router.get("/my-orders")
def get_my_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    orders = (
        db.query(Order)
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
            "razorpay_order_id": order.razorpay_order_id,
            "created_at": order.created_at,
            "items": [
                {
                    "title": item.title,
                    "price": item.price,
                    "quantity": item.quantity,
                    "book_id": item.book_id
                }
                for item in order.items
            ]
        })

    return result

# Get Single Order

# ---------------- GET SINGLE ORDER ----------------
@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    order = (
        db.query(Order)
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
        "items": [
            {
                "title": item.title,
                "price": item.price,
                "quantity": item.quantity
            }
            for item in order.items
        ]
    }

# Update order status Admin Only

from datetime import datetime


# ---------------- UPDATE ORDER STATUS (ADMIN ONLY - PHASE 1 CORE) ----------------
@router.put("/update-status/{order_id}")
def update_order_status(
    order_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Updates order status + tracking timestamps
    Safe extension for Phase 1 tracking system
    """

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = payload.get("status")

    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")

    valid_statuses = ["pending", "confirmed", "packed", "shipped", "delivered"]

    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    # ---------------- UPDATE STATUS ----------------
    order.status = new_status

    now = datetime.utcnow()

    # ---------------- AUTO TIMESTAMP HANDLING ----------------
    if new_status == "confirmed":
        if not order.confirmed_at:
            order.confirmed_at = now

    elif new_status == "packed":
        if not order.packed_at:
            order.packed_at = now

    elif new_status == "shipped":
        if not order.shipped_at:
            order.shipped_at = now

    elif new_status == "delivered":
        if not order.delivered_at:
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
