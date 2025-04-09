from typing import Any
from pydantic import UUID4

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.repository.notification import NotificationRepository
from app.schemas.notification import Notification, NotificationUpdate, NotificationList

router = APIRouter()


@router.get("", response_model=NotificationList)
def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_read: bool = None,
    type: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    notification_repo = NotificationRepository(db)

    skip = (page - 1) * limit

    notifications = notification_repo.get_user_notifications(
        user_id=current_user.id, skip=skip, limit=limit, is_read=is_read, type=type
    )

    total = notification_repo.count_user_notifications(
        user_id=current_user.id, is_read=is_read, type=type
    )

    unread_count = notification_repo.count_user_notifications(
        user_id=current_user.id, is_read=False
    )

    pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "items": notifications,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "unread_count": unread_count,
    }


@router.patch("/{notification_id}", response_model=Notification)
def mark_notification_as_read(
    notification_id: UUID4 = Path(...),
    notification_in: NotificationUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    notification_repo = NotificationRepository(db)

    notification = notification_repo.get(id=notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено"
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    return notification_repo.mark_as_read(notification_id=notification_id)


@router.patch("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    notification_repo = NotificationRepository(db)

    count = notification_repo.mark_all_as_read(user_id=current_user.id)

    return {"message": "Все уведомления отмечены как прочитанные", "count": count}
