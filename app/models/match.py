import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import date

from app.models.base import BaseModel


class Match(BaseModel):
    lost_pet_id = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("pet.id"), nullable=False
    )
    found_pet_id = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("foundpet.id"), nullable=False
    )
    similarity = sa.Column(sa.Float, nullable=False)
    status = sa.Column(
        sa.String, default="pending", nullable=False
    )  # pending, confirmed, rejected
    confirmation_date = sa.Column(sa.DateTime, nullable=True)
    matching_features = sa.Column(JSON, nullable=True)

    # Relationships
    lost_pet = relationship("Pet", back_populates="matches")
    found_pet = relationship("FoundPet", back_populates="matches")
