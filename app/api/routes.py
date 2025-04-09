from fastapi import APIRouter

from app.api.endpoints import auth, users, pets, found_pets, cv, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(found_pets.router, prefix="/found-pets", tags=["found-pets"])
api_router.include_router(cv.router, prefix="/cv", tags=["cv"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
