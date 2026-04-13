from pydantic import BaseModel
from typing import Optional, List

class BookCreate(BaseModel):
    title: str
    description: Optional[str] = None

    price: float
    original_price: Optional[float] = None

    image: Optional[str] = None
    stock: int
    author: Optional[List[str]] = None
    category: Optional[str] = None

class BookResponse(BookCreate):
    id: int
    title: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    image: Optional[str]
    stock: int
    author: Optional[List[str]]
    category: Optional[str]

    class Config:
        from_attributes = True
