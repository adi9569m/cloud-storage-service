"""Application configuration management using Pydantic Settings."""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General App Settings
    APP_NAME: str = "CloudStorageService"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS Origins (Comma-separated string in env or list of strings)
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # Database Configuration
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/cloud_storage"

    # JWT Authentication
    JWT_SECRET_KEY: str = "insecure-dev-secret-key-change-in-production-must-be-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Supabase Configuration
    SUPABASE_URL: str = "https://your-project-id.supabase.co"
    SUPABASE_SERVICE_KEY: str = "your-supabase-service-role-key"
    SUPABASE_STORAGE_BUCKET: str = "cloud-storage-bucket"

    # Storage Quotas & Limits
    DEFAULT_STORAGE_QUOTA_BYTES: int = 5368709120  # 5 GB
    MAX_BATCH_OPERATION_ITEMS: int = 100
    MAX_ZIP_DOWNLOAD_BYTES: int = 1073741824  # 1 GB
    MAX_PREVIEW_TEXT_BYTES: int = 1048576  # 1 MB

    # Maintenance & Security Settings
    AUTO_TRASH_PURGE_DAYS: int = 30
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10


settings = Settings()
