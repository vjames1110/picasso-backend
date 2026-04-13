from jose import jwt, JWTError
from fastapi import Depends, HTTPException
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
            raise HTTPException(status_code = 401)
        
    except JWTError:
        raise HTTPException(status_code = 401)
    
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code = 401)
    
    return user

