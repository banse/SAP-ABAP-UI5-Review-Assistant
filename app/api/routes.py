"""API routes for the SAP ABAP/UI5 Review Assistant.

Endpoints:
    GET  /health                         -- Health check with version + DB status
    POST /review                         -- Submit code for review
    GET  /export/{format}                -- Export last review as markdown/sarif/ci_json
    GET  /examples                       -- List available example cases
    GET  /examples/{case_id}             -- Get a specific example case with code
    GET  /history                        -- List past reviews
    GET  /history/{review_id}            -- Get full review response
    DELETE /history/{review_id}          -- Delete single review
    DELETE /history                      -- Clear all history
    POST /review/{review_id}/feedback    -- Submit feedback for a finding
    GET  /review/{review_id}/feedback    -- Get feedback for a review
    GET  /similar/{review_id}            -- Find reviews similar to a given review
    GET  /statistics                     -- Aggregate review statistics
    GET  /patterns                       -- Recurring pattern analysis
"""

from __future__ import annotations

import logging
from typing import Any

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from app.engines.pipeline import run_review_pipeline
from app.engines.quality_gate import QualityGateConfig as QGConfig
from app.engines.quality_gate import evaluate_quality_gate
from app.formatter.ci_json import format_as_ci_json
from app.formatter.output import format_review_as_markdown
from app.formatter.sarif import format_as_sarif
from app.formatter.templates import (
    format_as_clipboard,
    format_as_markdown,
    format_as_ticket_comment,
)
from app.models.schemas import FindingResolutionRequest, ReviewRequest, ReviewResponse
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

        # Enrich with similarity data (async, graceful degradation)
        try:
            result = await _try_enrich_similarity(request, response, result)
        except Exception:
            logger.warning(
                "Failed to enrich with similarity data — result still returned.",
                exc_info=True,
            )

        # Evaluate quality gate (always included for CI consumers)
        try:
            gate_result = evaluate_quality_gate(result)
            result["quality_gate"] = gate_result.to_dict()
        except Exception:
            logger.warning(
                "Quality gate evaluation failed — result still returned.",
                exc_info=True,
            )

        return result

    except Exception as exc:
        logger.error("Review pipeline failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Review pipeline failed: {exc!s}",
        ) from exc


@router.get("/export/{fmt}", response_model=None)
async def export_review(fmt: str) -> PlainTextResponse | JSONResponse:
    """Export the last review result in the requested format.

    Supported formats:
        - ``markdown`` / ``md``: Full Markdown document
        - ``ticket``: Condensed ticket comment format
        - ``clipboard``: Plain text summary
        - ``sarif``: SARIF v2.1.0 JSON for code scanning integration
        - ``ci`` / ``ci_json``: CI-friendly JSON with quality gate
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

    if fmt.lower() == "sarif":
        sarif_output = format_as_sarif(response_dict)
        return JSONResponse(
            content=sarif_output,
            media_type="application/sarif+json",
        )

    if fmt.lower() in ("ci", "ci_json"):
        ci_output = format_as_ci_json(response_dict)
        return JSONResponse(
            content=ci_output,
            media_type="application/json",
        )

    raise HTTPException(
        status_code=400,
        detail=(
            f"Unsupported export format: {fmt}. "
            "Supported: markdown, md, ticket, clipboard, sarif, ci, ci_json"
        ),
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


async def _try_enrich_similarity(
    request: ReviewRequest,
    response: ReviewResponse,
    result: dict,
) -> dict:
    """Attempt to add similarity and recurring pattern data to the result.

    Best-effort: if the DB is unavailable, the result dict is returned unchanged.
    """
    try:
        from app.db.connection import get_session_factory

        session_factory = get_session_factory()
        if session_factory is None:
            return result

        from app.engines.similarity import (
            detect_recurring_patterns,
            find_similar_reviews,
        )

        # Extract current rule_ids
        current_rule_ids = [
            f.rule_id for f in response.findings if f.rule_id
        ]

        similar = await find_similar_reviews(
            code=request.code_or_diff,
            artifact_type=request.artifact_type.value,
            current_findings=current_rule_ids,
            limit=3,
        )

        similar_dicts = [sr.to_dict() for sr in similar]
        patterns = detect_recurring_patterns(current_rule_ids, similar)

        result["similar_reviews"] = similar_dicts
        result["recurring_patterns"] = patterns

    except Exception:
        logger.warning("Similarity enrichment failed", exc_info=True)

    return result


# ---------------------------------------------------------------------------
# Similarity & Statistics endpoints
# ---------------------------------------------------------------------------


@router.get("/similar/{review_id}")
async def find_similar(review_id: str) -> list[dict[str, Any]]:
    """Find reviews similar to a given review."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            record = await get_review_history(session, review_id)
            if record is None:
                raise HTTPException(status_code=404, detail="Review not found")

            from app.engines.similarity import find_similar_reviews

            full_resp = record.get("full_response") or {}
            code = ""  # code_snippet is stored truncated; use what we have
            # Try to get code from request or stored snippet
            findings = full_resp.get("findings") or []
            current_rule_ids = [
                f.get("rule_id") for f in findings if f.get("rule_id")
            ]

            # Fetch the actual code snippet from the record
            from app.db.models import ReviewHistoryRecord
            import uuid as _uuid

            uid = _uuid.UUID(review_id)
            db_record = await session.get(ReviewHistoryRecord, uid)
            if db_record and db_record.code_snippet:
                code = db_record.code_snippet

            artifact_type = record.get("artifact_type", "")

            similar = await find_similar_reviews(
                code=code,
                artifact_type=artifact_type,
                current_findings=current_rule_ids,
                limit=5,
            )

            # Exclude the source review itself
            return [
                sr.to_dict()
                for sr in similar
                if sr.review_id != review_id
            ]

    except HTTPException:
        raise
    except Exception:
        logger.warning("Similar search failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/statistics")
async def review_statistics() -> dict[str, Any]:
    """Return aggregate review statistics."""
    try:
        from app.engines.similarity import get_review_statistics

        return await get_review_statistics()
    except Exception:
        logger.warning("Statistics failed", exc_info=True)
        return {
            "total_reviews": 0,
            "most_common_findings": [],
            "most_common_artifact_types": [],
            "avg_findings_per_review": 0.0,
            "assessment_distribution": {"GO": 0, "CONDITIONAL_GO": 0, "NO_GO": 0},
        }


@router.get("/patterns")
async def recurring_patterns() -> list[dict[str, Any]]:
    """Analyse recurring patterns across all reviews."""
    try:
        from app.db.connection import get_session_factory
        from app.db.models import ReviewHistoryRecord

        session_factory = get_session_factory()
        if session_factory is None:
            return []

        from sqlalchemy import select

        async with session_factory() as session:
            stmt = select(ReviewHistoryRecord).order_by(
                ReviewHistoryRecord.created_at.desc()
            ).limit(100)
            rows = (await session.execute(stmt)).scalars().all()

            if not rows:
                return []

            from collections import Counter

            rule_counter: Counter[str] = Counter()
            rule_reviews: dict[str, list[str]] = {}

            for row in rows:
                findings = (row.full_response or {}).get("findings") or []
                for f in findings:
                    rid = f.get("rule_id")
                    if rid:
                        rule_counter[rid] += 1
                        if rid not in rule_reviews:
                            rule_reviews[rid] = []
                        rule_reviews[rid].append(str(row.id))

            return [
                {
                    "rule_id": rid,
                    "occurrence_count": count,
                    "reviews": rule_reviews.get(rid, [])[:10],
                }
                for rid, count in rule_counter.most_common(20)
                if count >= 2
            ]

    except Exception:
        logger.warning("Patterns analysis failed", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Finding Resolution endpoints
# ---------------------------------------------------------------------------


VALID_RESOLUTION_STATUSES = {"OPEN", "ACCEPTED", "REJECTED", "DEFERRED", "FIXED"}


@router.put("/review/{review_id}/findings/{finding_index}/resolution")
async def set_resolution(
    review_id: str,
    finding_index: int,
    body: FindingResolutionRequest,
) -> dict[str, Any]:
    """Set or update the resolution status for a finding."""
    if body.status not in VALID_RESOLUTION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {body.status}. Valid: {', '.join(sorted(VALID_RESOLUTION_STATUSES))}",
        )

    try:
        from app.db.connection import get_session_factory
        from app.db.repository import set_finding_resolution

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            result = await set_finding_resolution(
                session,
                review_id=review_id,
                finding_index=finding_index,
                status=body.status,
                reviewer_name=body.reviewer_name,
                comment=body.comment,
            )
            if result is None:
                raise HTTPException(status_code=404, detail="Review not found")
            return result
    except HTTPException:
        raise
    except Exception:
        logger.warning("Resolution set failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/review/{review_id}/resolutions")
async def get_resolutions(review_id: str) -> list[dict[str, Any]]:
    """Get all resolutions for a review."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_resolutions_for_review

        session_factory = get_session_factory()
        if session_factory is None:
            return []

        async with session_factory() as session:
            return await get_resolutions_for_review(session, review_id)
    except Exception:
        logger.warning("Resolutions get failed", exc_info=True)
        return []


@router.get("/review/{review_id}/completion")
async def get_completion(review_id: str) -> dict[str, Any]:
    """Get completion metrics for a review."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_review_completion

        session_factory = get_session_factory()
        if session_factory is None:
            return {"total_findings": 0, "resolved": 0, "completion_pct": 0.0, "by_status": {}}

        async with session_factory() as session:
            result = await get_review_completion(session, review_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Review not found")
            return result
    except HTTPException:
        raise
    except Exception:
        logger.warning("Completion get failed", exc_info=True)
        return {"total_findings": 0, "resolved": 0, "completion_pct": 0.0, "by_status": {}}


@router.get("/shared/{review_id}")
async def get_shared_review(review_id: str) -> dict[str, Any]:
    """Get a shared review with full response and resolutions."""
    try:
        from app.db.connection import get_session_factory
        from app.db.repository import get_resolutions_for_review, get_review_history

        session_factory = get_session_factory()
        if session_factory is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with session_factory() as session:
            review = await get_review_history(session, review_id)
            if review is None:
                raise HTTPException(status_code=404, detail="Review not found")

            resolutions = await get_resolutions_for_review(session, review_id)
            review["resolutions"] = resolutions
            return review
    except HTTPException:
        raise
    except Exception:
        logger.warning("Shared review get failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


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
