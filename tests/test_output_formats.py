"""Tests for the template-based output formatters.

Covers Markdown, ticket comment, and clipboard formats
for both DE and EN, including edge cases.
"""

from __future__ import annotations

import pytest

from app.formatter.templates import (
    format_as_clipboard,
    format_as_markdown,
    format_as_ticket_comment,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def full_response() -> dict:
    """A complete review response with all sections populated."""
    return {
        "review_summary": "The code contains several issues requiring attention.",
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "findings": [
            {
                "severity": "CRITICAL",
                "title": "SELECT * without WHERE clause",
                "observation": "Full table scan detected.",
                "reasoning": "Missing WHERE clause causes performance issues.",
                "impact": "High memory consumption in production.",
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
                "title": "Consider using inline declarations",
                "observation": "Old-style DATA declarations found.",
                "reasoning": "Inline declarations improve readability.",
                "impact": "Readability improvement.",
                "recommendation": "Use DATA(...) inline.",
                "artifact_reference": None,
                "line_reference": "10-15",
                "rule_id": None,
            },
        ],
        "missing_information": [
            {
                "question": "Is this code running in a background job?",
                "why_it_matters": "Affects performance recommendations.",
                "default_assumption": "Assuming foreground execution.",
                "category": "context",
            },
        ],
        "test_gaps": [
            {
                "category": "ABAP_UNIT",
                "description": "No unit tests for GET_DATA method.",
                "priority": "CRITICAL",
                "suggested_test": "Test with empty and large datasets.",
            },
        ],
        "recommended_actions": [
            {
                "order": 1,
                "title": "Add WHERE clause to SELECT",
                "description": "Filter by relevant key fields.",
                "effort_hint": "30 minutes",
                "finding_references": ["PERF-001"],
            },
            {
                "order": 2,
                "title": "Add error handling",
                "description": "Wrap DB access in TRY-CATCH.",
                "effort_hint": "15 minutes",
                "finding_references": ["ERR-002"],
            },
        ],
        "refactoring_hints": [
            {
                "category": "SMALL_FIX",
                "title": "Use inline DATA",
                "description": "Replace DATA declarations with inline form.",
                "benefit": "Improved readability.",
                "effort_hint": "10 minutes",
            },
        ],
        "risk_notes": [
            {
                "category": "FUNCTIONAL",
                "description": "Full table scan may cause timeouts.",
                "severity": "HIGH",
                "mitigation": "Add WHERE clause.",
            },
            {
                "category": "MAINTAINABILITY",
                "description": "Code lacks structure.",
                "severity": "MEDIUM",
                "mitigation": None,
            },
        ],
        "clean_core_hints": [
            {
                "finding": "Direct DB access to SAP table.",
                "released_api_alternative": "Use CDS view instead.",
                "severity": "IMPORTANT",
            },
        ],
        "overall_assessment": {
            "go_no_go": "CONDITIONAL_GO",
            "confidence": "HIGH",
            "summary": "Code needs critical fixes before merge.",
            "critical_count": 1,
            "important_count": 1,
            "optional_count": 1,
        },
        "language": "EN",
    }


@pytest.fixture()
def empty_response() -> dict:
    """A minimal valid review response with no findings or extras."""
    return {
        "review_summary": "",
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "findings": [],
        "missing_information": [],
        "test_gaps": [],
        "recommended_actions": [],
        "refactoring_hints": [],
        "risk_notes": [],
        "clean_core_hints": [],
        "overall_assessment": {
            "go_no_go": "GO",
            "confidence": "HIGH",
            "summary": "",
            "critical_count": 0,
            "important_count": 0,
            "optional_count": 0,
        },
        "language": "EN",
    }


@pytest.fixture()
def go_response() -> dict:
    """A simple GO response."""
    return {
        "review_summary": "All good.",
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "findings": [],
        "missing_information": [],
        "test_gaps": [],
        "recommended_actions": [],
        "refactoring_hints": [],
        "risk_notes": [],
        "clean_core_hints": [],
        "overall_assessment": {
            "go_no_go": "GO",
            "confidence": "HIGH",
            "summary": "Code is production-ready.",
            "critical_count": 0,
            "important_count": 0,
            "optional_count": 0,
        },
        "language": "EN",
    }


@pytest.fixture()
def nogo_response() -> dict:
    """A NO_GO response."""
    return {
        "review_summary": "Severe issues found.",
        "review_type": "SNIPPET_REVIEW",
        "artifact_type": "ABAP_CLASS",
        "findings": [
            {
                "severity": "CRITICAL",
                "title": "SQL injection vulnerability",
                "observation": "User input concatenated into SQL.",
                "reasoning": "Allows arbitrary SQL execution.",
                "impact": "Security breach.",
                "recommendation": "Use parameterized queries.",
                "artifact_reference": None,
                "line_reference": "5",
                "rule_id": "SEC-001",
            },
        ],
        "missing_information": [],
        "test_gaps": [],
        "recommended_actions": [],
        "refactoring_hints": [],
        "risk_notes": [],
        "clean_core_hints": [],
        "overall_assessment": {
            "go_no_go": "NO_GO",
            "confidence": "HIGH",
            "summary": "Critical security issue must be fixed.",
            "critical_count": 1,
            "important_count": 0,
            "optional_count": 0,
        },
        "language": "EN",
    }


# ---------------------------------------------------------------------------
# Markdown Format Tests
# ---------------------------------------------------------------------------


class TestMarkdownFormat:
    """Tests for format_as_markdown."""

    def test_contains_title(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "# Review Report" in md

    def test_contains_assessment_section(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Overall Assessment" in md
        assert "CONDITIONAL GO" in md

    def test_contains_findings_section(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Findings" in md
        assert "SELECT * without WHERE clause" in md

    def test_contains_findings_table(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "| # | Severity | Title | Recommendation |" in md
        assert "| 1 |" in md

    def test_contains_test_gaps(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Test Gaps" in md
        assert "ABAP_UNIT" in md

    def test_contains_risk_dashboard(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Risk Dashboard" in md
        assert "FUNCTIONAL" in md

    def test_contains_clean_core_hints(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Clean-Core Hints" in md
        assert "CDS view" in md

    def test_contains_refactoring_hints(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Refactoring Hints" in md
        assert "SMALL_FIX" in md

    def test_contains_recommended_actions(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Recommended Actions" in md
        assert "Add WHERE clause" in md

    def test_contains_open_questions(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "## Open Questions" in md
        assert "background job" in md

    def test_de_title(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="DE")
        assert "# Review-Bericht" in md

    def test_de_sections(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="DE")
        assert "## Gesamtbewertung" in md
        assert "## Zusammenfassung" in md
        assert "## Befunde" in md
        assert "## Testluecken" in md

    def test_empty_response_valid(self, empty_response: dict) -> None:
        md = format_as_markdown(empty_response, language="EN")
        assert "# Review Report" in md
        assert "**GO**" in md

    def test_go_response(self, go_response: dict) -> None:
        md = format_as_markdown(go_response, language="EN")
        assert "**GO**" in md
        assert "production-ready" in md

    def test_nogo_response(self, nogo_response: dict) -> None:
        md = format_as_markdown(nogo_response, language="EN")
        assert "**NO-GO**" in md
        assert "SQL injection" in md

    def test_all_severity_levels_in_findings(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "CRITICAL" in md
        assert "IMPORTANT" in md
        assert "OPTIONAL" in md

    def test_confidence_displayed(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="EN")
        assert "Confidence: HIGH" in md

    def test_de_confidence_displayed(self, full_response: dict) -> None:
        md = format_as_markdown(full_response, language="DE")
        assert "Konfidenz: HIGH" in md


# ---------------------------------------------------------------------------
# Ticket Comment Format Tests
# ---------------------------------------------------------------------------


class TestTicketCommentFormat:
    """Tests for format_as_ticket_comment."""

    def test_starts_with_verdict(self, full_response: dict) -> None:
        text = format_as_ticket_comment(full_response, language="EN")
        assert text.startswith("[CONDITIONAL GO]")

    def test_is_concise(self, full_response: dict) -> None:
        text = format_as_ticket_comment(full_response, language="EN")
        assert len(text) < 2000

    def test_contains_findings(self, full_response: dict) -> None:
        text = format_as_ticket_comment(full_response, language="EN")
        assert "Findings:" in text
        assert "[CRITICAL]" in text

    def test_limits_findings_to_five(self) -> None:
        response = {
            "overall_assessment": {"go_no_go": "NO_GO", "summary": ""},
            "findings": [
                {"severity": "CRITICAL", "title": f"Finding {i}", "recommendation": "Fix it"}
                for i in range(8)
            ],
            "recommended_actions": [],
        }
        text = format_as_ticket_comment(response, language="EN")
        assert "+3 more" in text

    def test_de_labels(self, full_response: dict) -> None:
        text = format_as_ticket_comment(full_response, language="DE")
        assert "Code-Review Ergebnis" in text
        assert "Befunde:" in text

    def test_empty_response(self, empty_response: dict) -> None:
        text = format_as_ticket_comment(empty_response, language="EN")
        assert "[GO]" in text
        assert len(text) > 0


# ---------------------------------------------------------------------------
# Clipboard Format Tests
# ---------------------------------------------------------------------------


class TestClipboardFormat:
    """Tests for format_as_clipboard."""

    def test_is_plain_text(self, full_response: dict) -> None:
        text = format_as_clipboard(full_response, language="EN")
        # Should not contain markdown formatting characters
        assert "**" not in text
        assert "##" not in text

    def test_starts_with_verdict(self, full_response: dict) -> None:
        text = format_as_clipboard(full_response, language="EN")
        assert text.startswith("CONDITIONAL GO")

    def test_contains_findings_list(self, full_response: dict) -> None:
        text = format_as_clipboard(full_response, language="EN")
        assert "Findings:" in text
        assert "[CRITICAL]" in text

    def test_contains_actions(self, full_response: dict) -> None:
        text = format_as_clipboard(full_response, language="EN")
        assert "Actions:" in text
        assert "Add WHERE clause" in text

    def test_de_labels(self, full_response: dict) -> None:
        text = format_as_clipboard(full_response, language="DE")
        assert "Befunde:" in text
        assert "Massnahmen:" in text

    def test_empty_response(self, empty_response: dict) -> None:
        text = format_as_clipboard(empty_response, language="EN")
        assert "GO" in text
        assert len(text) > 0

    def test_go_verdict(self, go_response: dict) -> None:
        text = format_as_clipboard(go_response, language="EN")
        assert text.startswith("GO")
        assert "production-ready" in text
