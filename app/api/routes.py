"""API routes for the SAP ABAP/UI5 Review Assistant.

Endpoints:
    GET  /health             -- Health check with version
    POST /review             -- Submit code for review
    GET  /export/{format}    -- Export last review as markdown
    GET  /examples           -- List available example cases
    GET  /examples/{case_id} -- Get a specific example case with code
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.engines.pipeline import run_review_pipeline
from app.formatter.output import format_review_as_markdown
from app.models.schemas import ReviewRequest, ReviewResponse
from app.rules.example_cases import ALL_EXAMPLE_CASES, EXAMPLE_CASES_BY_ID

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for the last review result (for export endpoint)
_last_review: ReviewResponse | None = None


@router.get("/health")
async def health() -> dict[str, str]:
    """Return service health and version."""
    return {"status": "ok", "version": "0.1.0"}


@router.post("/review")
async def review(request: ReviewRequest) -> ReviewResponse:
    """Accept a review request and return a full review response.

    Runs the complete review pipeline synchronously and returns
    the structured review result.
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

        return response

    except Exception as exc:
        logger.error("Review pipeline failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Review pipeline failed: {exc!s}",
        ) from exc


@router.get("/export/{fmt}")
async def export_review(fmt: str) -> PlainTextResponse:
    """Export the last review result in the requested format.

    Currently supported formats:
        - ``markdown`` / ``md``: Markdown document
    """
    if _last_review is None:
        raise HTTPException(
            status_code=404,
            detail="No review result available. Run a review first.",
        )

    if fmt.lower() in ("markdown", "md"):
        content = format_review_as_markdown(_last_review)
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
        )

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported export format: {fmt}. Supported: markdown, md",
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
