import pytest

from mailhub.mail.oauth_settings import (
    google_redirect_uri,
    validate_public_base_url,
)


def test_google_redirect_uri() -> None:
    assert (
        google_redirect_uri("https://mail.example.com/")
        == "https://mail.example.com/api/v1/oauth/google/callback"
    )


def test_https_domain_is_allowed() -> None:
    assert (
        validate_public_base_url("https://mail.example.com/")
        == "https://mail.example.com"
    )


def test_http_localhost_is_allowed() -> None:
    assert (
        validate_public_base_url("http://localhost:3000")
        == "http://localhost:3000"
    )


def test_http_lan_address_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires HTTPS"):
        validate_public_base_url("http://192.168.0.219:3000")


def test_https_raw_ip_is_rejected() -> None:
    with pytest.raises(ValueError, match="raw IP"):
        validate_public_base_url("https://192.168.0.219")
