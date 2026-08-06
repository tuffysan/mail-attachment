import asyncio
import logging
import signal

from sqlalchemy import select

from mailhub.config import get_settings
from mailhub.core.lifecycle import WorkerState, lifecycle_manager, worker_registry
from mailhub.db import close_database, initialize_database
from mailhub.db.models import EmailAccount
from mailhub.db.session import get_session_factory
from mailhub.logging_config import configure_logging
from mailhub.mail.sync import sync_account

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)
WORKER_NAME = "mail-sync"


async def run_once() -> None:
    factory = get_session_factory()
    async with factory() as session:
        ids = list(
            await session.scalars(
                select(EmailAccount.id).where(EmailAccount.is_enabled.is_(True))
            )
        )

    for account_id in ids:
        if lifecycle_manager.shutdown_requested:
            break
        for attempt in range(1, settings.sync_retry_attempts + 1):
            if lifecycle_manager.shutdown_requested:
                break
            async with factory() as session:
                run = await sync_account(account_id, session, settings, attempt)
            worker_registry.heartbeat(WORKER_NAME, activity=True)
            if run.status == "succeeded":
                break
            if attempt < settings.sync_retry_attempts:
                try:
                    await asyncio.wait_for(
                        lifecycle_manager.wait_for_shutdown(),
                        timeout=settings.sync_retry_delay_seconds * attempt,
                    )
                except TimeoutError:
                    pass


def install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def stop() -> None:
        logger.info("mail_worker_shutdown_requested")
        lifecycle_manager.request_shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop())


async def main() -> None:
    lifecycle_manager.reset()
    lifecycle_manager.shutdown_timeout_seconds = settings.shutdown_timeout_seconds
    worker_registry.register(WORKER_NAME)
    loop = asyncio.get_running_loop()
    install_signal_handlers(loop)
    initialize_database(settings)
    lifecycle_manager.add_shutdown_hook("database", close_database)
    worker_registry.set_state(WORKER_NAME, WorkerState.RUNNING)
    logger.info("mail_worker_started")
    try:
        while not lifecycle_manager.shutdown_requested:
            worker_registry.set_state(WORKER_NAME, WorkerState.RUNNING)
            try:
                await run_once()
                worker_registry.record_cycle(WORKER_NAME)
                worker_registry.set_state(WORKER_NAME, WorkerState.IDLE)
            except Exception as exc:
                worker_registry.record_failure(WORKER_NAME, exc)
                logger.exception("mail_worker_cycle_failed")

            try:
                await asyncio.wait_for(
                    lifecycle_manager.wait_for_shutdown(),
                    timeout=settings.sync_interval_seconds,
                )
            except TimeoutError:
                worker_registry.heartbeat(WORKER_NAME)
    finally:
        worker_registry.set_state(WORKER_NAME, WorkerState.STOPPING)
        await lifecycle_manager.run_shutdown_hooks()
        worker_registry.set_state(WORKER_NAME, WorkerState.STOPPED)
        logger.info("mail_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
