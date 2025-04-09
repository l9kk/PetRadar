import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON, BYTEA
from datetime import date

from app.models.base import BaseModel


class FoundPet(BaseModel):
    finder_id = sa.Column(
        sa.UUID(as_uuid=True), sa.ForeignKey("user.id"), nullable=False
    )
    species = sa.Column(sa.String, nullable=False)
    photo_url = sa.Column(sa.String, nullable=False)
    photo_path = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    location = sa.Column(sa.String, nullable=False)
    found_date = sa.Column(sa.Date, nullable=False)
    color = sa.Column(sa.String, nullable=True)
    distinctive_features = sa.Column(sa.Text, nullable=True)
    approximate_age = sa.Column(sa.String, nullable=True)
    size = sa.Column(sa.String, nullable=True)
    feature_vector = sa.Column(BYTEA, nullable=True)
    detected_attributes = sa.Column(JSON, nullable=True)

    # Relationships
    finder = relationship("User", back_populates="found_pets")
    matches = relationship(
        "Match", back_populates="found_pet", cascade="all, delete-orphan"
    )
