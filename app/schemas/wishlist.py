from pydantic import BaseModel


class WishlistCreate(BaseModel):
    book_id: int


class WishlistResponse(BaseModel):
    id: int
    book_id: int

    class Config:
        from_attributes = True