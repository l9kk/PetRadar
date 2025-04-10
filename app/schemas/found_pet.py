from typing import List, Optional, Dict
from datetime import date, datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class FinderInfo(BaseSchema):
    id: UUID
    first_name: str
    last_name: str


class PotentialMatch(BaseSchema):
    pet_id: UUID
    name: str
    similarity: float
    photo_url: Optional[str] = None
    lost_date: Optional[date] = None


class FoundPetBase(BaseSchema):
    species: str
    description: Optional[str] = None
    location: str
    found_date: date
    color: Optional[str] = None
    distinctive_features: Optional[str] = None
    approximate_age: Optional[str] = None
    size: Optional[str] = None


class FoundPetCreate(FoundPetBase):
    pass


class FoundPetInDBBase(FoundPetBase):
    id: UUID
    finder_id: UUID
    photo_url: str
    photo_path: str
    created_at: datetime


class FoundPet(FoundPetInDBBase):
    finder: Optional[FinderInfo] = None
    detected_attributes: Optional[Dict] = None
    potential_matches: Optional[List[PotentialMatch]] = None


class FoundPetList(BaseSchema):
    id: UUID
    photo_url: str
    species: str
    location: str
    found_date: date
    finder: FinderInfo
    created_at: datetime


class FoundPetListResponse(BaseSchema):
    items: List[FoundPetList]
    total: int
    page: int
    limit: int
    pages: int
