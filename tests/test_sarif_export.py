"""Tests for the SARIF v2.1.0 export formatter.

Validates SARIF structure, severity mapping, rule definitions,
location mapping, and edge cases.
"""

from __future__ import annotations

import pytest

from app.formatter.sarif import format_as_sarif, _parse_start_line


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_response() -> dict:
    """A complete review response with multiple findings."""
    return {
        "review_summary": "The code contains several issues.",
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "findings": [
            {
                "severity": "CRITICAL",
                "title": "SELECT * without WHERE clause",
                "observation": "Full table scan detected.",
                "reasoning": "Missing WHERE clause causes performance issues.",
                "impact": "High memory consumption.",
                "recommendation": "Add WHERE clause with appropriate filter.",
                "artifact_reference": "ZCL_EXAMPLE",
                "line_reference": "42",
                "rule_id": "PERF-001",
            },
            {
                "severity": "IMPORTANT",
                "title": "Missing error handling",
                "observation": "No exception handling around DB access.",
                "reasoning": "Unhandled exceptions crash the application.",
                "impact": "Application dumps in production.",
                "recommendation": "Add TRY-CATCH block.",
                "artifact_reference": None,
                "line_reference": None,
                "rule_id": "ERR-002",
            },
            {
                "severity": "OPTIONAL",
                "title": "Consider inline declarations",
                "observation": "Old-style DATA declarations found.",
                "reasoning": "Inline declarations improve readability.",
                "impact": "Readability improvement.",
                "recommendation": "Use DATA(...) inline.",
                "artifact_reference": None,
                "line_reference": "10-15",
                "rule_id": None,
            },
            {
                "severity": "UNCLEAR",
                "title": "Potential naming issue",
                "observation": "Variable name unclear.",
                "reasoning": "Context insufficient to determine.",
                "impact": "Possible readability issue.",
                "recommendation": "Review variable naming.",
                "artifact_reference": None,
                "line_reference": None,
                "rule_id": None,
            },
        ],
        "overall_assessment": {
            "go_no_go": "CONDITIONAL_GO",
            "confidence": "HIGH",
            "summary": "Code needs fixes.",
            "critical_count": 1,
            "important_count": 1,
            "optional_count": 1,
        },
    }


@pytest.fixture()
def empty_response() -> dict:
    """A minimal valid response with no findings."""
    return {
        "review_summary": "",
        "findings": [],
        "overall_assessment": {
            "go_no_go": "GO",
            "confidence": "HIGH",
            "summary": "",
        },
    }


# ---------------------------------------------------------------------------
# SARIF Schema Structure Tests
# ---------------------------------------------------------------------------


class TestSarifSchema:
    """Tests for SARIF v2.1.0 schema compliance."""

    def test_has_schema_field(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        assert "$schema" in sarif
        assert "sarif-schema-2.1.0" in sarif["$schema"]

    def test_has_version_field(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        assert sarif["version"] == "2.1.0"

    def test_has_runs_array(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        assert "runs" in sarif
        assert isinstance(sarif["runs"], list)
        assert len(sarif["runs"]) == 1

    def test_run_has_tool_and_results(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        run = sarif["runs"][0]
        assert "tool" in run
        assert "results" in run


# ---------------------------------------------------------------------------
# Tool Driver Tests
# ---------------------------------------------------------------------------


class TestSarifToolDriver:
    """Tests for SARIF tool driver section."""

    def test_driver_has_name(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        driver = sarif["runs"][0]["tool"]["driver"]
        assert driver["name"] == "SAP ABAP/UI5 Review Assistant"

    def test_driver_has_version(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        driver = sarif["runs"][0]["tool"]["driver"]
        assert driver["version"] == "2.0.0"

    def test_custom_tool_name(self, full_response: dict) -> None:
        sarif = format_as_sarif(
            full_response,
            tool_name="Custom Tool",
            tool_version="1.0.0",
        )
        driver = sarif["runs"][0]["tool"]["driver"]
        assert driver["name"] == "Custom Tool"
        assert driver["version"] == "1.0.0"

    def test_driver_has_rules(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        driver = sarif["runs"][0]["tool"]["driver"]
        assert "rules" in driver
        assert isinstance(driver["rules"], list)


# ---------------------------------------------------------------------------
# Findings to Results Mapping Tests
# ---------------------------------------------------------------------------


class TestSarifResults:
    """Tests for SARIF result mapping from findings."""

    def test_result_count_matches_findings(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        assert len(results) == len(full_response["findings"])

    def test_critical_maps_to_error(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        critical_result = results[0]  # First finding is CRITICAL
        assert critical_result["level"] == "error"

    def test_important_maps_to_error(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        important_result = results[1]  # Second finding is IMPORTANT
        assert important_result["level"] == "error"

    def test_optional_maps_to_warning(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        optional_result = results[2]  # Third finding is OPTIONAL
        assert optional_result["level"] == "warning"

    def test_unclear_maps_to_note(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        unclear_result = results[3]  # Fourth finding is UNCLEAR
        assert unclear_result["level"] == "note"

    def test_result_has_rule_id(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        assert results[0]["ruleId"] == "PERF-001"
        assert results[1]["ruleId"] == "ERR-002"

    def test_result_has_message(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        assert results[0]["message"]["text"] == "Full table scan detected."


# ---------------------------------------------------------------------------
# Rule Definition Tests
# ---------------------------------------------------------------------------


class TestSarifRules:
    """Tests for SARIF rule definitions."""

    def test_rules_populated_from_findings(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        # 2 explicit rule_ids + 2 generated = 4 unique rules
        assert len(rules) >= 2

    def test_rule_has_short_description(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        rule = rules[0]
        assert "shortDescription" in rule
        assert rule["shortDescription"]["text"] == "SELECT * without WHERE clause"

    def test_rule_has_help_text(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        rule = rules[0]
        assert "help" in rule
        assert "WHERE clause" in rule["help"]["text"]

    def test_rule_has_default_configuration(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        rule = rules[0]
        assert "defaultConfiguration" in rule
        assert rule["defaultConfiguration"]["level"] == "error"


# ---------------------------------------------------------------------------
# Location Mapping Tests
# ---------------------------------------------------------------------------


class TestSarifLocations:
    """Tests for SARIF location mapping from line references."""

    def test_line_reference_maps_to_region(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        # First finding has line_reference "42"
        assert "locations" in results[0]
        region = results[0]["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] == 42

    def test_range_reference_uses_start_line(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        # Third finding has line_reference "10-15"
        assert "locations" in results[2]
        region = results[2]["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] == 10

    def test_no_line_reference_no_location(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        # Second finding has no line_reference and no artifact_reference
        assert "locations" not in results[1]

    def test_artifact_reference_maps_to_uri(self, full_response: dict) -> None:
        sarif = format_as_sarif(full_response)
        results = sarif["runs"][0]["results"]
        loc = results[0]["locations"][0]["physicalLocation"]
        assert loc["artifactLocation"]["uri"] == "ZCL_EXAMPLE"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestSarifEdgeCases:
    """Tests for edge cases in SARIF generation."""

    def test_empty_response_produces_valid_sarif(self, empty_response: dict) -> None:
        sarif = format_as_sarif(empty_response)
        assert sarif["version"] == "2.1.0"
        assert sarif["runs"][0]["results"] == []
        assert sarif["runs"][0]["tool"]["driver"]["rules"] == []

    def test_finding_without_rule_id_gets_generated_id(self) -> None:
        response = {
            "findings": [
                {
                    "severity": "OPTIONAL",
                    "title": "Test finding",
                    "observation": "Test obs.",
                    "recommendation": "Fix it.",
                },
            ],
        }
        sarif = format_as_sarif(response)
        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"].startswith("REVIEW-")

    def test_duplicate_rule_ids_deduplicated(self) -> None:
        response = {
            "findings": [
                {"severity": "CRITICAL", "title": "F1", "observation": "O1", "rule_id": "PERF-001"},
                {"severity": "CRITICAL", "title": "F2", "observation": "O2", "rule_id": "PERF-001"},
            ],
        }
        sarif = format_as_sarif(response)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        assert len(sarif["runs"][0]["results"]) == 2


# ---------------------------------------------------------------------------
# Line Reference Parsing Tests
# ---------------------------------------------------------------------------


class TestParseStartLine:
    """Tests for _parse_start_line helper."""

    def test_simple_number(self) -> None:
        assert _parse_start_line("42") == 42

    def test_range(self) -> None:
        assert _parse_start_line("10-15") == 10

    def test_line_prefix(self) -> None:
        assert _parse_start_line("Line 42") == 42

    def test_none_returns_none(self) -> None:
        assert _parse_start_line(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert _parse_start_line("") is None

    def test_non_numeric_returns_none(self) -> None:
        assert _parse_start_line("abc") is None
