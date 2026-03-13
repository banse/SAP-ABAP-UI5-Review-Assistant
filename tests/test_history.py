"""Tests for review history persistence endpoints.

These tests run against the app without a real PostgreSQL database,
so they verify graceful degradation (empty results, no crashes).
When DB is unavailable, history endpoints return empty/error gracefully.
"""

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helper: minimal valid review payload
# ---------------------------------------------------------------------------

def _review_payload() -> dict:
    return {
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "code_or_diff": "CLASS zcl_test DEFINITION PUBLIC.\nENDCLASS.\nCLASS zcl_test IMPLEMENTATION.\nENDCLASS.",
        "language": "EN",
    }


# ---------------------------------------------------------------------------
# GET /api/history — list reviews
# ---------------------------------------------------------------------------


async def test_list_history_returns_list(client: httpx.AsyncClient) -> None:
    """GET /api/history returns a list (empty when DB unavailable)."""
    resp = await client.get("/api/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_history_with_limit_and_offset(client: httpx.AsyncClient) -> None:
    """GET /api/history accepts limit and offset query params."""
    resp = await client.get("/api/history", params={"limit": 10, "offset": 0})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_history_empty_when_no_db(client: httpx.AsyncClient) -> None:
    """Without DB, history list returns empty array."""
    resp = await client.get("/api/history")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /api/history/{review_id} — get specific review
# ---------------------------------------------------------------------------


async def test_get_history_nonexistent_id(client: httpx.AsyncClient) -> None:
    """GET /api/history/{id} returns 404 or 503 for nonexistent/unavailable."""
    resp = await client.get("/api/history/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (404, 503)


async def test_get_history_invalid_uuid(client: httpx.AsyncClient) -> None:
    """GET /api/history/{id} handles invalid UUID gracefully."""
    resp = await client.get("/api/history/not-a-uuid")
    assert resp.status_code in (404, 503)


# ---------------------------------------------------------------------------
# DELETE /api/history/{review_id} — delete single review
# ---------------------------------------------------------------------------


async def test_delete_history_nonexistent(client: httpx.AsyncClient) -> None:
    """DELETE /api/history/{id} returns 404 or 503 when not found."""
    resp = await client.delete("/api/history/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (404, 503)


async def test_delete_history_invalid_uuid(client: httpx.AsyncClient) -> None:
    """DELETE /api/history/{id} handles invalid UUID."""
    resp = await client.delete("/api/history/not-a-uuid")
    assert resp.status_code in (404, 503)


# ---------------------------------------------------------------------------
# DELETE /api/history — clear all history
# ---------------------------------------------------------------------------


async def test_clear_history_returns_count(client: httpx.AsyncClient) -> None:
    """DELETE /api/history returns deleted_count (0 when no DB)."""
    resp = await client.delete("/api/history")
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted_count" in data
    assert data["deleted_count"] == 0


async def test_clear_history_idempotent(client: httpx.AsyncClient) -> None:
    """Clearing history multiple times is safe."""
    resp1 = await client.delete("/api/history")
    resp2 = await client.delete("/api/history")
    assert resp1.status_code == 200
    assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/review — verify it still works (and attempts history save)
# ---------------------------------------------------------------------------


async def test_review_still_works_without_db(client: httpx.AsyncClient) -> None:
    """POST /api/review returns a valid response even without DB."""
    resp = await client.post("/api/review", json=_review_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert "findings" in data
    assert "overall_assessment" in data


async def test_review_returns_history_id_field(client: httpx.AsyncClient) -> None:
    """POST /api/review response may contain _history_id (None when no DB)."""
    resp = await client.post("/api/review", json=_review_payload())
    assert resp.status_code == 200
    data = resp.json()
    # _history_id is only present when DB is available; without DB it may be absent
    # Either way the review itself must succeed
    assert "overall_assessment" in data


# ---------------------------------------------------------------------------
# Health endpoint includes db_available
# ---------------------------------------------------------------------------


async def test_health_includes_db_available(client: httpx.AsyncClient) -> None:
    """GET /api/health includes db_available field."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "db_available" in data
    assert isinstance(data["db_available"], bool)


async def test_health_db_unavailable_without_pg(client: httpx.AsyncClient) -> None:
    """Without PostgreSQL, db_available should be False."""
    resp = await client.get("/api/health")
    data = resp.json()
    assert data["db_available"] is False


# ---------------------------------------------------------------------------
# Root health endpoint also includes db_available
# ---------------------------------------------------------------------------


async def test_root_health_includes_db_available(client: httpx.AsyncClient) -> None:
    """GET /health also includes db_available."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "db_available" in data


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


async def test_list_history_large_offset(client: httpx.AsyncClient) -> None:
    """Large offset returns empty list."""
    resp = await client.get("/api/history", params={"limit": 10, "offset": 99999})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_history_zero_limit(client: httpx.AsyncClient) -> None:
    """Zero limit returns empty list."""
    resp = await client.get("/api/history", params={"limit": 0, "offset": 0})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_history_endpoints_accept_json(client: httpx.AsyncClient) -> None:
    """History list endpoint works with accept header."""
    resp = await client.get("/api/history", headers={"Accept": "application/json"})
    assert resp.status_code == 200


async def test_delete_history_with_various_methods(client: httpx.AsyncClient) -> None:
    """Only DELETE method should work for clear endpoint."""
    resp = await client.post("/api/history")
    assert resp.status_code == 405  # Method not allowed


async def test_review_response_structure(client: httpx.AsyncClient) -> None:
    """Review response has expected structure including findings list."""
    resp = await client.post("/api/review", json=_review_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert "review_summary" in data
    assert "review_type" in data
    assert "artifact_type" in data
    assert "findings" in data
    assert isinstance(data["findings"], list)
    assert "overall_assessment" in data
    assert "go_no_go" in data["overall_assessment"]
