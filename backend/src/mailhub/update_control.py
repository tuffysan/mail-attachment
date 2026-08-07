import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONTROL_DIR = Path(os.environ.get("UPDATE_CONTROL_DIR", "/control"))
STATUS_FILE = CONTROL_DIR / "status.json"
REQUEST_FILE = CONTROL_DIR / "request.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _default_status() -> dict[str, Any]:
    return {
        "state": "unavailable",
        "installed_commit": None,
        "latest_commit": None,
        "update_available": False,
        "latest_message": None,
        "latest_date": None,
        "checked_at": None,
        "started_at": None,
        "finished_at": None,
        "message": (
            "LXC update agent is not installed. "
            "Run scripts/install-update-agent.sh inside the LXC."
        ),
    }


def read_update_status() -> dict[str, Any]:
    try:
        raw = STATUS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return _default_status()
        return {**_default_status(), **data}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default_status()


def request_update_action(action: str) -> dict[str, Any]:
    if action not in {"check", "update"}:
        raise ValueError("Unsupported update action")

    if not CONTROL_DIR.exists():
        raise RuntimeError("LXC update agent control directory is not available")
    if not os.access(CONTROL_DIR, os.W_OK):
        raise RuntimeError("LXC update agent control directory is not writable")

    status = read_update_status()
    if status["state"] in {"checking", "updating"}:
        raise RuntimeError("An update operation is already running")

    payload = {
        "action": action,
        "requested_at": _now(),
    }

    temporary = CONTROL_DIR / f".request-{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, REQUEST_FILE)

    return {
        **status,
        "state": "checking" if action == "check" else "updating",
        "message": (
            "Checking GitHub for updates."
            if action == "check"
            else "Update requested. The web interface may restart briefly."
        ),
    }
