from fastapi import APIRouter, Depends, HTTPException, status
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
    book = db.query(Book).filter(
        Book.id == data.book_id,
        Book.is_active == True
    ).first()

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    if book.stock < 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book is out of stock")
    
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

    rows = (
        db.query(Cart, Book)
        .join(Book, Book.id == Cart.book_id)
        .filter(Cart.user_id == user.id, Book.is_active == True)
        .order_by(Cart.id.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "book_id": item.book_id,
            "quantity": item.quantity,
            "title": book.title,
            "price": book.price,
            "originalPrice": book.original_price,
            "image": book.image,
            "stock": book.stock
        }
        for item, book in rows
    ]


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    book = db.query(Book).filter(
        Book.id == item.book_id,
        Book.is_active == True
    ).first()

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    if book.stock < 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book is out of stock")

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

    item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == user.id
    ).first()

    # ---- FIX: prevent None delete crash ----
    if not item:
        return {"message": "Item already removed"}

    db.delete(item)
    db.commit()

    return {"message": "Removed"}
