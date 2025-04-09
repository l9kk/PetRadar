from typing import List, Optional, Dict
from datetime import date
from pydantic import BaseModel


class FinderInfo(BaseModel):
    id: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class PotentialMatch(BaseModel):
    pet_id: str
    name: str
    similarity: float
    photo_url: Optional[str] = None
    lost_date: Optional[date] = None


class FoundPetBase(BaseModel):
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
    id: str
    finder_id: str
    photo_url: str
    photo_path: str
    created_at: str

    class Config:
        from_attributes = True


class FoundPet(FoundPetInDBBase):
    finder: Optional[FinderInfo] = None
    detected_attributes: Optional[Dict] = None
    potential_matches: Optional[List[PotentialMatch]] = None


class FoundPetList(BaseModel):
    id: str
    photo_url: str
    species: str
    location: str
    found_date: date
    finder: FinderInfo
    created_at: str

    class Config:
        from_attributes = True


class FoundPetListResponse(BaseModel):
    items: List[FoundPetList]
    total: int
    page: int
    limit: int
    pages: int
