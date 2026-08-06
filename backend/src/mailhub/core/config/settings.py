from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvironmentName = Literal["development", "test", "production"]


class ApplicationConfig(BaseModel):
    environment: EnvironmentName
    name: str
    version: str
    log_level: str
    log_format: str
    base_url: str
    readiness_timeout_seconds: float
    shutdown_timeout_seconds: float
    request_id_header: str
    correlation_id_header: str
    security_headers_enabled: bool


class DatabaseConfig(BaseModel):
    url: str
    pool_size: int
    max_overflow: int


class RedisConfig(BaseModel):
    url: str


class SecurityConfig(BaseModel):
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int


class MailConfig(BaseModel):
    imap_timeout_seconds: float
    sync_interval_seconds: int
    sync_batch_size: int
    retry_attempts: int
    retry_delay_seconds: int
    attachment_data_dir: Path
    extract_zip_attachments: bool
    max_zip_files: int
    max_zip_expanded_bytes: int


class OAuthConfig(BaseModel):
    google_client_id: str | None
    google_client_secret: str | None
    microsoft_client_id: str | None
    microsoft_client_secret: str | None
    microsoft_tenant_id: str


class StorageConfig(BaseModel):
    retry_attempts: int


class Settings(BaseSettings):
    """Validated runtime configuration loaded from environment variables.

    The flat fields preserve compatibility with the existing codebase.
    Grouped computed properties provide clearer boundaries for new code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    app_env: EnvironmentName = "development"
    app_name: str = "Mail Attachment Hub"
    app_version: str = "1.0.0"
    app_base_url: str = "http://localhost:8080"
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    request_id_header: str = "X-Request-ID"
    correlation_id_header: str = "X-Correlation-ID"
    security_headers_enabled: bool = True
    request_log_excluded_paths: str = "/health/live,/health/ready"

    database_url: str = Field(
        default="postgresql+asyncpg://mailhub:mailhub@postgres:5432/mailhub",
        repr=False,
    )
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=200)

    redis_url: str = Field(default="redis://redis:6379/0", repr=False)
    readiness_timeout_seconds: float = Field(default=2.0, ge=0.1, le=30.0)
    shutdown_timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)

    app_secret_key: str = Field(min_length=32, repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=10080)

    admin_email: str | None = None
    admin_password: str | None = Field(default=None, min_length=12, repr=False)
    admin_display_name: str = "Administrator"

    imap_timeout_seconds: float = Field(default=15.0, ge=1.0, le=120.0)
    sync_interval_seconds: int = Field(default=300, ge=30, le=86400)
    sync_batch_size: int = Field(default=100, ge=1, le=1000)
    sync_retry_attempts: int = Field(default=3, ge=1, le=10)
    sync_retry_delay_seconds: int = Field(default=10, ge=1, le=3600)
    attachment_data_dir: str = "/data/attachments"
    extract_zip_attachments: bool = True
    max_zip_files: int = Field(default=100, ge=1, le=10000)
    max_zip_expanded_bytes: int = Field(default=104857600, ge=1048576)

    google_client_id: str | None = None
    google_client_secret: str | None = Field(default=None, repr=False)
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = Field(default=None, repr=False)
    microsoft_tenant_id: str = "common"

    storage_retry_attempts: int = Field(default=3, ge=1, le=10)

    @field_validator("request_id_header", "correlation_id_header")
    @classmethod
    def validate_header_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or any(char in normalized for char in "\r\n:"):
            raise ValueError("Header names must be non-empty and cannot contain CR, LF or colon")
        return normalized

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper().strip()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return normalized

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// or sqlite+aiosqlite://"
            )
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise ValueError("REDIS_URL must be a valid redis:// or rediss:// URL")
        return value

    @field_validator("app_base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("APP_BASE_URL must be a valid HTTP or HTTPS URL")
        return value.rstrip("/")

    @field_validator(
        "google_client_id",
        "google_client_secret",
        "microsoft_client_id",
        "microsoft_client_secret",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_runtime_requirements(self) -> "Settings":
        if self.app_env == "production":
            forbidden = (
                "replace-with",
                "change-this",
                "development-secret",
            )
            lowered = self.app_secret_key.lower()
            if any(fragment in lowered for fragment in forbidden):
                raise ValueError("APP_SECRET_KEY still contains a placeholder value")
            if self.admin_password and "replace-with" in self.admin_password.lower():
                raise ValueError("ADMIN_PASSWORD still contains a placeholder value")

        google_values = (self.google_client_id, self.google_client_secret)
        if any(google_values) and not all(google_values):
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured together"
            )

        microsoft_values = (
            self.microsoft_client_id,
            self.microsoft_client_secret,
        )
        if any(microsoft_values) and not all(microsoft_values):
            raise ValueError(
                "MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET "
                "must be configured together"
            )
        return self

    @computed_field
    @property
    def application(self) -> ApplicationConfig:
        return ApplicationConfig(
            environment=self.app_env,
            name=self.app_name,
            version=self.app_version,
            log_level=self.log_level,
            log_format=self.log_format,
            base_url=self.app_base_url,
            request_id_header=self.request_id_header,
            correlation_id_header=self.correlation_id_header,
            security_headers_enabled=self.security_headers_enabled,
            readiness_timeout_seconds=self.readiness_timeout_seconds,
        )

    @computed_field
    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.database_url,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
        )

    @computed_field
    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(url=self.redis_url)

    @computed_field
    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(
            secret_key=self.app_secret_key,
            jwt_algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.access_token_expire_minutes,
        )

    @computed_field
    @property
    def mail(self) -> MailConfig:
        return MailConfig(
            imap_timeout_seconds=self.imap_timeout_seconds,
            sync_interval_seconds=self.sync_interval_seconds,
            sync_batch_size=self.sync_batch_size,
            retry_attempts=self.sync_retry_attempts,
            retry_delay_seconds=self.sync_retry_delay_seconds,
            attachment_data_dir=Path(self.attachment_data_dir),
            extract_zip_attachments=self.extract_zip_attachments,
            max_zip_files=self.max_zip_files,
            max_zip_expanded_bytes=self.max_zip_expanded_bytes,
        )

    @computed_field
    @property
    def oauth(self) -> OAuthConfig:
        return OAuthConfig(
            google_client_id=self.google_client_id,
            google_client_secret=self.google_client_secret,
            microsoft_client_id=self.microsoft_client_id,
            microsoft_client_secret=self.microsoft_client_secret,
            microsoft_tenant_id=self.microsoft_tenant_id,
        )

    @computed_field
    @property
    def storage(self) -> StorageConfig:
        return StorageConfig(retry_attempts=self.storage_retry_attempts)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Clear the cached settings object, primarily for tests and tooling."""

    get_settings.cache_clear()
