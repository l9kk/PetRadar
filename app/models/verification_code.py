import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.models.base import BaseModel


class VerificationCode(BaseModel):
    user_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False)
    code = sa.Column(sa.String, nullable=False)
    expires_at = sa.Column(sa.DateTime, nullable=False)
    is_used = sa.Column(sa.Boolean, default=False, nullable=False)
    code_metadata = sa.Column(
        JSONB, default={}, nullable=False
    )  # Renamed from 'metadata' to 'code_metadata'

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
