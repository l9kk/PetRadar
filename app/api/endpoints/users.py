from typing import Any, List
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import verify_password
from app.repository.user import UserRepository
from app.repository.pet import PetRepository
from app.schemas.user import UserUpdate, User, UserProfile
from app.schemas.auth import ChangePassword, RequestEmailChange, EmailVerification
from app.schemas.pet import PetList
from app.models.user import User as UserModel
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    stats = user_repo.get_user_statistics(user_id=current_user.id)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
        "pets_count": stats["pets_count"],
        "lost_pets_count": stats["lost_pets_count"],
        "found_pets_count": stats["found_pets_count"],
    }


@router.patch("/me", response_model=User)
def update_user_info(
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    user_repo = UserRepository(db)
    return user_repo.update(db_obj=current_user, obj_in=user_in)


@router.post("/me/change-password", response_model=dict)
def change_password(
    password_data: ChangePassword,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный текущий пароль"
        )

    user_repo = UserRepository(db)
    user_repo.update_password(
        user_id=current_user.id, new_password=password_data.new_password
    )

    return {"message": "Пароль успешно изменен"}


@router.post("/me/change-email/request", response_model=dict)
async def request_email_change(
    data: RequestEmailChange,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль"
        )

    user_repo = UserRepository(db)
    if user_repo.get_by_email(email=data.new_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот email уже используется другим пользователем",
        )

    verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])

    from app.core.config import settings

    metadata = {"new_email": data.new_email}
    user_repo.store_verification_code(
        user_id=current_user.id,
        code=verification_code,
        expires_minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES,
        metadata=metadata,
    )

    notification_service = NotificationService(db)
    await notification_service.send_email_change_verification(
        user_id=current_user.id,
        new_email=data.new_email,
        verification_code=verification_code,
    )

    return {"message": "Код подтверждения отправлен на новый адрес электронной почты"}


@router.post("/me/change-email/confirm", response_model=dict)
def confirm_email_change(
    verification: EmailVerification,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    user_repo = UserRepository(db)
    verification_record = user_repo.verify_code(
        user_id=current_user.id, code=verification.verification_code
    )

    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный код подтверждения"
        )

    if user_repo.is_verification_code_expired(
        user_id=current_user.id, code=verification.verification_code
    ):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Срок действия кода истек",
        )

    new_email = verification_record.metadata.get("new_email")
    if not new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствует информация о новой электронной почте",
        )

    user_repo.update_email(user_id=current_user.id, new_email=new_email)

    user_repo.invalidate_verification_code(
        user_id=current_user.id, code=verification.verification_code
    )

    return {"message": "Адрес электронной почты успешно обновлен"}


@router.get("/me/pets", response_model=List[PetList])
def get_user_pets(
    status: str = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)
    return pet_repo.get_user_pets(user_id=current_user.id, status=status)
