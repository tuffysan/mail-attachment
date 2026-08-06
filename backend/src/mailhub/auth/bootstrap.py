import logging

from sqlalchemy import select

from mailhub.auth.security import hash_password
from mailhub.config import Settings
from mailhub.db.models import User
from mailhub.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def ensure_bootstrap_admin(settings: Settings) -> None:
    if not settings.admin_email or not settings.admin_password:
        logger.warning("admin_bootstrap_skipped")
        return
    factory = get_session_factory()
    async with factory() as session:
        existing = await session.scalar(select(User).where(User.email == settings.admin_email))
        if existing is not None:
            return
        session.add(
            User(
                email=settings.admin_email,
                display_name=settings.admin_display_name,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
                is_active=True,
            )
        )
        await session.commit()
        logger.info("admin_bootstrap_created", extra={"email": settings.admin_email})
