from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from mailhub.auth.dependencies import get_current_user
from mailhub.db.models import User
from mailhub.maintenance_control import (
    read_backups,
    read_maintenance_status,
    request_maintenance_action,
)

router = APIRouter(prefix="/api/v1/admin/backups", tags=["administration"])


class BackupItem(BaseModel):
    id: str
    created_at: str | None = None
    size_bytes: int = 0
    database_bytes: int = 0
    attachments_bytes: int = 0
    routed_bytes: int = 0
    has_environment: bool = False
    sha256_verified: bool | None = None


class BackupStatus(BaseModel):
    state: str
    action: str | None = None
    backup_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    message: str | None = None


class BackupOverview(BaseModel):
    status: BackupStatus
    backups: list[BackupItem]


class RestoreRequest(BaseModel):
    backup_id: str
    confirmation: str


async def require_backup_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


def _overview() -> dict[str, Any]:
    return {
        "status": read_maintenance_status(),
        "backups": read_backups(),
    }


@router.get(
    "",
    response_model=BackupOverview,
    dependencies=[Depends(require_backup_admin)],
)
async def list_backups() -> dict[str, Any]:
    return _overview()


@router.post(
    "/refresh",
    response_model=BackupStatus,
    dependencies=[Depends(require_backup_admin)],
)
async def refresh_backups() -> dict[str, Any]:
    try:
        return request_maintenance_action("backup_list")
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "",
    response_model=BackupStatus,
    dependencies=[Depends(require_backup_admin)],
)
async def create_backup() -> dict[str, Any]:
    try:
        return request_maintenance_action("backup_create")
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/restore",
    response_model=BackupStatus,
    dependencies=[Depends(require_backup_admin)],
)
async def restore_backup(payload: RestoreRequest) -> dict[str, Any]:
    expected = f"RESTORE {payload.backup_id}"
    if payload.confirmation != expected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Confirmation must be exactly: {expected}",
        )

    known = {item.get("id") for item in read_backups()}
    if payload.backup_id not in known:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found",
        )

    try:
        return request_maintenance_action(
            "backup_restore",
            backup_id=payload.backup_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
