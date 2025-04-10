from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class NotificationBase(BaseSchema):
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False


class NotificationCreate(BaseSchema):
    user_id: UUID
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class Notification(NotificationBase):
    id: UUID
    created_at: datetime


class NotificationUpdate(BaseSchema):
    is_read: bool


class NotificationList(BaseSchema):
    items: List[Notification]
    total: int
    page: int
    limit: int
    pages: int
    unread_count: int
