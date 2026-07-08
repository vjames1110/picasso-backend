from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import String, cast, or_, func

from app.core.database import get_db
from app.models.book import Book
from app.models.order import OrderItem
from app.schemas.book import BookCreate, BookResponse

router = APIRouter(prefix="/books", tags=["books"])


# ---------------- CREATE BOOK ----------------
@router.post("", response_model=BookResponse)
@router.post("/", response_model=BookResponse)
def create_book(data: BookCreate, db: Session = Depends(get_db)):

    book = Book(**data.dict())
    db.add(book)
    db.commit()
    db.refresh(book)

    return book


# ---------------- GET ALL BOOKS ----------------
@router.get("", response_model=list[BookResponse])
@router.get("/", response_model=list[BookResponse])
def get_books(
    search: str = Query(None),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    # IMPORTANT: only active books
    query = db.query(Book).filter(Book.is_active == True)

    # search filter
    if search:
        search_term = f"%{search.lower()}%"

        query = query.filter(
            or_(
                Book.title.ilike(search_term),
                Book.category.ilike(search_term),
                cast(Book.author, String).ilike(search_term)
            )
        )

    # category filter
    if category:
        query = query.filter(Book.category.ilike(f"%{category}%"))

    books = query.order_by(Book.created_at.desc(), Book.id.desc()).all()
    return books


# ---------------- TOP SELLING BOOKS ----------------
@router.get("/top-selling", response_model=list[BookResponse])
def get_top_selling_books(
    limit: int = Query(8, ge=1, le=24),
    db: Session = Depends(get_db)
):
    return (
        db.query(Book)
        .outerjoin(OrderItem, OrderItem.book_id == Book.id)
        .filter(Book.is_active == True)
        .group_by(Book.id)
        .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc(), Book.created_at.desc())
        .limit(limit)
        .all()
    )


# ---------------- GET SINGLE BOOK ----------------
@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):

    book = db.query(Book).filter(
        Book.id == book_id,
        Book.is_active == True
    ).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


# ---------------- UPDATE BOOK ----------------
@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, data: BookCreate, db: Session = Depends(get_db)):

    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404)

    for key, value in data.dict().items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)

    return book


# ---------------- DELETE BOOK (SOFT DELETE) ----------------
@router.delete("/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):

    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # SOFT DELETE
    book.is_active = False

    db.commit()

    return {"message": "Book deleted successfully"}
