from typing import Any, List, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.repository.webhook import WebhookRepository
from app.schemas.webhook import WebhookCreate, Webhook, WebhookNotification

router = APIRouter()


@router.post("", response_model=Webhook, status_code=status.HTTP_201_CREATED)
async def register_webhook(
    webhook_in: WebhookCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    if not webhook_in.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL must start with http:// or https://",
        )

    valid_event_types = [
        "match_found",
        "image_processed",
        "pet_lost",
        "match_confirmed",
    ]
    for event_type in webhook_in.event_types:
        if event_type not in valid_event_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}. Valid types are: {', '.join(valid_event_types)}",
            )

    webhook_repo = WebhookRepository(db)
    webhook = webhook_repo.create_webhook(user_id=current_user.id, obj_in=webhook_in)

    return webhook


@router.get("", response_model=List[Webhook])
async def get_webhooks(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    webhook_repo = WebhookRepository(db)
    return webhook_repo.get_user_webhooks(user_id=current_user.id)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> None:
    webhook_repo = WebhookRepository(db)
    webhook = webhook_repo.get(id=webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )

    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this webhook",
        )

    webhook_repo.deactivate_webhook(webhook_id=webhook_id)
    return None
