from pydantic import BaseModel, Field


class CartCreate(BaseModel):
    book_id: int
    quantity: int = Field(ge=1)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartResponse(BaseModel):
    id: int
    book_id: int
    quantity: int

    class Config:
        from_attributes = True
