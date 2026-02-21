from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserInDBBase(UserBase):
    uuid: UUID4

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
