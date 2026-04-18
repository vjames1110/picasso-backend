from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import SECRET_KEY, ALGORITHM
from app.models.user import User

security = HTTPBearer()


def get_current_user(
        token=Depends(security),
        db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401)

    except JWTError:
        raise HTTPException(status_code=401)

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401)

    return user


ADMIN_EMAILS = ["picasso.india10@gmail.com"]


def get_current_admin_user(current_user=Depends(get_current_user)):
    """
    Admin-only dependency.
    Reuses existing JWT auth without modifying core logic.
    """

    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )
    return current_user