import os
import secrets
from typing import Optional, Dict, Any, List, Union

from pydantic import validator, field_validator, model_validator
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    # Base settings
    APP_NAME: str = "PetRadar"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: Optional[PostgresDsn] = None

    # File storage
    UPLOADS_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: Optional[int] = 10

    # CORS
    ALLOWED_ORIGINS: Optional[str] = None

    # Email settings
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: Optional[bool] = True
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # CV Service settings
    CV_MODEL_PATH: str = "./app/cv/models"
    CV_DETECTION_THRESHOLD: float = 0.5
    CV_SIMILARITY_THRESHOLD: float = 0.6
    CV_MAX_IMAGE_SIZE_MB: int = 10
    CV_PROCESS_TIMEOUT_SECONDS: int = 30

    # Comparison component weights
    CV_WEIGHT_VISUAL: float = 0.6
    CV_WEIGHT_ATTRIBUTE: float = 0.2
    CV_WEIGHT_LOCATION: float = 0.1
    CV_WEIGHT_TIME: float = 0.1

    # Other settings
    DEFAULT_LANGUAGE: str = "ru"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",  # This allows extra fields in the .env file
    }

    @property
    def database_url_str(self) -> Optional[str]:
        """Return DATABASE_URL as a string for SQLAlchemy compatibility"""
        if self.DATABASE_URL:
            return str(self.DATABASE_URL)
        return None


settings = Settings()
