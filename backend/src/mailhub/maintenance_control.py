import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONTROL_DIR = Path(os.environ.get("UPDATE_CONTROL_DIR", "/control"))
REQUEST_FILE = CONTROL_DIR / "request.json"
STATUS_FILE = CONTROL_DIR / "maintenance-status.json"
BACKUPS_FILE = CONTROL_DIR / "backups.json"

_BACKUP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _default_status() -> dict[str, Any]:
    return {
        "state": "idle",
        "action": None,
        "backup_id": None,
        "started_at": None,
        "finished_at": None,
        "message": "Backuphanteraren är redo.",
    }


def read_maintenance_status() -> dict[str, Any]:
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_default_status(), **data}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return _default_status()


def read_backups() -> list[dict[str, Any]]:
    try:
        data = json.loads(BACKUPS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    result: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result.append(item)
    return result


def _ensure_agent_available() -> None:
    if not CONTROL_DIR.exists():
        raise RuntimeError("LXC control directory is not available")
    if not os.access(CONTROL_DIR, os.W_OK):
        raise RuntimeError("LXC control directory is not writable")

    update_status = CONTROL_DIR / "status.json"
    if not update_status.exists():
        raise RuntimeError("LXC maintenance agent is not installed")


def request_maintenance_action(
    action: str,
    *,
    backup_id: str | None = None,
) -> dict[str, Any]:
    if action not in {"backup_list", "backup_create", "backup_restore"}:
        raise ValueError("Unsupported maintenance action")

    if backup_id is not None and not _BACKUP_ID.fullmatch(backup_id):
        raise ValueError("Invalid backup identifier")

    if action == "backup_restore" and not backup_id:
        raise ValueError("backup_id is required for restore")

    _ensure_agent_available()

    current = read_maintenance_status()
    if current.get("state") in {"creating", "restoring", "refreshing"}:
        raise RuntimeError("A backup operation is already running")

    update_status_path = CONTROL_DIR / "status.json"
    try:
        update_status = json.loads(update_status_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        update_status = {}
    if update_status.get("state") in {"checking", "updating"}:
        raise RuntimeError("A software update operation is already running")

    if REQUEST_FILE.exists():
        raise RuntimeError("Another LXC maintenance request is already queued")

    payload: dict[str, Any] = {
        "action": action,
        "requested_at": _now(),
    }
    if backup_id:
        payload["backup_id"] = backup_id

    temporary = CONTROL_DIR / f".request-{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, REQUEST_FILE)

    state = {
        "backup_list": "refreshing",
        "backup_create": "creating",
        "backup_restore": "restoring",
    }[action]

    return {
        **current,
        "state": state,
        "action": action,
        "backup_id": backup_id,
        "started_at": _now(),
        "finished_at": None,
        "message": {
            "backup_list": "Backuphistoriken uppdateras.",
            "backup_create": "Backup har begärts.",
            "backup_restore": "Återställning har begärts. Webbgränssnittet kan startas om.",
        }[action],
    }
