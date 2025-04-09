import sqlalchemy as sa
from sqlalchemy.orm import relationship
from datetime import date

from app.models.base import BaseModel


class Pet(BaseModel):
    owner_id = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False
    )
    name = sa.Column(sa.String, nullable=False)
    species = sa.Column(sa.String, nullable=False)
    breed = sa.Column(sa.String, nullable=True)
    color = sa.Column(sa.String, nullable=True)
    age = sa.Column(sa.Integer, nullable=True)
    gender = sa.Column(sa.String, nullable=True)
    status = sa.Column(
        sa.String, default="normal", nullable=False
    )  # normal, lost, found
    lost_date = sa.Column(sa.Date, nullable=True)
    lost_location = sa.Column(sa.String, nullable=True)
    lost_description = sa.Column(sa.Text, nullable=True)
    description = sa.Column(sa.Text, nullable=True)
    microchipped = sa.Column(sa.Boolean, default=False, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="pets")
    photos = relationship(
        "PetPhoto", back_populates="pet", cascade="all, delete-orphan"
    )
    matches = relationship(
        "Match", back_populates="lost_pet", cascade="all, delete-orphan"
    )
