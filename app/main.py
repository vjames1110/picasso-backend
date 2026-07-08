import logging
from html import escape

from fastapi import FastAPI
from app.core.database import Base, engine, SessionLocal
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.routers import auth, books, cart, wishlist, orders, admin_dashboard

from fastapi.responses import HTMLResponse
from app.models.book import Book

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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

logger = logging.getLogger(__name__)


@app.on_event("startup")
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        logger.warning("Skipping database initialization on startup: %s", exc)


# ✅ HEALTH CHECK (for uptime robot)
@app.get("/")
def health():
    return {"status": "ok"}


# ✅ SEO SHARE ROUTE (FIXED DB LEAK)
@app.get("/seo/book/{book_id}", response_class=HTMLResponse)
def seo_book(book_id: int):

    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.id == book_id, Book.is_active == True).first()

        if not book:
            return HTMLResponse("<h1>Book not found</h1>", status_code=404)

        title = escape(book.title or "Picasso Publications", quote=True)
        image = escape(book.image or "", quote=True)
        html = f"""
<!DOCTYPE html>
<html>
<head>
<title>{title}</title>

<meta property="og:title" content="{title}" />
<meta property="og:description" content="Buy {title} at Rs. {book.price}" />
<meta property="og:image" content="{image}" />
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
