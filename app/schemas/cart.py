from pydantic import BaseModel


class CartCreate(BaseModel):
    book_id: int
    quantity: int


class CartUpdate(BaseModel):
    quantity: int


class CartResponse(BaseModel):
    id: int
    book_id: int
    quantity: int

    class Config:
        from_attributes = True