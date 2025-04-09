from typing import Any, List, Optional
from pydantic import UUID4

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_verified_user
from app.models.user import User
from app.repository.match import MatchRepository
from app.services.notification_service import NotificationService
from app.schemas.match import MatchDetail, MatchStatusUpdate, MatchResponse

router = APIRouter()


@router.get("/{match_id}", response_model=MatchDetail)
async def get_match(
    match_id: UUID4 = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    match_repo = MatchRepository(db)

    match = match_repo.get_with_details(match_id=match_id)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Совпадение не найдено"
        )

    if (
        match.lost_pet.owner_id != current_user.id
        and match.found_pet.finder_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    return match


@router.patch("/{match_id}/status", response_model=MatchResponse)
async def update_match_status(
    status_in: MatchStatusUpdate,
    match_id: UUID4 = Path(...),  # Updated to use UUID4 validation
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    match_repo = MatchRepository(db)

    match = match_repo.get_with_details(match_id=match_id)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Совпадение не найдено"
        )

    if match.lost_pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец питомца может подтвердить совпадение",
        )

    if status_in.status not in ["confirmed", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный статус. Допустимые значения: confirmed, rejected",
        )

    updated_match = match_repo.update_match_status(
        match_id=match_id, status=status_in.status
    )

    if status_in.status == "confirmed":
        notification_service = NotificationService(db)
        await notification_service.create_match_confirmed_notification(
            match=updated_match
        )

    return updated_match


@router.get("/mine", response_model=List[MatchDetail])
async def get_user_matches(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    match_repo = MatchRepository(db)
    skip = (page - 1) * limit

    matches = match_repo.get_user_matches(
        user_id=current_user.id, status=status, skip=skip, limit=limit
    )

    return matches


@router.get("/finder", response_model=List[MatchDetail])
async def get_finder_matches(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    match_repo = MatchRepository(db)
    skip = (page - 1) * limit

    matches = match_repo.get_finder_matches(
        user_id=current_user.id, status=status, skip=skip, limit=limit
    )

    return matches
