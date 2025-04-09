from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class PetPhotoBase(BaseModel):
    is_main: bool = False
    description: Optional[str] = None


class PetPhotoCreate(PetPhotoBase):
    pass


class PetPhotoUpdate(PetPhotoBase):
    is_main: Optional[bool] = None


class PetPhotoInDB(PetPhotoBase):
    id: str
    pet_id: str
    url: str
    is_main: bool
    image_processing_status: str
    created_at: str

    class Config:
        from_attributes = True


class PetPhoto(PetPhotoInDB):
    detected_attributes: Optional[dict] = None


class PetBase(BaseModel):
    name: str
    species: str
    breed: Optional[str] = None
    color: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    microchipped: bool = False


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    color: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    microchipped: Optional[bool] = None


class PetStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(normal|lost|found)$")
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None
    lost_description: Optional[str] = None


class PetOwner(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class PetInDBBase(PetBase):
    id: str
    owner_id: str
    status: str
    lost_date: Optional[date] = None
    lost_location: Optional[str] = None
    lost_description: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class Pet(PetInDBBase):
    owner: Optional[PetOwner] = None
    photos: Optional[List[PetPhoto]] = None


class PetList(BaseModel):
    id: str
    name: str
    species: str
    breed: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    lost_date: Optional[date] = None

    class Config:
        from_attributes = True


class PetListResponse(BaseModel):
    items: List[PetList]
