from typing import Any, Optional
from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    File,
    UploadFile,
    Form,
    Path,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from pydantic import UUID4

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.repository.pet import PetRepository
from app.services.pets_service import PetsService
from app.services.notification_service import NotificationService
from app.schemas.pet import (
    PetCreate,
    PetUpdate,
    PetStatusUpdate,
    Pet,
    PetListResponse,
    PetPhoto,
)

router = APIRouter()


@router.post("", response_model=Pet)
async def create_pet(
    pet_in: PetCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    pets_service = PetsService(db)
    return await pets_service.create_pet(owner_id=current_user.id, pet_in=pet_in)


@router.get("/lost", response_model=PetListResponse)
def get_lost_pets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    species: Optional[str] = None,
    location: Optional[str] = None,
    radius: Optional[float] = None,
    lost_date_from: Optional[date] = None,
    lost_date_to: Optional[date] = None,
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)

    skip = (page - 1) * limit

    pets = pet_repo.get_lost_pets(
        skip=skip,
        limit=limit,
        species=species,
        location=location,
        date_from=lost_date_from,
        date_to=lost_date_to,
    )

    total = pet_repo.count_lost_pets(
        species=species,
        location=location,
        date_from=lost_date_from,
        date_to=lost_date_to,
    )

    pages = (total + limit - 1) // limit

    return {"items": pets, "total": total, "page": page, "limit": limit, "pages": pages}


@router.get("/{pet_id}", response_model=Pet)
def get_pet(
    pet_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)
    pet = pet_repo.get_with_details(pet_id=pet_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Питомец не найден"
        )

    return pet


@router.patch("/{pet_id}", response_model=Pet)
async def update_pet(
    pet_in: PetUpdate,
    pet_id: UUID4 = Path(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)
    pet = pet_repo.get(id=pet_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Питомец не найден"
        )

    if pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    pets_service = PetsService(db)
    return await pets_service.update_pet(pet_id=pet_id, pet_in=pet_in)


@router.patch("/{pet_id}/status", response_model=Pet)
async def update_pet_status(
    status_in: PetStatusUpdate,
    pet_id: UUID4 = Path(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)
    pet = pet_repo.get(id=pet_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Питомец не найден"
        )

    if pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    pets_service = PetsService(db)
    updated_pet = await pets_service.update_pet_status(
        pet_id=pet_id, status_in=status_in
    )

    if status_in.status == "lost":
        notification_service = NotificationService(db)
        await notification_service.create_pet_lost_notification(pet=updated_pet)

    return updated_pet


@router.post(
    "/{pet_id}/photos", response_model=PetPhoto, status_code=status.HTTP_201_CREATED
)
async def upload_pet_photo(
    pet_id: UUID4 = Path(...),
    photo: UploadFile = File(...),
    is_main: bool = Form(False),
    description: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    pet_repo = PetRepository(db)
    pet = pet_repo.get(id=pet_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Питомец не найден"
        )

    if pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    if not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением",
        )

    pets_service = PetsService(db)
    return await pets_service.upload_pet_photo(
        pet_id=pet_id,
        file=photo,
        is_main=is_main,
        description=description,
        background_tasks=background_tasks,
    )
