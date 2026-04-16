from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemCreate(BaseModel):
    title: str
    book_id: int
    quantity: int
    price: int

class OrderCreate(BaseModel):
    amount: int
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    order_id: int
    amount: int
    status: str

    confirmed_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True