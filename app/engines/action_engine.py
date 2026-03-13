"""Recommended actions engine for the SAP ABAP/UI5 Review Assistant.

Transforms findings and test gaps into ordered, actionable recommendations
with effort hints and bilingual support.
"""

from __future__ import annotations

from app.models.enums import Language, Severity
from app.models.schemas import Finding, RecommendedAction, TestGap


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
# Effort estimation
# ---------------------------------------------------------------------------


def _estimate_effort(finding: Finding) -> str:
    """Estimate effort based on finding characteristics."""
    # Single-line fixes: style, simple readability
    category = ""
    if finding.impact and finding.impact.startswith("Category: "):
        category = finding.impact[len("Category: "):].strip().lower()

    if category in ("style", "i18n"):
        return "small"
    if category in ("structure", "readability", "maintainability"):
        return "medium"
    if category in ("performance", "error_handling", "security"):
        if finding.severity == Severity.CRITICAL:
            return "medium"
        return "small"
    return "medium"


def _finding_to_action(
    finding: Finding,
    order: int,
    language: Language,
) -> RecommendedAction:
    """Convert a finding into a recommended action."""
    is_de = language == Language.DE

    if is_de:
        severity_label = {
            Severity.CRITICAL: "KRITISCH",
            Severity.IMPORTANT: "WICHTIG",
            Severity.OPTIONAL: "OPTIONAL",
            Severity.UNCLEAR: "UNKLAR",
        }.get(finding.severity, "UNKLAR")
        title = f"[{severity_label}] {finding.title}"
    else:
        title = f"[{finding.severity.value}] {finding.title}"

    references: list[str] = []
    if finding.rule_id:
        references.append(finding.rule_id)

    return RecommendedAction(
        order=order,
        title=title,
        description=finding.recommendation,
        effort_hint=_estimate_effort(finding),
        finding_references=references,
    )


def _test_gap_to_action(
    gap: TestGap,
    order: int,
    language: Language,
) -> RecommendedAction:
    """Convert a test gap into a recommended action."""
    is_de = language == Language.DE

    if is_de:
        title = f"Testluecke schliessen: {gap.category.value}"
        desc = gap.description
        if gap.suggested_test:
            desc += f"\n\nVorgeschlagener Test: {gap.suggested_test}"
    else:
        title = f"Close test gap: {gap.category.value}"
        desc = gap.description
        if gap.suggested_test:
            desc += f"\n\nSuggested test: {gap.suggested_test}"

    return RecommendedAction(
        order=order,
        title=title,
        description=desc,
        effort_hint="medium",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_actions(
    findings: list[Finding],
    test_gaps: list[TestGap],
    language: Language,
) -> list[RecommendedAction]:
    """Generate ordered recommended actions from findings and test gaps.

    Parameters
    ----------
    findings:
        Findings produced by the findings engine.
    test_gaps:
        Test gaps identified during review.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[RecommendedAction]
        Actions ordered by severity (CRITICAL first), then test gaps.
    """
    # Sort findings by severity
    sorted_findings = sorted(
        findings,
        key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 99),
    )

    actions: list[RecommendedAction] = []
    order = 1

    # Findings-based actions
    for finding in sorted_findings:
        action = _finding_to_action(finding, order, language)
        actions.append(action)
        order += 1

    # Test-gap actions appended at the end
    for gap in test_gaps:
        action = _test_gap_to_action(gap, order, language)
        actions.append(action)
        order += 1

    return actions
