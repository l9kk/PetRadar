from typing import Optional
from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema


class Token(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenPayload(BaseSchema):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class Login(BaseSchema):
    username: str
    password: str


class RefreshToken(BaseSchema):
    refresh_token: str


class EmailVerification(BaseSchema):
    verification_code: str
    new_email: Optional[EmailStr] = None


class PasswordReset(BaseSchema):
    token: str
    new_password: str = Field(..., min_length=8)


class ForgotPassword(BaseSchema):
    email: EmailStr


class ChangePassword(BaseSchema):
    current_password: str
    new_password: str = Field(..., min_length=8)


class RequestEmailChange(BaseSchema):
    new_email: EmailStr
    password: str
