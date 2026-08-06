from mailhub.config import Settings


def test_settings_can_be_overridden() -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql://user:pass@example/db",
        redis_url="redis://example:6379/1",
    )
    assert settings.app_env == "test"
    assert settings.readiness_timeout_seconds == 2.0
