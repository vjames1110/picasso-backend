from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payment import create_razorpay_order, verify_payment_signature
from app.services.deps import get_current_user
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])


# CREATE ORDER + RAZORPAY ORDER
@router.post("/create")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    # 1. CREATE RAZORPAY ORDER
    razorpay_order = create_razorpay_order(
        amount=data.amount,
        receipt=f"user_{user.id}"
    )

    # 2. SAVE ORDER IN DB
    order = Order(
        user_id=user.id,
        total_amount=data.amount,
        status="created",
        razorpay_order_id=razorpay_order["id"]
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # 3. SAVE ORDER ITEMS
    for item in data.items:
        order_item = OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            title=item.title,
            quantity=item.quantity,
            price=item.price
        )
        db.add(order_item)

    db.commit()

    # 4. RETURN RAZORPAY DATA
    return {
        "order_id": order.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "currency": "INR"
    }


# VERIFY PAYMENT
@router.post("/verify")
def verify_payment(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    razorpay_order_id = payload.get("razorpay_order_id")
    razorpay_payment_id = payload.get("razorpay_payment_id")
    razorpay_signature = payload.get("razorpay_signature")

    # VERIFY SIGNATURE
    is_valid = verify_payment_signature({
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    })

    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # FIND ORDER
    order = db.query(Order).filter(
        Order.razorpay_order_id == razorpay_order_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # UPDATE ORDER
    order.status = "paid"
    order.payment_id = razorpay_payment_id

    db.commit()

    return {
        "status": "success",
        "order_id": order.id
    }


# GET USER ORDERS
@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == user.id
    ).all()

    return orders