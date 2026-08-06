import os
import signal
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from mailhub.auth.dependencies import get_current_user
from mailhub.core.health import startup_state
from mailhub.core.lifecycle import lifecycle_manager, worker_registry
from mailhub.db.models import User

router = APIRouter(prefix="/api/v1/system", tags=["system"])


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


@router.get("/status", dependencies=[Depends(require_admin)])
async def system_status() -> dict[str, object]:
    return {
        "status": "stopping" if startup_state.shutting_down else "running",
        "startup_complete": startup_state.startup_complete,
        "started_at": startup_state.started_at,
        "ready_at": startup_state.ready_at,
        "shutdown_requested": lifecycle_manager.shutdown_requested,
        "worker_count": len(worker_registry.snapshots()),
        "server_time": datetime.now(UTC),
    }


@router.get("/workers", dependencies=[Depends(require_admin)])
async def workers() -> list[dict[str, object]]:
    return [snapshot.as_dict() for snapshot in worker_registry.snapshots()]


@router.post("/shutdown", dependencies=[Depends(require_admin)])
async def request_shutdown() -> dict[str, str]:
    lifecycle_manager.request_shutdown()
    # Signal the ASGI server after the response has been scheduled.
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutdown_requested"}
