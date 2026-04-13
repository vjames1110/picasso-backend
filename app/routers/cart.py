from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cart import Cart
from app.schemas.cart import CartCreate, CartUpdate
from app.services.deps import get_current_user
from app.models.book import Book

router = APIRouter(prefix="/cart", tags=["Cart"])


# Add to cart
@router.post("/")
def add_to_cart(data: CartCreate,
                db: Session = Depends(get_db),
                user = Depends(get_current_user)):
    
    # Check Book
    book = db.query(Book).filter(Book.id == data.book_id).first()

    if not book:
        return {"error": "Book Not Found"}
    
    # Check existing cart item

    existing = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.book_id == data.book_id
    ).first()

    # Stock Validation

    qty = data.quantity

    if qty > book.stock:
        qty = book.stock

    if existing:
        existing.quantity = min(existing.quantity + qty, book.stock)
        db.commit()
        db.refresh(existing)
        return existing

    item = Cart(
        user_id=user.id,
        book_id=data.book_id,
        quantity=qty
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# Get cart
@router.get("/")
def get_cart(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    items = db.query(Cart).filter(
        Cart.user_id == user.id
    ).all()

    result = []

    for item in items:
        book = db.query(Book).filter(
            Book.id == item.book_id
        ).first()

        result.append({
            "id": item.id,
            "book_id": item.book_id,
            "quantity": item.quantity,
            "title": book.title,
            "price": book.price,
            "originalPrice": book.original_price,
            "image": book.image,
            "stock": book.stock
        })

    return result


# Update cart
@router.put("/{cart_id}")
def update_cart(
    cart_id: int,
    data: CartUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == user.id
    ).first()

    if not item:
        return {"error": "Item not found"}

    book = db.query(Book).filter(
        Book.id == item.book_id
    ).first()

    qty = data.quantity

    if qty > book.stock:
        qty = book.stock

    item.quantity = qty

    db.commit()
    db.refresh(item)

    return item


# Remove cart item
@router.delete("/{cart_id}")
def remove_cart(cart_id: int, 
                db: Session = Depends(get_db),
                user = Depends(get_current_user)):

    item = db.query(Cart).filter(Cart.id == cart_id,
                                 Cart.user_id == user.id).first()

    db.delete(item)
    db.commit()

    return {"message": "Removed"}