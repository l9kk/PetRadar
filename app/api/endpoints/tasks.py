from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Path

from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_verified_user
from app.models.user import User
from app.services.pets_service import PetsService

router = APIRouter()


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str = Path(..., title="ID of the background task"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the status of a background task
    """
    pets_service = PetsService(db)
    task_status = pets_service.get_background_task_status(task_id)

    if task_status["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )

    return task_status


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def cancel_task(
    task_id: str = Path(..., title="ID of the background task to cancel"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Cancel a running background task if possible
    """
    pets_service = PetsService(db)

    # Check if task exists and is running
    task_status = pets_service.get_background_task_status(task_id)
    if task_status["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )

    if task_status["status"] != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Задача не может быть отменена (текущий статус: {task_status['status']})",
        )

    # Try to cancel the task
    success = pets_service.cancel_background_task(task_id)

    if success:
        return {"message": "Задача успешно отменена", "task_id": task_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отменить задачу",
        )
