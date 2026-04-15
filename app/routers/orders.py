from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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