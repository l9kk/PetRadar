from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid

from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookUpdate
from app.repository.base import BaseRepository


class WebhookRepository(BaseRepository[Webhook, WebhookCreate, WebhookUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, Webhook)

    def get_user_webhooks(
        self, *, user_id: uuid.UUID, active_only: bool = True
    ) -> List[Webhook]:
        query = self.db.query(Webhook).filter(Webhook.user_id == user_id)

        if active_only:
            query = query.filter(Webhook.is_active == True)

        return query.order_by(desc(Webhook.created_at)).all()

    def create_webhook(self, *, user_id: uuid.UUID, obj_in: WebhookCreate) -> Webhook:
        db_obj = Webhook(
            user_id=user_id,
            url=obj_in.url,
            event_types=obj_in.event_types,
            secret=obj_in.secret,
            is_active=True,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def deactivate_webhook(self, *, webhook_id: uuid.UUID) -> Optional[Webhook]:
        webhook = self.get(id=webhook_id)
        if not webhook:
            return None

        webhook.is_active = False
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        return webhook
