from typing import Annotated

from fastapi import Request

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.auth.schemas import AuditLogResponse, LoginRequest, PasswordChangeRequest, TokenResponse, UserResponse
from mailhub.auth.rate_limit import check_login_rate_limit, clear_login_rate_limit
from mailhub.auth.security import create_access_token, hash_password, verify_password
from mailhub.config import Settings, get_settings
from mailhub.db.models import AuditLog, User
from mailhub.db.session import get_session

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    remote = http_request.client.host if http_request.client else "unknown"
    rate_key = f"{remote}:{request.email.lower()}"
    allowed, retry_after = check_login_rate_limit(rate_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = await session.scalar(
        select(User).where(User.email == request.email.lower())
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(request.password, user.password_hash)
    ):
        session.add(
            AuditLog(
                user_id=user.id if user else None,
                action="auth.login_failed",
                entity_type="user",
                entity_id=str(user.id) if user else None,
                remote_address=remote,
            )
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    clear_login_rate_limit(rate_key)
    session.add(
        AuditLog(
            user_id=user.id,
            action="auth.login_succeeded",
            entity_type="user",
            entity_id=str(user.id),
            remote_address=remote,
        )
    )
    await session.commit()

    return TokenResponse(
        access_token=create_access_token(
            user.id,
            settings,
            token_version=user.token_version,
        ),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return _user_response(user)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChangeRequest,
    http_request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Current password is incorrect",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different",
        )

    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    session.add(
        AuditLog(
            user_id=user.id,
            action="auth.password_changed",
            entity_type="user",
            entity_id=str(user.id),
            remote_address=(
                http_request.client.host
                if http_request.client
                else None
            ),
        )
    )
    await session.commit()


@router.get("/audit", response_model=list[AuditLogResponse])
async def audit_log(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 100,
) -> list[AuditLogResponse]:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    rows = (
        await session.scalars(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(max(1, min(limit, 500)))
        )
    ).all()

    return [
        AuditLogResponse(
            id=str(item.id),
            action=item.action,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            details_json=item.details_json,
            remote_address=item.remote_address,
            created_at=item.created_at.isoformat(),
        )
        for item in rows
    ]
