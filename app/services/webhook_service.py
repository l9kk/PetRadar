import json
import hmac
import hashlib
import aiohttp
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.repository.webhook import WebhookRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.webhook_repo = WebhookRepository(db)

    async def send_webhook_notification(
        self, *, user_id: uuid.UUID, event_type: str, data: Dict[str, Any]
    ) -> int:
        webhooks = self.webhook_repo.get_user_webhooks(
            user_id=user_id, active_only=True
        )

        relevant_webhooks = [w for w in webhooks if event_type in w.event_types]

        success_count = 0
        for webhook in relevant_webhooks:
            if await self._send_notification(webhook, event_type, data):
                success_count += 1

        return success_count

    async def _send_notification(
        self, webhook, event_type: str, data: Dict[str, Any]
    ) -> bool:
        try:
            timestamp = datetime.utcnow().isoformat()
            payload = {"event_type": event_type, "timestamp": timestamp, "data": data}

            signature = self._generate_signature(webhook.secret, json.dumps(payload))
            payload["signature"] = signature

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                ) as response:
                    if response.status < 200 or response.status >= 300:
                        logger.warning(
                            f"Webhook delivery failed: {webhook.url}, status: {response.status}, "
                            f"response: {await response.text()}"
                        )
                        return False
                    return True

        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False

    def _generate_signature(self, secret: str, payload: str) -> str:
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
