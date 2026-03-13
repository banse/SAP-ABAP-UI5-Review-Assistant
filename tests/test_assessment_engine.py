"""Tests for the assessment engine."""

from __future__ import annotations

import pytest

from app.engines.assessment_engine import generate_assessment
from app.models.enums import (
    Confidence,
    GoNoGo,
    Language,
    RiskCategory,
    Severity,
    TestGapCategory,
)
from app.models.schemas import Finding, OverallAssessment, RiskNote, TestGap


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


def _make_risk_note(
    severity: Severity = Severity.OPTIONAL,
    category: RiskCategory = RiskCategory.FUNCTIONAL,
) -> RiskNote:
    return RiskNote(
        category=category,
        description="Risk description",
        severity=severity,
        mitigation="Mitigation text",
    )


def _make_test_gap(
    priority: Severity = Severity.IMPORTANT,
) -> TestGap:
    return TestGap(
        category=TestGapCategory.ABAP_UNIT,
        description="Missing unit test",
        priority=priority,
    )


def _assess(
    findings: list[Finding] | None = None,
    test_gaps: list[TestGap] | None = None,
    risk_notes: list[RiskNote] | None = None,
    language: Language = Language.EN,
) -> OverallAssessment:
    return generate_assessment(
        findings=findings or [],
        test_gaps=test_gaps or [],
        risk_notes=risk_notes or [],
        language=language,
    )


# ===========================================================================
# Go / No-Go verdicts
# ===========================================================================


class TestGoNoGo:
    """Tests for go/no-go determination."""

    def test_no_findings_returns_go(self) -> None:
        result = _assess()
        assert result.go_no_go == GoNoGo.GO

    def test_few_optional_findings_returns_go(self) -> None:
        findings = [_make_finding(severity=Severity.OPTIONAL) for _ in range(5)]
        result = _assess(findings=findings)
        assert result.go_no_go == GoNoGo.GO

    def test_few_important_findings_returns_go(self) -> None:
        findings = [_make_finding(severity=Severity.IMPORTANT) for _ in range(3)]
        result = _assess(findings=findings)
        assert result.go_no_go == GoNoGo.GO

    def test_many_important_findings_returns_conditional_go(self) -> None:
        findings = [_make_finding(severity=Severity.IMPORTANT) for _ in range(4)]
        result = _assess(findings=findings)
        assert result.go_no_go == GoNoGo.CONDITIONAL_GO

    def test_critical_finding_returns_conditional_go(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        result = _assess(findings=findings)
        assert result.go_no_go == GoNoGo.CONDITIONAL_GO

    def test_critical_finding_with_critical_risk_returns_no_go(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        risk_notes = [_make_risk_note(severity=Severity.CRITICAL)]
        result = _assess(findings=findings, risk_notes=risk_notes)
        assert result.go_no_go == GoNoGo.NO_GO

    def test_no_critical_with_critical_risk_is_not_no_go(self) -> None:
        # NO_GO requires BOTH critical findings AND critical risk
        risk_notes = [_make_risk_note(severity=Severity.CRITICAL)]
        result = _assess(risk_notes=risk_notes)
        assert result.go_no_go == GoNoGo.GO

    def test_critical_finding_without_critical_risk_is_conditional(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        risk_notes = [_make_risk_note(severity=Severity.OPTIONAL)]
        result = _assess(findings=findings, risk_notes=risk_notes)
        assert result.go_no_go == GoNoGo.CONDITIONAL_GO


# ===========================================================================
# Confidence levels
# ===========================================================================


class TestConfidence:
    """Tests for confidence determination."""

    def test_no_findings_high_confidence(self) -> None:
        result = _assess()
        assert result.confidence == Confidence.HIGH

    def test_no_unclear_findings_high_confidence(self) -> None:
        findings = [_make_finding(severity=Severity.IMPORTANT) for _ in range(3)]
        result = _assess(findings=findings)
        assert result.confidence == Confidence.HIGH

    def test_few_unclear_findings_medium_confidence(self) -> None:
        # >10% unclear but <=30%
        findings = [_make_finding(severity=Severity.IMPORTANT) for _ in range(7)]
        findings.append(_make_finding(severity=Severity.UNCLEAR))
        result = _assess(findings=findings)
        assert result.confidence == Confidence.MEDIUM

    def test_many_unclear_findings_low_confidence(self) -> None:
        # >30% unclear
        findings = [_make_finding(severity=Severity.UNCLEAR) for _ in range(4)]
        findings.append(_make_finding(severity=Severity.IMPORTANT))
        result = _assess(findings=findings)
        assert result.confidence == Confidence.LOW


# ===========================================================================
# Counts
# ===========================================================================


class TestCounts:
    """Tests for severity counts."""

    def test_critical_count(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL) for _ in range(2)]
        result = _assess(findings=findings)
        assert result.critical_count == 2

    def test_important_count(self) -> None:
        findings = [_make_finding(severity=Severity.IMPORTANT) for _ in range(3)]
        result = _assess(findings=findings)
        assert result.important_count == 3

    def test_optional_count(self) -> None:
        findings = [_make_finding(severity=Severity.OPTIONAL) for _ in range(4)]
        result = _assess(findings=findings)
        assert result.optional_count == 4

    def test_mixed_counts(self) -> None:
        findings = [
            _make_finding(severity=Severity.CRITICAL),
            _make_finding(severity=Severity.IMPORTANT),
            _make_finding(severity=Severity.IMPORTANT),
            _make_finding(severity=Severity.OPTIONAL),
            _make_finding(severity=Severity.OPTIONAL),
            _make_finding(severity=Severity.OPTIONAL),
        ]
        result = _assess(findings=findings)
        assert result.critical_count == 1
        assert result.important_count == 2
        assert result.optional_count == 3

    def test_zero_counts_when_empty(self) -> None:
        result = _assess()
        assert result.critical_count == 0
        assert result.important_count == 0
        assert result.optional_count == 0


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    """Tests for bilingual summary generation."""

    def test_english_summary(self) -> None:
        result = _assess(language=Language.EN)
        assert "code" in result.summary.lower() or "released" in result.summary.lower()

    def test_german_summary(self) -> None:
        result = _assess(language=Language.DE)
        assert "code" in result.summary.lower() or "freigegeben" in result.summary.lower()

    def test_english_and_german_summaries_differ(self) -> None:
        en = _assess(language=Language.EN)
        de = _assess(language=Language.DE)
        assert en.summary != de.summary

    def test_no_go_english_summary(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        risk_notes = [_make_risk_note(severity=Severity.CRITICAL)]
        result = _assess(findings=findings, risk_notes=risk_notes, language=Language.EN)
        assert "NOT" in result.summary

    def test_no_go_german_summary(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        risk_notes = [_make_risk_note(severity=Severity.CRITICAL)]
        result = _assess(findings=findings, risk_notes=risk_notes, language=Language.DE)
        assert "NICHT" in result.summary
