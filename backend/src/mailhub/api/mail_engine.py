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
from mailhub.db.models import ActivityEvent, EmailAccount, MailMessage, SyncRun
from mailhub.db.session import get_session
from mailhub.mail.crypto import CredentialCipher
from mailhub.mail.oauth import (
    consume_state,
    create_authorization,
    exchange_code,
    fetch_google_identity,
    normalize_provider,
    validate_oauth_callback,
)
from mailhub.mail.oauth_settings import (
    google_redirect_uri,
    load_google_oauth_settings,
)
from mailhub.mail.sync import sync_account

router = APIRouter(prefix="/api/v1", tags=["mail engine"])


class OAuthStart(BaseModel):
    authorization_url: str


class ManualSyncResponse(BaseModel):
    run_id: str
    status: str
    attempt: int
    messages_seen: int
    messages_created: int
    attachments_created: int
    error_message: str | None = None


@router.get(
    "/oauth/{provider}/start",
    response_model=OAuthStart,
    dependencies=[Depends(get_current_user)],
)
async def oauth_start(
    provider: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> OAuthStart:
    try:
        provider = normalize_provider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if provider == "google":
        google = await load_google_oauth_settings(session, settings)
        if not google.configured or not google.public_base_url:
            raise HTTPException(
                status_code=422,
                detail="Google OAuth is not configured",
            )
        redirect = google_redirect_uri(google.public_base_url)
    else:
        redirect = str(request.url_for("oauth_callback", provider=provider))

    try:
        url = await create_authorization(
            provider,
            redirect,
            settings,
            session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return OAuthStart(authorization_url=url)


@router.get(
    "/oauth/{provider}/callback",
    name="oauth_callback",
)
async def oauth_callback(
    provider: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    try:
        provider, code, state = validate_oauth_callback(
            provider,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Unsupported OAuth provider" else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    try:
        record = await consume_state(provider, state, session)
        tokens = await exchange_code(
            provider,
            code,
            record.redirect_uri,
            settings,
            session,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"OAuth failed: {exc}",
        ) from exc

    cipher = CredentialCipher(settings.app_secret_key)
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=422,
            detail="OAuth provider did not return an access token",
        )

    if provider == "google":
        try:
            identity = await fetch_google_identity(access_token)
            email = str(identity.get("email") or "").strip().lower()
            if identity.get("email_verified") is False:
                raise ValueError("Google account email address is not verified")
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Google account identity could not be read: {exc}",
            ) from exc

        if not email:
            raise HTTPException(
                status_code=422,
                detail="Google did not return an email address",
            )

        existing = await session.scalar(
            select(EmailAccount).where(
                EmailAccount.email_address == email,
                EmailAccount.oauth_provider == "google",
            )
        )

        if existing is None and not refresh_token:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Google did not return a refresh token. Revoke the app grant "
                    "for this Google account and connect again with consent."
                ),
            )

        account = existing or EmailAccount(
            name=f"Google - {email}",
            email_address=email,
            host="imap.gmail.com",
            port=993,
            username=email,
            mailbox="INBOX",
            use_ssl=True,
            is_enabled=True,
            auth_type="oauth",
            oauth_provider="google",
        )

        account.name = f"Google - {email}"
        account.email_address = email
        account.username = email
        account.host = "imap.gmail.com"
        account.port = 993
        account.use_ssl = True
        account.is_enabled = True
        account.auth_type = "oauth"
        account.oauth_provider = "google"
        account.encrypted_access_token = cipher.encrypt(access_token)

        if refresh_token:
            account.encrypted_refresh_token = cipher.encrypt(refresh_token)

        try:
            expires_in = max(60, int(tokens.get("expires_in", 3600)))
        except (TypeError, ValueError):
            expires_in = 3600

        account.access_token_expires_at = (
            datetime.now(UTC)
            + timedelta(seconds=expires_in)
        )

        if existing is None:
            session.add(account)

        await session.commit()

        return RedirectResponse(
            url="/email-accounts?oauth=google-connected",
            status_code=303,
        )

    host = "outlook.office365.com"
    account = EmailAccount(
        name=f"{provider.title()} OAuth",
        email_address="pending@example.invalid",
        host=host,
        port=993,
        username="pending@example.invalid",
        mailbox="INBOX",
        use_ssl=True,
        is_enabled=False,
        auth_type="oauth",
        oauth_provider=provider,
        encrypted_refresh_token=(
            cipher.encrypt(refresh_token)
            if refresh_token
            else None
        ),
        encrypted_access_token=cipher.encrypt(access_token),
        access_token_expires_at=(
            datetime.now(UTC)
            + timedelta(
                seconds=(
                    max(60, int(tokens.get("expires_in", 3600)))
                    if str(tokens.get("expires_in", 3600)).isdigit()
                    else 3600
                )
            )
        ),
    )
    session.add(account)
    await session.commit()

    return RedirectResponse(
        url="/email-accounts?oauth=connected",
        status_code=303,
    )


@router.post(
    "/email-accounts/{account_id}/sync",
    response_model=ManualSyncResponse,
    dependencies=[Depends(get_current_user)],
)
async def manual_sync(
    account_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        run = await sync_account(account_id, session, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if run.status != "succeeded":
        raise HTTPException(
            status_code=422,
            detail=run.error_message or "Sync failed",
        )

    return ManualSyncResponse(
        run_id=str(run.id),
        status=run.status,
        attempt=run.attempt,
        messages_seen=run.messages_seen,
        messages_created=run.messages_created,
        attachments_created=run.attachments_created,
        error_message=run.error_message,
    )




@router.post(
    "/email-accounts/{account_id}/sync/retry",
    response_model=ManualSyncResponse,
    dependencies=[Depends(get_current_user)],
)
async def retry_sync(
    account_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ManualSyncResponse:
    account = await session.get(EmailAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Email account not found")

    latest_failed = await session.scalar(
        select(SyncRun)
        .where(
            SyncRun.email_account_id == account_id,
            SyncRun.status == "failed",
        )
        .order_by(desc(SyncRun.started_at))
        .limit(1)
    )

    attempt = (latest_failed.attempt + 1) if latest_failed else 1
    run = await sync_account(account_id, session, settings, attempt=attempt)

    if run.status != "succeeded":
        raise HTTPException(
            status_code=422,
            detail=run.error_message or "Retry failed",
        )

    return ManualSyncResponse(
        run_id=str(run.id),
        status=run.status,
        attempt=run.attempt,
        messages_seen=run.messages_seen,
        messages_created=run.messages_created,
        attachments_created=run.attachments_created,
        error_message=run.error_message,
    )

@router.get("/messages", dependencies=[Depends(get_current_user)])
async def messages(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 100,
):
    rows = (
        await session.scalars(
            select(MailMessage)
            .order_by(desc(MailMessage.created_at))
            .limit(min(limit, 500))
        )
    ).all()

    return [
        {
            "id": str(x.id),
            "account_id": str(x.email_account_id),
            "subject": x.subject,
            "sender": x.sender,
            "sent_at": x.sent_at,
            "created_at": x.created_at,
        }
        for x in rows
    ]


@router.get("/activity", dependencies=[Depends(get_current_user)])
async def activities(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 100,
):
    rows = (
        await session.scalars(
            select(ActivityEvent)
            .order_by(desc(ActivityEvent.created_at))
            .limit(min(limit, 500))
        )
    ).all()

    return [
        {
            "id": str(x.id),
            "level": x.level,
            "event_type": x.event_type,
            "message": x.message,
            "created_at": x.created_at,
        }
        for x in rows
    ]
