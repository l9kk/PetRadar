from typing import List, Optional, Dict, Any
from datetime import date
import uuid

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_

from app.models.found_pet import FoundPet
from app.schemas.found_pet import FoundPetCreate
from app.repository.base import BaseRepository


class FoundPetRepository(BaseRepository[FoundPet, FoundPetCreate, Any]):
    def __init__(self, db: Session):
        super().__init__(db, FoundPet)

    def get_with_details(self, found_pet_id: uuid.UUID) -> Optional[FoundPet]:
        return (
            self.db.query(FoundPet)
            .options(joinedload(FoundPet.finder))
            .filter(FoundPet.id == found_pet_id)
            .first()
        )

    def get_user_found_pets(
        self, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[FoundPet]:
        return (
            self.db.query(FoundPet)
            .filter(FoundPet.finder_id == user_id)
            .order_by(desc(FoundPet.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_found_pets(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        species: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[FoundPet]:
        query = self.db.query(FoundPet)

        if species:
            query = query.filter(FoundPet.species == species)

        if location:
            query = query.filter(FoundPet.location.ilike(f"%{location}%"))

        if date_from:
            query = query.filter(FoundPet.found_date >= date_from)

        if date_to:
            query = query.filter(FoundPet.found_date <= date_to)

        return query.order_by(desc(FoundPet.found_date)).offset(skip).limit(limit).all()

    def count_found_pets(
        self,
        *,
        species: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> int:
        query = self.db.query(func.count(FoundPet.id))

        if species:
            query = query.filter(FoundPet.species == species)

        if location:
            query = query.filter(FoundPet.location.ilike(f"%{location}%"))

        if date_from:
            query = query.filter(FoundPet.found_date >= date_from)

        if date_to:
            query = query.filter(FoundPet.found_date <= date_to)

        return query.scalar()

    def create_found_pet(
        self,
        *,
        obj_in: FoundPetCreate,
        finder_id: uuid.UUID,
        photo_url: str,
        photo_path: str,
        detected_attributes: Optional[Dict] = None,
        feature_vector: Optional[bytes] = None,
    ) -> FoundPet:
        db_obj = FoundPet(
            finder_id=finder_id,
            species=obj_in.species,
            photo_url=photo_url,
            photo_path=photo_path,
            description=obj_in.description,
            location=obj_in.location,
            found_date=obj_in.found_date,
            color=obj_in.color,
            distinctive_features=obj_in.distinctive_features,
            approximate_age=obj_in.approximate_age,
            size=obj_in.size,
            detected_attributes=detected_attributes,
            feature_vector=feature_vector,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_detected_attributes(
        self,
        *,
        found_pet_id: uuid.UUID,
        detected_attributes: Dict,
        feature_vector: Optional[bytes] = None,
    ) -> FoundPet:
        found_pet = self.get(id=found_pet_id)
        if not found_pet:
            raise ValueError("Found pet not found")

        found_pet.detected_attributes = detected_attributes
        if feature_vector:
            found_pet.feature_vector = feature_vector

        self.db.add(found_pet)
        self.db.commit()
        self.db.refresh(found_pet)
        return found_pet
