from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class PetPhotoBase(BaseSchema):
    is_main: bool = False
    description: Optional[str] = None


class PetPhotoCreate(PetPhotoBase):
    pass


class PetPhotoUpdate(PetPhotoBase):
    is_main: Optional[bool] = None


class PetPhotoInDB(PetPhotoBase):
    id: UUID
    pet_id: UUID
    url: str
    is_main: bool
    image_processing_status: str
    created_at: datetime


class PetPhoto(PetPhotoInDB):
    detected_attributes: Optional[dict] = None


class PetBase(BaseSchema):
    name: str
    species: str
    breed: Optional[str] = None
    color: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    microchipped: bool = False


class PetCreate(PetBase):
    status: str = "normal"  # Default status is "normal" (not lost)
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None
    lost_description: Optional[str] = None


class PetUpdate(BaseSchema):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    color: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    microchipped: Optional[bool] = None


class PetStatusUpdate(BaseSchema):
    status: str
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None
    lost_description: Optional[str] = None


class PetOwner(BaseSchema):
    id: UUID
    first_name: str
    last_name: str
    phone: Optional[str] = None


class PetInDBBase(PetBase):
    id: UUID
    owner_id: UUID
    status: str
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None
    lost_description: Optional[str] = None
    created_at: datetime


class Pet(PetInDBBase):
    owner: Optional[PetOwner] = None
    photos: Optional[List[PetPhoto]] = None


class PetList(BaseSchema):
    id: UUID
    name: str
    species: str
    breed: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    lost_date: Optional[date] = None


class PetListResponse(BaseSchema):
    items: List[PetList]
    total: int
    page: int
    limit: int
    pages: int
