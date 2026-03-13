"""Main findings engine for the SAP ABAP/UI5 Review Assistant.

Runs applicable review rules against source code and produces a sorted
list of ``Finding`` objects.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from app.models.enums import ArtifactType, Language, ReviewContext, ReviewType, Severity
from app.models.schemas import Finding
from app.rules.abap_basic import ABAP_CHECK_FUNCTIONS, ABAP_RULES
from app.rules.base_rules import ReviewRule, RuleMatch
from app.rules.cds_basic import CDS_CHECK_FUNCTIONS, CDS_RULES
from app.rules.ui5_basic import UI5_CHECK_FUNCTIONS, UI5_RULES

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
# Combined registries
# ---------------------------------------------------------------------------

ALL_RULES: tuple[ReviewRule, ...] = ABAP_RULES + CDS_RULES + UI5_RULES

ALL_CHECK_FUNCTIONS: dict[str, Any] = {
    **ABAP_CHECK_FUNCTIONS,
    **CDS_CHECK_FUNCTIONS,
    **UI5_CHECK_FUNCTIONS,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_applicable_rules(artifact_type: ArtifactType) -> list[ReviewRule]:
    """Return all rules whose artifact_types include the given type."""
    applicable: list[ReviewRule] = []
    art_val = artifact_type.value

    for rule in ALL_RULES:
        if art_val in rule.artifact_types or "MIXED_FULLSTACK" in rule.artifact_types:
            applicable.append(rule)

    return applicable


def _run_regex_rule(rule: ReviewRule, code: str) -> list[RuleMatch]:
    """Run a pure regex rule against the code and return matches."""
    matches: list[RuleMatch] = []
    try:
        compiled = re.compile(rule.pattern, rule.pattern_flags)
        for m in compiled.finditer(code):
            line_num = code[: m.start()].count("\n") + 1
            # Extract a small context window around the match
            start = max(0, m.start() - 40)
            end = min(len(code), m.end() + 40)
            context = code[start:end].strip()
            matches.append(RuleMatch(
                rule=rule,
                matched_text=m.group(),
                line_number=line_num,
                context=context,
            ))
    except re.error:
        pass  # Malformed regex — skip rule silently
    return matches


def _run_custom_check(rule: ReviewRule, code: str) -> list[RuleMatch]:
    """Run a custom check function and return matches."""
    fn = ALL_CHECK_FUNCTIONS.get(rule.check_fn_name or "")
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

    observation = f"{observation_text} — Matched: `{match.matched_text}`"
    if match.context:
        observation += f" (context: ...{match.context}...)"

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


def run_findings_engine(
    code: str,
    artifact_type: ArtifactType,
    review_type: ReviewType,
    review_context: ReviewContext,
    language: Language,
) -> list[Finding]:
    """Run all applicable rules against *code* and return sorted findings.

    Parameters
    ----------
    code:
        The source code (or diff) to analyse.
    artifact_type:
        The detected or user-provided artifact type.
    review_type:
        The detected or user-provided review type.
    review_context:
        The project phase / intent (GREENFIELD, EXTENSION, ...).
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

    # Collect applicable rules
    rules = _get_applicable_rules(artifact_type)

    # If artifact type is unknown / catch-all, use all rules
    if not rules:
        rules = list(ALL_RULES)

    # Run each rule
    all_matches: list[RuleMatch] = []
    seen_rule_ids: set[str] = set()

    for rule in rules:
        if rule.check_fn_name:
            # Custom check function
            matches = _run_custom_check(rule, code)
        else:
            # Pure regex
            matches = _run_regex_rule(rule, code)

        # Deduplicate: only keep first match per rule to avoid flooding
        for m in matches:
            if m.rule.rule_id not in seen_rule_ids:
                all_matches.append(m)
                seen_rule_ids.add(m.rule.rule_id)

    # Convert to Finding objects
    findings = [_match_to_finding(m, language) for m in all_matches]

    # Sort by severity
    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 99))

    return findings
