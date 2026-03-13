"""Tests for the refactoring engine."""

from __future__ import annotations

import pytest

from app.engines.refactoring_engine import generate_refactoring_hints
from app.models.enums import (
    ArtifactType,
    Language,
    RefactoringCategory,
    Severity,
)
from app.models.schemas import Finding, RefactoringHint


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
    findings: list[Finding] | None = None,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
) -> list[RefactoringHint]:
    return generate_refactoring_hints(
        findings=findings or [],
        artifact_type=artifact_type,
        language=language,
    )


# ===========================================================================
# Basic behaviour
# ===========================================================================


class TestBasicBehaviour:
    """Basic refactoring hint generation tests."""

    def test_no_findings_returns_empty(self) -> None:
        result = _run(findings=[])
        assert result == []

    def test_findings_with_matching_category_returns_hints(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings)
        assert len(result) > 0

    def test_hints_are_refactoring_hint_type(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings)
        for hint in result:
            assert isinstance(hint, RefactoringHint)


# ===========================================================================
# Specific trigger categories
# ===========================================================================


class TestTriggerCategories:
    """Tests for specific finding categories triggering hints."""

    def test_structure_findings_trigger_extract_method(self) -> None:
        findings = [_make_finding(category="structure")]
        result = _run(findings=findings)
        titles = [h.title.lower() for h in result]
        assert any("extract" in t for t in titles)

    def test_error_handling_triggers_error_hint(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings)
        titles = [h.title.lower() for h in result]
        assert any("error" in t or "fehler" in t or "exception" in t for t in titles)

    def test_performance_triggers_select_hint(self) -> None:
        findings = [_make_finding(category="performance")]
        result = _run(findings=findings)
        titles = [h.title.lower() for h in result]
        assert any("select" in t for t in titles)

    def test_readability_triggers_formatter_or_extract(self) -> None:
        findings = [_make_finding(category="readability")]
        result = _run(findings=findings)
        assert len(result) > 0

    def test_style_triggers_modernize(self) -> None:
        findings = [_make_finding(category="style")]
        result = _run(findings=findings)
        titles = [h.title.lower() for h in result]
        assert any("modern" in t for t in titles)


# ===========================================================================
# Categories correct
# ===========================================================================


class TestCategories:
    """Tests for correct refactoring category assignment."""

    def test_error_handling_hint_is_small_fix(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings)
        error_hints = [h for h in result if "error" in h.title.lower() or "fehler" in h.title.lower()]
        if error_hints:
            assert error_hints[0].category == RefactoringCategory.SMALL_FIX

    def test_structure_hint_is_targeted_improvement(self) -> None:
        findings = [_make_finding(category="structure")]
        result = _run(findings=findings)
        extract_hints = [h for h in result if "extract" in h.title.lower()]
        if extract_hints:
            assert extract_hints[0].category == RefactoringCategory.TARGETED_STRUCTURE_IMPROVEMENT

    def test_hints_sorted_by_urgency(self) -> None:
        findings = [
            _make_finding(category="error_handling"),
            _make_finding(category="style", rule_id="ABAP-STY-001"),
        ]
        result = _run(findings=findings)
        if len(result) >= 2:
            cat_orders = [
                {"SMALL_FIX": 0, "TARGETED_STRUCTURE_IMPROVEMENT": 1,
                 "MEDIUM_TERM_REFACTORING_HINT": 2, "NOT_IMMEDIATE_REBUILD": 3
                 }.get(h.category.value, 99) for h in result
            ]
            assert cat_orders == sorted(cat_orders)


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    """Tests for language support."""

    def test_english_output(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings, language=Language.EN)
        assert len(result) > 0
        for h in result:
            assert h.title  # not empty

    def test_german_output(self) -> None:
        findings = [_make_finding(category="error_handling")]
        result = _run(findings=findings, language=Language.DE)
        assert len(result) > 0
        for h in result:
            assert h.title  # not empty

    def test_german_and_english_titles_differ(self) -> None:
        findings = [_make_finding(category="error_handling")]
        en = _run(findings=findings, language=Language.EN)
        de = _run(findings=findings, language=Language.DE)
        if en and de:
            assert en[0].title != de[0].title
