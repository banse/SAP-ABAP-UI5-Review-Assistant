"""Database configuration: engine, session factory, and table bootstrap.

Reads DATABASE_URL from the environment.  When the variable is absent or the
database is unreachable the application continues without persistence and logs
a warning instead of crashing.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_DEFAULT_URL = "postgresql+asyncpg://localhost:5432/sap_review_assistant"

DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_URL)

# ---------------------------------------------------------------------------
# Engine & session factory (lazily initialised)
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


def get_engine() -> AsyncEngine | None:
    """Return the current engine, or *None* if persistence is disabled."""
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Return the current session factory, or *None* if persistence is disabled."""
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession | None, None]:
    """FastAPI dependency that yields a session (or *None*)."""
    if _session_factory is None:
        yield None
        return
    async with _session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Startup / shutdown helpers
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Create the engine, verify connectivity, and create tables.

    On failure the engine is torn down and the app continues without a DB.
    """
    global _engine, _session_factory  # noqa: PLW0603

    try:
        _engine = _build_engine()

        # Verify the connection is actually reachable.
        async with _engine.begin() as conn:
            await conn.run_sync(lambda c: None)  # ping

        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

        await create_tables()
        logger.info("Database connected — persistence enabled (%s)", DATABASE_URL)

    except Exception:
        logger.warning(
            "Database unavailable — persistence DISABLED.  "
            "The /api/review endpoint will still work but results will not be stored.  "
            "Set DATABASE_URL to a reachable PostgreSQL instance to enable persistence.",
            exc_info=True,
        )
        if _engine is not None:
            await _engine.dispose()
        _engine = None
        _session_factory = None


async def close_db() -> None:
    """Dispose of the connection pool (call on shutdown)."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def create_tables() -> None:
    """Issue CREATE TABLE IF NOT EXISTS for every mapped model."""
    from app.db.models import Base  # local import to avoid circular refs

    if _engine is None:
        return
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
