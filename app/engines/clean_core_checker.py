"""Clean-core compliance checker for the SAP ABAP/UI5 Review Assistant.

Runs clean-core rules against source code and produces a sorted list of
``CleanCoreHint`` objects.
"""

from __future__ import annotations

import re

from app.models.enums import ArtifactType, Language, Severity
from app.models.schemas import CleanCoreHint
from app.rules.clean_core_rules import CLEAN_CORE_RULES, CleanCoreRule

# ---------------------------------------------------------------------------
# Severity ordering (for sorting: CRITICAL first)
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {
    Severity.CRITICAL.value: 0,
    Severity.IMPORTANT.value: 1,
    Severity.OPTIONAL.value: 2,
    Severity.UNCLEAR.value: 3,
}

# Artifact types where clean-core checks are relevant
_ABAP_ARTIFACT_TYPES: set[str] = {
    ArtifactType.ABAP_CLASS.value,
    ArtifactType.ABAP_METHOD.value,
    ArtifactType.ABAP_REPORT.value,
    ArtifactType.BEHAVIOR_IMPLEMENTATION.value,
    ArtifactType.MIXED_FULLSTACK.value,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_clean_core_rule(
    rule: CleanCoreRule,
    code: str,
    language: Language,
) -> list[CleanCoreHint]:
    """Run a single clean-core rule and return hints for all matches."""
    hints: list[CleanCoreHint] = []
    is_de = language == Language.DE

    try:
        compiled = re.compile(rule.pattern, rule.pattern_flags)
    except re.error:
        return hints

    # Only keep first match per rule to avoid flooding
    match = compiled.search(code)
    if match is None:
        return hints

    matched_text = match.group().strip()
    # Truncate long matches for readability
    if len(matched_text) > 80:
        matched_text = matched_text[:77] + "..."

    template = rule.finding_template_de if is_de else rule.finding_template
    finding_text = template.replace("{match}", matched_text)

    hints.append(
        CleanCoreHint(
            finding=finding_text,
            released_api_alternative=rule.released_api_alternative,
            severity=Severity(rule.severity),
        )
    )

    return hints


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_clean_core(
    code: str,
    artifact_type: ArtifactType,
    language: Language,
) -> list[CleanCoreHint]:
    """Run all clean-core rules against *code* and return sorted hints.

    Parameters
    ----------
    code:
        The ABAP source code to analyse.
    artifact_type:
        The detected or user-provided artifact type.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[CleanCoreHint]
        Clean-core compliance hints sorted by severity (CRITICAL first).
    """
    if not code or not code.strip():
        return []

    # Clean-core checks are primarily for ABAP artifacts
    if artifact_type.value not in _ABAP_ARTIFACT_TYPES:
        return []

    all_hints: list[CleanCoreHint] = []
    seen_rule_ids: set[str] = set()

    for rule in CLEAN_CORE_RULES:
        if rule.rule_id in seen_rule_ids:
            continue

        hints = _run_clean_core_rule(rule, code, language)
        if hints:
            all_hints.extend(hints)
            seen_rule_ids.add(rule.rule_id)

    # Sort by severity (CRITICAL first)
    all_hints.sort(key=lambda h: _SEVERITY_ORDER.get(h.severity.value, 99))

    return all_hints
