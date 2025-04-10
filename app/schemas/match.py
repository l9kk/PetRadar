from typing import List, Optional, Dict
from datetime import date, datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class MatchPetInfo(BaseSchema):
    id: UUID
    name: str
    species: str
    breed: Optional[str] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None


class MatchFoundPetInfo(BaseSchema):
    id: UUID
    photo_url: str
    location: str
    found_date: date
    finder: Dict


class MatchOwnerInfo(BaseSchema):
    id: UUID
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: str


class MatchBase(BaseSchema):
    similarity: float


class MatchDetail(MatchBase):
    id: UUID
    similarity: float
    created_at: datetime
    status: str
    lost_pet: MatchPetInfo
    found_pet: MatchFoundPetInfo
    pet_owner: MatchOwnerInfo
    matching_features: Optional[List[str]] = None


class MatchStatusUpdate(BaseSchema):
    status: str


class MatchResponse(BaseSchema):
    id: UUID
    status: str
    confirmation_date: Optional[datetime] = None
    updated_at: datetime
