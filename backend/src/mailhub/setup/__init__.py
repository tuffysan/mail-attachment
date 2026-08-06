"""First-boot setup state and preferences."""

from mailhub.setup.service import (
    SETUP_COMPLETED_KEY,
    SETUP_LANGUAGE_KEY,
    SETUP_TIMEZONE_KEY,
    get_setup_state,
    set_metadata_value,
)

__all__ = [
    "SETUP_COMPLETED_KEY",
    "SETUP_LANGUAGE_KEY",
    "SETUP_TIMEZONE_KEY",
    "get_setup_state",
    "set_metadata_value",
]
