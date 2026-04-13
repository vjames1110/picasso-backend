from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.deps import get_current_user
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


# Add to wishlist
@router.post("/")
def add_to_wishlist(data: WishlistCreate, 
                    db: Session = Depends(get_db),
                    user = Depends(get_current_user)):

    item = Wishlist(
        user_id=user.id,
        book_id=data.book_id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# Get wishlist
@router.get("/")
def get_wishlist(db: Session = Depends(get_db),
                 user = Depends(get_current_user)):

    items = db.query(Wishlist).filter(Wishlist.user_id == user.id).all()

    return items


# Remove from wishlist
@router.delete("/{wishlist_id}")
def remove_wishlist(wishlist_id: int, 
                    db: Session = Depends(get_db),
                    user = Depends(get_current_user)):

    item = db.query(Wishlist).filter(Wishlist.id == wishlist_id,
                                     Wishlist.user_id == user.id).first()

    db.delete(item)
    db.commit()

    return {"message": "Removed"}