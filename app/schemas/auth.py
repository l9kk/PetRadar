from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class Login(BaseModel):
    username: str
    password: str


class RefreshToken(BaseModel):
    refresh_token: str


class EmailVerification(BaseModel):
    verification_code: str
    new_email: Optional[EmailStr] = None


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ForgotPassword(BaseModel):
    email: EmailStr


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class RequestEmailChange(BaseModel):
    new_email: EmailStr
    password: str
