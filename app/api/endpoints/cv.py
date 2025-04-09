import os
import logging
from typing import Any, Dict, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Body,
    Query,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.services.cv_service import CVService
from app.repository.pet import PetPhotoRepository
from app.repository.found_pet import FoundPetRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
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


@router.post("/compare-images")
async def compare_images(
    request_data: Dict = Body(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        source_image_id = request_data.get("source_image_id")
        target_image_ids = request_data.get("target_image_ids", [])
        filters = request_data.get("filters", {})
        feature_weights = request_data.get("feature_weights")

        if not source_image_id or not target_image_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Необходимо указать source_image_id и target_image_ids",
            )

        photo_repo = PetPhotoRepository(db)
        source_photo = photo_repo.get(id=source_image_id)

        if not source_photo or not source_photo.feature_vector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Исходное изображение не найдено или не обработано",
            )

        target_photos = []
        target_features = []
        target_attributes = []

        for id in target_image_ids:
            photo = photo_repo.get(id=id)
            if photo and photo.feature_vector:
                target_photos.append(photo)
                target_features.append(photo.feature_vector)
                target_attributes.append(photo.detected_attributes)

        if not target_features:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Целевые изображения не найдены или не обработаны",
            )

        location_data = None
        if "location_radius_km" in filters:
            location_data = {
                "source": None,
                "targets": [],
            }

        date_data = None
        if "lost_date_range" in filters:
            date_data = {
                "source": None,
                "targets": [],
            }

        cv_service = CVService()
        result = cv_service.compare_images(
            source_features=source_photo.feature_vector,
            target_features_list=target_features,
            source_attrs=source_photo.detected_attributes,
            target_attrs_list=target_attributes,
            location_data=location_data,
            date_data=date_data,
            feature_weights=feature_weights,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in compare_images: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}",
        )


@router.get("/find-matches/{pet_photo_id}")
async def find_matches(
    pet_photo_id: str,
    species: str = Query(None, description="Species filter (e.g., cat, dog)"),
    max_results: int = Query(
        10, ge=1, le=50, description="Maximum number of results to return"
    ),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        photo_repo = PetPhotoRepository(db)
        source_photo = photo_repo.get(id=pet_photo_id)

        if not source_photo or not source_photo.feature_vector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Исходное изображение не найдено или не обработано",
            )

        is_lost_pet = source_photo.pet.status == "lost" if source_photo.pet else False

        if is_lost_pet:
            found_pet_repo = FoundPetRepository(db)

            candidates = found_pet_repo.get_found_pets(
                species=species or source_photo.detected_attributes.get("species"),
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

        else:
            pet_repo = PetRepository(db)
            species_filter = species or source_photo.detected_attributes.get("species")
            candidates = pet_repo.get_lost_pets(species=species_filter, limit=100)

            target_features = []
            for pet in candidates:
                main_photo = photo_repo.get_main_photo(pet_id=pet.id)
                if main_photo and main_photo.feature_vector:
                    target_features.append(
                        (
                            str(pet.id),
                            main_photo.feature_vector,
                            main_photo.detected_attributes or {},
                        )
                    )

        if not target_features:
            return {
                "comparisons": [],
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
            result["comparisons"] = result["comparisons"][:max_results]

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in find_matches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}",
        )
