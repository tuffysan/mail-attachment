from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.auth.security import hash_password, verify_password
from mailhub.db.models import User
from mailhub.db.session import get_session
from mailhub.setup.schemas import (
    PasswordChangeRequest,
    SetupCompleteRequest,
    SetupCompleteResponse,
    SetupPreferencesRequest,
    SetupStatusResponse,
)
from mailhub.setup.service import (
    SETUP_COMPLETED_KEY,
    SETUP_LANGUAGE_KEY,
    SETUP_TIMEZONE_KEY,
    get_setup_state,
    set_metadata_value,
)

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SetupStatusResponse:
    return await get_setup_state(session)


@router.put(
    "/preferences",
    response_model=SetupStatusResponse,
    dependencies=[Depends(require_admin)],
)
async def update_preferences(
    request: SetupPreferencesRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(require_admin)],
) -> SetupStatusResponse:
    user.display_name = request.display_name.strip()
    await set_metadata_value(session, SETUP_LANGUAGE_KEY, request.language)
    await set_metadata_value(session, SETUP_TIMEZONE_KEY, request.timezone)
    await session.commit()
    return await get_setup_state(session)


@router.post(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def change_bootstrap_password(
    request: PasswordChangeRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(require_admin)],
) -> None:
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Current password is incorrect",
        )
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different",
        )
    user.password_hash = hash_password(request.new_password)
    user.token_version += 1
    await session.commit()


@router.post(
    "/complete",
    response_model=SetupCompleteResponse,
    dependencies=[Depends(require_admin)],
)
async def complete_setup(
    request: SetupCompleteRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SetupCompleteResponse:
    if not request.acknowledge_backup or not request.acknowledge_secret_storage:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both operational acknowledgements are required",
        )
    await set_metadata_value(session, SETUP_COMPLETED_KEY, "true")
    await session.commit()
    return SetupCompleteResponse(completed=True)
