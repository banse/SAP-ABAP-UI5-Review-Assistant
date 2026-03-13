"""Tests for the design review engine and pipeline routing."""

from __future__ import annotations

import pytest

from app.engines.design_reviewer import run_design_review
from app.engines.pipeline import run_review_pipeline
from app.models.enums import (
    ArtifactType,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import Finding, ReviewRequest, ReviewResponse


# ---------------------------------------------------------------------------
# Sample design texts
# ---------------------------------------------------------------------------

INCOMPLETE_DESIGN = (
    "We plan to build a custom Fiori app for sales order management. "
    "The app will use OData V4 with RAP managed scenario. "
    "Entities: SalesOrder, SalesOrderItem, Customer. "
    "The data volume is expected to be 500,000 orders per year."
)

COMPLETE_DESIGN = (
    "We plan to build a custom Fiori app for sales order management. "
    "The app will use OData V4 with RAP managed scenario using released APIs "
    "aligned with clean core strategy. "
    "Entities: SalesOrder (key field: SalesOrderID, attributes: BuyerName, Status, "
    "TotalAmount; association to SalesOrderItem with cardinality 1:N), "
    "SalesOrderItem (key field: ItemID, attributes: ProductID, Quantity, Price; "
    "foreign key to SalesOrder), Customer (key field: CustomerID, attributes: Name, "
    "Region; relationship to SalesOrder 1:N). "
    "The UI uses a list report floorplan for the overview and an object page "
    "for detail editing — this pattern was chosen because the primary user "
    "interaction is browse-then-edit on structured transactional data. "
    "Authorization is handled via CDS access control with roles for sales clerk "
    "and sales manager with different permission levels. "
    "Error handling: all RAP validations return structured messages; the UI shows "
    "message popover for backend errors; retry logic for transient failures. "
    "Test strategy: ABAP unit tests for validations and determinations, "
    "OPA5 integration tests for UI flows, test plan with acceptance criteria. "
    "Performance: pagination on list report (default 30 rows), background job "
    "for mass order processing, database indexes on status and date fields. "
    "The solution is upgrade safe by using only released APIs and ABAP Cloud tier 1."
)

DESIGN_WITH_ODATA_V2 = (
    "We will build a new Fiori app using OData V2 services. "
    "The app will create and process purchase orders."
)

DESIGN_WITH_DYNPRO = (
    "We will build a new screen painter Dynpro for warehouse management. "
    "The application will process goods movements."
)

DESIGN_WITH_INTEGRATION = (
    "The solution integrates with an external CRM system via API call. "
    "We will also connect to a third-party logistics provider."
)

DESIGN_WITH_MIGRATION = (
    "We need to migrate the legacy custom Z-reports to a new extension "
    "based on RAP. The existing data must be converted."
)

DESIGN_MINIMAL = "We plan to build something."

DESIGN_WITH_AUTH = (
    "We plan to build a custom app for sales order management. "
    "Authorization is handled via role-based access control. "
    "The security model includes data-level permissions."
)

DESIGN_WITH_TESTS = (
    "We plan to build a custom app for sales order management. "
    "Our test strategy includes unit tests, integration tests, "
    "and end-to-end acceptance criteria."
)

DESIGN_WITH_PERFORMANCE = (
    "We plan to build a custom app for processing 500,000 orders per year. "
    "Performance is ensured through caching, pagination, and background processing."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_design(
    text: str = INCOMPLETE_DESIGN,
    language: Language = Language.EN,
) -> list[Finding]:
    return run_design_review(code=text, language=language)


def _run_pipeline_design(
    text: str = INCOMPLETE_DESIGN,
    language: Language = Language.EN,
) -> ReviewResponse:
    request = ReviewRequest(
        review_type=ReviewType.SOLUTION_DESIGN_REVIEW,
        artifact_type=ArtifactType.MIXED_FULLSTACK,
        code_or_diff=text,
        review_context=ReviewContext.GREENFIELD,
        language=language,
    )
    return run_review_pipeline(request)


# ===========================================================================
# DESIGN-COMP-001: Missing error handling strategy
# ===========================================================================


class TestDesignComp001:
    """Missing error handling strategy."""

    def test_fires_on_operations_without_error_handling(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-001" in rule_ids

    def test_does_not_fire_on_complete_design(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-001" not in rule_ids

    def test_severity_is_important(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        comp001 = [f for f in findings if f.rule_id == "DESIGN-COMP-001"]
        assert comp001
        assert comp001[0].severity == Severity.IMPORTANT


# ===========================================================================
# DESIGN-COMP-002: Missing authorization concept
# ===========================================================================


class TestDesignComp002:
    """Missing authorization concept."""

    def test_fires_when_no_auth_mentioned(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-002" in rule_ids

    def test_does_not_fire_when_auth_present(self) -> None:
        findings = _run_design(DESIGN_WITH_AUTH)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-002" not in rule_ids

    def test_severity_is_important(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        comp002 = [f for f in findings if f.rule_id == "DESIGN-COMP-002"]
        assert comp002
        assert comp002[0].severity == Severity.IMPORTANT


# ===========================================================================
# DESIGN-COMP-003: Missing test strategy
# ===========================================================================


class TestDesignComp003:
    """Missing test strategy."""

    def test_fires_when_no_test_mentioned(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-003" in rule_ids

    def test_does_not_fire_when_tests_present(self) -> None:
        findings = _run_design(DESIGN_WITH_TESTS)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-003" not in rule_ids

    def test_severity_is_important(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        comp003 = [f for f in findings if f.rule_id == "DESIGN-COMP-003"]
        assert comp003
        assert comp003[0].severity == Severity.IMPORTANT


# ===========================================================================
# DESIGN-COMP-004: Missing performance considerations
# ===========================================================================


class TestDesignComp004:
    """Missing performance considerations."""

    def test_fires_on_large_volume_without_perf(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-004" in rule_ids

    def test_does_not_fire_when_perf_addressed(self) -> None:
        findings = _run_design(DESIGN_WITH_PERFORMANCE)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-004" not in rule_ids

    def test_does_not_fire_without_volume_mention(self) -> None:
        findings = _run_design(DESIGN_MINIMAL)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-004" not in rule_ids


# ===========================================================================
# DESIGN-COMP-005: Missing migration/cutover plan
# ===========================================================================


class TestDesignComp005:
    """Missing migration/cutover plan."""

    def test_fires_on_migration_without_cutover(self) -> None:
        findings = _run_design(DESIGN_WITH_MIGRATION)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-005" in rule_ids

    def test_does_not_fire_without_migration(self) -> None:
        findings = _run_design(DESIGN_MINIMAL)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-005" not in rule_ids


# ===========================================================================
# DESIGN-COMP-006: Technology choice concern
# ===========================================================================


class TestDesignComp006:
    """Technology choice concern."""

    def test_fires_on_odata_v2(self) -> None:
        findings = _run_design(DESIGN_WITH_ODATA_V2)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-006" in rule_ids

    def test_fires_on_dynpro(self) -> None:
        findings = _run_design(DESIGN_WITH_DYNPRO)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-006" in rule_ids

    def test_does_not_fire_on_modern_stack(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-006" not in rule_ids

    def test_severity_is_optional(self) -> None:
        findings = _run_design(DESIGN_WITH_ODATA_V2)
        comp006 = [f for f in findings if f.rule_id == "DESIGN-COMP-006"]
        assert comp006
        assert comp006[0].severity == Severity.OPTIONAL


# ===========================================================================
# DESIGN-COMP-007: Missing clean-core considerations
# ===========================================================================


class TestDesignComp007:
    """Missing clean-core considerations."""

    def test_fires_on_custom_without_clean_core(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-007" in rule_ids

    def test_does_not_fire_on_complete_design(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-007" not in rule_ids


# ===========================================================================
# DESIGN-COMP-008: Missing integration point documentation
# ===========================================================================


class TestDesignComp008:
    """Missing integration point documentation."""

    def test_fires_on_integration_without_details(self) -> None:
        findings = _run_design(DESIGN_WITH_INTEGRATION)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-008" in rule_ids

    def test_does_not_fire_without_integration(self) -> None:
        findings = _run_design(DESIGN_MINIMAL)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-008" not in rule_ids


# ===========================================================================
# DESIGN-COMP-009: Incomplete entity model
# ===========================================================================


class TestDesignComp009:
    """Incomplete entity model."""

    def test_fires_on_entities_without_fields(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-009" in rule_ids

    def test_does_not_fire_on_fully_specified_entities(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-009" not in rule_ids


# ===========================================================================
# DESIGN-COMP-010: Missing UI pattern justification
# ===========================================================================


class TestDesignComp010:
    """Missing UI pattern justification."""

    def test_fires_on_fiori_without_pattern_rationale(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-010" in rule_ids

    def test_does_not_fire_on_complete_design(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        rule_ids = [f.rule_id for f in findings]
        assert "DESIGN-COMP-010" not in rule_ids


# ===========================================================================
# Complete design text — negative tests
# ===========================================================================


class TestCompleteDesign:
    """Complete design text should trigger minimal or no findings."""

    def test_complete_design_has_few_findings(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        # Complete design should have very few findings
        assert len(findings) <= 2

    def test_complete_design_no_important_findings(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        important = [f for f in findings if f.severity == Severity.IMPORTANT]
        assert len(important) == 0

    def test_complete_design_no_critical_findings(self) -> None:
        findings = _run_design(COMPLETE_DESIGN)
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(critical) == 0


# ===========================================================================
# Findings structure and sorting
# ===========================================================================


class TestFindingsStructure:
    """Design review findings have correct structure and sorting."""

    def test_findings_are_finding_objects(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        assert len(findings) > 0
        for f in findings:
            assert isinstance(f, Finding)

    def test_findings_have_rule_ids(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        for f in findings:
            assert f.rule_id is not None
            assert f.rule_id.startswith("DESIGN-COMP-")

    def test_findings_have_category(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        for f in findings:
            assert "design_completeness" in f.impact

    def test_findings_sorted_by_severity(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.IMPORTANT: 1,
            Severity.OPTIONAL: 2,
            Severity.UNCLEAR: 3,
        }
        for i in range(len(findings) - 1):
            assert severity_order[findings[i].severity] <= severity_order[findings[i + 1].severity]

    def test_empty_text_returns_no_findings(self) -> None:
        findings = _run_design("")
        assert findings == []

    def test_whitespace_only_returns_no_findings(self) -> None:
        findings = _run_design("   \n  ")
        assert findings == []


# ===========================================================================
# Pipeline routing
# ===========================================================================


class TestPipelineRouting:
    """Pipeline correctly routes SOLUTION_DESIGN_REVIEW to design reviewer."""

    def test_pipeline_returns_review_response(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert isinstance(result, ReviewResponse)

    def test_pipeline_review_type_is_design(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert result.review_type == ReviewType.SOLUTION_DESIGN_REVIEW

    def test_pipeline_has_findings(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert len(result.findings) > 0

    def test_pipeline_skips_test_gaps(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert result.test_gaps == []

    def test_pipeline_skips_clean_core_hints(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert result.clean_core_hints == []

    def test_pipeline_has_assessment(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert result.overall_assessment is not None

    def test_pipeline_has_summary(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert result.review_summary
        assert len(result.review_summary) > 10

    def test_pipeline_has_recommended_actions(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN)
        assert len(result.recommended_actions) > 0

    def test_pipeline_non_design_still_works(self) -> None:
        """Non-design reviews should still use the standard findings engine."""
        request = ReviewRequest(
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.ABAP_CLASS,
            code_or_diff="CLASS zcl_test DEFINITION PUBLIC.\nENDCLASS.\nCLASS zcl_test IMPLEMENTATION.\nENDCLASS.",
            review_context=ReviewContext.GREENFIELD,
            language=Language.EN,
        )
        result = run_review_pipeline(request)
        assert isinstance(result, ReviewResponse)
        assert result.review_type == ReviewType.SNIPPET_REVIEW


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualDesignReview:
    """Design review produces bilingual output."""

    def test_english_findings(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN, language=Language.EN)
        assert len(findings) > 0
        # English findings should have English titles
        comp001 = [f for f in findings if f.rule_id == "DESIGN-COMP-001"]
        assert comp001
        assert "error handling" in comp001[0].title.lower()

    def test_german_findings(self) -> None:
        findings = _run_design(INCOMPLETE_DESIGN, language=Language.DE)
        assert len(findings) > 0
        comp001 = [f for f in findings if f.rule_id == "DESIGN-COMP-001"]
        assert comp001
        assert "Fehlerbehandlung" in comp001[0].title

    def test_german_pipeline_summary(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN, language=Language.DE)
        assert "Review-Typ" in result.review_summary

    def test_english_pipeline_summary(self) -> None:
        result = _run_pipeline_design(INCOMPLETE_DESIGN, language=Language.EN)
        assert "Review Type" in result.review_summary
