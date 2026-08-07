from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.db.models import EmailAccount
from mailhub.mail.crypto import CredentialCipher
from mailhub.mail.oauth import refresh_access_token


@dataclass(frozen=True)
class MailCredential:
    password: str | None = None
    access_token: str | None = None


async def resolve_mail_credential(
    account: EmailAccount,
    settings: Settings,
    session: AsyncSession,
) -> MailCredential:
    """Return a usable IMAP credential and refresh OAuth tokens when needed."""

    cipher = CredentialCipher(settings.app_secret_key)

    if account.auth_type == "oauth":
        if not account.oauth_provider:
            raise ValueError("OAuth account has no provider")
        if not account.encrypted_refresh_token:
            raise ValueError("OAuth account has no refresh token")

        now = datetime.now(UTC)
        token_is_fresh = (
            account.encrypted_access_token
            and account.access_token_expires_at
            and account.access_token_expires_at > now + timedelta(minutes=2)
        )

        if token_is_fresh:
            return MailCredential(
                access_token=cipher.decrypt(account.encrypted_access_token)
            )

        tokens = await refresh_access_token(
            account.oauth_provider,
            cipher.decrypt(account.encrypted_refresh_token),
            settings,
            session,
        )
        access_token = str(tokens.get("access_token") or "").strip()
        if not access_token:
            raise ValueError("OAuth provider did not return an access token")

        account.encrypted_access_token = cipher.encrypt(access_token)
        account.access_token_expires_at = now + timedelta(
            seconds=int(tokens.get("expires_in", 3600))
        )
        await session.flush()
        return MailCredential(access_token=access_token)

    if account.auth_type != "password":
        raise ValueError(f"Unsupported email account auth type: {account.auth_type}")
    if not account.encrypted_password:
        raise ValueError("Password account has no password")

    return MailCredential(password=cipher.decrypt(account.encrypted_password))
