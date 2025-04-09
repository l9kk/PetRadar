import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON, BYTEA

from app.models.base import BaseModel


class PetPhoto(BaseModel):
    pet_id = sa.Column(sa.UUID(as_uuid=True), sa.ForeignKey("pet.id"), nullable=False)
    url = sa.Column(sa.String, nullable=False)
    path = sa.Column(sa.String, nullable=False)
    is_main = sa.Column(sa.Boolean, default=False, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    image_processing_status = sa.Column(
        sa.String, default="pending", nullable=False
    )  # pending, processing, completed, failed
    detected_attributes = sa.Column(JSON, nullable=True)
    feature_vector = sa.Column(BYTEA, nullable=True)

    # Relationships
    pet = relationship("Pet", back_populates="photos")
