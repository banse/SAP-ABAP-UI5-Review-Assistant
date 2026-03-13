"""Cross-artifact consistency checker for the SAP ABAP/UI5 Review Assistant.

Runs cross-artifact rules across multiple artifact sections in a change
package and returns consolidated, deduplicated, severity-sorted findings.

Only activates when 2+ distinct artifact types are present.
"""

from __future__ import annotations

from app.engines.multi_artifact_handler import ArtifactSection
from app.models.enums import Language, Severity
from app.models.schemas import Finding
from app.rules.cross_artifact_rules import (
    CROSS_ARTIFACT_CHECK_FUNCTIONS,
    CROSS_ARTIFACT_RULES,
    CrossArtifactRule,
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


def _distinct_artifact_types(sections: list[ArtifactSection]) -> set[str]:
    """Return the set of distinct artifact type values across sections."""
    return {s.artifact_type.value for s in sections}


def _rule_is_applicable(
    rule: CrossArtifactRule,
    present_types: set[str],
) -> bool:
    """Check whether the required source AND target types are present."""
    has_source = any(t in present_types for t in rule.source_artifact_types)
    has_target = any(t in present_types for t in rule.target_artifact_types)
    return has_source and has_target


def _deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    """Remove duplicate findings based on rule_id + observation."""
    seen: set[str] = set()
    unique: list[Finding] = []
    for f in findings:
        key = f"{f.rule_id}|{f.observation}"
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_cross_artifact_consistency(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """Run cross-artifact consistency checks across multiple artifact sections.

    Only runs when 2+ different artifact types are present.
    Returns findings referencing both source and target artifacts.

    Parameters
    ----------
    sections:
        The artifact sections from the change package.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[Finding]
        Cross-artifact findings sorted by severity (CRITICAL first).
    """
    if not sections:
        return []

    # Step 1: Group by artifact type and check diversity
    present_types = _distinct_artifact_types(sections)
    if len(present_types) < 2:
        return []

    # Step 2: Run applicable cross-artifact rules
    all_findings: list[Finding] = []

    for rule in CROSS_ARTIFACT_RULES:
        if not _rule_is_applicable(rule, present_types):
            continue

        # Look up and call the check function
        check_fn = CROSS_ARTIFACT_CHECK_FUNCTIONS.get(rule.check_fn_name)
        if check_fn is None:
            continue

        try:
            findings = check_fn(sections, language)
        except Exception:
            continue

        all_findings.extend(findings)

    # Step 3: Deduplicate
    all_findings = _deduplicate_findings(all_findings)

    # Step 4: Sort by severity
    all_findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 99))

    return all_findings
