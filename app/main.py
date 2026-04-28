from fastapi import FastAPI
from app.core.database import Base, engine, SessionLocal
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, books, cart, wishlist, orders, admin_dashboard

app = FastAPI()

from fastapi.responses import HTMLResponse
from app.models.book import Book

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://picasso-publications.netlify.app",
        "https://www.picassopublications.com",
        "https://picassopublications.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(orders.router)
app.include_router(
    admin_dashboard.router,
    prefix="/admin",
    tags=["Admin Dashboard"]
)

Base.metadata.create_all(bind=engine)

# ✅ SEO SHARE ROUTE
@app.get("/seo/book/{book_id}", response_class=HTMLResponse)
def seo_book(book_id: int):

    db = SessionLocal()
    book = db.query(Book).filter(Book.id == book_id).first()

    if not book:
        return HTMLResponse("<h1>Book not found</h1>", status_code=404)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>{book.title}</title>

<meta property="og:title" content="{book.title}" />
<meta property="og:description" content="Buy {book.title} at ₹{book.price}" />
<meta property="og:image" content="{book.image}" />
<meta property="og:url" content="https://picassopublications.com/book/{book.id}" />
<meta property="og:type" content="product" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{book.title}" />
<meta name="twitter:description" content="Buy {book.title}" />
<meta name="twitter:image" content="{book.image}" />

<meta name="robots" content="index, follow">

</head>

<body>
<script>
window.location.replace("https://picassopublications.com/book/{book.id}");
</script>
</body>

</html>
"""

    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-cache",
            "X-Robots-Tag": "index, follow"
        }
    )