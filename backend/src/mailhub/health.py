import asyncio
from dataclasses import dataclass

import redis.asyncio as redis
from sqlalchemy import text

from mailhub.config import Settings
from mailhub.db.session import get_engine


@dataclass(frozen=True)
class ProbeResult:
    name: str
    healthy: bool
    detail: str


async def check_postgres(settings: Settings) -> ProbeResult:
    try:
        async with asyncio.timeout(settings.readiness_timeout_seconds):
            async with get_engine().connect() as connection:
                value = await connection.scalar(text("SELECT 1"))
        if value != 1:
            return ProbeResult("postgres", False, "unexpected query result")
        return ProbeResult("postgres", True, "ok")
    except Exception as exc:  # health endpoint must return a result, not crash
        return ProbeResult("postgres", False, type(exc).__name__)


async def check_redis(settings: Settings) -> ProbeResult:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        response = await asyncio.wait_for(
            client.ping(),
            timeout=settings.readiness_timeout_seconds,
        )
        if response is not True:
            return ProbeResult("redis", False, "unexpected ping result")
        return ProbeResult("redis", True, "ok")
    except Exception as exc:  # health endpoint must return a result, not crash
        return ProbeResult("redis", False, type(exc).__name__)
    finally:
        await client.aclose()


async def run_readiness_checks(settings: Settings) -> list[ProbeResult]:
    postgres_result, redis_result = await asyncio.gather(
        check_postgres(settings),
        check_redis(settings),
    )
    return [postgres_result, redis_result]
