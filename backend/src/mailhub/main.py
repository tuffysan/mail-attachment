import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status

from mailhub import __version__
from mailhub.config import get_settings
from mailhub.health import run_readiness_checks
from mailhub.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_started")
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": __version__,
        "environment": settings.app_env,
    }


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/health/ready", tags=["health"])
async def readiness(response: Response) -> dict[str, Any]:
    checks = await run_readiness_checks(settings)
    healthy = all(check.healthy for check in checks)
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if healthy else "degraded",
        "checks": {
            check.name: {
                "status": "ok" if check.healthy else "failed",
                "detail": check.detail,
            }
            for check in checks
        },
    }
