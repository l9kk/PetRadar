from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl


class WebhookBase(BaseModel):
    url: HttpUrl
    event_types: List[str]


class WebhookCreate(WebhookBase):
    secret: str


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    event_types: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None


class Webhook(WebhookBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True


class WebhookNotificationBase(BaseModel):
    event_type: str
    timestamp: str
    data: Dict[str, Any]


class WebhookNotification(WebhookNotificationBase):
    signature: str
