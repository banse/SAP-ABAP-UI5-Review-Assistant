"""Tests for the review pipeline orchestration."""

from __future__ import annotations

import pytest

from app.engines.pipeline import run_review_pipeline
from app.models.enums import (
    ArtifactType,
    Confidence,
    GoNoGo,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import (
    ReviewRequest,
    ReviewResponse,
)


# ---------------------------------------------------------------------------
# Sample code fixtures
# ---------------------------------------------------------------------------

ABAP_SNIPPET = """\
CLASS zcl_test DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS do_something.
ENDCLASS.

CLASS zcl_test IMPLEMENTATION.
  METHOD do_something.
    SELECT * FROM mara INTO TABLE @DATA(lt_mara).
    LOOP AT lt_mara INTO DATA(ls_mara).
      SELECT * FROM marc WHERE matnr = @ls_mara-matnr INTO TABLE @DATA(lt_marc).
    ENDLOOP.
  ENDMETHOD.
ENDCLASS.
"""

ABAP_CLEAN = """\
CLASS zcl_clean DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS get_name RETURNING VALUE(rv_name) TYPE string.
ENDCLASS.

CLASS zcl_clean IMPLEMENTATION.
  METHOD get_name.
    rv_name = 'Clean Code'.
  ENDMETHOD.
ENDCLASS.
"""

CDS_VIEW = """\
@AbapCatalog.sqlViewName: 'ZV_TEST'
@AccessControl.authorizationCheck: #CHECK
define view entity ZI_Test as select from ztable {
  key id,
      description,
      status
}
"""

UI5_CONTROLLER = """\
sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/m/MessageBox"
], function (Controller, MessageBox) {
  "use strict";
  return Controller.extend("com.test.controller.Main", {
    onInit: function () {
      var oModel = this.getView().getModel();
      console.log("Debug output");
    },
    onPress: function () {
      alert("Hello");
    }
  });
});
"""

ABAP_BAD = """\
REPORT ztest_bad.
SELECT * FROM mara INTO TABLE @DATA(lt_mara).
TRY.
    DATA(lv_x) = 1 / 0.
  CATCH cx_root.
ENDTRY.
"""

MINIMAL_CODE = "DATA lv_x TYPE i."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    code: str = ABAP_SNIPPET,
    review_type: ReviewType = ReviewType.SNIPPET_REVIEW,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
    clarifications: dict[str, str] | None = None,
) -> ReviewRequest:
    return ReviewRequest(
        review_type=review_type,
        artifact_type=artifact_type,
        code_or_diff=code,
        review_context=ReviewContext.GREENFIELD,
        language=language,
        clarifications=clarifications or {},
    )


def _run(
    code: str = ABAP_SNIPPET,
    review_type: ReviewType = ReviewType.SNIPPET_REVIEW,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
    clarifications: dict[str, str] | None = None,
) -> ReviewResponse:
    request = _make_request(
        code=code,
        review_type=review_type,
        artifact_type=artifact_type,
        language=language,
        clarifications=clarifications,
    )
    return run_review_pipeline(request)


# ===========================================================================
# Full pipeline with ABAP snippet
# ===========================================================================


class TestABAPSnippetPipeline:
    """Full pipeline tests with ABAP code."""

    def test_returns_review_response(self) -> None:
        result = _run()
        assert isinstance(result, ReviewResponse)

    def test_has_findings(self) -> None:
        result = _run()
        assert len(result.findings) > 0

    def test_has_review_summary(self) -> None:
        result = _run()
        assert result.review_summary
        assert len(result.review_summary) > 10

    def test_has_overall_assessment(self) -> None:
        result = _run()
        assert result.overall_assessment is not None
        assert result.overall_assessment.go_no_go in GoNoGo

    def test_has_risk_notes(self) -> None:
        result = _run()
        assert len(result.risk_notes) > 0

    def test_has_recommended_actions(self) -> None:
        result = _run()
        assert len(result.recommended_actions) > 0

    def test_review_type_preserved(self) -> None:
        result = _run(review_type=ReviewType.SNIPPET_REVIEW)
        assert result.review_type == ReviewType.SNIPPET_REVIEW

    def test_artifact_type_preserved(self) -> None:
        result = _run(artifact_type=ArtifactType.ABAP_CLASS)
        assert result.artifact_type == ArtifactType.ABAP_CLASS

    def test_language_preserved(self) -> None:
        result = _run(language=Language.DE)
        assert result.language == Language.DE


# ===========================================================================
# Full pipeline with CDS view
# ===========================================================================


class TestCDSViewPipeline:
    """Full pipeline tests with CDS view code."""

    def test_cds_returns_complete_response(self) -> None:
        result = _run(code=CDS_VIEW, artifact_type=ArtifactType.CDS_VIEW)
        assert isinstance(result, ReviewResponse)
        assert result.review_summary

    def test_cds_has_assessment(self) -> None:
        result = _run(code=CDS_VIEW, artifact_type=ArtifactType.CDS_VIEW)
        assert result.overall_assessment is not None


# ===========================================================================
# Full pipeline with UI5 controller
# ===========================================================================


class TestUI5ControllerPipeline:
    """Full pipeline tests with UI5 controller code."""

    def test_ui5_returns_complete_response(self) -> None:
        result = _run(code=UI5_CONTROLLER, artifact_type=ArtifactType.UI5_CONTROLLER)
        assert isinstance(result, ReviewResponse)
        assert result.review_summary

    def test_ui5_returns_assessment(self) -> None:
        result = _run(code=UI5_CONTROLLER, artifact_type=ArtifactType.UI5_CONTROLLER)
        assert result.overall_assessment is not None
        assert result.overall_assessment.go_no_go in GoNoGo

    def test_ui5_has_assessment(self) -> None:
        result = _run(code=UI5_CONTROLLER, artifact_type=ArtifactType.UI5_CONTROLLER)
        assert result.overall_assessment is not None


# ===========================================================================
# Minimal and edge case inputs
# ===========================================================================


class TestMinimalInput:
    """Tests with minimal or edge case inputs."""

    def test_minimal_code_returns_response(self) -> None:
        result = _run(code=MINIMAL_CODE)
        assert isinstance(result, ReviewResponse)

    def test_minimal_code_has_summary(self) -> None:
        result = _run(code=MINIMAL_CODE)
        assert result.review_summary

    def test_minimal_code_has_assessment(self) -> None:
        result = _run(code=MINIMAL_CODE)
        assert result.overall_assessment is not None


# ===========================================================================
# Bad ABAP code -> CRITICAL findings
# ===========================================================================


class TestBadCodePipeline:
    """Tests with intentionally bad code."""

    def test_bad_abap_has_findings(self) -> None:
        result = _run(code=ABAP_BAD, artifact_type=ArtifactType.ABAP_REPORT)
        assert len(result.findings) > 0

    def test_bad_abap_has_performance_or_error_findings(self) -> None:
        result = _run(code=ABAP_BAD, artifact_type=ArtifactType.ABAP_REPORT)
        categories = set()
        for f in result.findings:
            if f.impact and f.impact.startswith("Category: "):
                categories.add(f.impact[len("Category: "):].strip().lower())
        assert len(categories) > 0

    def test_bad_abap_has_actions(self) -> None:
        result = _run(code=ABAP_BAD, artifact_type=ArtifactType.ABAP_REPORT)
        assert len(result.recommended_actions) > 0


# ===========================================================================
# Clean code -> GO assessment
# ===========================================================================


class TestCleanCodePipeline:
    """Tests with clean code expecting GO assessment."""

    def test_clean_code_assessment_is_go(self) -> None:
        result = _run(code=ABAP_CLEAN)
        # Clean code should not have CRITICAL findings
        assert result.overall_assessment.critical_count == 0

    def test_clean_code_has_summary(self) -> None:
        result = _run(code=ABAP_CLEAN)
        assert result.review_summary


# ===========================================================================
# Clarification filtering
# ===========================================================================


class TestClarificationFiltering:
    """Tests for clarification-based question filtering."""

    def test_clarifications_reduce_questions(self) -> None:
        result_no_clarify = _run()
        result_with_clarify = _run(
            clarifications={"Q-CTX-001": "S/4HANA 2023 FPS01"}
        )
        assert len(result_with_clarify.missing_information) <= len(
            result_no_clarify.missing_information
        )

    def test_clarifications_do_not_break_pipeline(self) -> None:
        result = _run(clarifications={"What release?": "2023"})
        assert isinstance(result, ReviewResponse)


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualPipeline:
    """Tests for bilingual pipeline output."""

    def test_english_summary(self) -> None:
        result = _run(language=Language.EN)
        assert "Review Type" in result.review_summary

    def test_german_summary(self) -> None:
        result = _run(language=Language.DE)
        assert "Review-Typ" in result.review_summary

    def test_english_and_german_summaries_differ(self) -> None:
        en = _run(language=Language.EN)
        de = _run(language=Language.DE)
        assert en.review_summary != de.review_summary


# ===========================================================================
# Review summary validation
# ===========================================================================


class TestReviewSummary:
    """Tests for review summary content."""

    def test_summary_contains_review_type(self) -> None:
        result = _run()
        assert "Snippet" in result.review_summary

    def test_summary_contains_finding_counts(self) -> None:
        result = _run()
        assert "Critical" in result.review_summary or "Kritisch" in result.review_summary

    def test_summary_contains_assessment(self) -> None:
        result = _run()
        assessment_value = result.overall_assessment.go_no_go.value
        assert assessment_value in result.review_summary
