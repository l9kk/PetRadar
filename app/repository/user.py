from typing import Optional, Dict
import uuid
import hashlib
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.pet import Pet
from app.models.verification_code import VerificationCode
from app.models.reset_token import ResetToken
from app.models.token import ActiveToken
from app.schemas.user import UserCreate, UserUpdate
from app.repository.base import BaseRepository
from app.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            phone=obj_in.phone,
            is_verified=False,
            language=obj_in.language or "ru",
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def update_password(self, *, user_id: uuid.UUID, new_password: str) -> User:
        user = self.get(id=user_id)
        if not user:
            raise ValueError("User not found")
        user.password_hash = get_password_hash(new_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def mark_verified(self, *, user_id: uuid.UUID) -> User:
        user = self.get(id=user_id)
        if not user:
            raise ValueError("User not found")
        user.is_verified = True
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_statistics(self, *, user_id: uuid.UUID) -> Dict[str, int]:
        user = self.get(id=user_id)
        if not user:
            raise ValueError("User not found")

        pets_count = (
            self.db.query(func.count(Pet.id)).filter(Pet.owner_id == user_id).scalar()
        )
        lost_pets_count = (
            self.db.query(func.count(Pet.id))
            .filter(Pet.owner_id == user_id, Pet.status == "lost")
            .scalar()
        )
        found_pets_count = (
            self.db.query(func.count(Pet.id))
            .filter(Pet.owner_id == user_id, Pet.status == "found")
            .scalar()
        )

        return {
            "pets_count": pets_count,
            "lost_pets_count": lost_pets_count,
            "found_pets_count": found_pets_count,
        }

    def store_verification_code(
        self,
        *,
        user_id: uuid.UUID,
        code: str,
        expires_minutes: int,
        metadata: Dict = None,
    ) -> VerificationCode:
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        self.db.query(VerificationCode).filter(
            VerificationCode.user_id == user_id, VerificationCode.is_used == False
        ).update({"is_used": True})

        verification_code = VerificationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            is_used=False,
            metadata=metadata or {},
        )
        self.db.add(verification_code)
        self.db.commit()
        self.db.refresh(verification_code)
        return verification_code

    def verify_code(
        self, *, user_id: uuid.UUID, code: str
    ) -> Optional[VerificationCode]:
        verification_code = (
            self.db.query(VerificationCode)
            .filter(
                VerificationCode.user_id == user_id,
                VerificationCode.code == code,
                VerificationCode.is_used == False,
            )
            .first()
        )

        return verification_code

    def is_verification_code_expired(self, *, user_id: uuid.UUID, code: str) -> bool:
        verification_code = (
            self.db.query(VerificationCode)
            .filter(
                VerificationCode.user_id == user_id,
                VerificationCode.code == code,
                VerificationCode.is_used == False,
            )
            .first()
        )

        if not verification_code:
            return True

        return verification_code.is_expired

    def invalidate_verification_code(self, *, user_id: uuid.UUID, code: str) -> None:
        self.db.query(VerificationCode).filter(
            VerificationCode.user_id == user_id,
            VerificationCode.code == code,
        ).update({"is_used": True})
        self.db.commit()

    def delete_verification_code(self, *, user_id: uuid.UUID, code: str) -> None:
        self.db.query(VerificationCode).filter(
            VerificationCode.user_id == user_id,
            VerificationCode.code == code,
        ).delete()
        self.db.commit()

    def store_reset_token(
        self, *, user_id: uuid.UUID, token: str, expires_minutes: int
    ) -> ResetToken:
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        self.db.query(ResetToken).filter(
            ResetToken.user_id == user_id, ResetToken.is_used == False
        ).update({"is_used": True})

        reset_token = ResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_used=False,
        )
        self.db.add(reset_token)
        self.db.commit()
        self.db.refresh(reset_token)
        return reset_token

    def get_user_by_reset_token(self, *, token: str) -> Optional[User]:
        reset_token = (
            self.db.query(ResetToken)
            .filter(
                ResetToken.token == token,
                ResetToken.is_used == False,
            )
            .first()
        )

        if not reset_token:
            return None

        return self.get(id=reset_token.user_id)

    def is_reset_token_expired(self, *, token: str) -> bool:
        reset_token = (
            self.db.query(ResetToken)
            .filter(
                ResetToken.token == token,
                ResetToken.is_used == False,
            )
            .first()
        )

        if not reset_token:
            return True

        return reset_token.is_expired

    def invalidate_reset_token(self, *, token: str) -> None:
        self.db.query(ResetToken).filter(
            ResetToken.token == token,
        ).update({"is_used": True})
        self.db.commit()

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def store_token(
        self, *, user_id: uuid.UUID, token: str, device_info: str = None
    ) -> ActiveToken:
        from jose import jwt

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp", 0)
            expires_at = datetime.fromtimestamp(exp_timestamp)
        except Exception:
            expires_at = datetime.utcnow() + timedelta(days=7)

        token_hash = self._hash_token(token)

        active_token = ActiveToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
        )
        self.db.add(active_token)
        self.db.commit()
        self.db.refresh(active_token)
        return active_token

    def is_token_valid(self, token: str) -> bool:
        token_hash = self._hash_token(token)

        active_token = (
            self.db.query(ActiveToken)
            .filter(
                ActiveToken.token_hash == token_hash,
                ActiveToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

        return active_token is not None

    def revoke_token(self, token: str) -> bool:
        token_hash = self._hash_token(token)

        deleted = (
            self.db.query(ActiveToken)
            .filter(ActiveToken.token_hash == token_hash)
            .delete()
        )

        self.db.commit()
        return deleted > 0

    def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        result = (
            self.db.query(ActiveToken).filter(ActiveToken.user_id == user_id).delete()
        )

        self.db.commit()
        return result

    def clean_expired_tokens(self) -> int:
        now = datetime.utcnow()
        result = (
            self.db.query(ActiveToken).filter(ActiveToken.expires_at < now).delete()
        )
        self.db.commit()
        return result

    def update_email(self, *, user_id: uuid.UUID, new_email: str) -> User:
        user = self.get(id=user_id)
        if not user:
            raise ValueError("User not found")

        user.email = new_email
        user.is_verified = True

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
