from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "menu.tn"
    APP_VERSION: str = "1.0.0"
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://menutn:menutn_secret@localhost:5432/menutn_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth / JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Storage
    STORAGE_PROVIDER: Literal["local", "s3", "r2"] = "local"
    STORAGE_BUCKET: str = "menutn-assets"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "auto"
    S3_ENDPOINT_URL: str = ""
    CDN_BASE_URL: str = "http://localhost:8000/static"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@menu.tn"

    # Plan limits
    FREE_PLAN_MAX_PRODUCTS: int = 10
    PREMIUM_PRICE_TND: float = 99.0
    BUSINESS_PRICE_TND: float = 149.0

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
