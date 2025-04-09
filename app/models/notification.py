import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from app.models.base import BaseModel


class Notification(BaseModel):
    user_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False)
    type = sa.Column(sa.String, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    message = sa.Column(sa.Text, nullable=False)
    data = sa.Column(JSON, nullable=True)
    is_read = sa.Column(sa.Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
