from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.deps import get_current_user
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    order = Order(
        user_id=user.id,
        total_amount=data.amount,
        status="created"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

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

    return {
        "order_id": order.id,
        "amount": order.total_amount,
        "status": order.status
    }


@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == user.id
    ).all()

    return orders