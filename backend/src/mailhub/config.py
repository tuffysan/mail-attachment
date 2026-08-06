"""Backward-compatible configuration imports.

New code should import from ``mailhub.core.config``. This module remains so
existing application modules and third-party integrations do not break.
"""

from mailhub.core.config import Settings, clear_settings_cache, get_settings

__all__ = ["Settings", "clear_settings_cache", "get_settings"]
