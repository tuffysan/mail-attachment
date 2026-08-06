import pytest
from pydantic import ValidationError

from mailhub.core.config import Settings


BASE_ENV = {
    "app_secret_key": "x" * 32,
    "admin_password": "a-secure-password",
}


def settings(**overrides: str) -> Settings:
    values = {**BASE_ENV, **overrides}
    return Settings(_env_file=None, **values)


def test_email_engine_settings_are_part_of_settings_model() -> None:
    config = settings(
        sync_interval_seconds="600",
        sync_batch_size="250",
        storage_retry_attempts="5",
    )

    assert config.sync_interval_seconds == 600
    assert config.sync_batch_size == 250
    assert config.storage_retry_attempts == 5
    assert config.mail.sync_interval_seconds == 600
    assert config.storage.retry_attempts == 5


def test_empty_oauth_values_are_normalized_to_none() -> None:
    config = settings(
        google_client_id="",
        google_client_secret="",
        microsoft_client_id="",
        microsoft_client_secret="",
    )

    assert config.google_client_id is None
    assert config.oauth.microsoft_client_secret is None


def test_partial_google_oauth_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must be configured together"):
        settings(google_client_id="client-only")


def test_invalid_redis_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match="redis_url"):
        settings(redis_url="http://redis:6379")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError, match="log_level"):
        settings(log_level="verbose")


def test_production_placeholder_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="placeholder"):
        Settings(
            _env_file=None,
            app_env="production",
            app_secret_key="replace-with-at-least-32-random-characters",
            admin_password="a-secure-password",
        )


def test_grouped_views_preserve_flat_values() -> None:
    config = settings(
        database_pool_size="8",
        access_token_expire_minutes="90",
        attachment_data_dir="/tmp/mailhub",
    )

    assert config.database.pool_size == config.database_pool_size == 8
    assert (
        config.security.access_token_expire_minutes
        == config.access_token_expire_minutes
        == 90
    )
    assert str(config.mail.attachment_data_dir) == "/tmp/mailhub"
