from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.config import Settings, get_settings
from mailhub.db.models import ActivityEvent, EmailAccount, MailMessage
from mailhub.db.session import get_session
from mailhub.mail.crypto import CredentialCipher
from mailhub.mail.oauth import consume_state, create_authorization, exchange_code
from mailhub.mail.sync import sync_account

router = APIRouter(prefix="/api/v1", tags=["mail engine"])


class OAuthStart(BaseModel):
    authorization_url: str


@router.get("/oauth/{provider}/start", response_model=OAuthStart, dependencies=[Depends(get_current_user)])
async def oauth_start(provider: str, request: Request, session: Annotated[AsyncSession, Depends(get_session)],
                      settings: Annotated[Settings, Depends(get_settings)]) -> OAuthStart:
    redirect = str(request.url_for("oauth_callback", provider=provider))
    try:
        url = await create_authorization(provider, redirect, settings, session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return OAuthStart(authorization_url=url)


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(provider: str, code: str, state: str,
                         session: Annotated[AsyncSession, Depends(get_session)],
                         settings: Annotated[Settings, Depends(get_settings)]):
    try:
        record = await consume_state(provider, state, session)
        tokens = await exchange_code(provider, code, record.redirect_uri, settings)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"OAuth failed: {exc}") from exc
    # The account address is supplied later in the UI; create provider defaults.
    cipher = CredentialCipher(settings.app_secret_key)
    host = "imap.gmail.com" if provider == "google" else "outlook.office365.com"
    account = EmailAccount(
        name=f"{provider.title()} OAuth", email_address="pending@example.invalid",
        host=host, port=993, username="pending@example.invalid", mailbox="INBOX",
        use_ssl=True, is_enabled=False, auth_type="oauth", oauth_provider=provider,
        encrypted_refresh_token=cipher.encrypt(tokens.get("refresh_token", "")),
        encrypted_access_token=cipher.encrypt(tokens["access_token"]),
        access_token_expires_at=datetime.now(UTC) + timedelta(seconds=int(tokens.get("expires_in", 3600))),
    )
    session.add(account)
    await session.commit()
    return RedirectResponse(url="/email-accounts?oauth=connected")


@router.post("/email-accounts/{account_id}/sync", dependencies=[Depends(get_current_user)])
async def manual_sync(account_id: UUID, session: Annotated[AsyncSession, Depends(get_session)],
                      settings: Annotated[Settings, Depends(get_settings)]):
    try:
        run = await sync_account(account_id, session, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if run.status != "succeeded":
        raise HTTPException(status_code=422, detail=run.error_message or "Sync failed")
    return {"status": run.status, "messages_created": run.messages_created,
            "attachments_created": run.attachments_created}


@router.get("/messages", dependencies=[Depends(get_current_user)])
async def messages(session: Annotated[AsyncSession, Depends(get_session)], limit: int = 100):
    rows = (await session.scalars(select(MailMessage).order_by(desc(MailMessage.created_at)).limit(min(limit, 500)))).all()
    return [{"id": str(x.id), "account_id": str(x.email_account_id), "subject": x.subject,
             "sender": x.sender, "sent_at": x.sent_at, "created_at": x.created_at} for x in rows]


@router.get("/activity", dependencies=[Depends(get_current_user)])
async def activities(session: Annotated[AsyncSession, Depends(get_session)], limit: int = 100):
    rows = (await session.scalars(select(ActivityEvent).order_by(desc(ActivityEvent.created_at)).limit(min(limit, 500)))).all()
    return [{"id": str(x.id), "level": x.level, "event_type": x.event_type,
             "message": x.message, "created_at": x.created_at} for x in rows]
