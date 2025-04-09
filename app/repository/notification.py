from typing import List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.repository.base import BaseRepository


class NotificationRepository(
    BaseRepository[Notification, NotificationCreate, NotificationUpdate]
):
    def __init__(self, db: Session):
        super().__init__(db, Notification)

    def get_user_notifications(
        self,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        is_read: Optional[bool] = None,
        type: Optional[str] = None,
    ) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if type:
            query = query.filter(Notification.type == type)

        return (
            query.order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_user_notifications(
        self,
        *,
        user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        type: Optional[str] = None,
    ) -> int:
        query = self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        )

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if type:
            query = query.filter(Notification.type == type)

        return query.scalar()

    def mark_as_read(self, *, notification_id: uuid.UUID) -> Optional[Notification]:
        notification = self.get(id=notification_id)
        if not notification:
            return None

        notification.is_read = True
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, *, user_id: uuid.UUID) -> int:
        result = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({Notification.is_read: True})
        )

        self.db.commit()
        return result
