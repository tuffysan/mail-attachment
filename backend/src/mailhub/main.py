import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse

from mailhub import __version__
from mailhub.api.auth import router as auth_router
from mailhub.api.backups import router as backups_router
from mailhub.api.email_accounts import router as email_accounts_router
from mailhub.api.mail_engine import router as mail_engine_router
from mailhub.api.rules import router as rules_router
from mailhub.api.storage import router as storage_router
from mailhub.api.admin import router as admin_router
from mailhub.api.system import router as system_router
from mailhub.api.setup import router as setup_router
from mailhub.api.operations import router as operations_router
from mailhub.api.oauth_admin import router as oauth_admin_router
from mailhub.api.updates import router as update_router
from mailhub.auth.bootstrap import ensure_bootstrap_admin
from mailhub.config import get_settings
from mailhub.db import close_database, initialize_database
from mailhub.health import run_readiness_checks
from mailhub.core.errors import install_exception_handlers
from mailhub.core.health import startup_state
from mailhub.core.metrics import metrics_registry
from mailhub.core.lifecycle import lifecycle_manager
from mailhub.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from mailhub.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    startup_state.begin()
    lifecycle_manager.reset()
    lifecycle_manager.shutdown_timeout_seconds = settings.shutdown_timeout_seconds
    lifecycle_manager.add_shutdown_hook("database", close_database)
    try:
        initialize_database(settings)
        await ensure_bootstrap_admin(settings)
        await lifecycle_manager.run_startup_hooks()
        startup_state.mark_ready()
        logger.info("application_started")
        yield
    except Exception as exc:
        startup_state.mark_failed(exc)
        logger.exception("application_startup_failed")
        raise
    finally:
        startup_state.mark_shutdown()
        lifecycle_manager.request_shutdown()
        await lifecycle_manager.run_shutdown_hooks()
        logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
install_exception_handlers(app)

excluded_paths = {
    path.strip()
    for path in settings.request_log_excluded_paths.split(",")
    if path.strip()
}
app.add_middleware(
    SecurityHeadersMiddleware,
    enabled=settings.security_headers_enabled,
)
app.add_middleware(
    RequestContextMiddleware,
    request_id_header=settings.request_id_header,
    correlation_id_header=settings.correlation_id_header,
    excluded_paths=excluded_paths,
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
    return {
        "status": "ok",
        "version": __version__,
    }


@app.get("/health/startup", tags=["health"])
async def startup(response: Response) -> dict[str, object]:
    healthy = startup_state.startup_complete and not startup_state.shutting_down
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if healthy else "starting",
        "startup_complete": startup_state.startup_complete,
        "shutting_down": startup_state.shutting_down,
        "started_at": startup_state.started_at,
        "ready_at": startup_state.ready_at,
        "startup_error": startup_state.startup_error,
    }


@app.get("/health/ready", tags=["health"])
async def readiness(response: Response) -> dict[str, Any]:
    checks = await run_readiness_checks(settings)
    healthy = (
        startup_state.startup_complete
        and not startup_state.shutting_down
        and all(check.healthy for check in checks)
    )
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if healthy else "degraded",
        "checks": {
            check.name: {
                "status": "ok" if check.healthy else "failed",
                "detail": check.detail,
                "latency_ms": check.latency_ms,
            }
            for check in checks
        },
    }


@app.get("/metrics", tags=["monitoring"], response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        metrics_registry.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


app.include_router(auth_router)
app.include_router(email_accounts_router)
app.include_router(mail_engine_router)
app.include_router(rules_router)
app.include_router(storage_router)
app.include_router(admin_router)
app.include_router(backups_router)
app.include_router(system_router)
app.include_router(setup_router)
app.include_router(operations_router)
app.include_router(oauth_admin_router)
app.include_router(update_router)
