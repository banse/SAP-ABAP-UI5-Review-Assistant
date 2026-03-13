"""API routes for the SAP ABAP/UI5 Review Assistant.

Endpoints:
    GET  /health                         -- Health check with version + DB status
    POST /review                         -- Submit code for review
    GET  /export/{format}                -- Export last review as markdown
    GET  /examples                       -- List available example cases
    GET  /examples/{case_id}             -- Get a specific example case with code
    GET  /history                        -- List past reviews
    GET  /history/{review_id}            -- Get full review response
    DELETE /history/{review_id}          -- Delete single review
    DELETE /history                      -- Clear all history
    POST /review/{review_id}/feedback    -- Submit feedback for a finding
    GET  /review/{review_id}/feedback    -- Get feedback for a review
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.engines.pipeline import run_review_pipeline
from app.formatter.output import format_review_as_markdown
from app.formatter.templates import (
    format_as_clipboard,
    format_as_markdown,
    format_as_ticket_comment,
)
from app.models.schemas import ReviewRequest, ReviewResponse
from app.rules.example_cases import ALL_EXAMPLE_CASES, EXAMPLE_CASES_BY_ID

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for the last review result (for export endpoint)
_last_review: ReviewResponse | None = None


# ---------------------------------------------------------------------------
# Pydantic models for request bodies
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    """Body for POST /review/{review_id}/feedback."""
    finding_index: int
    rule_id: str | None = None
    helpful: bool
    comment: str | None = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> dict[str, Any]:
    """Return service health, version, and DB availability."""
    from app.db.connection import get_session_factory

    db_available = get_session_factory() is not None
    return {"status": "ok", "version": "0.1.0", "db_available": db_available}


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

@router.post("/review")
async def review(request: ReviewRequest) -> dict[str, Any]:
    """Accept a review request and return a full review response.

    Runs the complete review pipeline synchronously and returns
    the structured review result, plus an optional ``_history_id``.
    """
    global _last_review  # noqa: PLW0603

    try:
        response = run_review_pipeline(request)
        _last_review = response

        # Optionally persist to DB (async, graceful degradation)
        try:
            await _try_persist_review(request, response)
        except Exception:
            logger.warning(
                "Failed to persist review to database — result still returned.",
                exc_info=True,
            )

        # Also save to history (async, graceful degradation)
        history_id: str | None = None
        try:
            history_id = await _try_save_history(request, response)
        except Exception:
            logger.warning(
                "Failed to save review to history — result still returned.",
                exc_info=True,
            )

        result = response.model_dump(mode="json")
        if history_id:
            result["_history_id"] = history_id
        return result

    except Exception as exc:
        logger.error("Review pipeline failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Review pipeline failed: {exc!s}",
        ) from exc


@router.get("/export/{fmt}")
async def export_review(fmt: str) -> PlainTextResponse:
    """Export the last review result in the requested format.

    Supported formats:
        - ``markdown`` / ``md``: Full Markdown document
        - ``ticket``: Condensed ticket comment format
        - ``clipboard``: Plain text summary
    """
    if _last_review is None:
        raise HTTPException(
            status_code=404,
            detail="No review result available. Run a review first.",
        )

    response_dict = _last_review.model_dump(mode="json")
    lang = _last_review.language.value if _last_review.language else "EN"

    if fmt.lower() in ("markdown", "md"):
        content = format_review_as_markdown(_last_review)
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
        )

    if fmt.lower() == "ticket":
        content = format_as_ticket_comment(response_dict, language=lang)
        return PlainTextResponse(
            content=content,
            media_type="text/plain",
        )

    if fmt.lower() == "clipboard":
        content = format_as_clipboard(response_dict, language=lang)
        return PlainTextResponse(
            content=content,
            media_type="text/plain",
        )

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported export format: {fmt}. Supported: markdown, md, ticket, clipboard",
    )


@router.get("/examples")
async def list_examples() -> list[dict[str, str]]:
    """Return metadata for all available example cases.

    Each entry includes ``case_id``, ``title``, ``title_de``,
    ``description``, ``description_de``, ``review_type``, and
    ``artifact_type``.
    """
    return [
        {
            "case_id": case.case_id,
            "title": case.title,
            "title_de": case.title_de,
            "description": case.description,
            "description_de": case.description_de,
            "review_type": case.review_type,
            "artifact_type": case.artifact_type,
            "review_context": case.review_context,
        }
        for case in ALL_EXAMPLE_CASES
    ]


@router.get("/examples/{case_id}")
async def get_example(case_id: str) -> dict[str, Any]:
    """Return full example case including code for the given case_id."""
    case = EXAMPLE_CASES_BY_ID.get(case_id)
    if case is None:
        raise HTTPException(
            status_code=404,
            detail=f"Example case '{case_id}' not found.",
        )

    return {
        "case_id": case.case_id,
        "title": case.title,
        "title_de": case.title_de,
        "description": case.description,
        "description_de": case.description_de,
        "review_type": case.review_type,
        "artifact_type": case.artifact_type,
        "review_context": case.review_context,
        "code": case.code,
        "domain_tag": case.domain_tag,
    }


async def _try_persist_review(
    request: ReviewRequest,
    response: ReviewResponse,
) -> None:
    """Attempt to save the review to the database.

    This is best-effort: if the DB is unavailable, the review
    result is still returned to the caller.
    """
    try:
        from app.db.connection import get_session_factory

        session_factory = get_session_factory()
        if session_factory is None:
            return

        from app.db.models import ReviewRecord

        async with session_factory() as session:
            record = ReviewRecord(
                object_type=request.artifact_type.value,
                request_payload=request.model_dump(mode="json"),
                response_payload=response.model_dump(mode="json"),
            )
            session.add(record)
            await session.commit()
    except ImportError:
        pass  # DB models not available
    except Exception:
        raise


async def _try_save_history(
    request: ReviewRequest,
    response: ReviewResponse,
) -> str | None:
    """Attempt to save the review to the history table.

    Best-effort: if the DB is unavailable, the review result
    is still returned to the caller. Returns the history ID if saved.
    """
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import save_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            return None

        async with session_factory() as session:
            return await save_review_history(
                session,
                response=response.model_dump(mode="json"),
                request_summary=request.model_dump(mode="json"),
            )
    except Exception:
        logger.warning("Failed to save review to history", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# History endpoints
# ---------------------------------------------------------------------------


@router.get("/history")
async def list_history(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Return a summary list of past reviews."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import list_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            return []

        async with session_factory() as session:
            return await list_review_history(session, limit=limit, offset=offset)
    except Exception:
        logger.warning("History list failed", exc_info=True)
        return []


@router.get("/history/{review_id}")
async def get_history_entry(review_id: str) -> dict[str, Any]:
    """Return full review response for a given history record."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            result = await get_review_history(session, review_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Review not found")
            return result
    except HTTPException:
        raise
    except Exception:
        logger.warning("History get failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.delete("/history/{review_id}")
async def delete_history_entry(review_id: str) -> dict[str, Any]:
    """Delete a single history record."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import delete_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            deleted = await delete_review_history(session, review_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Review not found")
            return {"deleted": True}
    except HTTPException:
        raise
    except Exception:
        logger.warning("History delete failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.delete("/history")
async def clear_history() -> dict[str, Any]:
    """Clear all history records."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import clear_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            return {"deleted_count": 0}

        async with session_factory() as session:
            count = await clear_review_history(session)
            return {"deleted_count": count}
    except Exception:
        logger.warning("History clear failed", exc_info=True)
        return {"deleted_count": 0}


# ---------------------------------------------------------------------------
# Feedback endpoints
# ---------------------------------------------------------------------------


@router.post("/review/{review_id}/feedback")
async def submit_feedback(
    review_id: str,
    body: FeedbackRequest,
) -> dict[str, Any]:
    """Submit feedback for a finding."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import save_feedback

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            feedback_id = await save_feedback(
                session,
                review_id=review_id,
                finding_index=body.finding_index,
                rule_id=body.rule_id,
                helpful=body.helpful,
                comment=body.comment,
            )
            if feedback_id is None:
                raise HTTPException(status_code=404, detail="Review not found")
            return {"id": feedback_id}
    except HTTPException:
        raise
    except Exception:
        logger.warning("Feedback submit failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/review/{review_id}/feedback")
async def get_feedback(review_id: str) -> list[dict[str, Any]]:
    """Get all feedback for a review."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_feedback_for_review

        session_factory = get_session_factory()
        if session_factory is None:
            return []

        async with session_factory() as session:
            return await get_feedback_for_review(session, review_id)
    except Exception:
        logger.warning("Feedback get failed", exc_info=True)
        return []
