import json
from pathlib import Path

import pytest

from mailhub import maintenance_control


@pytest.fixture
def control_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(maintenance_control, "CONTROL_DIR", tmp_path)
    monkeypatch.setattr(
        maintenance_control,
        "REQUEST_FILE",
        tmp_path / "request.json",
    )
    monkeypatch.setattr(
        maintenance_control,
        "STATUS_FILE",
        tmp_path / "maintenance-status.json",
    )
    monkeypatch.setattr(
        maintenance_control,
        "BACKUPS_FILE",
        tmp_path / "backups.json",
    )
    (tmp_path / "status.json").write_text(
        json.dumps({"state": "up_to_date"}),
        encoding="utf-8",
    )
    return tmp_path


def test_read_backups_rejects_non_list(
    control_dir: Path,
) -> None:
    (control_dir / "backups.json").write_text(
        json.dumps({"unexpected": True}),
        encoding="utf-8",
    )
    assert maintenance_control.read_backups() == []


def test_read_backups_keeps_valid_items(
    control_dir: Path,
) -> None:
    (control_dir / "backups.json").write_text(
        json.dumps(
            [
                {"id": "mailhub-20260807T200000Z", "size_bytes": 123},
                "invalid",
                {"missing": "id"},
            ]
        ),
        encoding="utf-8",
    )

    assert maintenance_control.read_backups() == [
        {"id": "mailhub-20260807T200000Z", "size_bytes": 123}
    ]


def test_restore_requires_safe_backup_id(
    control_dir: Path,
) -> None:
    with pytest.raises(ValueError, match="Invalid backup identifier"):
        maintenance_control.request_maintenance_action(
            "backup_restore",
            backup_id="../root",
        )


def test_restore_requires_backup_id(
    control_dir: Path,
) -> None:
    with pytest.raises(ValueError, match="backup_id is required"):
        maintenance_control.request_maintenance_action("backup_restore")


def test_request_writes_atomic_payload(
    control_dir: Path,
) -> None:
    status = maintenance_control.request_maintenance_action("backup_create")

    payload = json.loads(
        (control_dir / "request.json").read_text(encoding="utf-8")
    )
    assert payload["action"] == "backup_create"
    assert status["state"] == "creating"


def test_backup_request_blocked_while_update_running(
    control_dir: Path,
) -> None:
    (control_dir / "status.json").write_text(
        json.dumps({"state": "updating"}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="software update"):
        maintenance_control.request_maintenance_action("backup_create")
