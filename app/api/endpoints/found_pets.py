from typing import Any, Optional
from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    File,
    UploadFile,
    Form,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.repository.found_pet import FoundPetRepository
from app.services.pets_service import PetsService
from app.schemas.found_pet import (
    FoundPetCreate,
    FoundPet,
    FoundPetList,
    FoundPetListResponse,
)

router = APIRouter()


@router.post("", response_model=FoundPet, status_code=status.HTTP_201_CREATED)
async def report_found_pet(
    species: str = Form(...),
    location: str = Form(...),
    found_date: date = Form(...),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    distinctive_features: Optional[str] = Form(None),
    approximate_age: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    if not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением",
        )

    found_pet_in = FoundPetCreate(
        species=species,
        description=description,
        location=location,
        found_date=found_date,
        color=color,
        distinctive_features=distinctive_features,
        approximate_age=approximate_age,
        size=size,
    )

    pets_service = PetsService(db)
    found_pet = await pets_service.report_found_pet(
        finder_id=current_user.id,
        found_pet_in=found_pet_in,
        file=photo,
        background_tasks=background_tasks,
    )

    return found_pet


@router.get("", response_model=FoundPetListResponse)
def get_found_pets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    species: Optional[str] = None,
    location: Optional[str] = None,
    radius: Optional[float] = None,
    found_date_from: Optional[date] = None,
    found_date_to: Optional[date] = None,
    db: Session = Depends(get_db),
) -> Any:
    found_pet_repo = FoundPetRepository(db)

    skip = (page - 1) * limit

    found_pets = found_pet_repo.get_found_pets(
        skip=skip,
        limit=limit,
        species=species,
        location=location,
        date_from=found_date_from,
        date_to=found_date_to,
    )

    total = found_pet_repo.count_found_pets(
        species=species,
        location=location,
        date_from=found_date_from,
        date_to=found_date_to,
    )

    pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "items": found_pets,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/{found_pet_id}", response_model=FoundPet)
def get_found_pet(found_pet_id: UUID, db: Session = Depends(get_db)) -> Any:
    found_pet_repo = FoundPetRepository(db)
    found_pet = found_pet_repo.get_with_details(found_pet_id=found_pet_id)

    if not found_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Найденный питомец не найден"
        )

    return found_pet
