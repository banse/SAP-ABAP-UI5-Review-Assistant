"""Tests for the risk assessment engine."""

from __future__ import annotations

import pytest

from app.engines.risk_engine import assess_risks
from app.models.enums import (
    Language,
    RiskCategory,
    Severity,
    TestGapCategory,
)
from app.models.schemas import CleanCoreHint, Finding, RiskNote, TestGap


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


def _make_test_gap(
    priority: Severity = Severity.IMPORTANT,
    category: TestGapCategory = TestGapCategory.ABAP_UNIT,
) -> TestGap:
    return TestGap(
        category=category,
        description="Missing unit test for order validation",
        priority=priority,
        suggested_test="Add ABAP unit test for validate_order method",
    )


def _make_clean_core_hint(
    severity: Severity = Severity.IMPORTANT,
) -> CleanCoreHint:
    return CleanCoreHint(
        finding="Direct table access detected",
        released_api_alternative="Use CDS view",
        severity=severity,
    )


def _get_risk(notes: list[RiskNote], category: RiskCategory) -> RiskNote | None:
    return next((rn for rn in notes if rn.category == category), None)


# ===========================================================================
# Empty / no-risk scenarios
# ===========================================================================


class TestNoRisk:
    def test_no_findings_all_low(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        assert len(notes) == 4
        for note in notes:
            assert note.severity == Severity.UNCLEAR  # LOW maps to UNCLEAR

    def test_empty_inputs_returns_four_dimensions(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        categories = {rn.category for rn in notes}
        assert RiskCategory.FUNCTIONAL in categories
        assert RiskCategory.MAINTAINABILITY in categories
        assert RiskCategory.TESTABILITY in categories
        assert RiskCategory.UPGRADE_CLEAN_CORE in categories

    def test_no_findings_low_description_en(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "No significant risk" in functional.description

    def test_no_findings_low_description_de(self) -> None:
        notes = assess_risks([], [], [], Language.DE)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "Kein signifikantes Risiko" in functional.description

    def test_no_findings_low_mitigation(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "No immediate action" in functional.mitigation


# ===========================================================================
# Functional risk
# ===========================================================================


class TestFunctionalRisk:
    def test_one_critical_finding_triggers_high(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        # CRITICAL threshold=1 => HIGH risk => IMPORTANT severity
        assert functional.severity == Severity.IMPORTANT

    def test_two_critical_findings_triggers_critical(self) -> None:
        findings = [
            _make_finding(Severity.CRITICAL, "error_handling", "ERR-001"),
            _make_finding(Severity.CRITICAL, "security", "SEC-001"),
        ]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert functional.severity == Severity.CRITICAL

    def test_three_important_findings_trigger_medium(self) -> None:
        findings = [
            _make_finding(Severity.IMPORTANT, "error_handling", "ERR-001"),
            _make_finding(Severity.IMPORTANT, "security", "SEC-001"),
            _make_finding(Severity.IMPORTANT, "performance", "PERF-001"),
        ]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        # 3 important >= threshold 3 => MEDIUM risk => OPTIONAL severity
        assert functional.severity == Severity.OPTIONAL

    def test_one_important_finding_still_medium(self) -> None:
        """Even below threshold, any important finding triggers at least MEDIUM."""
        findings = [_make_finding(Severity.IMPORTANT, "error_handling")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert functional.severity == Severity.OPTIONAL  # MEDIUM

    def test_optional_findings_only_stay_low(self) -> None:
        findings = [_make_finding(Severity.OPTIONAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert functional.severity == Severity.UNCLEAR  # LOW

    def test_non_contributing_category_ignored(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "readability")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert functional.severity == Severity.UNCLEAR  # LOW — readability does not contribute

    def test_functional_mitigation_text(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "error handling" in functional.mitigation.lower()


# ===========================================================================
# Maintainability risk
# ===========================================================================


class TestMaintainabilityRisk:
    def test_readability_findings_contribute(self) -> None:
        findings = [
            _make_finding(Severity.CRITICAL, "readability", "READ-001"),
            _make_finding(Severity.CRITICAL, "readability", "READ-002"),
        ]
        notes = assess_risks(findings, [], [], Language.EN)
        maint = _get_risk(notes, RiskCategory.MAINTAINABILITY)
        assert maint is not None
        # critical_threshold=2 => HIGH => IMPORTANT
        assert maint.severity == Severity.IMPORTANT

    def test_structure_findings_contribute(self) -> None:
        findings = [
            _make_finding(Severity.CRITICAL, "structure", "STR-001"),
            _make_finding(Severity.CRITICAL, "structure", "STR-002"),
        ]
        notes = assess_risks(findings, [], [], Language.EN)
        maint = _get_risk(notes, RiskCategory.MAINTAINABILITY)
        assert maint is not None
        assert maint.severity == Severity.IMPORTANT

    def test_style_findings_contribute(self) -> None:
        findings = [_make_finding(Severity.IMPORTANT, "style")]
        notes = assess_risks(findings, [], [], Language.EN)
        maint = _get_risk(notes, RiskCategory.MAINTAINABILITY)
        assert maint is not None
        # 1 important, below threshold but still MEDIUM
        assert maint.severity == Severity.OPTIONAL


# ===========================================================================
# Testability risk
# ===========================================================================


class TestTestabilityRisk:
    def test_three_critical_gaps_trigger_high(self) -> None:
        gaps = [_make_test_gap(Severity.CRITICAL) for _ in range(3)]
        notes = assess_risks([], gaps, [], Language.EN)
        test_risk = _get_risk(notes, RiskCategory.TESTABILITY)
        assert test_risk is not None
        assert test_risk.severity == Severity.IMPORTANT  # HIGH

    def test_five_important_gaps_trigger_medium(self) -> None:
        gaps = [_make_test_gap(Severity.IMPORTANT) for _ in range(5)]
        notes = assess_risks([], gaps, [], Language.EN)
        test_risk = _get_risk(notes, RiskCategory.TESTABILITY)
        assert test_risk is not None
        assert test_risk.severity == Severity.OPTIONAL  # MEDIUM

    def test_no_gaps_low(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        test_risk = _get_risk(notes, RiskCategory.TESTABILITY)
        assert test_risk is not None
        assert test_risk.severity == Severity.UNCLEAR  # LOW

    def test_one_gap_still_medium(self) -> None:
        gaps = [_make_test_gap(Severity.OPTIONAL)]
        notes = assess_risks([], gaps, [], Language.EN)
        test_risk = _get_risk(notes, RiskCategory.TESTABILITY)
        assert test_risk is not None
        # 1 gap counted as important-level => MEDIUM
        assert test_risk.severity == Severity.OPTIONAL


# ===========================================================================
# Upgrade / Clean Core risk
# ===========================================================================


class TestUpgradeCleanCoreRisk:
    def test_two_critical_hints_trigger_high(self) -> None:
        hints = [_make_clean_core_hint(Severity.CRITICAL) for _ in range(2)]
        notes = assess_risks([], [], hints, Language.EN)
        cc = _get_risk(notes, RiskCategory.UPGRADE_CLEAN_CORE)
        assert cc is not None
        assert cc.severity == Severity.IMPORTANT  # HIGH

    def test_three_important_hints_trigger_medium(self) -> None:
        hints = [_make_clean_core_hint(Severity.IMPORTANT) for _ in range(3)]
        notes = assess_risks([], [], hints, Language.EN)
        cc = _get_risk(notes, RiskCategory.UPGRADE_CLEAN_CORE)
        assert cc is not None
        assert cc.severity == Severity.OPTIONAL  # MEDIUM

    def test_no_hints_low(self) -> None:
        notes = assess_risks([], [], [], Language.EN)
        cc = _get_risk(notes, RiskCategory.UPGRADE_CLEAN_CORE)
        assert cc is not None
        assert cc.severity == Severity.UNCLEAR  # LOW

    def test_clean_core_mitigation_text(self) -> None:
        hints = [_make_clean_core_hint(Severity.CRITICAL) for _ in range(2)]
        notes = assess_risks([], [], hints, Language.EN)
        cc = _get_risk(notes, RiskCategory.UPGRADE_CLEAN_CORE)
        assert cc is not None
        assert "released" in cc.mitigation.lower()


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    def test_german_risk_description(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.DE)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "kritische" in functional.description.lower()

    def test_english_risk_description(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.EN)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "critical" in functional.description.lower()

    def test_german_mitigation(self) -> None:
        findings = [_make_finding(Severity.CRITICAL, "error_handling")]
        notes = assess_risks(findings, [], [], Language.DE)
        functional = _get_risk(notes, RiskCategory.FUNCTIONAL)
        assert functional is not None
        assert "Findings" in functional.mitigation or "Fehler" in functional.mitigation


# ===========================================================================
# Sorting
# ===========================================================================


class TestSorting:
    def test_risk_notes_sorted_by_severity(self) -> None:
        findings = [
            _make_finding(Severity.CRITICAL, "error_handling"),  # FUNCTIONAL => HIGH
        ]
        gaps = [_make_test_gap(Severity.CRITICAL) for _ in range(3)]  # TESTABILITY => HIGH
        notes = assess_risks(findings, gaps, [], Language.EN)
        severities = [rn.severity for rn in notes]
        # Verify sorted order (CRITICAL/IMPORTANT before OPTIONAL/UNCLEAR)
        severity_values = [_SEVERITY_ORDER.get(s.value, 99) for s in severities]
        assert severity_values == sorted(severity_values)


_SEVERITY_ORDER: dict[str, int] = {
    Severity.CRITICAL.value: 0,
    Severity.IMPORTANT.value: 1,
    Severity.OPTIONAL.value: 2,
    Severity.UNCLEAR.value: 3,
}
