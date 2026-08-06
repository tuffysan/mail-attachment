from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.config import Settings, get_settings
from mailhub.db.models import User
from mailhub.db.session import get_session
from mailhub.operations.schemas import OperationsDashboardResponse
from mailhub.operations.service import build_operations_dashboard

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


@router.get(
    "/dashboard",
    response_model=OperationsDashboardResponse,
    dependencies=[Depends(require_admin)],
)
async def dashboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> OperationsDashboardResponse:
    return await build_operations_dashboard(session, settings)
