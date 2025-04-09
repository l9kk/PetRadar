import sqlalchemy as sa
from datetime import datetime

from app.models.base import BaseModel


class ActiveToken(BaseModel):
    user_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False)
    token_hash = sa.Column(sa.String, nullable=False, index=True, unique=True)
    expires_at = sa.Column(sa.DateTime, nullable=False)
    device_info = sa.Column(sa.String, nullable=True)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
