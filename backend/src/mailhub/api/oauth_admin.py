from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.config import Settings, get_settings
from mailhub.db.models import User
from mailhub.db.session import get_session
from mailhub.mail.oauth_settings import (
    clear_google_oauth_settings,
    google_redirect_uri,
    load_google_oauth_settings,
    save_google_oauth_settings,
)

router = APIRouter(
    prefix="/api/v1/admin/oauth",
    tags=["oauth administration"],
)


GOOGLE_AUTH_OVERVIEW_URL = "https://console.cloud.google.com/auth/overview"
GOOGLE_CLIENTS_URL = "https://console.cloud.google.com/auth/clients"
GMAIL_API_URL = (
    "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
)


class GoogleOAuthConfigResponse(BaseModel):
    configured: bool
    client_id: str | None
    client_secret_configured: bool
    public_base_url: str | None
    redirect_uri: str | None
    google_auth_overview_url: str
    google_clients_url: str
    gmail_api_url: str


class GoogleOAuthConfigUpdate(BaseModel):
    client_id: str = Field(min_length=1, max_length=500)
    client_secret: str | None = Field(default=None, max_length=2000)
    public_base_url: str = Field(min_length=1, max_length=2000)


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


def _response(config) -> GoogleOAuthConfigResponse:
    redirect = (
        google_redirect_uri(config.public_base_url)
        if config.public_base_url
        else None
    )
    return GoogleOAuthConfigResponse(
        configured=config.configured and bool(config.public_base_url),
        client_id=config.client_id,
        client_secret_configured=bool(config.client_secret),
        public_base_url=config.public_base_url,
        redirect_uri=redirect,
        google_auth_overview_url=GOOGLE_AUTH_OVERVIEW_URL,
        google_clients_url=GOOGLE_CLIENTS_URL,
        gmail_api_url=GMAIL_API_URL,
    )


@router.get(
    "/google",
    response_model=GoogleOAuthConfigResponse,
    dependencies=[Depends(require_admin)],
)
async def google_oauth_config(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GoogleOAuthConfigResponse:
    config = await load_google_oauth_settings(session, settings)
    return _response(config)


@router.put(
    "/google",
    response_model=GoogleOAuthConfigResponse,
    dependencies=[Depends(require_admin)],
)
async def update_google_oauth_config(
    payload: GoogleOAuthConfigUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GoogleOAuthConfigResponse:
    try:
        config = await save_google_oauth_settings(
            session,
            settings,
            client_id=payload.client_id,
            client_secret=payload.client_secret,
            public_base_url=payload.public_base_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _response(config)


@router.delete(
    "/google",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_google_oauth_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await clear_google_oauth_settings(session)
