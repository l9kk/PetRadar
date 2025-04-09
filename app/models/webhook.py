import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import BaseModel


class Webhook(BaseModel):
    user_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False)
    url = sa.Column(sa.String, nullable=False)
    event_types = sa.Column(ARRAY(sa.String), nullable=False)
    secret = sa.Column(sa.String, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="webhooks")
