from unittest.mock import patch

import pytest

from mailhub.mail.imap_client import test_imap_connection as run_imap_test


class FakePasswordImap:
    def __init__(self, *args, **kwargs) -> None:
        self.logged_out = False

    def login(self, username: str, password: str):
        assert username == "user@example.com"
        assert password == "secret"
        return "OK", []

    def select(self, mailbox: str, readonly: bool = False):
        assert mailbox == "INBOX"
        assert readonly is True
        return "OK", [b"17"]

    def logout(self):
        self.logged_out = True


class FakeOAuthImap:
    def __init__(self, *args, **kwargs) -> None:
        self.logged_out = False

    def authenticate(self, mechanism: str, callback):
        assert mechanism == "XOAUTH2"
        payload = callback(None)
        assert b"user=user@example.com" in payload
        assert b"auth=Bearer access-token" in payload
        return "OK", []

    def select(self, mailbox: str, readonly: bool = False):
        assert mailbox == "INBOX"
        assert readonly is True
        return "OK", [b"9"]

    def logout(self):
        self.logged_out = True


@pytest.mark.asyncio
async def test_imap_password_connection_reports_message_count() -> None:
    with patch("mailhub.mail.imap_client.imaplib.IMAP4_SSL", FakePasswordImap):
        result = await run_imap_test(
            host="imap.example.com",
            port=993,
            username="user@example.com",
            password="secret",
            mailbox="INBOX",
            use_ssl=True,
            timeout_seconds=5,
        )
    assert result.ok is True
    assert result.message_count == 17


@pytest.mark.asyncio
async def test_imap_oauth_connection_uses_xoauth2() -> None:
    with patch("mailhub.mail.imap_client.imaplib.IMAP4_SSL", FakeOAuthImap):
        result = await run_imap_test(
            host="imap.gmail.com",
            port=993,
            username="user@example.com",
            access_token="access-token",
            mailbox="INBOX",
            use_ssl=True,
            timeout_seconds=5,
        )
    assert result.ok is True
    assert result.message_count == 9


@pytest.mark.asyncio
async def test_imap_connection_rejects_missing_credential() -> None:
    with patch("mailhub.mail.imap_client.imaplib.IMAP4_SSL", FakePasswordImap):
        result = await run_imap_test(
            host="imap.example.com",
            port=993,
            username="user@example.com",
            mailbox="INBOX",
            use_ssl=True,
            timeout_seconds=5,
        )
    assert result.ok is False
    assert "No usable IMAP credential" in result.message
