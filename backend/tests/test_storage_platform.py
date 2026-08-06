from pathlib import Path

import pytest

from mailhub.storage.crypto import decrypt_config, encrypt_config
from mailhub.storage.rclone import test_destination, upload_file


def test_storage_config_round_trip() -> None:
    encrypted = encrypt_config("x" * 32, {"user": "me", "pass": "secret"})
    assert "secret" not in encrypted
    assert decrypt_config("x" * 32, encrypted) == {"user": "me", "pass": "secret"}


@pytest.mark.asyncio
async def test_local_destination(tmp_path: Path) -> None:
    result = await test_destination("local", str(tmp_path), {})
    assert result.ok is True


@pytest.mark.asyncio
async def test_local_upload(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    target_root = tmp_path / "target"
    result = await upload_file("local", str(target_root), {}, str(source), "a/b.txt")
    assert result.ok is True
    assert (target_root / "a" / "b.txt").read_text(encoding="utf-8") == "hello"
