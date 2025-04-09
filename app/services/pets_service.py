import os
import aiofiles
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import uuid
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from fastapi import UploadFile, BackgroundTasks

from app.core.config import settings
from app.repository.pet import PetRepository, PetPhotoRepository
from app.repository.found_pet import FoundPetRepository
from app.repository.match import MatchRepository
from app.schemas.pet import PetCreate, PetUpdate, PetStatusUpdate, PetPhotoCreate
from app.schemas.found_pet import FoundPetCreate
from app.cv.pet_finder import SimplePetFinder
from app.services.notification_service import NotificationService
from app.services.cv_service import CVService

# Set up logging
logger = logging.getLogger(__name__)

# Thread pool for background processing
_thread_pool = ThreadPoolExecutor(max_workers=5)
# Map to track running background tasks
_background_tasks = {}


class PetsService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.photo_repo = PetPhotoRepository(db)
        self.found_pet_repo = FoundPetRepository(db)
        self.match_repo = MatchRepository(db)
        self.pet_finder = SimplePetFinder()
        self.notification_service = NotificationService(db)
        self.cv_service = CVService()

        os.makedirs(os.path.join(settings.UPLOADS_DIR, "pets"), exist_ok=True)
        os.makedirs(os.path.join(settings.UPLOADS_DIR, "found_pets"), exist_ok=True)

    async def create_pet(self, owner_id: uuid.UUID, pet_in: PetCreate):
        return self.pet_repo.create(obj_in=pet_in, owner_id=owner_id)

    async def update_pet(self, pet_id: uuid.UUID, pet_in: PetUpdate):
        pet = self.pet_repo.get(id=pet_id)
        if not pet:
            return None
        return self.pet_repo.update(db_obj=pet, obj_in=pet_in)

    async def update_pet_status(self, pet_id: uuid.UUID, status_in: PetStatusUpdate):
        return self.pet_repo.update_status(pet_id=pet_id, status_data=status_in)

    async def upload_pet_photo(
        self,
        pet_id: uuid.UUID,
        file: UploadFile,
        is_main: bool = False,
        description: Optional[str] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join("pets", filename)
        absolute_path = os.path.join(settings.UPLOADS_DIR, file_path)

        async with aiofiles.open(absolute_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        photo_in = PetPhotoCreate(is_main=is_main, description=description)
        photo_url = f"/uploads/{file_path}"

        photo = self.photo_repo.create(
            pet_id=pet_id, obj_in=photo_in, url=photo_url, path=absolute_path
        )

        if background_tasks:
            logger.info(f"Scheduling background processing for photo {photo.id}")
            background_tasks.add_task(
                self.process_pet_photo_background, str(photo.id), absolute_path
            )
        else:
            logger.info(f"Running synchronous processing for photo {photo.id}")
            self._process_pet_photo(photo.id, absolute_path)

        return photo

    async def process_pet_photo_background(self, photo_id: str, file_path: str):
        task_id = f"proc_photo_{photo_id}"
        try:
            logger.info(f"Starting background processing of photo {photo_id}")
            _background_tasks[task_id] = {
                "status": "running",
                "started_at": time.time(),
            }

            photo_id_uuid = uuid.UUID(photo_id)

            self.photo_repo.update_processing_status(
                photo_id=photo_id_uuid, status="processing"
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                _thread_pool, self._process_pet_photo, photo_id_uuid, file_path
            )

            logger.info(f"Completed background processing of photo {photo_id}")
            _background_tasks[task_id]["status"] = "completed"

        except Exception as e:
            logger.error(
                f"Error in background processing of photo {photo_id}: {str(e)}",
                exc_info=True,
            )
            self.photo_repo.update_processing_status(
                photo_id=uuid.UUID(photo_id), status="failed"
            )
            _background_tasks[task_id] = {"status": "failed", "error": str(e)}

    def _process_pet_photo(self, photo_id: uuid.UUID, file_path: str):
        try:
            self.photo_repo.update_processing_status(
                photo_id=photo_id, status="processing"
            )

            cropped_pet, pet_class, attributes = self.pet_finder.detect_pet(file_path)
            if cropped_pet is None:
                self.photo_repo.update_processing_status(
                    photo_id=photo_id, status="failed"
                )
                return

            feature_vector = self.pet_finder.extract_features(cropped_pet)
            feature_bytes = (
                feature_vector.tobytes() if feature_vector is not None else None
            )

            self.photo_repo.update_processing_status(
                photo_id=photo_id,
                status="completed",
                detected_attributes=attributes,
                feature_vector=feature_bytes,
            )

        except Exception as e:
            logger.error(f"Error processing photo {photo_id}: {str(e)}", exc_info=True)
            self.photo_repo.update_processing_status(photo_id=photo_id, status="failed")

    def _process_photo_task(
        self, photo_id: uuid.UUID, file_path: str
    ) -> Dict[str, Any]:
        """
        Worker function to process a photo - runs in a separate thread

        Args:
            photo_id: UUID of the photo
            file_path: Path to the image file

        Returns:
            Dictionary with processing results
        """
        try:
            # Use the CV service to analyze the image instead of direct pet_finder usage
            result = self.cv_service.analyze_image(file_path)

            if "error" in result or not result.get("detected_animals"):
                logger.warning(f"No animals detected or error in photo {photo_id}")
                self.photo_repo.update_processing_status(
                    photo_id=photo_id, status="failed"
                )
                return {
                    "success": False,
                    "reason": "No animals detected or analysis error",
                }

            animal = result["detected_animals"][0]
            attributes = animal["attributes"]

            cropped_pet, pet_class, _ = self.pet_finder.detect_pet(file_path)
            feature_bytes = None

            if cropped_pet is not None:
                feature_vector = self.pet_finder.extract_features(cropped_pet)
                if feature_vector is not None:
                    feature_bytes = feature_vector.tobytes()

                self.photo_repo.update_processing_status(
                    photo_id=photo_id,
                    status="completed",
                    detected_attributes=attributes,
                    feature_vector=feature_bytes,
                )

                return {
                    "success": True,
                    "species": animal["species"],
                    "attributes": attributes,
                }
            else:
                self.photo_repo.update_processing_status(
                    photo_id=photo_id, status="failed"
                )
                return {"success": False, "reason": "Could not crop pet from image"}

        except Exception as e:
            logger.error(f"Error processing photo {photo_id}: {str(e)}", exc_info=True)
            self.photo_repo.update_processing_status(photo_id=photo_id, status="failed")
            return {"success": False, "error": str(e)}

    async def report_found_pet(
        self,
        finder_id: uuid.UUID,
        found_pet_in: FoundPetCreate,
        file: UploadFile,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join("found_pets", filename)
        absolute_path = os.path.join(settings.UPLOADS_DIR, file_path)

        async with aiofiles.open(absolute_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        cropped_pet, pet_class, attributes = self.pet_finder.detect_pet(absolute_path)

        feature_bytes = None
        if cropped_pet is not None:
            feature_vector = self.pet_finder.extract_features(cropped_pet)
            feature_bytes = (
                feature_vector.tobytes() if feature_vector is not None else None
            )

        photo_url = f"/uploads/{file_path}"
        found_pet = self.found_pet_repo.create_found_pet(
            obj_in=found_pet_in,
            finder_id=finder_id,
            photo_url=photo_url,
            photo_path=absolute_path,
            detected_attributes=attributes,
            feature_vector=feature_bytes,
        )

        if cropped_pet is not None and feature_bytes is not None:
            if background_tasks:
                logger.info(
                    f"Scheduling background match finding for found pet {found_pet.id}"
                )
                background_tasks.add_task(
                    self.find_matches_for_found_pet_background, str(found_pet.id)
                )
            else:
                logger.info(
                    f"Running synchronous match finding for found pet {found_pet.id}"
                )
                self._find_matches_for_found_pet(found_pet.id)

        return found_pet

    async def find_matches_for_found_pet_background(self, found_pet_id: str):
        task_id = f"find_matches_{found_pet_id}"
        try:
            logger.info(
                f"Starting background match finding for found pet {found_pet_id}"
            )
            _background_tasks[task_id] = {
                "status": "running",
                "started_at": time.time(),
            }

            found_pet_id_uuid = uuid.UUID(found_pet_id)

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                _thread_pool, self._find_matches_for_found_pet, found_pet_id_uuid
            )

            logger.info(
                f"Found {len(matches)} potential matches for found pet {found_pet_id}"
            )
            _background_tasks[task_id] = {
                "status": "completed",
                "matches_count": len(matches),
                "completed_at": time.time(),
            }

            await self.notify_about_matches(found_pet_id_uuid, matches)

        except Exception as e:
            logger.error(
                f"Error finding matches for found pet {found_pet_id}: {str(e)}",
                exc_info=True,
            )
            _background_tasks[task_id] = {"status": "failed", "error": str(e)}

    def _find_matches_for_found_pet(
        self, found_pet_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Find potential matches for a found pet using the CV service
        """
        start_time = time.time()
        found_pet = self.found_pet_repo.get(id=found_pet_id)
        if not found_pet or not found_pet.feature_vector:
            logger.warning(
                f"Found pet {found_pet_id} not found or has no feature vector"
            )
            return []

        lost_pets = self.pet_repo.get_lost_pets(species=found_pet.species, limit=1000)

        target_features: List[Tuple[str, bytes, Dict]] = []
        for pet in lost_pets:
            photos = self.photo_repo.get_pet_photos(pet_id=pet.id)
            if not photos:
                continue

            main_photo = next((p for p in photos if p.is_main), photos[0])
            if not main_photo.feature_vector:
                continue

            target_features.append(
                (
                    str(pet.id),
                    main_photo.feature_vector,
                    main_photo.detected_attributes or {},
                )
            )

        if not target_features:
            logger.info(
                f"No potential matches found for pet {found_pet_id} - no suitable target features"
            )
            return []

        location_data = None
        if found_pet.location and any(
            pet.lost_location for pet in lost_pets if hasattr(pet, "lost_location")
        ):
            location_data = {
                "source": None,
                "targets": [],
            }

        date_data = None
        if found_pet.found_date:
            target_dates = []
            for pet in lost_pets:
                if hasattr(pet, "lost_date") and pet.lost_date:
                    target_dates.append(pet.lost_date)
                else:
                    target_dates.append(None)

            if any(target_dates):
                date_data = {"source": found_pet.found_date, "targets": target_dates}

        result = self.cv_service.find_potential_matches(
            pet_photo_id=str(found_pet_id),
            feature_vector=found_pet.feature_vector,
            attributes=found_pet.detected_attributes or {},
            target_features=target_features,
            location_data=location_data,
            date_data=date_data,
        )

        potential_matches = []
        for comp in result.get("comparisons", []):
            target_id = comp.get("target_id")
            if not target_id:
                continue

            pet = next((p for p in lost_pets if str(p.id) == target_id), None)
            if not pet:
                continue

            photos = self.photo_repo.get_pet_photos(pet_id=pet.id)
            if not photos:
                continue

            main_photo = next((p for p in photos if p.is_main), photos[0])

            potential_matches.append(
                {
                    "pet_id": pet.id,
                    "name": pet.name,
                    "similarity": comp["similarity"]["overall"],
                    "photo_url": main_photo.url if main_photo else None,
                    "lost_date": pet.lost_date,
                    "matching_features": comp.get("matching_features", []),
                }
            )

        logger.info(
            f"Found {len(potential_matches)} potential matches for found pet {found_pet_id} in {time.time() - start_time:.2f}s"
        )
        return potential_matches

    async def notify_about_matches(
        self, found_pet_id: uuid.UUID, matches: List[Dict[str, Any]]
    ):
        """
        Create notifications for potential matches

        Args:
            found_pet_id: ID of the found pet
            matches: List of potential matches
        """
        for match_data in matches:
            try:
                existing_match = self.match_repo.get_by_pet_ids(
                    lost_pet_id=match_data["pet_id"], found_pet_id=found_pet_id
                )

                if existing_match:
                    logger.info(
                        f"Match already exists between lost pet {match_data['pet_id']} and found pet {found_pet_id}"
                    )
                    continue

                match = self.match_repo.create_match(
                    lost_pet_id=match_data["pet_id"],
                    found_pet_id=found_pet_id,
                    similarity=match_data["similarity"],
                    matching_features=match_data.get("matching_features", []),
                )

                await self.notification_service.create_match_found_notification(
                    match=match
                )
                logger.info(
                    f"Created match notification for lost pet {match_data['pet_id']} and found pet {found_pet_id}"
                )

            except Exception as e:
                logger.error(
                    f"Error creating notification for match: {str(e)}", exc_info=True
                )

    def get_background_task_status(self, task_id: str) -> Dict[str, Any]:
        if task_id in _background_tasks:
            result = _background_tasks[task_id].copy()
            if "started_at" in result:
                end_time = result.get("completed_at", time.time())
                result["duration_seconds"] = end_time - result["started_at"]
            return result
        else:
            return {"status": "not_found"}

    def cancel_background_task(self, task_id: str) -> bool:
        if (
            task_id in _background_tasks
            and _background_tasks[task_id]["status"] == "running"
        ):
            try:
                _background_tasks[task_id]["status"] = "canceled"
                return True
            except Exception as e:
                logger.error(f"Error canceling task {task_id}: {str(e)}")
                return False
        return False
