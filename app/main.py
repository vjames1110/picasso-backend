from fastapi import FastAPI
from app.core.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, books, cart, wishlist, orders, admin_dashboard

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://picasso-publications.netlify.app",
        "https://www.picassopublications.com",
        "https://picassopublications.com/"
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