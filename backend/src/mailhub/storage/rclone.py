import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from mailhub.storage.providers import provider_definition


@dataclass(frozen=True)
class StorageResult:
    ok: bool
    message: str
    target: str | None = None


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", " ").strip()


def _config_text(provider: str, config: dict[str, str]) -> str:
    definition = provider_definition(provider)
    if definition.rclone_type is None:
        return ""
    lines = ["[mailhub]", f"type = {definition.rclone_type}"]
    values = dict(config)
    if provider == "minio":
        values.setdefault("provider", "Minio")
        values.setdefault("region", "us-east-1")
    if provider == "s3":
        values.setdefault("provider", "AWS")
    for key in definition.fields:
        value = values.get(key)
        if value is None or str(value).strip() == "":
            continue
        lines.append(f"{key} = {_quote(str(value))}")
    return "\\n".join(lines) + "\\n"


async def _run(*args: str, config_text: str, timeout: float = 120) -> tuple[int, str]:
    fd, config_path = tempfile.mkstemp(prefix="mailhub-rclone-", suffix=".conf")
    try:
        os.write(fd, config_text.encode("utf-8"))
        os.close(fd)
        process = await asyncio.create_subprocess_exec(
            "rclone", "--config", config_path, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError:
            process.kill()
            await process.communicate()
            return 124, "rclone command timed out"
        return process.returncode or 0, stdout.decode("utf-8", errors="replace").strip()
    finally:
        try:
            os.unlink(config_path)
        except FileNotFoundError:
            pass


async def test_destination(provider: str, base_path: str, config: dict[str, str]) -> StorageResult:
    if provider == "local":
        try:
            path = Path(base_path)
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".mailhub-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return StorageResult(True, "Local path is writable")
        except OSError as exc:
            return StorageResult(False, str(exc))

    code, output = await _run(
        "lsd", f"mailhub:{base_path}", "--max-depth", "1",
        config_text=_config_text(provider, config), timeout=60,
    )
    return StorageResult(code == 0, output or ("Connection succeeded" if code == 0 else "Connection failed"))


async def upload_file(
    provider: str,
    base_path: str,
    config: dict[str, str],
    source_path: str,
    relative_path: str,
    retries: int = 3,
) -> StorageResult:
    if provider == "local":
        target = Path(base_path) / relative_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
            return StorageResult(True, "Copied to local destination", str(target))
        except OSError as exc:
            return StorageResult(False, str(exc), str(target))

    target = f"mailhub:{base_path.rstrip('/')}/{relative_path.lstrip('/')}"
    last = ""
    for attempt in range(1, retries + 1):
        code, output = await _run(
            "copyto", source_path, target,
            "--retries", "1",
            "--low-level-retries", "2",
            "--checkers", "4",
            "--transfers", "2",
            config_text=_config_text(provider, config),
            timeout=300,
        )
        if code == 0:
            return StorageResult(True, output or "Upload succeeded", target)
        last = f"Attempt {attempt}/{retries}: {output}"
        await asyncio.sleep(min(attempt * 2, 10))
    return StorageResult(False, last or "Upload failed", target)
