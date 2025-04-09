from typing import List, Optional, Dict
from datetime import date
import uuid

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.pet import Pet
from app.models.pet_photo import PetPhoto
from app.schemas.pet import PetCreate, PetUpdate, PetStatusUpdate, PetPhotoCreate
from app.repository.base import BaseRepository


class PetRepository(BaseRepository[Pet, PetCreate, PetUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, Pet)

    def get_with_details(self, pet_id: uuid.UUID) -> Optional[Pet]:
        return (
            self.db.query(Pet)
            .options(joinedload(Pet.owner), joinedload(Pet.photos))
            .filter(Pet.id == pet_id)
            .first()
        )

    def get_user_pets(
        self,
        *,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Pet]:
        query = self.db.query(Pet).filter(Pet.owner_id == user_id)
        if status:
            query = query.filter(Pet.status == status)
        return query.order_by(desc(Pet.created_at)).offset(skip).limit(limit).all()

    def get_lost_pets(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        species: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Pet]:
        query = self.db.query(Pet).filter(Pet.status == "lost")

        if species:
            query = query.filter(Pet.species == species)

        if location:
            query = query.filter(Pet.lost_location.ilike(f"%{location}%"))

        if date_from:
            query = query.filter(Pet.lost_date >= date_from)

        if date_to:
            query = query.filter(Pet.lost_date <= date_to)

        return query.order_by(desc(Pet.lost_date)).offset(skip).limit(limit).all()

    def update_status(
        self, *, pet_id: uuid.UUID, status_data: PetStatusUpdate
    ) -> Optional[Pet]:
        pet = self.get(id=pet_id)
        if not pet:
            return None

        update_data = status_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pet, field, value)

        self.db.add(pet)
        self.db.commit()
        self.db.refresh(pet)
        return pet

    def count_lost_pets(
        self,
        *,
        species: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> int:
        query = self.db.query(func.count(Pet.id)).filter(Pet.status == "lost")

        if species:
            query = query.filter(Pet.species == species)

        if location:
            query = query.filter(Pet.lost_location.ilike(f"%{location}%"))

        if date_from:
            query = query.filter(Pet.lost_date >= date_from)

        if date_to:
            query = query.filter(Pet.lost_date <= date_to)

        return query.scalar()


class PetPhotoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, pet_id: uuid.UUID, obj_in: PetPhotoCreate, url: str, path: str
    ) -> PetPhoto:
        if obj_in.is_main:
            self.db.query(PetPhoto).filter(
                PetPhoto.pet_id == pet_id, PetPhoto.is_main == True
            ).update({PetPhoto.is_main: False})

        db_obj = PetPhoto(
            pet_id=pet_id,
            url=url,
            path=path,
            is_main=obj_in.is_main,
            description=obj_in.description,
            image_processing_status="pending",
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, *, id: uuid.UUID) -> Optional[PetPhoto]:
        return self.db.query(PetPhoto).filter(PetPhoto.id == id).first()

    def get_pet_photos(self, *, pet_id: uuid.UUID) -> List[PetPhoto]:
        return self.db.query(PetPhoto).filter(PetPhoto.pet_id == pet_id).all()

    def get_main_photo(self, *, pet_id: uuid.UUID) -> Optional[PetPhoto]:
        return (
            self.db.query(PetPhoto)
            .filter(PetPhoto.pet_id == pet_id, PetPhoto.is_main == True)
            .first()
        )

    def update_processing_status(
        self,
        *,
        photo_id: uuid.UUID,
        status: str,
        detected_attributes: Optional[Dict] = None,
        feature_vector: Optional[bytes] = None,
    ) -> PetPhoto:
        photo = self.get(id=photo_id)
        if not photo:
            raise ValueError("Photo not found")

        photo.image_processing_status = status
        if detected_attributes:
            photo.detected_attributes = detected_attributes
        if feature_vector:
            photo.feature_vector = feature_vector

        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return photo
