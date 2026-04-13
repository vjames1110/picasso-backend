from pydantic import BaseModel, EmailStr

class SendOTP(BaseModel):
    email: EmailStr


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str


class AddressUpdate(BaseModel):
    name: str
    email: str
    phone: str
    pincode: str
    house: str
    area: str
    city: str
    state: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    phone: str
    

    class Config:
        from_attributes = True