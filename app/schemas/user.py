from pydantic import BaseModel, EmailStr, Field

class SendOTP(BaseModel):
    email: EmailStr


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str


class AddressUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    pincode: str = Field(pattern=r"^\d{6}$")
    house: str = Field(min_length=1, max_length=160)
    area: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)

class UserResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    phone: str
    

    class Config:
        from_attributes = True
