from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import SendOTP, VerifyOTP, UserResponse, AddressUpdate
from app.services.otp import send_email_otp, generate_otp, verify_otp
from app.services.auth import create_access_token
from app.services.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/send-otp")
def send_otp(data: SendOTP):
    otp = generate_otp(data.email)
    # In a real application, you would send the OTP via SMS here
    return {"message": "OTP sent to email",
            "otp": otp}  # For testing purposes, we return the OTP in the response

@router.post("/verify-otp")
def verify(data: VerifyOTP, db: Session = Depends(get_db)):
    is_valid = verify_otp(data.email, data.otp)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        user = User(email=data.email, phone=None, is_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"user_id": user.id})

    return {
        "message": "Login Successful",
        "token": token,
        "user_id": user.id
    }

@router.get("/me")
def get_me(user=Depends(get_current_user)):
    return {"id": user.id,
            "phone": user.phone}

@router.put("/address")
def update_address(
    data: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    user.name = data.name
    user.phone = data.phone
    user.email = data.email
    user.pincode = data.pincode
    user.house = data.house
    user.area = data.area
    user.city = data.city
    user.state = data.state

    db.commit()
    db.refresh(user)

    return {"message": "Address saved"}

@router.get("/address")
def get_address(user: User = Depends(get_current_user)):

    if not user.house:
        return {"has_address": False}

    return {
        "has_address": True,
        "address": {
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "pincode": user.pincode,
            "house": user.house,
            "area": user.area,
            "city": user.city,
            "state": user.state
        }
    }