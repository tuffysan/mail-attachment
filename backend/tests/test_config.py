from mailhub.config import Settings


def test_settings_can_be_overridden() -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql+asyncpg://user:pass@example/db",
        redis_url="redis://example:6379/1",
        database_pool_size=3,
        database_max_overflow=4,
    )
    assert settings.app_env == "test"
    assert settings.readiness_timeout_seconds == 2.0
    assert settings.database_pool_size == 3
    assert settings.database_max_overflow == 4
