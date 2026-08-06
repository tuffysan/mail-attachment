from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.db.models import (
    AttachmentRule,
    EmailAccount,
    StorageDestination,
    SystemMetadata,
)
from mailhub.setup.schemas import SetupStatusResponse

SETUP_COMPLETED_KEY = "setup.completed"
SETUP_LANGUAGE_KEY = "setup.language"
SETUP_TIMEZONE_KEY = "setup.timezone"


async def get_metadata_value(
    session: AsyncSession,
    key: str,
    default: str | None = None,
) -> str | None:
    value = await session.scalar(
        select(SystemMetadata.value).where(SystemMetadata.key == key)
    )
    return value if value is not None else default


async def set_metadata_value(
    session: AsyncSession,
    key: str,
    value: str,
) -> None:
    row = await session.scalar(
        select(SystemMetadata).where(SystemMetadata.key == key)
    )
    if row is None:
        session.add(SystemMetadata(key=key, value=value))
    else:
        row.value = value
    await session.flush()


async def _has_rows(session: AsyncSession, model: type) -> bool:
    count = await session.scalar(select(func.count()).select_from(model))
    return bool(count)


async def get_setup_state(session: AsyncSession) -> SetupStatusResponse:
    completed_value = await get_metadata_value(
        session,
        SETUP_COMPLETED_KEY,
        "false",
    )
    language = await get_metadata_value(session, SETUP_LANGUAGE_KEY, "sv")
    timezone = await get_metadata_value(
        session,
        SETUP_TIMEZONE_KEY,
        "Europe/Stockholm",
    )

    return SetupStatusResponse(
        completed=(completed_value or "").lower() == "true",
        language=language or "sv",
        timezone=timezone or "Europe/Stockholm",
        has_email_account=await _has_rows(session, EmailAccount),
        has_storage_destination=await _has_rows(session, StorageDestination),
        has_rule=await _has_rows(session, AttachmentRule),
    )
