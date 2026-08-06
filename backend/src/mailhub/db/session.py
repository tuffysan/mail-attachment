from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mailhub.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def initialize_database(settings: Settings | None = None) -> None:
    """Create the process-wide async engine and session factory once."""

    global _engine, _session_factory
    if _engine is not None:
        return

    runtime_settings = settings or get_settings()
    _engine = create_async_engine(
        runtime_settings.database_url,
        pool_pre_ping=True,
        pool_size=runtime_settings.database_pool_size,
        max_overflow=runtime_settings.database_max_overflow,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def get_engine() -> AsyncEngine:
    if _engine is None:
        initialize_database()
    assert _engine is not None
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        initialize_database()
    assert _session_factory is not None
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that owns one transaction-capable session."""

    factory = get_session_factory()
    async with factory() as session:
        yield session


async def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
