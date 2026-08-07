import pytest

from mailhub.mail.oauth import (
    normalize_provider,
    validate_oauth_callback,
)
from mailhub.mail.oauth_settings import (
    validate_google_client_id,
    validate_public_base_url,
)


def test_normalize_provider_is_case_insensitive() -> None:
    assert normalize_provider(" Google ") == "google"
    assert normalize_provider("MICROSOFT") == "microsoft"


def test_normalize_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported OAuth provider"):
        normalize_provider("dropbox")


def test_google_client_id_is_normalized() -> None:
    assert (
        validate_google_client_id(
            " 123456.apps.googleusercontent.com "
        )
        == "123456.apps.googleusercontent.com"
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-a-google-client",
        "123 456.apps.googleusercontent.com",
    ],
)
def test_google_client_id_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        validate_google_client_id(value)


@pytest.mark.parametrize(
    "url",
    [
        "https://user:secret@mail.example.com",
        "https://mail.example.com?next=/oauth",
        "https://mail.example.com#fragment",
    ],
)
def test_oauth_base_url_rejects_ambiguous_or_sensitive_components(
    url: str,
) -> None:
    with pytest.raises(ValueError):
        validate_public_base_url(url)


def test_callback_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported OAuth provider"):
        validate_oauth_callback(
            "dropbox",
            code="abc",
            state="state",
        )


def test_callback_returns_clear_google_denial_message() -> None:
    with pytest.raises(ValueError) as captured:
        validate_oauth_callback(
            "google",
            code=None,
            state="state",
            error="access_denied",
            error_description="The user denied access",
        )

    assert "user denied access" in str(captured.value).lower()


def test_callback_requires_code_and_state() -> None:
    with pytest.raises(ValueError, match="missing code or state"):
        validate_oauth_callback(
            "google",
            code=None,
            state=None,
        )


def test_callback_normalizes_provider_and_returns_values() -> None:
    provider, code, state = validate_oauth_callback(
        " Google ",
        code="code-1",
        state="state-1",
    )
    assert provider == "google"
    assert code == "code-1"
    assert state == "state-1"
