from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.order import Order
from app.services.deps import get_current_admin_user

router = APIRouter()

@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user)
):
    total_orders = db.query(Order).count()

    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    shipped_orders = db.query(Order).filter(Order.status == "shipped").count()
    delivered_orders = db.query(Order).filter(Order.status == "delivered").count()

    total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0

    return {
        "totalOrders": total_orders,
        "pendingOrders": pending_orders,
        "shippedOrders": shipped_orders,
        "deliveredOrders": delivered_orders,
        "totalRevenue": float(total_revenue)
    }