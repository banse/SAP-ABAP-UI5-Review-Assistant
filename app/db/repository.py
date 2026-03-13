"""Async CRUD helpers for ReviewRecord and ReviewHistoryRecord persistence."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FindingFeedback, ReviewHistoryRecord, ReviewRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Legacy ReviewRecord helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Review History helpers
# ---------------------------------------------------------------------------


async def save_review_history(
    session: AsyncSession | None,
    *,
    response: dict,
    request_summary: dict,
) -> str | None:
    """Save a review to history. Returns the new record ID or None if DB unavailable."""
    if session is None:
        return None
    try:
        code_snippet = (request_summary.get("code_or_diff") or "")[:500]
        findings = response.get("findings") or []
        assessment = response.get("overall_assessment") or {}

        record = ReviewHistoryRecord(
            review_type=request_summary.get("review_type", "SNIPPET_REVIEW"),
            artifact_type=request_summary.get("artifact_type", "ABAP_CLASS"),
            code_snippet=code_snippet if code_snippet else None,
            finding_count=len(findings),
            overall_assessment=assessment.get("go_no_go", "GO"),
            full_response=response,
            language=request_summary.get("language"),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return str(record.id)
    except Exception:
        logger.warning("Failed to save review to history", exc_info=True)
        return None


async def list_review_history(
    session: AsyncSession | None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Return summary list of past reviews, newest first.

    Returns empty list if DB unavailable.
    """
    if session is None:
        return []
    try:
        stmt = (
            select(ReviewHistoryRecord)
            .order_by(ReviewHistoryRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(r.id),
                "created_at": r.created_at.isoformat(),
                "review_type": r.review_type,
                "artifact_type": r.artifact_type,
                "finding_count": r.finding_count,
                "overall_assessment": r.overall_assessment,
                "language": r.language,
            }
            for r in rows
        ]
    except Exception:
        logger.warning("Failed to list review history", exc_info=True)
        return []


async def get_review_history(
    session: AsyncSession | None,
    review_id: str,
) -> dict | None:
    """Return full review response for a given history record, or None."""
    if session is None:
        return None
    try:
        uid = uuid.UUID(review_id)
        record = await session.get(ReviewHistoryRecord, uid)
        if record is None:
            return None
        return {
            "id": str(record.id),
            "created_at": record.created_at.isoformat(),
            "review_type": record.review_type,
            "artifact_type": record.artifact_type,
            "finding_count": record.finding_count,
            "overall_assessment": record.overall_assessment,
            "language": record.language,
            "full_response": record.full_response,
        }
    except Exception:
        logger.warning("Failed to get review history record", exc_info=True)
        return None


async def delete_review_history(
    session: AsyncSession | None,
    review_id: str,
) -> bool:
    """Delete a single history record. Returns True if deleted, False otherwise."""
    if session is None:
        return False
    try:
        uid = uuid.UUID(review_id)
        record = await session.get(ReviewHistoryRecord, uid)
        if record is None:
            return False
        await session.delete(record)
        await session.commit()
        return True
    except Exception:
        logger.warning("Failed to delete review history record", exc_info=True)
        return False


async def clear_review_history(
    session: AsyncSession | None,
) -> int:
    """Delete all history records. Returns count deleted."""
    if session is None:
        return 0
    try:
        result = await session.execute(delete(ReviewHistoryRecord))
        await session.commit()
        return result.rowcount  # type: ignore[return-value]
    except Exception:
        logger.warning("Failed to clear review history", exc_info=True)
        return 0


# ---------------------------------------------------------------------------
# Finding Feedback helpers
# ---------------------------------------------------------------------------


async def save_feedback(
    session: AsyncSession | None,
    *,
    review_id: str,
    finding_index: int,
    rule_id: str | None = None,
    helpful: bool,
    comment: str | None = None,
) -> str | None:
    """Save feedback for a finding. Returns feedback ID or None."""
    if session is None:
        return None
    try:
        uid = uuid.UUID(review_id)
        # Verify the review exists
        review = await session.get(ReviewHistoryRecord, uid)
        if review is None:
            return None

        feedback = FindingFeedback(
            review_id=uid,
            finding_index=finding_index,
            rule_id=rule_id,
            helpful=helpful,
            comment=comment,
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return str(feedback.id)
    except Exception:
        logger.warning("Failed to save feedback", exc_info=True)
        return None


async def get_feedback_for_review(
    session: AsyncSession | None,
    review_id: str,
) -> list[dict]:
    """Return all feedback entries for a review."""
    if session is None:
        return []
    try:
        uid = uuid.UUID(review_id)
        stmt = (
            select(FindingFeedback)
            .where(FindingFeedback.review_id == uid)
            .order_by(FindingFeedback.finding_index)
        )
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(fb.id),
                "review_id": str(fb.review_id),
                "finding_index": fb.finding_index,
                "rule_id": fb.rule_id,
                "helpful": fb.helpful,
                "comment": fb.comment,
                "created_at": fb.created_at.isoformat(),
            }
            for fb in rows
        ]
    except Exception:
        logger.warning("Failed to get feedback for review", exc_info=True)
        return []
