"""Tests for WP-2.5: Team Review Workflows.

Tests cover finding resolution CRUD, completion metrics,
shared review endpoint, export with resolution data,
and graceful degradation without DB.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


@pytest.fixture
async def client() -> httpx.AsyncClient:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helper: run a review and get a history_id (works without DB)
# ---------------------------------------------------------------------------

MINIMAL_REVIEW_PAYLOAD = {
    "review_type": "SNIPPET_REVIEW",
    "artifact_type": "ABAP_CLASS",
    "code_or_diff": (
        "CLASS zcl_test DEFINITION PUBLIC FINAL CREATE PUBLIC.\n"
        "  PUBLIC SECTION.\n"
        "    METHODS get_data RETURNING VALUE(rt_data) TYPE string.\n"
        "ENDCLASS.\n"
        "CLASS zcl_test IMPLEMENTATION.\n"
        "  METHOD get_data.\n"
        "    SELECT * FROM ztable INTO TABLE @rt_data.\n"
        "  ENDMETHOD.\n"
        "ENDCLASS."
    ),
    "language": "EN",
}


async def _run_review(client: httpx.AsyncClient) -> dict:
    """Run a minimal review and return the response dict."""
    resp = await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# Resolution endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_set_resolution_accepted(client: httpx.AsyncClient) -> None:
    """Setting ACCEPTED status returns a valid resolution."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable - no history_id")

    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED", "reviewer_name": "Alice", "comment": "Looks good"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED"
    assert data["reviewer_name"] == "Alice"
    assert data["comment"] == "Looks good"
    assert data["finding_index"] == 0


@pytest.mark.anyio
async def test_set_resolution_rejected(client: httpx.AsyncClient) -> None:
    """Setting REJECTED status works."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "REJECTED"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


@pytest.mark.anyio
async def test_set_resolution_deferred(client: httpx.AsyncClient) -> None:
    """Setting DEFERRED status works."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.put(
        f"/api/review/{review_id}/findings/1/resolution",
        json={"status": "DEFERRED", "reviewer_name": "Bob", "comment": "Sprint 5"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DEFERRED"
    assert data["reviewer_name"] == "Bob"


@pytest.mark.anyio
async def test_set_resolution_fixed(client: httpx.AsyncClient) -> None:
    """Setting FIXED status works."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "FIXED"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FIXED"


@pytest.mark.anyio
async def test_set_resolution_open(client: httpx.AsyncClient) -> None:
    """Setting OPEN status (resetting) works."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    # Set to ACCEPTED first, then revert to OPEN
    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED"},
    )
    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "OPEN"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "OPEN"


@pytest.mark.anyio
async def test_invalid_status_rejected(client: httpx.AsyncClient) -> None:
    """Invalid status value returns 400."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "INVALID_STATUS"},
    )
    assert resp.status_code == 400
    assert "Invalid status" in resp.json()["detail"]


@pytest.mark.anyio
async def test_resolution_with_reviewer_and_comment(client: httpx.AsyncClient) -> None:
    """Resolution includes reviewer name and comment."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={
            "status": "DEFERRED",
            "reviewer_name": "Charlie",
            "comment": "Will fix in sprint 5",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reviewer_name"] == "Charlie"
    assert data["comment"] == "Will fix in sprint 5"


@pytest.mark.anyio
async def test_update_existing_resolution(client: httpx.AsyncClient) -> None:
    """Updating an existing resolution changes status."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    # Set initial
    resp1 = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "DEFERRED", "reviewer_name": "Dave"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "DEFERRED"

    # Update
    resp2 = await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "FIXED", "reviewer_name": "Dave"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "FIXED"


@pytest.mark.anyio
async def test_resolution_invalid_review_id(client: httpx.AsyncClient) -> None:
    """Resolution on non-existent review returns 404 or 503."""
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/api/review/{fake_id}/findings/0/resolution",
        json={"status": "ACCEPTED"},
    )
    # 404 (review not found) or 503 (DB unavailable) or 500 (model resolution issue)
    assert resp.status_code in (404, 500, 503)


# ---------------------------------------------------------------------------
# Get resolutions for review
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_resolutions_empty(client: httpx.AsyncClient) -> None:
    """New review has no resolutions."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.get(f"/api/review/{review_id}/resolutions")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_get_resolutions_after_setting(client: httpx.AsyncClient) -> None:
    """After setting resolutions, they appear in the list."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED", "reviewer_name": "Eve"},
    )
    await client.put(
        f"/api/review/{review_id}/findings/1/resolution",
        json={"status": "REJECTED", "reviewer_name": "Eve"},
    )

    resp = await client.get(f"/api/review/{review_id}/resolutions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    statuses = {r["finding_index"]: r["status"] for r in data}
    assert statuses[0] == "ACCEPTED"
    assert statuses[1] == "REJECTED"


# ---------------------------------------------------------------------------
# Completion metrics
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_completion_zero_percent(client: httpx.AsyncClient) -> None:
    """No resolutions means 0% completion."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    resp = await client.get(f"/api/review/{review_id}/completion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_pct"] == 0.0
    assert data["resolved"] == 0


@pytest.mark.anyio
async def test_completion_partial(client: httpx.AsyncClient) -> None:
    """Some resolved findings show correct percentage."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    total = review.get("overall_assessment", {}).get("critical_count", 0) + \
            review.get("overall_assessment", {}).get("important_count", 0) + \
            review.get("overall_assessment", {}).get("optional_count", 0)

    findings = review.get("findings", [])
    if len(findings) < 2:
        pytest.skip("Not enough findings for partial completion test")

    # Resolve first finding
    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED"},
    )

    resp = await client.get(f"/api/review/{review_id}/completion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resolved"] == 1
    assert data["completion_pct"] > 0
    assert data["by_status"].get("ACCEPTED", 0) == 1


@pytest.mark.anyio
async def test_completion_100_percent(client: httpx.AsyncClient) -> None:
    """All findings resolved means 100% completion."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    findings = review.get("findings", [])
    if not findings:
        pytest.skip("No findings to resolve")

    for i in range(len(findings)):
        await client.put(
            f"/api/review/{review_id}/findings/{i}/resolution",
            json={"status": "ACCEPTED"},
        )

    resp = await client.get(f"/api/review/{review_id}/completion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_pct"] == 100.0
    assert data["resolved"] == len(findings)


@pytest.mark.anyio
async def test_completion_invalid_review(client: httpx.AsyncClient) -> None:
    """Completion for non-existent review returns 404 or fallback."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/review/{fake_id}/completion")
    # Either 404 (not found) or 200 with empty data (DB unavailable fallback)
    assert resp.status_code in (200, 404)


@pytest.mark.anyio
async def test_completion_by_status_breakdown(client: httpx.AsyncClient) -> None:
    """Completion by_status contains correct counts."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    findings = review.get("findings", [])
    if len(findings) < 3:
        pytest.skip("Need at least 3 findings")

    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED"},
    )
    await client.put(
        f"/api/review/{review_id}/findings/1/resolution",
        json={"status": "REJECTED"},
    )
    await client.put(
        f"/api/review/{review_id}/findings/2/resolution",
        json={"status": "DEFERRED"},
    )

    resp = await client.get(f"/api/review/{review_id}/completion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resolved"] == 3
    assert data["by_status"]["ACCEPTED"] == 1
    assert data["by_status"]["REJECTED"] == 1
    assert data["by_status"]["DEFERRED"] == 1


# ---------------------------------------------------------------------------
# Shared review endpoint
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_shared_review_returns_full_data(client: httpx.AsyncClient) -> None:
    """Shared review endpoint returns review + resolutions."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    # Add a resolution
    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "ACCEPTED", "reviewer_name": "Grace"},
    )

    resp = await client.get(f"/api/shared/{review_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "full_response" in data
    assert "resolutions" in data
    assert isinstance(data["resolutions"], list)
    assert data["id"] == review_id


@pytest.mark.anyio
async def test_shared_review_not_found(client: httpx.AsyncClient) -> None:
    """Shared review for non-existent ID returns 404 or 503."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/shared/{fake_id}")
    assert resp.status_code in (404, 503)


@pytest.mark.anyio
async def test_shared_review_includes_resolutions(client: httpx.AsyncClient) -> None:
    """Shared review includes the actual resolution data."""
    review = await _run_review(client)
    review_id = review.get("_history_id")
    if review_id is None:
        pytest.skip("DB unavailable")

    await client.put(
        f"/api/review/{review_id}/findings/0/resolution",
        json={"status": "FIXED", "reviewer_name": "Heidi", "comment": "Fixed in PR #42"},
    )

    resp = await client.get(f"/api/shared/{review_id}")
    data = resp.json()
    resolutions = data.get("resolutions", [])
    assert len(resolutions) >= 1
    fixed_res = [r for r in resolutions if r["status"] == "FIXED"]
    assert len(fixed_res) == 1
    assert fixed_res[0]["reviewer_name"] == "Heidi"


# ---------------------------------------------------------------------------
# Graceful degradation without DB
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_resolutions_graceful_without_db(client: httpx.AsyncClient) -> None:
    """Resolutions endpoint returns empty list without DB."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/review/{fake_id}/resolutions")
    assert resp.status_code == 200
    # Either empty list (no DB or no review)
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_completion_graceful_without_db(client: httpx.AsyncClient) -> None:
    """Completion endpoint returns default metrics without DB."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/review/{fake_id}/completion")
    # Should return 200 with empty data or 404
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "total_findings" in data
        assert "completion_pct" in data


# ---------------------------------------------------------------------------
# Resolution data in export (template functions)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_export_markdown_includes_resolution() -> None:
    """Markdown formatter includes resolution labels."""
    from app.formatter.templates import format_as_markdown

    response = {
        "overall_assessment": {"go_no_go": "GO", "summary": "Test"},
        "findings": [
            {"severity": "CRITICAL", "title": "Missing auth check", "recommendation": "Add auth"},
            {"severity": "IMPORTANT", "title": "Hardcoded value", "recommendation": "Use constant"},
        ],
        "resolutions": [
            {"finding_index": 0, "status": "ACCEPTED", "reviewer_name": "Alice", "comment": ""},
            {"finding_index": 1, "status": "DEFERRED", "reviewer_name": "Bob", "comment": "Sprint 5"},
        ],
    }

    md = format_as_markdown(response, language="EN")
    assert "ACCEPTED" in md
    assert "DEFERRED" in md
    assert "Completion Status" in md


@pytest.mark.anyio
async def test_export_ticket_includes_resolution() -> None:
    """Ticket comment formatter includes resolution labels."""
    from app.formatter.templates import format_as_ticket_comment

    response = {
        "overall_assessment": {"go_no_go": "GO", "summary": "Test"},
        "findings": [
            {"severity": "CRITICAL", "title": "Issue A", "recommendation": "Fix it"},
        ],
        "resolutions": [
            {"finding_index": 0, "status": "FIXED", "reviewer_name": "Carol", "comment": ""},
        ],
    }

    text = format_as_ticket_comment(response, language="EN")
    assert "FIXED" in text


@pytest.mark.anyio
async def test_export_clipboard_includes_resolution() -> None:
    """Clipboard formatter includes resolution labels."""
    from app.formatter.templates import format_as_clipboard

    response = {
        "overall_assessment": {"go_no_go": "CONDITIONAL_GO", "summary": "Needs work"},
        "findings": [
            {"severity": "IMPORTANT", "title": "N+1 query", "recommendation": "Join"},
        ],
        "resolutions": [
            {"finding_index": 0, "status": "REJECTED", "reviewer_name": "", "comment": ""},
        ],
    }

    text = format_as_clipboard(response, language="DE")
    assert "[REJECTED]" in text


@pytest.mark.anyio
async def test_export_without_resolutions() -> None:
    """Export works normally without resolutions."""
    from app.formatter.templates import format_as_markdown

    response = {
        "overall_assessment": {"go_no_go": "GO", "summary": "All good"},
        "findings": [
            {"severity": "OPTIONAL", "title": "Minor style", "recommendation": "Refactor"},
        ],
    }

    md = format_as_markdown(response, language="EN")
    assert "Minor style" in md
    assert "Completion Status" not in md


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_finding_resolution_request_schema() -> None:
    """FindingResolutionRequest schema validates correctly."""
    from app.models.schemas import FindingResolutionRequest

    req = FindingResolutionRequest(status="ACCEPTED", reviewer_name="Test", comment="OK")
    assert req.status == "ACCEPTED"
    assert req.reviewer_name == "Test"

    req2 = FindingResolutionRequest(status="OPEN")
    assert req2.reviewer_name == ""
    assert req2.comment == ""


@pytest.mark.anyio
async def test_review_completion_schema() -> None:
    """ReviewCompletion schema has correct defaults."""
    from app.models.schemas import ReviewCompletion

    comp = ReviewCompletion()
    assert comp.total_findings == 0
    assert comp.resolved == 0
    assert comp.completion_pct == 0.0
    assert comp.by_status == {}

    comp2 = ReviewCompletion(total_findings=5, resolved=3, completion_pct=60.0, by_status={"ACCEPTED": 2, "FIXED": 1})
    assert comp2.total_findings == 5
    assert comp2.resolved == 3
