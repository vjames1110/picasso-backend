from fastapi import FastAPI
from app.core.database import Base, engine, SessionLocal
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, books, cart, wishlist, orders, admin_dashboard

from fastapi.responses import HTMLResponse
from app.models.book import Book

app = FastAPI()

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


# ✅ HEALTH CHECK (for uptime robot)
@app.get("/")
def health():
    return {"status": "ok"}


# ✅ SEO SHARE ROUTE (FIXED DB LEAK)
@app.get("/seo/book/{book_id}", response_class=HTMLResponse)
def seo_book(book_id: int):

    db = SessionLocal()
    try:
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
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:type" content="product" />

<script>
if(!window.location.search.includes("redirected=true")){{
window.location.href =
"https://picassopublications.com/book/{book.id}?redirected=true";
}}
</script>

</head>
<body>
Redirecting...
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

    finally:
        db.close()