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
    app_version: str = "0.4.0"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+asyncpg://mailhub:mailhub@postgres:5432/mailhub",
        repr=False,
    )
    redis_url: str = Field(default="redis://redis:6379/0", repr=False)
    database_pool_size: int = 5
    database_max_overflow: int = 10
    readiness_timeout_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
