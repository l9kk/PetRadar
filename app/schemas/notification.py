from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class NotificationBase(BaseModel):
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class Notification(NotificationBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: bool


class NotificationList(BaseModel):
    items: List[Notification]
    total: int
    page: int
    limit: int
    pages: int
    unread_count: int
