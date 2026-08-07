from pathlib import Path

import pytest

import mailhub.storage.local_permissions as permissions


def test_rejects_path_outside_managed_roots() -> None:
    with pytest.raises(ValueError):
        permissions.inspect_local_permissions("/etc")


def test_inspect_and_change_permissions(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "routed"
    monkeypatch.setattr(permissions, "ALLOWED_LOCAL_ROOTS", (root,))

    result = permissions.set_local_permissions(
        str(root),
        "0770",
        recursive=False,
    )

    assert result["exists"] is True
    assert result["mode"] == "0770"
    assert result["writable"] is True
