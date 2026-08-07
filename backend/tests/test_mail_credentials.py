from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from mailhub.db.models import EmailAccount
from mailhub.mail.credentials import resolve_mail_credential
from mailhub.mail.crypto import CredentialCipher


@pytest.fixture
def settings():
    return SimpleNamespace(app_secret_key="x" * 32)


@pytest.mark.asyncio
async def test_password_account_returns_decrypted_password(settings) -> None:
    cipher = CredentialCipher(settings.app_secret_key)
    account = EmailAccount(
        name="Inbox",
        email_address="user@example.com",
        host="imap.example.com",
        port=993,
        username="user@example.com",
        encrypted_password=cipher.encrypt("secret"),
        mailbox="INBOX",
        use_ssl=True,
        is_enabled=True,
        auth_type="password",
    )
    session = AsyncMock()

    credential = await resolve_mail_credential(account, settings, session)

    assert credential.password == "secret"
    assert credential.access_token is None


@pytest.mark.asyncio
async def test_oauth_account_reuses_fresh_access_token(settings) -> None:
    cipher = CredentialCipher(settings.app_secret_key)
    account = EmailAccount(
        name="Google",
        email_address="user@example.com",
        host="imap.gmail.com",
        port=993,
        username="user@example.com",
        mailbox="INBOX",
        use_ssl=True,
        is_enabled=True,
        auth_type="oauth",
        oauth_provider="google",
        encrypted_refresh_token=cipher.encrypt("refresh"),
        encrypted_access_token=cipher.encrypt("access"),
        access_token_expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    session = AsyncMock()

    credential = await resolve_mail_credential(account, settings, session)

    assert credential.access_token == "access"
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_oauth_account_refreshes_expired_access_token(settings) -> None:
    cipher = CredentialCipher(settings.app_secret_key)
    account = EmailAccount(
        name="Google",
        email_address="user@example.com",
        host="imap.gmail.com",
        port=993,
        username="user@example.com",
        mailbox="INBOX",
        use_ssl=True,
        is_enabled=True,
        auth_type="oauth",
        oauth_provider="google",
        encrypted_refresh_token=cipher.encrypt("refresh"),
        encrypted_access_token=cipher.encrypt("old"),
        access_token_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    session = AsyncMock()

    with patch(
        "mailhub.mail.credentials.refresh_access_token",
        new=AsyncMock(return_value={"access_token": "new", "expires_in": 3600}),
    ) as refresh:
        credential = await resolve_mail_credential(account, settings, session)

    assert credential.access_token == "new"
    assert cipher.decrypt(account.encrypted_access_token) == "new"
    refresh.assert_awaited_once()
    session.flush.assert_awaited_once()
