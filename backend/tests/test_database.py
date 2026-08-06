import pytest

from mailhub.config import Settings
from mailhub.db import session as db_session


@pytest.mark.asyncio
async def test_database_engine_is_initialized_once() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://mailhub:secret@postgres:5432/mailhub"
    )

    db_session.initialize_database(settings)
    first_engine = db_session.get_engine()
    db_session.initialize_database(settings)

    assert db_session.get_engine() is first_engine
    await db_session.close_database()
