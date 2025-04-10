from typing import Any, Optional, Dict, List
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
    Body,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.repository.found_pet import FoundPetRepository
from app.repository.pet import PetRepository, PetPhotoRepository
from app.services.pets_service import PetsService
from app.services.cv_service import CVService
from app.schemas.found_pet import (
    FoundPetCreate,
    FoundPet,
    FoundPetList,
    FoundPetListResponse,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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

    # Validate image size
    max_size_mb = getattr(settings, "CV_MAX_IMAGE_SIZE_MB", 10)
    max_size_bytes = max_size_mb * 1024 * 1024

    photo.file.seek(0, 2)
    file_size = photo.file.tell()
    photo.file.seek(0)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Размер изображения превышает {max_size_mb} MB",
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
    pet_photo_id: Optional[str] = Query(
        None, description="Lost pet photo ID to find matches for"
    ),
    max_results: int = Query(
        20, ge=1, le=50, description="Maximum number of matched results to return"
    ),
    db: Session = Depends(get_db),
) -> Any:
    if pet_photo_id:
        try:
            photo_repo = PetPhotoRepository(db)
            source_photo = photo_repo.get(id=pet_photo_id)

            if not source_photo or not source_photo.feature_vector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Исходное изображение не найдено или не обработано",
                )

            is_lost_pet = (
                source_photo.pet.status == "lost" if source_photo.pet else False
            )
            if not is_lost_pet:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Исходное изображение должно быть от потерянного питомца",
                )

            found_pet_repo = FoundPetRepository(db)
            candidates = found_pet_repo.get_found_pets(
                species=species or source_photo.detected_attributes.get("species"),
                location=location,
                date_from=found_date_from,
                date_to=found_date_to,
                limit=100,
            )

            target_features = []
            for candidate in candidates:
                if candidate.feature_vector:
                    target_features.append(
                        (
                            str(candidate.id),
                            candidate.feature_vector,
                            candidate.detected_attributes or {},
                        )
                    )

            if not target_features:
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "pages": 1,
                    "search_metadata": {
                        "source_id": pet_photo_id,
                        "total_candidates_considered": 0,
                        "filtered_candidates": 0,
                        "message": "Не найдено подходящих кандидатов для сравнения",
                    },
                }

            cv_service = CVService()
            result = cv_service.find_potential_matches(
                pet_photo_id=pet_photo_id,
                feature_vector=source_photo.feature_vector,
                attributes=source_photo.detected_attributes or {},
                target_features=target_features,
            )

            if "comparisons" in result:
                matched_ids = [
                    match["id"] for match in result["comparisons"][:max_results]
                ]
                matched_pets = []

                for pet_id in matched_ids:
                    pet = found_pet_repo.get_with_details(found_pet_id=UUID(pet_id))
                    if pet:
                        matched_pets.append(pet)

                return {
                    "items": matched_pets,
                    "total": len(matched_pets),
                    "page": 1,
                    "limit": max_results,
                    "pages": 1,
                    "search_metadata": {
                        "source_id": pet_photo_id,
                        "total_candidates_considered": result.get(
                            "search_metadata", {}
                        ).get("total_candidates_considered", 0),
                        "match_details": result.get("comparisons", []),
                    },
                }

            return {
                "items": [],
                "total": 0,
                "page": 1,
                "limit": max_results,
                "pages": 1,
                "search_metadata": result.get("search_metadata", {}),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exception in find_matches: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}",
            )

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
def get_found_pet(
    found_pet_id: UUID,
    compare_with: Optional[str] = Query(
        None, description="Pet photo ID to compare with"
    ),
    db: Session = Depends(get_db),
) -> Any:
    found_pet_repo = FoundPetRepository(db)
    found_pet = found_pet_repo.get_with_details(found_pet_id=found_pet_id)

    if not found_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Найденный питомец не найден"
        )

    if compare_with:
        try:
            photo_repo = PetPhotoRepository(db)
            source_photo = photo_repo.get(id=compare_with)

            if not source_photo or not source_photo.feature_vector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Исходное изображение для сравнения не найдено или не обработано",
                )

            if not found_pet.feature_vector:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У найденного питомца отсутствуют данные для сравнения",
                )

            cv_service = CVService()
            comparison = cv_service.compare_images(
                source_features=source_photo.feature_vector,
                target_features_list=[found_pet.feature_vector],
                source_attrs=source_photo.detected_attributes or {},
                target_attrs_list=[found_pet.detected_attributes or {}],
                location_data=None,
                date_data=None,
                feature_weights=None,
            )

            # Add comparison data to the response
            found_pet_dict = found_pet.dict()
            found_pet_dict["comparison"] = comparison.get("comparisons", [{}])[0]
            return found_pet_dict

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exception in compare_images: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}",
            )

    return found_pet


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Analyze a pet image to detect species, features and attributes.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением",
        )

    max_size_mb = getattr(settings, "CV_MAX_IMAGE_SIZE_MB", 10)
    max_size_bytes = max_size_mb * 1024 * 1024

    image.file.seek(0, 2)
    file_size = image.file.tell()
    image.file.seek(0)

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Размер изображения превышает {max_size_mb} MB",
        )

    cv_service = CVService()

    try:
        result = cv_service.analyze_image_content(image.file)

        if "error" in result:
            logger.error(f"Error analyzing image: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Ошибка обработки изображения: {result['error']}",
            )

        return result
    except Exception as e:
        logger.error(f"Exception in analyze_image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}",
        )
