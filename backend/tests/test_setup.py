import pytest
from pydantic import ValidationError

from mailhub.setup.schemas import (
    PasswordChangeRequest,
    SetupCompleteRequest,
    SetupPreferencesRequest,
)


def test_setup_preferences_accept_supported_timezone() -> None:
    request = SetupPreferencesRequest(
        display_name="Administrator",
        language="sv",
        timezone="Europe/Stockholm",
    )
    assert request.timezone == "Europe/Stockholm"


def test_setup_preferences_reject_unknown_timezone() -> None:
    with pytest.raises(ValidationError, match="Unknown timezone"):
        SetupPreferencesRequest(
            display_name="Administrator",
            language="sv",
            timezone="Mars/Olympus",
        )


def test_password_requires_twelve_characters() -> None:
    with pytest.raises(ValidationError):
        PasswordChangeRequest(
            current_password="old",
            new_password="too-short",
        )


def test_setup_completion_requires_explicit_acknowledgements() -> None:
    request = SetupCompleteRequest(
        acknowledge_backup=True,
        acknowledge_secret_storage=True,
    )
    assert request.acknowledge_backup is True
    assert request.acknowledge_secret_storage is True
