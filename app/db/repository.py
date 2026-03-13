"""Async CRUD helpers for ReviewRecord persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReviewRecord


async def save_review(
    session: AsyncSession | None,
    *,
    object_type: str | None = None,
    request_payload: dict,
    response_payload: dict,
) -> ReviewRecord | None:
    """Insert a new review record and return it.

    Returns *None* if session is unavailable (no DB).
    """
    if session is None:
        return None
    record = ReviewRecord(
        object_type=object_type,
        request_payload=request_payload,
        response_payload=response_payload,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_reviews(
    session: AsyncSession | None,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ReviewRecord], int]:
    """Return a page of records (newest first) together with the total count.

    Returns an empty list and zero count if session is unavailable.
    """
    if session is None:
        return [], 0

    count_stmt = select(func.count()).select_from(ReviewRecord)
    total: int = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(ReviewRecord)
        .order_by(ReviewRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()

    return list(rows), total


async def get_review_by_id(
    session: AsyncSession | None,
    record_id: uuid.UUID,
) -> ReviewRecord | None:
    """Fetch a single record by primary key, or *None* if not found.

    Returns *None* if session is unavailable.
    """
    if session is None:
        return None
    return await session.get(ReviewRecord, record_id)
