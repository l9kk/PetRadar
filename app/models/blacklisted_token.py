import sqlalchemy as sa

from app.models.base import BaseModel


class BlacklistedToken(BaseModel):
    token_hash = sa.Column(sa.String, nullable=False, index=True, unique=True)
    expires_at = sa.Column(sa.DateTime, nullable=False)
