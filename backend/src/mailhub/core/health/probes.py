import asyncio
from dataclasses import dataclass
from pathlib import Path

import redis.asyncio as redis
from sqlalchemy import text

from mailhub.config import Settings
from mailhub.db.session import get_engine


@dataclass(frozen=True)
class ProbeResult:
    name: str
    healthy: bool
    detail: str
    latency_ms: float | None = None


async def _timed(name: str, operation) -> ProbeResult:
    loop = asyncio.get_running_loop()
    started = loop.time()
    try:
        detail = await operation()
        latency_ms = round((loop.time() - started) * 1000, 2)
        return ProbeResult(name=name, healthy=True, detail=detail, latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = round((loop.time() - started) * 1000, 2)
        return ProbeResult(
            name=name,
            healthy=False,
            detail=type(exc).__name__,
            latency_ms=latency_ms,
        )


async def check_postgres(settings: Settings) -> ProbeResult:
    async def operation() -> str:
        async with asyncio.timeout(settings.readiness_timeout_seconds):
            async with get_engine().connect() as connection:
                value = await connection.scalar(text("SELECT 1"))
        if value != 1:
            raise RuntimeError("Unexpected database probe result")
        return "ok"

    return await _timed("postgres", operation)


async def check_redis(settings: Settings) -> ProbeResult:
    async def operation() -> str:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            response = await asyncio.wait_for(
                client.ping(),
                timeout=settings.readiness_timeout_seconds,
            )
            if response is not True:
                raise RuntimeError("Unexpected Redis probe result")
            return "ok"
        finally:
            await client.aclose()

    return await _timed("redis", operation)


async def check_attachment_storage(settings: Settings) -> ProbeResult:
    async def operation() -> str:
        path = Path(settings.attachment_data_dir)
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".mailhub-health-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return "writable"

    return await _timed("attachment_storage", operation)


async def run_readiness_checks(settings: Settings) -> list[ProbeResult]:
    return list(
        await asyncio.gather(
            check_postgres(settings),
            check_redis(settings),
            check_attachment_storage(settings),
        )
    )
