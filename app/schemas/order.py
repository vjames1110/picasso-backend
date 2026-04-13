from pydantic import BaseModel
from typing import List

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

    class Config:
        from_attributes = True