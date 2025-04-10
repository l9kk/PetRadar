from typing import Optional
from pydantic import EmailStr, Field
from uuid import UUID
from datetime import datetime

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str


class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)


class UserInDBBase(UserBase):
    id: UUID
    email: EmailStr
    is_verified: bool
    created_at: datetime


class User(UserInDBBase):
    pass


class UserProfile(User):
    pets_count: int = 0
    lost_pets_count: int = 0
    found_pets_count: int = 0


class UserInDB(UserInDBBase):
    password_hash: str
