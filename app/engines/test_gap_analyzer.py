"""Test gap detection engine for the SAP ABAP/UI5 Review Assistant.

Analyses source code against test gap rules and produces a prioritised list
of ``TestGap`` objects describing missing test coverage.
"""

from __future__ import annotations

import re

from app.models.enums import ArtifactType, Language, ReviewContext, Severity, TestGapCategory
from app.models.schemas import TestGap
from app.rules.test_gap_rules import ALL_TEST_GAP_RULES, TestGapRule

# ---------------------------------------------------------------------------
# Severity ordering (CRITICAL first)
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {
    Severity.CRITICAL.value: 0,
    Severity.IMPORTANT.value: 1,
    Severity.OPTIONAL.value: 2,
    Severity.UNCLEAR.value: 3,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_applicable_rules(artifact_type: ArtifactType) -> list[TestGapRule]:
    """Return all test gap rules whose artifact_types include the given type."""
    art_val = artifact_type.value
    applicable: list[TestGapRule] = []
    for rule in ALL_TEST_GAP_RULES:
        if art_val in rule.artifact_types:
            applicable.append(rule)
    return applicable


def _has_test_class(code: str) -> bool:
    """Return True if the code already contains an ABAP Unit test class."""
    return bool(re.search(r"FOR\s+TESTING", code, re.IGNORECASE))


def _run_detection(rule: TestGapRule, code: str) -> list[re.Match[str]]:
    """Run a rule's detection pattern against the code and return matches."""
    try:
        compiled = re.compile(rule.detection_pattern, rule.detection_flags)
        return list(compiled.finditer(code))
    except re.error:
        return []


def _match_to_test_gap(
    rule: TestGapRule,
    match: re.Match[str],
    language: Language,
) -> TestGap:
    """Convert a rule match into a ``TestGap`` schema object."""
    is_de = language == Language.DE

    description = rule.description_de if is_de else rule.description
    matched_text = match.group().strip()
    if len(matched_text) > 120:
        matched_text = matched_text[:117] + "..."
    description = f"{description} [Detected: {matched_text}]"

    suggested = rule.suggested_test_template_de if is_de else rule.suggested_test_template

    return TestGap(
        category=TestGapCategory(rule.category),
        description=description,
        priority=Severity(rule.default_priority),
        suggested_test=suggested if suggested else None,
    )


def _dedup_key(gap: TestGap) -> str:
    """Return a deduplication key for a TestGap."""
    return f"{gap.category.value}::{gap.priority.value}::{gap.description[:80]}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_test_gaps(
    code: str,
    artifact_type: ArtifactType,
    review_context: ReviewContext,
    language: Language,
) -> list[TestGap]:
    """Analyse *code* for missing test coverage and return prioritised gaps.

    Parameters
    ----------
    code:
        The source code to analyse.
    artifact_type:
        The SAP artifact type being reviewed.
    review_context:
        The project phase / intent (GREENFIELD, EXTENSION, ...).
    language:
        Output language (EN or DE).

    Returns
    -------
    list[TestGap]
        Test gaps sorted by priority (CRITICAL first), then by category.
    """
    if not code or not code.strip():
        return []

    rules = _get_applicable_rules(artifact_type)
    if not rules:
        return []

    # Check whether the code already contains test classes (ABAP only).
    # If it does, we lower the priority of TG-ABAP-001 matches since some
    # test infrastructure already exists (but we still report for completeness).
    has_tests = _has_test_class(code)

    all_gaps: list[TestGap] = []
    seen_rule_ids: set[str] = set()

    for rule in rules:
        matches = _run_detection(rule, code)
        if not matches:
            continue

        # Only keep first match per rule to avoid flooding
        if rule.rule_id in seen_rule_ids:
            continue
        seen_rule_ids.add(rule.rule_id)

        gap = _match_to_test_gap(rule, matches[0], language)

        # Downgrade priority if test class already exists and this is
        # the basic "public method without test" rule
        if has_tests and rule.rule_id == "TG-ABAP-001":
            gap = TestGap(
                category=gap.category,
                description=gap.description,
                priority=Severity.OPTIONAL,
                suggested_test=gap.suggested_test,
            )

        all_gaps.append(gap)

    # Deduplicate by content similarity
    seen_keys: set[str] = set()
    deduped: list[TestGap] = []
    for gap in all_gaps:
        key = _dedup_key(gap)
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(gap)

    # Sort: CRITICAL first, then IMPORTANT, OPTIONAL, UNCLEAR.
    # Within same priority, sort by category for stable ordering.
    deduped.sort(
        key=lambda g: (
            _SEVERITY_ORDER.get(g.priority.value, 99),
            g.category.value,
        )
    )

    return deduped
