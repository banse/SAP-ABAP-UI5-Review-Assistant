"""Comprehensive tests for the Pydantic v2 schema layer.

Covers all enums, input models, output models, validation rules,
and JSON round-trip serialization.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.models.enums import (
    ArtifactType,
    Confidence,
    GoNoGo,
    Language,
    ODataVersion,
    QuestionFocus,
    RefactoringCategory,
    ReviewContext,
    ReviewType,
    RiskCategory,
    RiskLevel,
    Severity,
    TestGapCategory,
)
from app.models.schemas import (
    CleanCoreHint,
    Finding,
    MissingInformation,
    OverallAssessment,
    RecommendedAction,
    RefactoringHint,
    ReviewRequest,
    ReviewResponse,
    RiskNote,
    TechnologyContext,
    TestGap,
)


# ===================================================================
# Enum tests
# ===================================================================


class TestReviewTypeEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "SNIPPET_REVIEW",
            "DIFF_REVIEW",
            "PRE_MERGE_REVIEW",
            "SOLUTION_DESIGN_REVIEW",
            "TICKET_BASED_PRE_REVIEW",
            "REGRESSION_RISK_REVIEW",
            "CLEAN_CORE_ARCHITECTURE_CHECK",
        }
        assert {m.name for m in ReviewType} == expected

    def test_is_str_enum(self) -> None:
        assert isinstance(ReviewType.SNIPPET_REVIEW, str)
        assert ReviewType.SNIPPET_REVIEW == "SNIPPET_REVIEW"


class TestArtifactTypeEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
            "CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION",
            "BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION",
            "SERVICE_DEFINITION", "SERVICE_BINDING",
            "ODATA_SERVICE",
            "UI5_VIEW", "UI5_CONTROLLER", "UI5_FRAGMENT", "UI5_FORMATTER",
            "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK",
        }
        assert {m.name for m in ArtifactType} == expected

    def test_member_count(self) -> None:
        assert len(ArtifactType) == 17


class TestReviewContextEnum:
    def test_all_members_exist(self) -> None:
        expected = {"GREENFIELD", "EXTENSION", "BUGFIX", "REFACTORING"}
        assert {m.name for m in ReviewContext} == expected


class TestQuestionFocusEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "PERFORMANCE", "MAINTAINABILITY", "CLEAN_CORE",
            "TESTS", "SECURITY", "READABILITY",
        }
        assert {m.name for m in QuestionFocus} == expected


class TestSeverityEnum:
    def test_all_levels_exist(self) -> None:
        expected = {"CRITICAL", "IMPORTANT", "OPTIONAL", "UNCLEAR"}
        assert {m.name for m in Severity} == expected

    def test_is_str_enum(self) -> None:
        assert isinstance(Severity.CRITICAL, str)


class TestGoNoGoEnum:
    def test_all_values(self) -> None:
        expected = {"GO", "CONDITIONAL_GO", "NO_GO"}
        assert {m.name for m in GoNoGo} == expected

    def test_value_equals_name(self) -> None:
        for member in GoNoGo:
            assert member.value == member.name


class TestConfidenceEnum:
    def test_all_members_exist(self) -> None:
        expected = {"HIGH", "MEDIUM", "LOW"}
        assert {m.name for m in Confidence} == expected


class TestLanguageEnum:
    def test_default_is_en(self) -> None:
        assert Language.EN == "EN"

    def test_both_languages(self) -> None:
        assert {m.name for m in Language} == {"DE", "EN"}


class TestODataVersionEnum:
    def test_versions(self) -> None:
        assert ODataVersion.V2 == "V2"
        assert ODataVersion.V4 == "V4"


class TestTestGapCategoryEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "ABAP_UNIT", "ACTION_VALIDATION", "UI_BEHAVIOR",
            "UI_ROLE", "UI_FILTER_SEARCH", "REGRESSION_SIDE_EFFECT",
        }
        assert {m.name for m in TestGapCategory} == expected


class TestRiskCategoryEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "FUNCTIONAL", "MAINTAINABILITY",
            "TESTABILITY", "UPGRADE_CLEAN_CORE",
        }
        assert {m.name for m in RiskCategory} == expected


class TestRiskLevelEnum:
    def test_all_members_exist(self) -> None:
        expected = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert {m.name for m in RiskLevel} == expected


class TestRefactoringCategoryEnum:
    def test_all_members_exist(self) -> None:
        expected = {
            "SMALL_FIX", "TARGETED_STRUCTURE_IMPROVEMENT",
            "MEDIUM_TERM_REFACTORING_HINT", "NOT_IMMEDIATE_REBUILD",
        }
        assert {m.name for m in RefactoringCategory} == expected


# ===================================================================
# Input model tests
# ===================================================================


class TestTechnologyContext:
    def test_all_none_defaults(self) -> None:
        ctx = TechnologyContext()
        assert ctx.sap_release is None
        assert ctx.ui5_version is None
        assert ctx.odata_version is None
        assert ctx.rap_managed is None
        assert ctx.fiori_elements is None

    def test_full_context(self) -> None:
        ctx = TechnologyContext(
            sap_release="2023",
            ui5_version="1.120",
            odata_version=ODataVersion.V4,
            rap_managed=True,
            fiori_elements=True,
        )
        assert ctx.sap_release == "2023"
        assert ctx.odata_version == ODataVersion.V4


class TestReviewRequest:
    def test_minimal_input(self) -> None:
        req = ReviewRequest(
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.ABAP_CLASS,
            code_or_diff="CLASS zcl_test DEFINITION.",
        )
        assert req.review_type == ReviewType.SNIPPET_REVIEW
        assert req.artifact_type == ArtifactType.ABAP_CLASS
        assert req.code_or_diff == "CLASS zcl_test DEFINITION."
        assert req.context_summary == ""
        assert req.review_context == ReviewContext.GREENFIELD
        assert req.language == Language.EN
        assert req.question_focus == []
        assert req.known_constraints == []
        assert req.clarifications == {}

    def test_full_input(self) -> None:
        req = ReviewRequest(
            review_type=ReviewType.PRE_MERGE_REVIEW,
            artifact_type=ArtifactType.MIXED_FULLSTACK,
            code_or_diff="diff --git a/zcl_test.abap",
            context_summary="Adding approval workflow",
            review_context=ReviewContext.EXTENSION,
            goal_of_review="Check clean core compliance",
            technology_context=TechnologyContext(
                sap_release="2023",
                odata_version=ODataVersion.V4,
                rap_managed=True,
            ),
            known_constraints=["No custom tables allowed"],
            domain_pack="yard",
            question_focus=[QuestionFocus.CLEAN_CORE, QuestionFocus.PERFORMANCE],
            language=Language.DE,
            clarifications={"draft needed?": "yes"},
        )
        assert req.review_context == ReviewContext.EXTENSION
        assert req.language == Language.DE
        assert len(req.question_focus) == 2
        assert req.technology_context is not None
        assert req.technology_context.rap_managed is True

    def test_empty_code_or_diff_fails(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(
                review_type=ReviewType.SNIPPET_REVIEW,
                artifact_type=ArtifactType.ABAP_CLASS,
                code_or_diff="",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code_or_diff",) for e in errors)

    def test_missing_required_fields_fails(self) -> None:
        with pytest.raises(ValidationError):
            ReviewRequest()  # type: ignore[call-arg]

    def test_whitespace_stripping(self) -> None:
        req = ReviewRequest(
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.CDS_VIEW,
            code_or_diff="  define view entity ZI_Test  ",
            context_summary="  some context  ",
        )
        assert req.code_or_diff == "define view entity ZI_Test"
        assert req.context_summary == "some context"


# ===================================================================
# Output model tests
# ===================================================================


class TestFinding:
    def test_full_finding(self) -> None:
        f = Finding(
            severity=Severity.CRITICAL,
            title="Missing authorization check",
            observation="No auth check before data modification",
            reasoning="CDS access control is not sufficient alone",
            impact="Unauthorized data changes possible",
            recommendation="Add authority-check in determination",
            artifact_reference="ZCL_TEST",
            line_reference="42",
            rule_id="SEC-001",
        )
        assert f.severity == Severity.CRITICAL
        assert f.rule_id == "SEC-001"

    def test_minimal_finding(self) -> None:
        f = Finding(
            severity=Severity.OPTIONAL,
            title="Minor naming issue",
            observation="Prefix missing",
            reasoning="Convention says Z prefix",
            impact="Low",
            recommendation="Rename",
        )
        assert f.artifact_reference is None
        assert f.line_reference is None
        assert f.rule_id is None


class TestTestGap:
    def test_full_test_gap(self) -> None:
        tg = TestGap(
            category=TestGapCategory.ABAP_UNIT,
            description="No unit test for validation method",
            priority=Severity.IMPORTANT,
            suggested_test="Test validation with invalid input",
        )
        assert tg.category == TestGapCategory.ABAP_UNIT
        assert tg.suggested_test is not None

    def test_minimal_test_gap(self) -> None:
        tg = TestGap(
            category=TestGapCategory.UI_BEHAVIOR,
            description="No UI test for filter bar",
            priority=Severity.OPTIONAL,
        )
        assert tg.suggested_test is None


class TestRiskNote:
    def test_full_risk_note(self) -> None:
        rn = RiskNote(
            category=RiskCategory.UPGRADE_CLEAN_CORE,
            description="Uses unreleased API",
            severity=Severity.CRITICAL,
            mitigation="Switch to released wrapper",
        )
        assert rn.mitigation == "Switch to released wrapper"

    def test_minimal_risk_note(self) -> None:
        rn = RiskNote(
            category=RiskCategory.FUNCTIONAL,
            description="Edge case not covered",
            severity=Severity.IMPORTANT,
        )
        assert rn.mitigation is None


class TestCleanCoreHint:
    def test_full_hint(self) -> None:
        h = CleanCoreHint(
            finding="Direct table access to VBAK",
            released_api_alternative="I_SalesOrder CDS view",
            severity=Severity.CRITICAL,
        )
        assert h.released_api_alternative == "I_SalesOrder CDS view"

    def test_minimal_hint(self) -> None:
        h = CleanCoreHint(
            finding="Custom function module call",
            severity=Severity.IMPORTANT,
        )
        assert h.released_api_alternative is None


class TestRecommendedAction:
    def test_full_action(self) -> None:
        a = RecommendedAction(
            order=1,
            title="Fix authorization",
            description="Add instance authorization",
            effort_hint="small",
            finding_references=["SEC-001", "SEC-002"],
        )
        assert a.order == 1
        assert len(a.finding_references) == 2

    def test_minimal_action(self) -> None:
        a = RecommendedAction(
            order=2,
            title="Improve naming",
            description="Rename class",
        )
        assert a.effort_hint is None
        assert a.finding_references == []


class TestRefactoringHint:
    def test_full_hint(self) -> None:
        rh = RefactoringHint(
            category=RefactoringCategory.TARGETED_STRUCTURE_IMPROVEMENT,
            title="Extract validation logic",
            description="Move inline validation to dedicated method",
            benefit="Improved testability and reuse",
            effort_hint="medium",
        )
        assert rh.category == RefactoringCategory.TARGETED_STRUCTURE_IMPROVEMENT

    def test_minimal_hint(self) -> None:
        rh = RefactoringHint(
            category=RefactoringCategory.SMALL_FIX,
            title="Remove dead code",
            description="Commented-out block in line 80-95",
            benefit="Better readability",
        )
        assert rh.effort_hint is None


class TestMissingInformation:
    def test_full_missing_info(self) -> None:
        mi = MissingInformation(
            question="Is draft handling required?",
            why_it_matters="Affects behavior definition structure",
            default_assumption="Draft is enabled",
            category="design",
        )
        assert mi.category == "design"

    def test_minimal_missing_info(self) -> None:
        mi = MissingInformation(
            question="What SAP release?",
            why_it_matters="Determines available RAP features",
        )
        assert mi.default_assumption is None
        assert mi.category == "context"


class TestOverallAssessment:
    def test_go_assessment(self) -> None:
        oa = OverallAssessment(
            go_no_go=GoNoGo.GO,
            confidence=Confidence.HIGH,
            summary="Code is clean and well-structured",
            critical_count=0,
            important_count=1,
            optional_count=3,
        )
        assert oa.go_no_go == GoNoGo.GO
        assert oa.critical_count == 0

    def test_no_go_assessment(self) -> None:
        oa = OverallAssessment(
            go_no_go=GoNoGo.NO_GO,
            confidence=Confidence.MEDIUM,
            summary="Critical security issues found",
            critical_count=2,
        )
        assert oa.important_count == 0
        assert oa.optional_count == 0

    def test_conditional_go(self) -> None:
        oa = OverallAssessment(
            go_no_go=GoNoGo.CONDITIONAL_GO,
            confidence=Confidence.LOW,
            summary="Needs test coverage before merge",
        )
        assert oa.go_no_go == GoNoGo.CONDITIONAL_GO


# ===================================================================
# ReviewResponse tests
# ===================================================================


class TestReviewResponse:
    def test_empty_lists(self) -> None:
        resp = ReviewResponse(
            review_summary="Looks good overall",
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.ABAP_CLASS,
            overall_assessment=OverallAssessment(
                go_no_go=GoNoGo.GO,
                confidence=Confidence.HIGH,
                summary="No issues found",
            ),
        )
        assert resp.findings == []
        assert resp.missing_information == []
        assert resp.test_gaps == []
        assert resp.recommended_actions == []
        assert resp.refactoring_hints == []
        assert resp.risk_notes == []
        assert resp.clean_core_hints == []
        assert resp.language == Language.EN

    def test_populated_response(self) -> None:
        resp = ReviewResponse(
            review_summary="Several issues found",
            review_type=ReviewType.PRE_MERGE_REVIEW,
            artifact_type=ArtifactType.CDS_VIEW,
            findings=[
                Finding(
                    severity=Severity.CRITICAL,
                    title="Missing access control",
                    observation="No DCL defined",
                    reasoning="Required for authorization",
                    impact="Unauthorized access",
                    recommendation="Create DCL",
                ),
            ],
            missing_information=[
                MissingInformation(
                    question="Is this a root entity?",
                    why_it_matters="Affects composition model",
                ),
            ],
            test_gaps=[
                TestGap(
                    category=TestGapCategory.ABAP_UNIT,
                    description="No unit test",
                    priority=Severity.IMPORTANT,
                ),
            ],
            recommended_actions=[
                RecommendedAction(
                    order=1,
                    title="Add DCL",
                    description="Create data control language file",
                ),
            ],
            refactoring_hints=[
                RefactoringHint(
                    category=RefactoringCategory.SMALL_FIX,
                    title="Simplify join",
                    description="Use association instead",
                    benefit="Better readability",
                ),
            ],
            risk_notes=[
                RiskNote(
                    category=RiskCategory.FUNCTIONAL,
                    description="Join may fail for null keys",
                    severity=Severity.IMPORTANT,
                ),
            ],
            clean_core_hints=[
                CleanCoreHint(
                    finding="Uses VBAK directly",
                    released_api_alternative="I_SalesOrder",
                    severity=Severity.CRITICAL,
                ),
            ],
            overall_assessment=OverallAssessment(
                go_no_go=GoNoGo.NO_GO,
                confidence=Confidence.HIGH,
                summary="Critical issues must be fixed",
                critical_count=1,
                important_count=1,
            ),
            language=Language.DE,
        )
        assert len(resp.findings) == 1
        assert len(resp.test_gaps) == 1
        assert len(resp.clean_core_hints) == 1
        assert resp.language == Language.DE
        assert resp.overall_assessment.go_no_go == GoNoGo.NO_GO


# ===================================================================
# JSON round-trip tests
# ===================================================================


class TestJsonRoundTrip:
    def test_review_request_round_trip(self) -> None:
        original = ReviewRequest(
            review_type=ReviewType.DIFF_REVIEW,
            artifact_type=ArtifactType.BEHAVIOR_DEFINITION,
            code_or_diff="managed implementation in class zbp;",
            context_summary="New BO",
            review_context=ReviewContext.GREENFIELD,
            technology_context=TechnologyContext(
                sap_release="2023",
                odata_version=ODataVersion.V4,
            ),
            question_focus=[QuestionFocus.CLEAN_CORE],
            language=Language.DE,
            clarifications={"draft?": "yes"},
        )
        json_str = original.model_dump_json()
        restored = ReviewRequest.model_validate_json(json_str)

        assert restored.review_type == original.review_type
        assert restored.artifact_type == original.artifact_type
        assert restored.code_or_diff == original.code_or_diff
        assert restored.technology_context is not None
        assert restored.technology_context.odata_version == ODataVersion.V4
        assert restored.question_focus == [QuestionFocus.CLEAN_CORE]
        assert restored.clarifications == {"draft?": "yes"}

    def test_review_response_round_trip(self) -> None:
        original = ReviewResponse(
            review_summary="All good",
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.UI5_CONTROLLER,
            findings=[
                Finding(
                    severity=Severity.OPTIONAL,
                    title="Minor style",
                    observation="Long line",
                    reasoning="Readability",
                    impact="Low",
                    recommendation="Break line",
                    rule_id="STYLE-001",
                ),
            ],
            overall_assessment=OverallAssessment(
                go_no_go=GoNoGo.GO,
                confidence=Confidence.HIGH,
                summary="Clean code",
                optional_count=1,
            ),
        )
        json_str = original.model_dump_json()
        restored = ReviewResponse.model_validate_json(json_str)

        assert restored.review_summary == "All good"
        assert len(restored.findings) == 1
        assert restored.findings[0].rule_id == "STYLE-001"
        assert restored.overall_assessment.optional_count == 1

    def test_review_request_dict_round_trip(self) -> None:
        original = ReviewRequest(
            review_type=ReviewType.REGRESSION_RISK_REVIEW,
            artifact_type=ArtifactType.ABAP_METHOD,
            code_or_diff="METHOD do_something.",
        )
        data = original.model_dump()
        assert isinstance(data, dict)
        restored = ReviewRequest.model_validate(data)
        assert restored.review_type == original.review_type

    def test_review_response_dict_round_trip(self) -> None:
        original = ReviewResponse(
            review_summary="Summary",
            review_type=ReviewType.CLEAN_CORE_ARCHITECTURE_CHECK,
            artifact_type=ArtifactType.SERVICE_BINDING,
            overall_assessment=OverallAssessment(
                go_no_go=GoNoGo.CONDITIONAL_GO,
                confidence=Confidence.MEDIUM,
                summary="Needs review",
            ),
        )
        data = original.model_dump()
        restored = ReviewResponse.model_validate(data)
        assert restored.overall_assessment.go_no_go == GoNoGo.CONDITIONAL_GO

    def test_json_contains_enum_values(self) -> None:
        """Ensure enums serialize as their string values, not names."""
        req = ReviewRequest(
            review_type=ReviewType.SNIPPET_REVIEW,
            artifact_type=ArtifactType.CDS_VIEW,
            code_or_diff="define view",
        )
        data = json.loads(req.model_dump_json())
        assert data["review_type"] == "SNIPPET_REVIEW"
        assert data["artifact_type"] == "CDS_VIEW"
        assert data["review_context"] == "GREENFIELD"
        assert data["language"] == "EN"
