"""Tests for the action engine."""

from __future__ import annotations

import pytest

from app.engines.action_engine import generate_actions
from app.models.enums import Language, Severity, TestGapCategory
from app.models.schemas import Finding, RecommendedAction, TestGap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_finding(
    severity: Severity = Severity.IMPORTANT,
    category: str = "error_handling",
    rule_id: str = "ABAP-ERR-001",
    title: str = "Test finding",
) -> Finding:
    return Finding(
        severity=severity,
        title=title,
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
        description="Missing unit test for public method",
        priority=priority,
        suggested_test="Add ABAP Unit test class",
    )


# ===========================================================================
# Basic behaviour
# ===========================================================================


class TestBasicBehaviour:
    """Basic action generation tests."""

    def test_empty_findings_returns_empty(self) -> None:
        result = generate_actions([], [], Language.EN)
        assert result == []

    def test_single_finding_returns_single_action(self) -> None:
        findings = [_make_finding()]
        result = generate_actions(findings, [], Language.EN)
        assert len(result) == 1

    def test_actions_are_recommended_action_type(self) -> None:
        findings = [_make_finding()]
        result = generate_actions(findings, [], Language.EN)
        for action in result:
            assert isinstance(action, RecommendedAction)


# ===========================================================================
# Ordering
# ===========================================================================


class TestOrdering:
    """Tests for action ordering by severity."""

    def test_critical_finding_gets_order_1(self) -> None:
        findings = [
            _make_finding(severity=Severity.OPTIONAL, title="opt"),
            _make_finding(severity=Severity.CRITICAL, title="crit"),
        ]
        result = generate_actions(findings, [], Language.EN)
        assert "CRITICAL" in result[0].title
        assert result[0].order == 1

    def test_sequential_numbering(self) -> None:
        findings = [_make_finding(), _make_finding(title="Second")]
        result = generate_actions(findings, [], Language.EN)
        for i, action in enumerate(result, 1):
            assert action.order == i

    def test_multiple_findings_ordered_by_severity(self) -> None:
        findings = [
            _make_finding(severity=Severity.OPTIONAL, title="opt"),
            _make_finding(severity=Severity.CRITICAL, title="crit"),
            _make_finding(severity=Severity.IMPORTANT, title="imp"),
        ]
        result = generate_actions(findings, [], Language.EN)
        assert "CRITICAL" in result[0].title
        assert "IMPORTANT" in result[1].title
        assert "OPTIONAL" in result[2].title


# ===========================================================================
# Effort hints
# ===========================================================================


class TestEffortHints:
    """Tests for effort estimation."""

    def test_style_category_is_small(self) -> None:
        findings = [_make_finding(category="style")]
        result = generate_actions(findings, [], Language.EN)
        assert result[0].effort_hint == "small"

    def test_structure_category_is_medium(self) -> None:
        findings = [_make_finding(category="structure")]
        result = generate_actions(findings, [], Language.EN)
        assert result[0].effort_hint == "medium"

    def test_performance_critical_is_medium(self) -> None:
        findings = [_make_finding(category="performance", severity=Severity.CRITICAL)]
        result = generate_actions(findings, [], Language.EN)
        assert result[0].effort_hint == "medium"


# ===========================================================================
# Test gap actions
# ===========================================================================


class TestTestGapActions:
    """Tests for test gap action generation."""

    def test_test_gaps_appended_after_findings(self) -> None:
        findings = [_make_finding()]
        gaps = [_make_test_gap()]
        result = generate_actions(findings, gaps, Language.EN)
        assert len(result) == 2
        assert result[0].order == 1
        assert result[1].order == 2
        assert "test gap" in result[1].title.lower() or "Testluecke" in result[1].title

    def test_test_gap_only(self) -> None:
        gaps = [_make_test_gap()]
        result = generate_actions([], gaps, Language.EN)
        assert len(result) == 1
        assert result[0].order == 1


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    """Tests for language support."""

    def test_english_severity_label(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        result = generate_actions(findings, [], Language.EN)
        assert "CRITICAL" in result[0].title

    def test_german_severity_label(self) -> None:
        findings = [_make_finding(severity=Severity.CRITICAL)]
        result = generate_actions(findings, [], Language.DE)
        assert "KRITISCH" in result[0].title

    def test_german_test_gap_title(self) -> None:
        gaps = [_make_test_gap()]
        result = generate_actions([], gaps, Language.DE)
        assert "Testluecke" in result[0].title
