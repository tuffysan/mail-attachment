"""Application configuration.

``Settings`` keeps the existing flat attribute API while exposing typed
grouped views such as ``settings.database`` and ``settings.mail``.
"""

from mailhub.core.config.settings import (
    ApplicationConfig,
    DatabaseConfig,
    MailConfig,
    OAuthConfig,
    RedisConfig,
    SecurityConfig,
    Settings,
    StorageConfig,
    clear_settings_cache,
    get_settings,
)

__all__ = [
    "ApplicationConfig",
    "DatabaseConfig",
    "MailConfig",
    "OAuthConfig",
    "RedisConfig",
    "SecurityConfig",
    "Settings",
    "StorageConfig",
    "clear_settings_cache",
    "get_settings",
]
