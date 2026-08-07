from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.config import Settings, get_settings
from mailhub.db.models import EmailAccount
from mailhub.db.session import get_session
from mailhub.mail.credentials import resolve_mail_credential
from mailhub.mail.crypto import CredentialCipher
from mailhub.mail.imap_client import test_imap_connection
from mailhub.mail.schemas import (
    ConnectionTestResponse,
    EmailAccountConnectionTestRequest,
    EmailAccountCreate,
    EmailAccountResponse,
    EmailAccountUpdate,
)

router = APIRouter(
    prefix="/api/v1/email-accounts",
    tags=["email accounts"],
    dependencies=[Depends(get_current_user)],
)


def _response(account: EmailAccount) -> EmailAccountResponse:
    return EmailAccountResponse(
        id=str(account.id),
        name=account.name,
        email_address=account.email_address,
        host=account.host,
        port=account.port,
        username=account.username,
        mailbox=account.mailbox,
        use_ssl=account.use_ssl,
        is_enabled=account.is_enabled,
        auth_type=account.auth_type,
        oauth_provider=account.oauth_provider,
        last_test_status=account.last_test_status,
        last_test_message=account.last_test_message,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


async def _get_account(account_id: UUID, session: AsyncSession) -> EmailAccount:
    account = await session.get(EmailAccount, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )
    return account


@router.get("", response_model=list[EmailAccountResponse])
async def list_accounts(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[EmailAccountResponse]:
    accounts = (
        await session.scalars(
            select(EmailAccount).order_by(
                EmailAccount.name,
                EmailAccount.created_at,
            )
        )
    ).all()
    return [_response(account) for account in accounts]


@router.post("/validate", response_model=ConnectionTestResponse)
async def validate_account_connection(
    request: EmailAccountConnectionTestRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConnectionTestResponse:
    """Test password IMAP settings before storing credentials."""

    result = await test_imap_connection(
        host=request.host.strip(),
        port=request.port,
        username=request.username.strip(),
        password=request.password,
        mailbox=request.mailbox.strip(),
        use_ssl=request.use_ssl,
        timeout_seconds=settings.imap_timeout_seconds,
    )
    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.message,
        )
    return ConnectionTestResponse(
        status="ok",
        message=result.message,
        mailbox=request.mailbox.strip(),
        message_count=result.message_count,
    )


@router.post("", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: EmailAccountCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmailAccountResponse:
    cipher = CredentialCipher(settings.app_secret_key)
    account = EmailAccount(
        name=request.name.strip(),
        email_address=str(request.email_address).lower(),
        host=request.host.strip(),
        port=request.port,
        username=request.username.strip(),
        encrypted_password=cipher.encrypt(request.password),
        mailbox=request.mailbox.strip(),
        use_ssl=request.use_ssl,
        is_enabled=request.is_enabled,
        auth_type="password",
        oauth_provider=None,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return _response(account)


@router.patch("/{account_id}", response_model=EmailAccountResponse)
async def update_account(
    account_id: UUID,
    request: EmailAccountUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmailAccountResponse:
    account = await _get_account(account_id, session)
    if account.auth_type != "password":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="OAuth accounts are managed by their OAuth provider",
        )

    values = request.model_dump(exclude_unset=True)
    password = values.pop("password", None)
    if "email_address" in values:
        values["email_address"] = str(values["email_address"]).lower()
    for field, value in values.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(account, field, value)
    if password:
        account.encrypted_password = CredentialCipher(
            settings.app_secret_key
        ).encrypt(password)
    await session.commit()
    await session.refresh(account)
    return _response(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    account = await _get_account(account_id, session)
    await session.delete(account)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{account_id}/test", response_model=ConnectionTestResponse)
async def test_account(
    account_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConnectionTestResponse:
    account = await _get_account(account_id, session)

    try:
        credential = await resolve_mail_credential(account, settings, session)
    except ValueError as exc:
        account.last_test_status = "failed"
        account.last_test_message = str(exc)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    result = await test_imap_connection(
        host=account.host,
        port=account.port,
        username=account.username,
        password=credential.password,
        access_token=credential.access_token,
        mailbox=account.mailbox,
        use_ssl=account.use_ssl,
        timeout_seconds=settings.imap_timeout_seconds,
    )
    account.last_test_status = "ok" if result.ok else "failed"
    account.last_test_message = result.message
    await session.commit()
    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.message,
        )
    return ConnectionTestResponse(
        status="ok",
        message=result.message,
        mailbox=account.mailbox,
        message_count=result.message_count,
    )
