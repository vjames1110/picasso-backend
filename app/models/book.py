from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from app.core.database import Base

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, index=True)
    description = Column(Text)

    price = Column(Float)
    original_price = Column(Float)
    image = Column(String)
    stock = Column(Integer, default=0)
    author = Column(ARRAY(String))
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)