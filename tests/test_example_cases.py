"""Validation tests for example cases in the SAP ABAP/UI5 Review Assistant.

Runs each of the 15 example cases through the pipeline and validates
that classification, finding counts, severities, test gaps, risk
dimensions, and overall assessments match expectations.
"""

from __future__ import annotations

import pytest

from app.engines.pipeline import run_review_pipeline
from app.models.enums import (
    ArtifactType,
    GoNoGo,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import ReviewRequest, ReviewResponse
from app.rules.example_cases import (
    ALL_EXAMPLE_CASES,
    EXAMPLE_CASES_BY_ID,
    ExampleCase,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_case(case: ExampleCase, language: Language = Language.EN) -> ReviewResponse:
    """Build a ReviewRequest from an ExampleCase and run the pipeline."""
    request = ReviewRequest(
        review_type=ReviewType(case.review_type),
        artifact_type=ArtifactType(case.artifact_type),
        code_or_diff=case.code,
        review_context=ReviewContext(case.review_context),
        language=language,
    )
    return run_review_pipeline(request)


# ---------------------------------------------------------------------------
# Parametrized tests — run for each of the 15 example cases
# ---------------------------------------------------------------------------

CASE_IDS = [case.case_id for case in ALL_EXAMPLE_CASES]


@pytest.fixture(params=ALL_EXAMPLE_CASES, ids=CASE_IDS)
def example_case(request: pytest.FixtureRequest) -> ExampleCase:
    """Parametrize over all example cases."""
    return request.param


@pytest.fixture
def pipeline_result(example_case: ExampleCase) -> ReviewResponse:
    """Run the pipeline once per case and cache the result."""
    return _run_case(example_case)


class TestPipelineCompletion:
    """Verify the pipeline completes without exceptions for every case."""

    def test_returns_review_response(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        assert isinstance(pipeline_result, ReviewResponse), (
            f"Case {example_case.case_id}: pipeline did not return ReviewResponse"
        )

    def test_has_review_summary(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        assert pipeline_result.review_summary, (
            f"Case {example_case.case_id}: review_summary is empty"
        )
        assert len(pipeline_result.review_summary) > 10

    def test_has_overall_assessment(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        assert pipeline_result.overall_assessment is not None
        assert pipeline_result.overall_assessment.go_no_go in GoNoGo

    def test_valid_go_no_go(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        assert pipeline_result.overall_assessment.go_no_go in (
            GoNoGo.GO,
            GoNoGo.CONDITIONAL_GO,
            GoNoGo.NO_GO,
        )


class TestFindingCounts:
    """Verify finding counts are within expected ranges."""

    def test_finding_count_within_range(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        count = len(pipeline_result.findings)
        assert example_case.expected_finding_count_min <= count <= example_case.expected_finding_count_max, (
            f"Case {example_case.case_id}: expected {example_case.expected_finding_count_min}-"
            f"{example_case.expected_finding_count_max} findings, got {count}"
        )


class TestExpectedSeverities:
    """Verify expected severity levels appear in findings."""

    def test_expected_severities_present(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        if not example_case.expected_severities:
            return  # No specific severities expected

        actual_severities = {f.severity.value for f in pipeline_result.findings}
        for expected_sev in example_case.expected_severities:
            assert expected_sev in actual_severities, (
                f"Case {example_case.case_id}: expected severity {expected_sev} "
                f"not found in {actual_severities}"
            )


class TestTestGapCategories:
    """Verify expected test gap categories appear."""

    def test_expected_test_gap_categories(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        if not example_case.expected_test_gap_categories:
            return  # No specific test gaps expected

        actual_categories = {tg.category.value for tg in pipeline_result.test_gaps}
        for expected_cat in example_case.expected_test_gap_categories:
            assert expected_cat in actual_categories, (
                f"Case {example_case.case_id}: expected test gap category "
                f"{expected_cat} not found in {actual_categories}"
            )


class TestRiskDimensions:
    """Verify expected risk dimensions are above LOW."""

    def test_expected_risk_dimensions_above_low(
        self, example_case: ExampleCase, pipeline_result: ReviewResponse
    ) -> None:
        if not example_case.expected_risk_dimensions_above_low:
            return  # No specific risk expectations

        above_low_dims = set()
        for rn in pipeline_result.risk_notes:
            if rn.severity != Severity.UNCLEAR:
                above_low_dims.add(rn.category.value)

        for expected_dim in example_case.expected_risk_dimensions_above_low:
            assert expected_dim in above_low_dims, (
                f"Case {example_case.case_id}: expected risk dimension "
                f"{expected_dim} above LOW not found in {above_low_dims}"
            )


# ===========================================================================
# Non-parametrized aggregate tests
# ===========================================================================


class TestExampleCaseRegistry:
    """Verify the example case registry is well-formed."""

    def test_all_15_cases_present(self) -> None:
        assert len(ALL_EXAMPLE_CASES) == 15

    def test_case_ids_unique(self) -> None:
        ids = [case.case_id for case in ALL_EXAMPLE_CASES]
        assert len(ids) == len(set(ids)), "Duplicate case_id detected"

    def test_lookup_by_id_matches(self) -> None:
        for case in ALL_EXAMPLE_CASES:
            assert EXAMPLE_CASES_BY_ID[case.case_id] is case

    def test_all_cases_have_code(self) -> None:
        for case in ALL_EXAMPLE_CASES:
            assert len(case.code.strip()) >= 20, (
                f"Case {case.case_id}: code too short"
            )

    def test_all_cases_have_bilingual_titles(self) -> None:
        for case in ALL_EXAMPLE_CASES:
            assert case.title, f"Case {case.case_id}: missing title"
            assert case.title_de, f"Case {case.case_id}: missing title_de"
            assert case.description, f"Case {case.case_id}: missing description"
            assert case.description_de, f"Case {case.case_id}: missing description_de"

    def test_all_cases_have_valid_enums(self) -> None:
        for case in ALL_EXAMPLE_CASES:
            ReviewType(case.review_type)
            ArtifactType(case.artifact_type)
            ReviewContext(case.review_context)

    def test_finding_range_valid(self) -> None:
        for case in ALL_EXAMPLE_CASES:
            assert case.expected_finding_count_min >= 0
            assert case.expected_finding_count_max >= case.expected_finding_count_min


class TestCriticalCases:
    """Verify at least 2 cases produce CRITICAL findings."""

    def test_at_least_two_cases_with_critical_findings(self) -> None:
        critical_cases = 0
        for case in ALL_EXAMPLE_CASES:
            result = _run_case(case)
            if any(f.severity == Severity.CRITICAL for f in result.findings):
                critical_cases += 1

        assert critical_cases >= 2, (
            f"Only {critical_cases} cases produce CRITICAL findings, expected >= 2"
        )


class TestCleanCases:
    """Verify at least 2 cases produce GO assessment (clean code)."""

    def test_at_least_two_cases_with_go_assessment(self) -> None:
        go_cases = 0
        for case in ALL_EXAMPLE_CASES:
            result = _run_case(case)
            if result.overall_assessment.go_no_go == GoNoGo.GO:
                go_cases += 1

        assert go_cases >= 2, (
            f"Only {go_cases} cases produce GO assessment, expected >= 2"
        )


class TestBilingualOutput:
    """Verify example cases produce valid output in both languages."""

    def test_german_output_for_clean_class(self) -> None:
        case = EXAMPLE_CASES_BY_ID["abap_clean_class"]
        result = _run_case(case, language=Language.DE)
        assert isinstance(result, ReviewResponse)
        assert "Review-Typ" in result.review_summary

    def test_english_output_for_clean_class(self) -> None:
        case = EXAMPLE_CASES_BY_ID["abap_clean_class"]
        result = _run_case(case, language=Language.EN)
        assert isinstance(result, ReviewResponse)
        assert "Review Type" in result.review_summary


# ===========================================================================
# Specific case validation tests
# ===========================================================================


class TestABAPCleanClass:
    """Validate the abap_clean_class example specifically."""

    def test_few_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_clean_class"])
        assert len(result.findings) <= 2

    def test_no_critical_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_clean_class"])
        critical = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert len(critical) == 0


class TestABAPProblematicReport:
    """Validate the abap_problematic_report example specifically."""

    def test_multiple_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_problematic_report"])
        assert len(result.findings) >= 5

    def test_has_critical_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_problematic_report"])
        critical = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert len(critical) >= 1

    def test_has_recommended_actions(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_problematic_report"])
        assert len(result.recommended_actions) >= 1


class TestABAPMissingAuth:
    """Validate the abap_missing_auth example specifically."""

    def test_has_security_related_finding(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_missing_auth"])
        security_findings = [
            f for f in result.findings
            if f.rule_id and "SEC" in f.rule_id
        ]
        assert len(security_findings) >= 1


class TestABAPLegacyCode:
    """Validate the abap_legacy_code example specifically."""

    def test_has_clean_core_hints(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_legacy_code"])
        assert len(result.clean_core_hints) >= 2

    def test_has_enhancement_point_finding(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_legacy_code"])
        cc_texts = [h.finding for h in result.clean_core_hints]
        assert any("ENHANCEMENT" in t for t in cc_texts)


class TestABAPComplexMethod:
    """Validate the abap_complex_method example specifically."""

    def test_has_structure_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_complex_method"])
        struct_findings = [
            f for f in result.findings
            if f.rule_id and "STRUCT" in f.rule_id
        ]
        assert len(struct_findings) >= 1

    def test_method_length_detected(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["abap_complex_method"])
        length_findings = [
            f for f in result.findings
            if f.rule_id and "STRUCT-001" in f.rule_id
        ]
        assert len(length_findings) >= 1


class TestCDSCleanView:
    """Validate the cds_clean_view example specifically."""

    def test_few_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["cds_clean_view"])
        assert len(result.findings) <= 2


class TestCDSMissingAnnotations:
    """Validate the cds_missing_annotations example specifically."""

    def test_has_annotation_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["cds_missing_annotations"])
        anno_findings = [
            f for f in result.findings
            if f.rule_id and "ANNO" in f.rule_id
        ]
        assert len(anno_findings) >= 2


class TestBDEFStandard:
    """Validate the bdef_standard example specifically."""

    def test_has_action_validation_gaps(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["bdef_standard"])
        av_gaps = [
            tg for tg in result.test_gaps
            if tg.category.value == "ACTION_VALIDATION"
        ]
        assert len(av_gaps) >= 1


class TestBDEFComplex:
    """Validate the bdef_complex example specifically."""

    def test_has_draft_or_determination_gaps(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["bdef_complex"])
        av_gaps = [
            tg for tg in result.test_gaps
            if tg.category.value == "ACTION_VALIDATION"
        ]
        assert len(av_gaps) >= 1


class TestUI5CleanController:
    """Validate the ui5_clean_controller example specifically."""

    def test_few_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["ui5_clean_controller"])
        assert len(result.findings) <= 3


class TestUI5ProblematicController:
    """Validate the ui5_problematic_controller example specifically."""

    def test_multiple_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["ui5_problematic_controller"])
        assert len(result.findings) >= 4

    def test_has_dom_manipulation_finding(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["ui5_problematic_controller"])
        dom_findings = [
            f for f in result.findings
            if f.rule_id and "STRUCT-002" in f.rule_id
        ]
        assert len(dom_findings) >= 1

    def test_has_deprecated_api_finding(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["ui5_problematic_controller"])
        depr_findings = [
            f for f in result.findings
            if f.rule_id and "DEPR" in f.rule_id
        ]
        assert len(depr_findings) >= 1


class TestMixedFullstackChange:
    """Validate the mixed_fullstack_change example specifically."""

    def test_has_mixed_findings(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["mixed_fullstack_change"])
        assert len(result.findings) >= 2


class TestEmptyEdgeCase:
    """Validate the empty_edge_case example specifically."""

    def test_pipeline_does_not_crash(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["empty_edge_case"])
        assert isinstance(result, ReviewResponse)

    def test_has_valid_assessment(self) -> None:
        result = _run_case(EXAMPLE_CASES_BY_ID["empty_edge_case"])
        assert result.overall_assessment.go_no_go in GoNoGo


# ===========================================================================
# API endpoint tests
# ===========================================================================


@pytest.mark.anyio
async def test_examples_list_endpoint(client) -> None:
    """GET /api/examples returns all 15 example case metadata."""
    resp = await client.get("/api/examples")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 15
    assert all("case_id" in item for item in data)
    assert all("title" in item for item in data)
    assert all("code" not in item for item in data)


@pytest.mark.anyio
async def test_example_detail_endpoint(client) -> None:
    """GET /api/examples/{case_id} returns full example with code."""
    resp = await client.get("/api/examples/abap_clean_class")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "abap_clean_class"
    assert "code" in data
    assert len(data["code"]) > 20


@pytest.mark.anyio
async def test_example_detail_not_found(client) -> None:
    """GET /api/examples/{unknown} returns 404."""
    resp = await client.get("/api/examples/nonexistent_case")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_examples_list_has_all_case_ids(client) -> None:
    """The list endpoint returns every registered case_id."""
    resp = await client.get("/api/examples")
    assert resp.status_code == 200
    data = resp.json()
    returned_ids = {item["case_id"] for item in data}
    expected_ids = {case.case_id for case in ALL_EXAMPLE_CASES}
    assert returned_ids == expected_ids


@pytest.mark.anyio
async def test_each_example_detail_accessible(client) -> None:
    """Every case in the registry is accessible via the detail endpoint."""
    for case in ALL_EXAMPLE_CASES:
        resp = await client.get(f"/api/examples/{case.case_id}")
        assert resp.status_code == 200, (
            f"Case {case.case_id} returned status {resp.status_code}"
        )
