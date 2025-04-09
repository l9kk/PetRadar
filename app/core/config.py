import os
import secrets
import logging

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, field_validator


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
    DATABASE_URL: PostgresDsn

    # File storage
    UPLOADS_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # CORS
    ALLOWED_ORIGINS: str = ""

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v):
        return v.split(",") if v else []

    # Email settings
    SMTP_SERVER: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    EMAILS_FROM_EMAIL: str
    EMAILS_FROM_NAME: str

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
        "extra": "ignore",
        "case_sensitive": False,
    }

    @property
    def database_url_str(self) -> str:
        return str(self.DATABASE_URL)


settings = Settings()
