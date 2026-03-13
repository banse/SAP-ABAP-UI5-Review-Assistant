"""Design review engine for the SAP ABAP/UI5 Review Assistant.

Analyses solution design text for completeness and feasibility by running
design-specific rules that check for missing sections, technology concerns,
and architectural gaps.
"""

from __future__ import annotations

from app.models.enums import Language, Severity
from app.models.schemas import Finding
from app.rules.base_rules import RuleMatch
from app.rules.design_review_rules import (
    DESIGN_REVIEW_CHECK_FUNCTIONS,
    DESIGN_REVIEW_RULES,
)

# ---------------------------------------------------------------------------
# Severity ordering (for sorting: CRITICAL first)
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


def _run_design_check(rule, code: str) -> list[RuleMatch]:
    """Run a design rule's custom check function against the text."""
    fn = DESIGN_REVIEW_CHECK_FUNCTIONS.get(rule.check_fn_name or "")
    if fn is None:
        return []

    try:
        results: list[tuple[str, int]] = fn(code)
    except Exception:
        return []

    matches: list[RuleMatch] = []
    for matched_text, line_num in results:
        matches.append(RuleMatch(
            rule=rule,
            matched_text=matched_text,
            line_number=line_num,
        ))
    return matches


def _match_to_finding(match: RuleMatch, language: Language) -> Finding:
    """Convert a ``RuleMatch`` into a ``Finding`` schema object."""
    rule = match.rule
    is_de = language == Language.DE

    title = rule.name_de if is_de else rule.name
    observation_text = rule.description_de if is_de else rule.description
    recommendation_text = rule.recommendation_de if is_de else rule.recommendation

    observation = f"{observation_text} — Finding: {match.matched_text}"

    return Finding(
        severity=Severity(rule.default_severity),
        title=title,
        observation=observation,
        reasoning=rule.description_de if is_de else rule.description,
        impact=f"Category: {rule.category}",
        recommendation=recommendation_text,
        rule_id=rule.rule_id,
        line_reference=str(match.line_number) if match.line_number else None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_design_review(code: str, language: Language) -> list[Finding]:
    """Analyze solution design text for completeness and feasibility.

    Iterates over all design review rules, runs each rule's custom check
    function against the design text, and produces Finding objects sorted
    by severity.

    Parameters
    ----------
    code:
        The solution design text to analyse.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[Finding]
        Findings sorted by severity (CRITICAL first, then IMPORTANT,
        OPTIONAL, UNCLEAR).
    """
    if not code or not code.strip():
        return []

    all_matches: list[RuleMatch] = []
    seen_rule_ids: set[str] = set()

    for rule in DESIGN_REVIEW_RULES:
        matches = _run_design_check(rule, code)

        # Deduplicate: only keep first match per rule
        for m in matches:
            if m.rule.rule_id not in seen_rule_ids:
                all_matches.append(m)
                seen_rule_ids.add(m.rule.rule_id)

    # Convert to Finding objects
    findings = [_match_to_finding(m, language) for m in all_matches]

    # Sort by severity
    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 99))

    return findings
