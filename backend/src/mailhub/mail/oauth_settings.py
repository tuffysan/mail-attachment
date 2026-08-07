from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.db.models import SystemMetadata
from mailhub.mail.crypto import CredentialCipher

GOOGLE_CLIENT_ID_KEY = "oauth.google.client_id"
GOOGLE_CLIENT_SECRET_KEY = "oauth.google.client_secret"
GOOGLE_PUBLIC_BASE_URL_KEY = "oauth.google.public_base_url"


@dataclass(frozen=True)
class GoogleOAuthSettings:
    client_id: str | None
    client_secret: str | None
    public_base_url: str | None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


async def _metadata(session: AsyncSession, key: str) -> SystemMetadata | None:
    return await session.scalar(
        select(SystemMetadata).where(SystemMetadata.key == key)
    )


async def _value(
    session: AsyncSession,
    key: str,
) -> str | None:
    row = await _metadata(session, key)
    return row.value if row is not None else None


async def _set_value(
    session: AsyncSession,
    key: str,
    value: str,
) -> None:
    row = await _metadata(session, key)
    if row is None:
        session.add(SystemMetadata(key=key, value=value))
    else:
        row.value = value


async def _delete_value(
    session: AsyncSession,
    key: str,
) -> None:
    row = await _metadata(session, key)
    if row is not None:
        await session.delete(row)


def validate_public_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("OAuth Base URL must be a valid http:// or https:// URL")

    hostname = (parsed.hostname or "").lower()
    is_localhost = hostname in {"localhost", "127.0.0.1", "::1"}

    if parsed.scheme != "https" and not is_localhost:
        raise ValueError(
            "Google requires HTTPS for OAuth redirect URIs unless the host is localhost"
        )

    if not is_localhost:
        # Google rejects raw IP addresses for web OAuth redirects.
        try:
            import ipaddress
            ipaddress.ip_address(hostname)
        except ValueError:
            pass
        else:
            raise ValueError(
                "Google does not allow a raw IP address as a web OAuth redirect host. "
                "Use an HTTPS hostname."
            )

    return normalized


async def load_google_oauth_settings(
    session: AsyncSession,
    settings: Settings,
) -> GoogleOAuthSettings:
    cipher = CredentialCipher(settings.app_secret_key)

    stored_id = await _value(session, GOOGLE_CLIENT_ID_KEY)
    stored_secret = await _value(session, GOOGLE_CLIENT_SECRET_KEY)
    stored_base_url = await _value(session, GOOGLE_PUBLIC_BASE_URL_KEY)

    secret: str | None = None
    if stored_secret:
        secret = cipher.decrypt(stored_secret)
    elif settings.google_client_secret:
        secret = settings.google_client_secret

    return GoogleOAuthSettings(
        client_id=stored_id or settings.google_client_id,
        client_secret=secret,
        public_base_url=stored_base_url,
    )


async def save_google_oauth_settings(
    session: AsyncSession,
    settings: Settings,
    *,
    client_id: str,
    client_secret: str | None,
    public_base_url: str,
) -> GoogleOAuthSettings:
    normalized_id = client_id.strip()
    if not normalized_id:
        raise ValueError("Google Client ID is required")
    if not normalized_id.endswith(".apps.googleusercontent.com"):
        raise ValueError(
            "Google Client ID should end with .apps.googleusercontent.com"
        )

    normalized_base_url = validate_public_base_url(public_base_url)
    current = await load_google_oauth_settings(session, settings)

    secret = (client_secret or "").strip() or current.client_secret
    if not secret:
        raise ValueError("Google Client Secret is required")

    cipher = CredentialCipher(settings.app_secret_key)

    await _set_value(session, GOOGLE_CLIENT_ID_KEY, normalized_id)
    await _set_value(
        session,
        GOOGLE_CLIENT_SECRET_KEY,
        cipher.encrypt(secret),
    )
    await _set_value(
        session,
        GOOGLE_PUBLIC_BASE_URL_KEY,
        normalized_base_url,
    )

    await session.commit()

    return GoogleOAuthSettings(
        client_id=normalized_id,
        client_secret=secret,
        public_base_url=normalized_base_url,
    )


async def clear_google_oauth_settings(
    session: AsyncSession,
) -> None:
    for key in (
        GOOGLE_CLIENT_ID_KEY,
        GOOGLE_CLIENT_SECRET_KEY,
        GOOGLE_PUBLIC_BASE_URL_KEY,
    ):
        await _delete_value(session, key)
    await session.commit()


def google_redirect_uri(public_base_url: str) -> str:
    return (
        public_base_url.rstrip("/")
        + "/api/v1/oauth/google/callback"
    )
