import sqlalchemy as sa
from datetime import datetime

from app.models.base import BaseModel


class ResetToken(BaseModel):
    user_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False)
    token = sa.Column(sa.String, nullable=False, index=True, unique=True)
    expires_at = sa.Column(sa.DateTime, nullable=False)
    is_used = sa.Column(sa.Boolean, default=False, nullable=False)

    @property
    def is_expired(self) -> bool:
        """Check if the reset token has expired"""
        return datetime.utcnow() > self.expires_at
