import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.db.models import OAuthState
from mailhub.mail.oauth_settings import load_google_oauth_settings


@dataclass(frozen=True)
class ProviderConfig:
    authorize_url: str
    token_url: str
    scopes: tuple[str, ...]
    client_id: str
    client_secret: str


async def provider_config(
    provider: str,
    settings: Settings,
    session: AsyncSession,
) -> ProviderConfig:
    if provider == "google":
        google = await load_google_oauth_settings(session, settings)
        if not google.client_id or not google.client_secret:
            raise ValueError("Google OAuth is not configured")
        return ProviderConfig(
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            (
                "openid",
                "email",
                "https://mail.google.com/",
            ),
            google.client_id,
            google.client_secret,
        )

    if provider == "microsoft":
        if not settings.microsoft_client_id or not settings.microsoft_client_secret:
            raise ValueError("Microsoft OAuth is not configured")
        tenant = settings.microsoft_tenant_id or "common"
        return ProviderConfig(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            (
                "openid",
                "email",
                "offline_access",
                "https://outlook.office.com/IMAP.AccessAsUser.All",
            ),
            settings.microsoft_client_id,
            settings.microsoft_client_secret,
        )

    raise ValueError("Unsupported OAuth provider")


async def create_authorization(
    provider: str,
    redirect_uri: str,
    settings: Settings,
    session: AsyncSession,
) -> str:
    config = await provider_config(provider, settings, session)
    state = secrets.token_urlsafe(32)
    record = OAuthState(
        provider=provider,
        state_hash=hashlib.sha256(state.encode()).hexdigest(),
        redirect_uri=redirect_uri,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    session.add(record)
    await session.commit()

    params = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }

    return f"{config.authorize_url}?{urlencode(params)}"


async def consume_state(
    provider: str,
    state: str,
    session: AsyncSession,
) -> OAuthState:
    digest = hashlib.sha256(state.encode()).hexdigest()
    record = await session.scalar(
        select(OAuthState).where(OAuthState.state_hash == digest)
    )

    if (
        record is None
        or record.provider != provider
        or record.consumed_at is not None
        or record.expires_at < datetime.now(UTC)
    ):
        raise ValueError("Invalid or expired OAuth state")

    record.consumed_at = datetime.now(UTC)
    await session.commit()
    return record


async def exchange_code(
    provider: str,
    code: str,
    redirect_uri: str,
    settings: Settings,
    session: AsyncSession,
) -> dict:
    config = await provider_config(provider, settings, session)

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            config.token_url,
            data={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(
    provider: str,
    refresh_token: str,
    settings: Settings,
    session: AsyncSession,
) -> dict:
    config = await provider_config(provider, settings, session)

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            config.token_url,
            data={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(config.scopes),
            },
        )
        response.raise_for_status()
        return response.json()


async def fetch_google_identity(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
