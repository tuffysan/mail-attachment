from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from mailhub.auth.dependencies import get_current_user
from mailhub.db.models import User
from mailhub.update_control import read_update_status, request_update_action

router = APIRouter(prefix="/api/v1/admin/update", tags=["administration"])


class UpdateStatusResponse(BaseModel):
    state: str
    installed_commit: str | None = None
    latest_commit: str | None = None
    update_available: bool = False
    latest_message: str | None = None
    latest_date: str | None = None
    checked_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    message: str | None = None


async def require_update_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


@router.get(
    "/status",
    response_model=UpdateStatusResponse,
    dependencies=[Depends(require_update_admin)],
)
async def update_status() -> dict[str, Any]:
    return read_update_status()


@router.post(
    "/check",
    response_model=UpdateStatusResponse,
    dependencies=[Depends(require_update_admin)],
)
async def check_update() -> dict[str, Any]:
    try:
        return request_update_action("check")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/apply",
    response_model=UpdateStatusResponse,
    dependencies=[Depends(require_update_admin)],
)
async def apply_update() -> dict[str, Any]:
    current = read_update_status()
    if current.get("state") == "unavailable":
        raise HTTPException(
            status_code=503,
            detail=current.get("message") or "LXC update agent is unavailable",
        )
    if not current.get("update_available"):
        raise HTTPException(
            status_code=409,
            detail="No newer GitHub commit is currently available",
        )

    try:
        return request_update_action("update")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
