"""End-to-end tests for the SAP ABAP/UI5 Review Assistant API.

These tests exercise the full request/response cycle through the FastAPI
application using httpx AsyncClient (no browser required).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

ABAP_SNIPPET = """\
CLASS zcl_test DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    METHODS do_something IMPORTING iv_value TYPE string.
ENDCLASS.

CLASS zcl_test IMPLEMENTATION.
  METHOD do_something.
    SELECT * FROM mara INTO TABLE @DATA(lt_mara).
    LOOP AT lt_mara INTO DATA(ls_mara).
      WRITE: / ls_mara-matnr.
    ENDLOOP.
  ENDMETHOD.
ENDCLASS.
"""

UI5_CONTROLLER_SNIPPET = """\
sap.ui.define([
  "sap/ui/core/mvc/Controller"
], function(Controller) {
  "use strict";
  return Controller.extend("my.app.controller.Main", {
    onInit: function() {
      var oModel = this.getView().getModel();
      oModel.read("/ProductSet", {
        success: function(oData) { console.log(oData); },
        error: function(oErr) { alert(oErr); }
      });
    }
  });
});
"""

DIFF_SNIPPET = """\
--- a/src/zcl_example.clas.abap
+++ b/src/zcl_example.clas.abap
@@ -10,6 +10,8 @@
   METHOD do_work.
     DATA lv_count TYPE i.
+    SELECT COUNT(*) FROM mara INTO lv_count.
+    IF lv_count > 100.
     WRITE: / 'Done'.
+    ENDIF.
   ENDMETHOD.
"""

MINIMAL_REVIEW_PAYLOAD = {
    "review_type": "SNIPPET_REVIEW",
    "artifact_type": "ABAP_CLASS",
    "code_or_diff": ABAP_SNIPPET,
    "input_mode": "snippet",
}


# ---------------------------------------------------------------------------
# Health & static endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_root_serves_html(client):
    """GET / returns the single-page frontend HTML."""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_root_health(client):
    """GET /health at root level returns status ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "db_available" in body


@pytest.mark.asyncio
async def test_api_health(client):
    """GET /api/health returns status ok with version."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.asyncio
async def test_static_css(client):
    """Static CSS file is served correctly."""
    resp = await client.get("/static/style.css")
    assert resp.status_code == 200
    assert "text/css" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_static_js(client):
    """Static JS file is served correctly."""
    resp = await client.get("/static/app.js")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Review endpoint — snippet mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_abap_snippet(client):
    """POST /api/review with ABAP snippet returns structured findings."""
    resp = await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert "findings" in body
    assert "overall_assessment" in body
    assert isinstance(body["findings"], list)


@pytest.mark.asyncio
async def test_review_ui5_controller(client):
    """POST /api/review with UI5 controller snippet returns findings."""
    payload = {
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "UI5_CONTROLLER",
        "code_or_diff": UI5_CONTROLLER_SNIPPET,
        "input_mode": "snippet",
    }
    resp = await client.post("/api/review", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "findings" in body
    assert isinstance(body["findings"], list)


@pytest.mark.asyncio
async def test_review_quality_gate_present(client):
    """POST /api/review response includes quality_gate."""
    resp = await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert "quality_gate" in body
    gate = body["quality_gate"]
    assert "passed" in gate or "status" in gate


# ---------------------------------------------------------------------------
# Review endpoint — diff mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_diff_mode(client):
    """POST /api/review with diff input_mode returns findings."""
    payload = {
        "review_type": "DIFF_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "code_or_diff": DIFF_SNIPPET,
        "input_mode": "diff",
    }
    resp = await client.post("/api/review", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "findings" in body


# ---------------------------------------------------------------------------
# Review endpoint — validation / error cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_empty_code_rejected(client):
    """POST /api/review with empty code_or_diff returns 422."""
    payload = {
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "code_or_diff": "",
        "input_mode": "snippet",
    }
    resp = await client.post("/api/review", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_review_whitespace_only_rejected(client):
    """POST /api/review with whitespace-only code returns 422."""
    payload = {
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "code_or_diff": "   \n\t  ",
        "input_mode": "snippet",
    }
    resp = await client.post("/api/review", json=payload)
    # Pydantic strips whitespace -> effectively empty -> min_length=1 fails
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_review_missing_required_field(client):
    """POST /api/review without review_type returns 422."""
    payload = {
        "artifact_type": "ABAP_CLASS",
        "code_or_diff": ABAP_SNIPPET,
    }
    resp = await client.post("/api/review", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_review_invalid_artifact_type(client):
    """POST /api/review with invalid artifact_type returns 422."""
    payload = {
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "NOT_A_REAL_TYPE",
        "code_or_diff": ABAP_SNIPPET,
    }
    resp = await client.post("/api/review", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_no_review_returns_404(client):
    """GET /api/export/markdown without prior review returns 404."""
    resp = await client.get("/api/export/markdown")
    # Could be 404 if no prior review in this test session
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_export_after_review(client):
    """Export markdown after running a review returns content."""
    # First run a review so _last_review is populated
    await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)

    resp = await client.get("/api/export/markdown")
    assert resp.status_code == 200
    assert len(resp.text) > 0


@pytest.mark.asyncio
async def test_export_sarif_format(client):
    """Export SARIF after review returns valid JSON."""
    await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)

    resp = await client.get("/api/export/sarif")
    assert resp.status_code == 200
    body = resp.json()
    assert "$schema" in body or "runs" in body


@pytest.mark.asyncio
async def test_export_unsupported_format(client):
    """GET /api/export/unknown returns 400."""
    await client.post("/api/review", json=MINIMAL_REVIEW_PAYLOAD)
    resp = await client.get("/api/export/unknown_format")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Examples endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_examples(client):
    """GET /api/examples returns a list of example cases."""
    resp = await client.get("/api/examples")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    first = body[0]
    assert "case_id" in first
    assert "title" in first


@pytest.mark.asyncio
async def test_get_example_by_id(client):
    """GET /api/examples/{case_id} returns example with code."""
    # First get the list to find a valid case_id
    list_resp = await client.get("/api/examples")
    cases = list_resp.json()
    assert len(cases) > 0

    case_id = cases[0]["case_id"]
    resp = await client.get(f"/api/examples/{case_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "code" in body
    assert len(body["code"]) > 0


@pytest.mark.asyncio
async def test_get_example_not_found(client):
    """GET /api/examples/nonexistent returns 404."""
    resp = await client.get("/api/examples/this_case_does_not_exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# History & statistics (graceful with no DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_history_list_graceful(client):
    """GET /api/history returns empty list when DB unavailable."""
    resp = await client.get("/api/history")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)


@pytest.mark.asyncio
async def test_statistics_graceful(client):
    """GET /api/statistics returns default stats when DB unavailable."""
    resp = await client.get("/api/statistics")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_reviews" in body
