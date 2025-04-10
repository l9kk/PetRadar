from typing import Optional, Dict, Any
import uuid

from sqlalchemy.orm import Session

from app.repository.notification import NotificationRepository
from app.repository.user import UserRepository
from app.repository.pet import PetRepository
from app.schemas.notification import NotificationCreate
from app.models.match import Match
from app.models.pet import Pet
from app.services.email_service import EmailService
from app.services.webhook_service import WebhookService


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_repo = NotificationRepository(db)
        self.user_repo = UserRepository(db)
        self.pet_repo = PetRepository(db)
        self.email_service = EmailService()
        self.webhook_service = WebhookService(db)

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        send_email: bool = False,
    ):
        notification_data = NotificationCreate(
            user_id=str(user_id),
            type=type,
            title=title,
            message=message,
            data=data or {},
        )
        notification = self.notification_repo.create(obj_in=notification_data)

        if send_email:
            user = self.user_repo.get(id=user_id)
            if user and user.email:
                email_methods = {
                    "pet_lost_confirmation": self.email_service.send_pet_lost_confirmation,
                    "match_found": self.email_service.send_match_found_notification,
                    "match_confirmed": self.email_service.send_match_confirmed_notification,
                }

                if type in email_methods:
                    await email_methods[type](
                        to_email=user.email,
                        user_name=f"{user.first_name} {user.last_name}",
                        **data,
                    )

        return notification

    async def create_pet_lost_notification(self, *, pet):
        user = self.user_repo.get(id=pet.owner_id)
        if not user:
            return False

        notification = await self.create_notification(
            user_id=pet.owner_id,
            type="pet_lost_confirmation",
            title="Питомец отмечен как потерянный",
            message=f"Ваш питомец {pet.name} отмечен как потерянный. Мы начнем поиск совпадений.",
            data={
                "pet_id": str(pet.id),
                "pet_name": pet.name,
                "lost_date": pet.lost_date.isoformat() if pet.lost_date else None,
                "lost_location": pet.lost_location,
            },
        )

        if user.email:
            await self.email_service.send_pet_lost_confirmation(
                to_email=user.email,
                user_name=f"{user.first_name} {user.last_name}",
                pet_name=pet.name,
                lost_date=(
                    pet.lost_date.strftime("%d.%m.%Y")
                    if pet.lost_date
                    else "Не указана"
                ),
                lost_location=pet.lost_location or "Не указано",
            )

        return True

    async def create_match_found_notification(self, *, match):
        pet = self.pet_repo.get_with_details(pet_id=match.lost_pet_id)
        if not pet:
            return False

        user = self.user_repo.get(id=pet.owner_id)
        if not user:
            return False

        notification = await self.create_notification(
            user_id=pet.owner_id,
            type="match_found",
            title="Найдено возможное совпадение",
            message=f"Мы нашли питомца, похожего на вашего {pet.name}, с вероятностью {match.similarity:.0%}",
            data={
                "match_id": str(match.id),
                "pet_id": str(pet.id),
                "pet_name": pet.name,
                "similarity": match.similarity,
                "found_pet_id": str(match.found_pet_id),
            },
        )

        if user.email:
            await self.email_service.send_match_found_notification(
                to_email=user.email,
                user_name=f"{user.first_name} {user.last_name}",
                pet_name=pet.name,
                similarity=match.similarity,
                match_id=str(match.id),
            )

        if user:
            await self.trigger_webhook_notification(
                user_id=pet.owner_id,
                event_type="match_found",
                data={
                    "match_id": str(match.id),
                    "pet_id": str(pet.id),
                    "found_pet_id": str(match.found_pet_id),
                    "similarity": match.similarity,
                },
            )

        return True

    async def create_match_confirmed_notification(self, *, match):
        found_pet = self.db.query(match.found_pet).first()
        if not found_pet:
            return False

        finder = self.user_repo.get(id=found_pet.finder_id)
        if not finder:
            return False

        lost_pet = self.pet_repo.get(id=match.lost_pet_id)
        if not lost_pet:
            return False

        notification = await self.create_notification(
            user_id=found_pet.finder_id,
            type="match_confirmed",
            title="Подтверждено совпадение",
            message="Владелец подтвердил, что найденный вами питомец - это их пропавший питомец",
            data={
                "match_id": str(match.id),
                "found_pet_id": str(found_pet.id),
                "lost_pet_id": str(match.lost_pet_id),
            },
        )

        if finder.email:
            pet_details = {
                "name": lost_pet.name,
                "species": lost_pet.species,
                "breed": lost_pet.breed,
                "lost_date": (
                    lost_pet.lost_date.strftime("%d.%m.%Y")
                    if lost_pet.lost_date
                    else "Не указана"
                ),
            }

            await self.email_service.send_match_confirmed_notification(
                to_email=finder.email,
                user_name=f"{finder.first_name} {finder.last_name}",
                pet_details=pet_details,
            )

        if finder:
            await self.trigger_webhook_notification(
                user_id=found_pet.finder_id,
                event_type="match_confirmed",
                data={
                    "match_id": str(match.id),
                    "lost_pet_id": str(match.lost_pet_id),
                    "found_pet_id": str(found_pet.id),
                },
            )

        return True

    async def create_image_processed_notification(
        self, *, photo_id: uuid.UUID, pet_id: uuid.UUID, user_id: uuid.UUID
    ):
        await self.create_notification(
            user_id=user_id,
            type="image_processed",
            title="Изображение обработано",
            message="Ваше изображение было успешно проанализировано нашей системой",
            data={"photo_id": str(photo_id), "pet_id": str(pet_id)},
        )

        return True

    async def send_verification_email(
        self, *, user_id: uuid.UUID, verification_code: str
    ):
        user = self.user_repo.get(id=user_id)
        if not user or not user.email:
            return False

        return await self.email_service.send_verification_email(
            to_email=user.email,
            verification_code=verification_code,
            user_name=f"{user.first_name} {user.last_name}",
        )

    async def send_password_reset_email(self, *, email: str, reset_token: str):
        user = self.user_repo.get_by_email(email=email)
        if not user:
            return False

        return await self.email_service.send_password_reset_email(
            to_email=email,
            reset_token=reset_token,
            user_name=f"{user.first_name} {user.last_name}",
        )

    async def send_email_change_verification(
        self, *, user_id: uuid.UUID, new_email: str, verification_code: str
    ):
        user = self.user_repo.get(id=user_id)
        if not user:
            return False

        return await self.email_service.send_email_change_verification(
            to_email=new_email,
            verification_code=verification_code,
            user_name=f"{user.first_name} {user.last_name}",
        )

    async def trigger_webhook_notification(
        self, *, user_id: uuid.UUID, event_type: str, data: Dict[str, Any]
    ) -> int:
        """Send a webhook notification to the user's registered webhook endpoints.

        Args:
            user_id: The ID of the user to send notifications to
            event_type: The type of event (match_found, pet_lost, etc.)
            data: Data payload to include in the notification

        Returns:
            The number of successfully delivered webhook notifications
        """
        return await self.webhook_service.send_webhook_notification(
            user_id=user_id, event_type=event_type, data=data
        )
