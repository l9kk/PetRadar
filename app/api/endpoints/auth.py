from datetime import timedelta
from typing import Any
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.repository.user import UserRepository
from app.services.notification_service import NotificationService
from app.schemas.auth import (
    Token,
    RefreshToken,
    EmailVerification,
    PasswordReset,
    ForgotPassword,
)
from app.schemas.user import UserCreate, User
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/register", response_model=User)
async def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    user_repo = UserRepository(db)

    if user_repo.get_by_email(email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    user = user_repo.create(obj_in=user_in)

    verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])

    user_repo.store_verification_code(
        user_id=user.id,
        code=verification_code,
        expires_minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES,
    )

    notification_service = NotificationService(db)
    await notification_service.send_verification_email(
        user_id=user.id, verification_code=verification_code
    )

    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    user_repo = UserRepository(db)
    user = user_repo.authenticate(email=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    device_info = request.headers.get("User-Agent", "")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.id)

    user_repo.store_token(user_id=user.id, token=refresh_token, device_info=device_info)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    request: Request, refresh_token_data: RefreshToken, db: Session = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)

    try:
        from jose import jwt
        from app.core.security import TokenPayload

        if not user_repo.is_token_valid(refresh_token_data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный или отозванный refresh token",
            )

        payload = jwt.decode(
            refresh_token_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        token_data = TokenPayload(**payload)

        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный refresh token",
            )

        device_info = request.headers.get("User-Agent", "")

        user_repo.revoke_token(token=refresh_token_data.refresh_token)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            token_data.sub, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(token_data.sub)

        user_repo.store_token(
            user_id=token_data.sub, token=refresh_token, device_info=device_info
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh token",
        )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    email_in: ForgotPassword, db: Session = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email=email_in.email)

    if user:
        reset_token = secrets.token_urlsafe(32)

        user_repo.store_reset_token(
            user_id=user.id,
            token=reset_token,
            expires_minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES,
        )

        notification_service = NotificationService(db)
        await notification_service.send_password_reset_email(
            email=user.email, reset_token=reset_token
        )

    return {
        "message": "Если ваш адрес электронной почты зарегистрирован, вы получите ссылку для сброса пароля."
    }


@router.post("/reset-password", response_model=dict)
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)) -> Any:
    user_repo = UserRepository(db)

    user = user_repo.get_user_by_reset_token(token=reset_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный токен сброса пароля",
        )

    if user_repo.is_reset_token_expired(token=reset_data.token):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Срок действия токена истек",
        )

    user_repo.update_password(user_id=user.id, new_password=reset_data.new_password)

    user_repo.invalidate_reset_token(token=reset_data.token)

    return {"message": "Пароль успешно сброшен"}


@router.post("/request-verification-email", response_model=dict)
async def request_verification_email(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    if current_user.is_verified:
        return {"message": "Ваш адрес электронной почты уже подтвержден"}

    user_repo = UserRepository(db)

    verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])

    user_repo.store_verification_code(
        user_id=current_user.id,
        code=verification_code,
        expires_minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES,
    )

    notification_service = NotificationService(db)
    await notification_service.send_verification_email(
        user_id=current_user.id, verification_code=verification_code
    )

    return {"message": "На вашу электронную почту отправлен код подтверждения"}


@router.post("/verify-email", response_model=dict)
def verify_email(
    verification_data: EmailVerification,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if current_user.is_verified:
        return {"message": "Ваш адрес электронной почты уже подтвержден"}

    user_repo = UserRepository(db)

    is_valid = user_repo.verify_code(
        user_id=current_user.id, code=verification_data.verification_code
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код подтверждения",
        )

    if user_repo.is_verification_code_expired(
        user_id=current_user.id, code=verification_data.verification_code
    ):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Срок действия кода истек",
        )

    user_repo.mark_verified(user_id=current_user.id)

    user_repo.invalidate_verification_code(
        user_id=current_user.id, code=verification_data.verification_code
    )

    return {"message": "Электронная почта успешно подтверждена"}


@router.post("/logout", response_model=dict)
def logout(
    refresh_token_data: RefreshToken,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    user_repo = UserRepository(db)

    user_repo.revoke_token(token=refresh_token_data.refresh_token)

    user_repo.clean_expired_tokens()

    return {"message": "Вы успешно вышли из системы"}
