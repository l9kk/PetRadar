from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class BaseModel(Base):
    """Base model for all database models"""

    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = sa.Column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
