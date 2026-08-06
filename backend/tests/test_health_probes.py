from pathlib import Path

import pytest

from mailhub.core.health.probes import check_attachment_storage
from mailhub.core.config import Settings


@pytest.mark.asyncio
async def test_attachment_storage_probe(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        APP_SECRET_KEY="x" * 32,
        ADMIN_PASSWORD="a-secure-password",
        ATTACHMENT_DATA_DIR=str(tmp_path),
    )

    result = await check_attachment_storage(settings)

    assert result.healthy is True
    assert result.detail == "writable"
    assert result.latency_ms is not None
    assert not (tmp_path / ".mailhub-health-probe").exists()
