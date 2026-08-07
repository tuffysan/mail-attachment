import json
from pathlib import Path

import pytest

import mailhub.update_control as update_control


def test_missing_status_reports_unavailable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(update_control, "CONTROL_DIR", tmp_path)
    monkeypatch.setattr(update_control, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setattr(update_control, "REQUEST_FILE", tmp_path / "request.json")

    status = update_control.read_update_status()

    assert status["state"] == "unavailable"
    assert status["update_available"] is False


def test_check_request_is_written_atomically(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(update_control, "CONTROL_DIR", tmp_path)
    monkeypatch.setattr(update_control, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setattr(update_control, "REQUEST_FILE", tmp_path / "request.json")

    (tmp_path / "status.json").write_text(
        json.dumps(
            {
                "state": "up_to_date",
                "installed_commit": "abc",
                "latest_commit": "abc",
                "update_available": False,
            }
        ),
        encoding="utf-8",
    )

    response = update_control.request_update_action("check")
    request = json.loads((tmp_path / "request.json").read_text(encoding="utf-8"))

    assert response["state"] == "checking"
    assert request["action"] == "check"


def test_parallel_operation_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(update_control, "CONTROL_DIR", tmp_path)
    monkeypatch.setattr(update_control, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setattr(update_control, "REQUEST_FILE", tmp_path / "request.json")

    (tmp_path / "status.json").write_text(
        json.dumps({"state": "updating"}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="already running"):
        update_control.request_update_action("check")
