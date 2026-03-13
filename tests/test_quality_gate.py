"""Tests for the quality gate engine.

Validates threshold logic, default configuration, custom thresholds,
and edge cases for CI/CD quality gate evaluation.
"""

from __future__ import annotations

import pytest

from app.engines.quality_gate import (
    QualityGateConfig,
    QualityGateResult,
    evaluate_quality_gate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def response_with_critical() -> dict:
    """A response with one CRITICAL finding."""
    return {
        "findings": [
            {"severity": "CRITICAL", "title": "Critical issue", "rule_id": "SEC-001"},
            {"severity": "IMPORTANT", "title": "Important issue", "rule_id": "ERR-001"},
            {"severity": "OPTIONAL", "title": "Optional issue", "rule_id": None},
        ],
        "overall_assessment": {
            "go_no_go": "CONDITIONAL_GO",
            "confidence": "HIGH",
            "summary": "Issues found.",
        },
        "clean_core_hints": [
            {"finding": "Direct DB access", "severity": "IMPORTANT"},
        ],
    }


@pytest.fixture()
def response_no_critical() -> dict:
    """A response with no CRITICAL findings."""
    return {
        "findings": [
            {"severity": "IMPORTANT", "title": "Important issue", "rule_id": "ERR-001"},
            {"severity": "OPTIONAL", "title": "Optional issue", "rule_id": None},
        ],
        "overall_assessment": {
            "go_no_go": "GO",
            "confidence": "HIGH",
            "summary": "Minor issues only.",
        },
        "clean_core_hints": [],
    }


@pytest.fixture()
def empty_response() -> dict:
    """A response with no findings at all."""
    return {
        "findings": [],
        "overall_assessment": {
            "go_no_go": "GO",
            "confidence": "HIGH",
            "summary": "All good.",
        },
        "clean_core_hints": [],
    }


# ---------------------------------------------------------------------------
# Default Config Tests
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    """Tests for the default quality gate configuration."""

    def test_fails_on_any_critical(self, response_with_critical: dict) -> None:
        result = evaluate_quality_gate(response_with_critical)
        assert result.passed is False
        assert any("CRITICAL" in v for v in result.violations)

    def test_passes_when_no_critical(self, response_no_critical: dict) -> None:
        result = evaluate_quality_gate(response_no_critical)
        assert result.passed is True
        assert result.violations == []

    def test_empty_response_passes(self, empty_response: dict) -> None:
        result = evaluate_quality_gate(empty_response)
        assert result.passed is True
        assert result.reason == "All quality gate checks passed"

    def test_result_includes_config(self, empty_response: dict) -> None:
        result = evaluate_quality_gate(empty_response)
        assert "max_critical" in result.config
        assert result.config["max_critical"] == 0


# ---------------------------------------------------------------------------
# Custom Threshold Tests
# ---------------------------------------------------------------------------


class TestCustomThresholds:
    """Tests for custom quality gate thresholds."""

    def test_max_critical_allows_some(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=1)
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is True

    def test_max_important_threshold(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=5, max_important=0)
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is False
        assert any("IMPORTANT" in v for v in result.violations)

    def test_max_total_threshold(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=5, max_total=2)
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is False
        assert any("Total findings" in v for v in result.violations)

    def test_require_go_fails_on_conditional(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=5, require_go=True)
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is False
        assert any("CONDITIONAL_GO" in v for v in result.violations)

    def test_require_go_passes_on_go(self, response_no_critical: dict) -> None:
        config = QualityGateConfig(require_go=True)
        result = evaluate_quality_gate(response_no_critical, config)
        assert result.passed is True

    def test_require_clean_core_fails_on_hints(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=5, require_clean_core=True)
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is False
        assert any("clean-core" in v.lower() for v in result.violations)

    def test_require_clean_core_passes_when_empty(self, response_no_critical: dict) -> None:
        config = QualityGateConfig(require_clean_core=True)
        result = evaluate_quality_gate(response_no_critical, config)
        assert result.passed is True

    def test_custom_blocked_rules(self, response_with_critical: dict) -> None:
        config = QualityGateConfig(max_critical=5, custom_blocked_rules=["SEC-001"])
        result = evaluate_quality_gate(response_with_critical, config)
        assert result.passed is False
        assert any("SEC-001" in v for v in result.violations)

    def test_custom_blocked_rules_not_present(self, response_no_critical: dict) -> None:
        config = QualityGateConfig(custom_blocked_rules=["XYZ-999"])
        result = evaluate_quality_gate(response_no_critical, config)
        assert result.passed is True


# ---------------------------------------------------------------------------
# Result Structure Tests
# ---------------------------------------------------------------------------


class TestResultStructure:
    """Tests for QualityGateResult structure."""

    def test_result_has_all_fields(self, empty_response: dict) -> None:
        result = evaluate_quality_gate(empty_response)
        assert isinstance(result, QualityGateResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.reason, str)
        assert isinstance(result.violations, list)
        assert isinstance(result.config, dict)

    def test_failure_reason_includes_violation_count(
        self, response_with_critical: dict
    ) -> None:
        result = evaluate_quality_gate(response_with_critical)
        assert "violation" in result.reason.lower()

    def test_to_dict_serializable(self, empty_response: dict) -> None:
        result = evaluate_quality_gate(empty_response)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "passed" in d
        assert "reason" in d
        assert "violations" in d
        assert "config" in d

    def test_multiple_violations_accumulated(self) -> None:
        response = {
            "findings": [
                {"severity": "CRITICAL", "title": "C1", "rule_id": "BLK-001"},
                {"severity": "CRITICAL", "title": "C2", "rule_id": None},
                {"severity": "IMPORTANT", "title": "I1", "rule_id": None},
            ],
            "overall_assessment": {"go_no_go": "NO_GO"},
            "clean_core_hints": [{"finding": "Bad access", "severity": "IMPORTANT"}],
        }
        config = QualityGateConfig(
            max_critical=0,
            max_important=0,
            require_go=True,
            require_clean_core=True,
            custom_blocked_rules=["BLK-001"],
        )
        result = evaluate_quality_gate(response, config)
        assert result.passed is False
        # Should have at least 4 violations: critical, important, require_go, clean_core, blocked
        assert len(result.violations) >= 4
