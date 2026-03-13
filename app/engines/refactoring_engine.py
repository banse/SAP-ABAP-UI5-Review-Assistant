"""Refactoring hint engine for the SAP ABAP/UI5 Review Assistant.

Matches findings to refactoring rules and generates structured
refactoring suggestions with categories and effort hints.
"""

from __future__ import annotations

from app.models.enums import ArtifactType, Language, RefactoringCategory
from app.models.schemas import Finding, RefactoringHint
from app.rules.refactoring_rules import ALL_REFACTORING_RULES, RefactoringRule


# ---------------------------------------------------------------------------
# Category ordering (most urgent first)
# ---------------------------------------------------------------------------

_CATEGORY_ORDER: dict[str, int] = {
    RefactoringCategory.SMALL_FIX.value: 0,
    RefactoringCategory.TARGETED_STRUCTURE_IMPROVEMENT.value: 1,
    RefactoringCategory.MEDIUM_TERM_REFACTORING_HINT.value: 2,
    RefactoringCategory.NOT_IMMEDIATE_REBUILD.value: 3,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_finding_categories(findings: list[Finding]) -> set[str]:
    """Extract unique finding categories from the impact field."""
    categories: set[str] = set()
    for finding in findings:
        if finding.impact and finding.impact.startswith("Category: "):
            cat = finding.impact[len("Category: "):].strip().lower()
            if cat:
                categories.add(cat)
    return categories


def _rule_to_hint(rule: RefactoringRule, language: Language) -> RefactoringHint:
    """Convert a refactoring rule into a RefactoringHint schema object."""
    is_de = language == Language.DE

    return RefactoringHint(
        category=RefactoringCategory(rule.category),
        title=rule.name_de if is_de else rule.name,
        description=rule.description_de if is_de else rule.description,
        benefit=rule.benefit_de if is_de else rule.benefit,
        effort_hint=rule.effort_hint,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_refactoring_hints(
    findings: list[Finding],
    artifact_type: ArtifactType,
    language: Language,
) -> list[RefactoringHint]:
    """Generate refactoring hints triggered by findings.

    Parameters
    ----------
    findings:
        Findings produced by the findings engine.
    artifact_type:
        The detected or provided artifact type.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[RefactoringHint]
        Refactoring hints sorted by category urgency (SMALL_FIX first).
    """
    if not findings:
        return []

    active_categories = _extract_finding_categories(findings)
    if not active_categories:
        return []

    hints: list[RefactoringHint] = []
    seen_rule_ids: set[str] = set()

    for rule in ALL_REFACTORING_RULES:
        if rule.rule_id in seen_rule_ids:
            continue

        # Check if any of the rule's trigger categories match active findings
        trigger_cats = {c.lower() for c in rule.trigger_finding_categories}
        if trigger_cats & active_categories:
            hint = _rule_to_hint(rule, language)
            hints.append(hint)
            seen_rule_ids.add(rule.rule_id)

    # Sort by category urgency
    hints.sort(
        key=lambda h: _CATEGORY_ORDER.get(h.category.value, 99),
    )

    return hints
