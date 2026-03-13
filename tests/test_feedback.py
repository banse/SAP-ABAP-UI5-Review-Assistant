"""Tests for per-finding feedback endpoints.

These tests run against the app without a real PostgreSQL database,
so they verify graceful degradation behavior.
"""

import httpx
import pytest


# ---------------------------------------------------------------------------
# POST /api/review/{review_id}/feedback — submit feedback
# ---------------------------------------------------------------------------


async def test_submit_feedback_no_db(client: httpx.AsyncClient) -> None:
    """POST feedback returns 503 or 404 when DB unavailable."""
    resp = await client.post(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback",
        json={"finding_index": 0, "helpful": True},
    )
    assert resp.status_code in (404, 503)


async def test_submit_feedback_with_comment(client: httpx.AsyncClient) -> None:
    """POST feedback with optional comment field."""
    resp = await client.post(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback",
        json={
            "finding_index": 1,
            "rule_id": "ABAP-PERF-001",
            "helpful": False,
            "comment": "This finding was not applicable to my case",
        },
    )
    assert resp.status_code in (404, 503)


async def test_submit_feedback_invalid_review_id(client: httpx.AsyncClient) -> None:
    """POST feedback with invalid UUID returns error gracefully."""
    resp = await client.post(
        "/api/review/not-a-valid-uuid/feedback",
        json={"finding_index": 0, "helpful": True},
    )
    assert resp.status_code in (404, 503)


async def test_submit_feedback_missing_fields(client: httpx.AsyncClient) -> None:
    """POST feedback without required fields returns 422."""
    resp = await client.post(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback",
        json={},
    )
    assert resp.status_code == 422


async def test_submit_feedback_missing_helpful(client: httpx.AsyncClient) -> None:
    """POST feedback without helpful field returns 422."""
    resp = await client.post(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback",
        json={"finding_index": 0},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/review/{review_id}/feedback — get feedback
# ---------------------------------------------------------------------------


async def test_get_feedback_no_db(client: httpx.AsyncClient) -> None:
    """GET feedback returns empty list when DB unavailable."""
    resp = await client.get(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback"
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_feedback_invalid_uuid(client: httpx.AsyncClient) -> None:
    """GET feedback with invalid UUID returns empty list gracefully."""
    resp = await client.get("/api/review/bad-uuid/feedback")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_feedback_nonexistent_review(client: httpx.AsyncClient) -> None:
    """GET feedback for nonexistent review returns empty list."""
    resp = await client.get(
        "/api/review/11111111-1111-1111-1111-111111111111/feedback"
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_feedback_request_body_types(client: httpx.AsyncClient) -> None:
    """Feedback request validates field types."""
    resp = await client.post(
        "/api/review/00000000-0000-0000-0000-000000000000/feedback",
        json={"finding_index": "not_a_number", "helpful": True},
    )
    assert resp.status_code == 422
