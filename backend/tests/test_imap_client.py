from unittest.mock import patch

import pytest

from mailhub.mail.imap_client import test_imap_connection as run_imap_test


class FakeImap:
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


@pytest.mark.asyncio
async def test_imap_connection_reports_message_count() -> None:
    with patch("mailhub.mail.imap_client.imaplib.IMAP4_SSL", FakeImap):
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
