"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "healthcare_db"
    MODEL_PATH: str = "app/ml/model.joblib"
    LABEL_ENCODER_PATH: str = "app/ml/label_encoder.joblib"
    SYMPTOM_LIST_PATH: str = "app/ml/symptom_list.json"
    PORT: int = 8000
    APP_TITLE: str = "HealthGuard AI"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
