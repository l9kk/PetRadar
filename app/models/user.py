import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    email = sa.Column(sa.String, unique=True, index=True, nullable=False)
    password_hash = sa.Column(sa.String, nullable=False)
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    phone = sa.Column(sa.String, nullable=True)
    is_verified = sa.Column(sa.Boolean, default=False, nullable=False)
    language = sa.Column(sa.String, default="ru", nullable=False)

    # Relationships
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    found_pets = relationship(
        "FoundPet", back_populates="finder", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    webhooks = relationship(
        "Webhook", back_populates="user", cascade="all, delete-orphan"
    )
