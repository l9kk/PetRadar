from typing import List, Optional, Dict
from datetime import date, datetime
from pydantic import BaseModel


class MatchPetInfo(BaseModel):
    id: str
    name: str
    species: str
    breed: Optional[str] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None

    class Config:
        from_attributes = True


class MatchFoundPetInfo(BaseModel):
    id: str
    photo_url: str
    location: str
    found_date: date
    finder: Dict

    class Config:
        from_attributes = True


class MatchOwnerInfo(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    similarity: float

    class Config:
        from_attributes = True


class MatchDetail(MatchBase):
    id: str
    similarity: float
    created_at: str
    status: str
    lost_pet: MatchPetInfo
    found_pet: MatchFoundPetInfo
    pet_owner: MatchOwnerInfo
    matching_features: Optional[List[str]] = None

    class Config:
        from_attributes = True


class MatchStatusUpdate(BaseModel):
    status: str


class MatchResponse(BaseModel):
    id: str
    status: str
    confirmation_date: Optional[datetime] = None
    updated_at: str
