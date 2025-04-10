from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import json
import logging
from datetime import datetime
from uuid import UUID

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import get_db, Base, engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info(f"Starting {settings.APP_NAME} API")
logger.info(
    f"Database URL: {str(settings.DATABASE_URL).replace('://', '://***:***@') if settings.DATABASE_URL else 'Not set'}"
)

try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


app = FastAPI(
    title=settings.APP_NAME,
    json_encoder=CustomJSONEncoder,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": f"Welcome to {settings.APP_NAME} API", "status": "online"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "app_name": settings.APP_NAME,
    }


if __name__ == "__main__":
    import uvicorn

    try:
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting server on port: {port}")
        uvicorn.run("app.main:app", host="0.0.0.0", port=port)
    except ValueError as e:
        logger.error(f"Error parsing PORT value: {os.environ.get('PORT')}")
        logger.info("Using default port 8000 instead")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
