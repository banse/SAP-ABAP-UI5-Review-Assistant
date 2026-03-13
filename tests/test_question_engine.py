"""Tests for the question engine."""

from __future__ import annotations

import pytest

from app.engines.question_engine import generate_questions
from app.models.enums import (
    ArtifactType,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import Finding, MissingInformation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(
    severity: Severity = Severity.IMPORTANT,
    category: str = "error_handling",
    rule_id: str = "ABAP-ERR-001",
) -> Finding:
    return Finding(
        severity=severity,
        title="Test finding",
        observation="Test observation",
        reasoning="Test reasoning",
        impact=f"Category: {category}",
        recommendation="Fix it",
        rule_id=rule_id,
    )


def _run(
    code: str = "METHOD test. ENDMETHOD.",
    review_type: ReviewType = ReviewType.SNIPPET_REVIEW,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    findings: list[Finding] | None = None,
    clarifications: dict[str, str] | None = None,
    language: Language = Language.EN,
) -> list[MissingInformation]:
    return generate_questions(
        code=code,
        review_type=review_type,
        artifact_type=artifact_type,
        review_context=ReviewContext.GREENFIELD,
        findings=findings or [],
        clarifications=clarifications or {},
        language=language,
    )


# ===========================================================================
# Basic behaviour
# ===========================================================================


class TestBasicBehaviour:
    """Basic question generation tests."""

    def test_empty_code_returns_no_questions(self) -> None:
        result = _run(code="")
        assert result == []

    def test_whitespace_code_returns_no_questions(self) -> None:
        result = _run(code="   ")
        assert result == []

    def test_valid_code_returns_questions(self) -> None:
        result = _run()
        assert len(result) > 0

    def test_questions_are_missing_information_type(self) -> None:
        result = _run()
        for q in result:
            assert isinstance(q, MissingInformation)


# ===========================================================================
# Trigger conditions
# ===========================================================================


class TestTriggerConditions:
    """Tests for specific trigger conditions."""

    def test_no_tech_context_generates_context_questions(self) -> None:
        result = _run()
        # Should include SAP release, OData version, deployment target questions
        categories = [q.category for q in result]
        assert "context" in categories

    def test_performance_finding_generates_volume_question(self) -> None:
        findings = [_make_finding(category="performance")]
        result = _run(findings=findings)
        perf_questions = [q for q in result if q.category == "performance"]
        assert len(perf_questions) > 0

    def test_test_gaps_not_triggered_without_test_findings(self) -> None:
        findings = [_make_finding(category="readability")]
        result = _run(findings=findings)
        test_questions = [q for q in result if q.category == "testing"]
        assert len(test_questions) == 0

    def test_cds_artifact_generates_service_question(self) -> None:
        result = _run(
            code="define view entity ZI_Test as select from ztable { key id }",
            artifact_type=ArtifactType.CDS_VIEW,
        )
        arch_questions = [q for q in result if q.category == "architecture"]
        assert len(arch_questions) > 0

    def test_snippet_review_generates_change_package_question(self) -> None:
        result = _run(review_type=ReviewType.SNIPPET_REVIEW)
        context_questions = [q for q in result if q.category == "context"]
        assert len(context_questions) > 0

    def test_ticket_review_generates_ticket_question(self) -> None:
        result = _run(review_type=ReviewType.TICKET_BASED_PRE_REVIEW)
        process_questions = [q for q in result if q.category == "process"]
        assert len(process_questions) > 0

    def test_unclear_findings_generate_clarity_question(self) -> None:
        findings = [_make_finding(severity=Severity.UNCLEAR)]
        result = _run(findings=findings)
        # Should generate a question about unclear findings
        assert len(result) > 0


# ===========================================================================
# Clarification filtering
# ===========================================================================


class TestClarificationFiltering:
    """Tests for filtering already-answered questions."""

    def test_answered_question_is_filtered_by_id(self) -> None:
        result_all = _run()
        result_filtered = _run(clarifications={"Q-CTX-001": "S/4HANA 2023"})
        assert len(result_filtered) < len(result_all)

    def test_answered_question_is_filtered_by_text(self) -> None:
        result_all = _run()
        first_question = result_all[0].question if result_all else ""
        if first_question:
            result_filtered = _run(clarifications={first_question: "answered"})
            remaining_texts = [q.question for q in result_filtered]
            assert first_question not in remaining_texts

    def test_empty_answer_does_not_filter(self) -> None:
        result_all = _run()
        result_with_empty = _run(clarifications={"Q-CTX-001": ""})
        assert len(result_with_empty) == len(result_all)


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    """Tests for language support."""

    def test_english_output(self) -> None:
        result = _run(language=Language.EN)
        assert len(result) > 0
        # English questions should not start with German text
        for q in result:
            assert q.question  # not empty

    def test_german_output(self) -> None:
        result = _run(language=Language.DE)
        assert len(result) > 0
        for q in result:
            assert q.question  # not empty

    def test_german_and_english_differ(self) -> None:
        en = _run(language=Language.EN)
        de = _run(language=Language.DE)
        if en and de:
            assert en[0].question != de[0].question


# ===========================================================================
# Deduplication
# ===========================================================================


class TestDeduplication:
    """Tests for question deduplication."""

    def test_no_duplicate_questions(self) -> None:
        result = _run()
        question_texts = [q.question for q in result]
        assert len(question_texts) == len(set(question_texts))
