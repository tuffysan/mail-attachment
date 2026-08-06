from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Mail Attachment Hub"
    app_version: str = "0.5.0"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+asyncpg://mailhub:mailhub@postgres:5432/mailhub",
        repr=False,
    )
    redis_url: str = Field(default="redis://redis:6379/0", repr=False)
    database_pool_size: int = 5
    database_max_overflow: int = 10
    readiness_timeout_seconds: float = 2.0
    app_secret_key: str = Field(min_length=32, repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_email: str | None = None
    admin_password: str | None = Field(default=None, min_length=12, repr=False)
    admin_display_name: str = "Administrator"


@lru_cache
def get_settings() -> Settings:
    return Settings()
