import asyncio
from dataclasses import dataclass

import asyncpg
import redis.asyncio as redis

from mailhub.config import Settings


@dataclass(frozen=True)
class ProbeResult:
    name: str
    healthy: bool
    detail: str


async def check_postgres(settings: Settings) -> ProbeResult:
    connection: asyncpg.Connection | None = None
    try:
        connection = await asyncio.wait_for(
            asyncpg.connect(settings.database_url),
            timeout=settings.readiness_timeout_seconds,
        )
        value = await asyncio.wait_for(
            connection.fetchval("SELECT 1"),
            timeout=settings.readiness_timeout_seconds,
        )
        if value != 1:
            return ProbeResult("postgres", False, "unexpected query result")
        return ProbeResult("postgres", True, "ok")
    except Exception as exc:  # health endpoint must return a result, not crash
        return ProbeResult("postgres", False, type(exc).__name__)
    finally:
        if connection is not None:
            await connection.close()


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
