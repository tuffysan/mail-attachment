import pytest
from pydantic import ValidationError

from mailhub.core.config import Settings


BASE_ENV = {
    "APP_SECRET_KEY": "x" * 32,
    "ADMIN_PASSWORD": "a-secure-password",
}


def settings(**overrides: str) -> Settings:
    values = {**BASE_ENV, **overrides}
    return Settings(_env_file=None, **values)


def test_email_engine_settings_are_part_of_settings_model() -> None:
    config = settings(
        SYNC_INTERVAL_SECONDS="600",
        SYNC_BATCH_SIZE="250",
        STORAGE_RETRY_ATTEMPTS="5",
    )

    assert config.sync_interval_seconds == 600
    assert config.sync_batch_size == 250
    assert config.storage_retry_attempts == 5
    assert config.mail.sync_interval_seconds == 600
    assert config.storage.retry_attempts == 5


def test_empty_oauth_values_are_normalized_to_none() -> None:
    config = settings(
        GOOGLE_CLIENT_ID="",
        GOOGLE_CLIENT_SECRET="",
        MICROSOFT_CLIENT_ID="",
        MICROSOFT_CLIENT_SECRET="",
    )

    assert config.google_client_id is None
    assert config.oauth.microsoft_client_secret is None


def test_partial_google_oauth_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must be configured together"):
        settings(GOOGLE_CLIENT_ID="client-only")


def test_invalid_redis_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match="REDIS_URL"):
        settings(REDIS_URL="http://redis:6379")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError, match="LOG_LEVEL"):
        settings(LOG_LEVEL="verbose")


def test_production_placeholder_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="placeholder"):
        Settings(
            _env_file=None,
            APP_ENV="production",
            APP_SECRET_KEY="replace-with-at-least-32-random-characters",
            ADMIN_PASSWORD="a-secure-password",
        )


def test_grouped_views_preserve_flat_values() -> None:
    config = settings(
        DATABASE_POOL_SIZE="8",
        ACCESS_TOKEN_EXPIRE_MINUTES="90",
        ATTACHMENT_DATA_DIR="/tmp/mailhub",
    )

    assert config.database.pool_size == config.database_pool_size == 8
    assert (
        config.security.access_token_expire_minutes
        == config.access_token_expire_minutes
        == 90
    )
    assert str(config.mail.attachment_data_dir) == "/tmp/mailhub"
