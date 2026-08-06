import asyncio
import logging

from sqlalchemy import select

from mailhub.config import get_settings
from mailhub.db import close_database, initialize_database
from mailhub.db.models import EmailAccount
from mailhub.db.session import session_factory
from mailhub.logging_config import configure_logging
from mailhub.mail.sync import sync_account

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


async def run_once() -> None:
    async with session_factory() as session:
        ids = list(await session.scalars(select(EmailAccount.id).where(EmailAccount.is_enabled.is_(True))))
    for account_id in ids:
        for attempt in range(1, settings.sync_retry_attempts + 1):
            async with session_factory() as session:
                run = await sync_account(account_id, session, settings, attempt)
            if run.status == "succeeded":
                break
            if attempt < settings.sync_retry_attempts:
                await asyncio.sleep(settings.sync_retry_delay_seconds * attempt)


async def main() -> None:
    initialize_database(settings)
    logger.info("mail_worker_started")
    try:
        while True:
            try:
                await run_once()
            except Exception:
                logger.exception("mail_worker_cycle_failed")
            await asyncio.sleep(settings.sync_interval_seconds)
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
