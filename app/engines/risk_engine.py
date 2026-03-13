"""Risk assessment engine for the SAP ABAP/UI5 Review Assistant.

Aggregates findings, test gaps, and clean-core hints into per-dimension
``RiskNote`` objects with computed risk levels and mitigation suggestions.
"""

from __future__ import annotations

from app.models.enums import Language, RiskCategory, RiskLevel, Severity
from app.models.schemas import CleanCoreHint, Finding, RiskNote, TestGap
from app.rules.risk_rules import RISK_DIMENSION_CONFIGS, RiskDimensionConfig

# ---------------------------------------------------------------------------
# Severity ordering (for risk level computation)
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {
    Severity.CRITICAL.value: 0,
    Severity.IMPORTANT.value: 1,
    Severity.OPTIONAL.value: 2,
    Severity.UNCLEAR.value: 3,
}

_RISK_LEVEL_ORDER: dict[str, int] = {
    RiskLevel.CRITICAL.value: 0,
    RiskLevel.HIGH.value: 1,
    RiskLevel.MEDIUM.value: 2,
    RiskLevel.LOW.value: 3,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _count_findings_by_severity(
    findings: list[Finding],
    contributing_categories: tuple[str, ...],
) -> dict[str, int]:
    """Count findings by severity for the given rule categories.

    The finding's ``impact`` field contains ``Category: <category>`` as set
    by the findings engine.
    """
    counts: dict[str, int] = {
        Severity.CRITICAL.value: 0,
        Severity.IMPORTANT.value: 0,
        Severity.OPTIONAL.value: 0,
        Severity.UNCLEAR.value: 0,
    }

    for finding in findings:
        # Extract category from impact field (format: "Category: <cat>")
        category = ""
        if finding.impact and finding.impact.startswith("Category: "):
            category = finding.impact[len("Category: "):].strip().lower()

        if category in [c.lower() for c in contributing_categories]:
            counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1

    return counts


def _compute_risk_level(
    critical_count: int,
    important_count: int,
    critical_threshold: int,
    important_threshold: int,
) -> RiskLevel:
    """Compute the risk level based on finding counts and thresholds."""
    if critical_count >= critical_threshold:
        if critical_count >= critical_threshold * 2:
            return RiskLevel.CRITICAL
        return RiskLevel.HIGH
    if important_count >= important_threshold:
        return RiskLevel.MEDIUM
    if critical_count > 0 or important_count > 0:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _risk_level_to_severity(risk_level: RiskLevel) -> Severity:
    """Map a risk level to a Severity for the RiskNote schema."""
    mapping = {
        RiskLevel.CRITICAL: Severity.CRITICAL,
        RiskLevel.HIGH: Severity.IMPORTANT,
        RiskLevel.MEDIUM: Severity.OPTIONAL,
        RiskLevel.LOW: Severity.UNCLEAR,
    }
    return mapping.get(risk_level, Severity.UNCLEAR)


def _build_description(
    config: RiskDimensionConfig,
    risk_level: RiskLevel,
    critical_count: int,
    important_count: int,
    language: Language,
) -> str:
    """Build a human-readable risk description."""
    is_de = language == Language.DE

    if risk_level == RiskLevel.LOW:
        if is_de:
            return f"{config.name_de}: Kein signifikantes Risiko erkannt."
        return f"{config.name}: No significant risk detected."

    parts: list[str] = []
    if critical_count > 0:
        if is_de:
            parts.append(f"{critical_count} kritische(s) Finding(s)")
        else:
            parts.append(f"{critical_count} critical finding(s)")
    if important_count > 0:
        if is_de:
            parts.append(f"{important_count} wichtige(s) Finding(s)")
        else:
            parts.append(f"{important_count} important finding(s)")

    summary = ", ".join(parts)

    if is_de:
        return f"{config.name_de}: {summary} erkannt. {config.description_de}"
    return f"{config.name}: {summary} detected. {config.description}"


def _build_mitigation(
    config: RiskDimensionConfig,
    risk_level: RiskLevel,
    language: Language,
) -> str:
    """Build a mitigation suggestion based on risk level and dimension."""
    is_de = language == Language.DE

    category = config.category

    if risk_level == RiskLevel.LOW:
        if is_de:
            return "Kein unmittelbarer Handlungsbedarf."
        return "No immediate action required."

    mitigations: dict[str, dict[str, str]] = {
        "FUNCTIONAL": {
            "EN": (
                "Review and fix error handling, security, and performance findings. "
                "Prioritize CRITICAL findings before merge."
            ),
            "DE": (
                "Fehlerbehandlungs-, Sicherheits- und Performance-Findings ueberpruefen "
                "und beheben. CRITICAL-Findings vor dem Merge priorisieren."
            ),
        },
        "MAINTAINABILITY": {
            "EN": (
                "Improve code structure, reduce complexity, and address readability "
                "findings. Consider refactoring long methods and deep nesting."
            ),
            "DE": (
                "Codestruktur verbessern, Komplexitaet reduzieren und Lesbarkeits-"
                "Findings adressieren. Lange Methoden und tiefe Verschachtelungen refactoren."
            ),
        },
        "TESTABILITY": {
            "EN": (
                "Close identified test gaps. Add unit tests for critical business "
                "logic and integration tests for key workflows."
            ),
            "DE": (
                "Identifizierte Testluecken schliessen. Unit-Tests fuer kritische "
                "Geschaeftslogik und Integrationstests fuer zentrale Workflows ergaenzen."
            ),
        },
        "UPGRADE_CLEAN_CORE": {
            "EN": (
                "Replace non-released APIs and modification patterns with released "
                "alternatives. Migrate to ABAP Cloud-compatible patterns."
            ),
            "DE": (
                "Nicht freigegebene APIs und Modifikationsmuster durch freigegebene "
                "Alternativen ersetzen. Auf ABAP-Cloud-kompatible Muster migrieren."
            ),
        },
    }

    lang_key = "DE" if is_de else "EN"
    return mitigations.get(category, {}).get(lang_key, "Address identified findings.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_risks(
    findings: list[Finding],
    test_gaps: list[TestGap],
    clean_core_hints: list[CleanCoreHint],
    language: Language,
) -> list[RiskNote]:
    """Assess risks across all dimensions and return sorted ``RiskNote`` list.

    Parameters
    ----------
    findings:
        Findings produced by the findings engine.
    test_gaps:
        Test gaps identified during review.
    clean_core_hints:
        Clean-core compliance hints.
    language:
        Output language (EN or DE).

    Returns
    -------
    list[RiskNote]
        Risk notes sorted by severity (CRITICAL first).
    """
    risk_notes: list[RiskNote] = []

    for config in RISK_DIMENSION_CONFIGS:
        if config.category == "TESTABILITY":
            # Testability is driven by test gap count, not findings
            critical_count = sum(
                1 for tg in test_gaps if tg.priority == Severity.CRITICAL
            )
            important_count = sum(
                1 for tg in test_gaps if tg.priority == Severity.IMPORTANT
            )
            total_gaps = len(test_gaps)
            # Use total gap count as a proxy — critical gaps map 1:1,
            # remaining gaps count as important
            if critical_count == 0 and important_count == 0:
                # Count all gaps as important-level for threshold purposes
                important_count = total_gaps

            risk_level = _compute_risk_level(
                critical_count=critical_count,
                important_count=important_count,
                critical_threshold=config.critical_threshold,
                important_threshold=config.important_threshold,
            )

        elif config.category == "UPGRADE_CLEAN_CORE":
            # Clean-core risk is driven by clean-core hints
            critical_count = sum(
                1 for h in clean_core_hints if h.severity == Severity.CRITICAL
            )
            important_count = sum(
                1 for h in clean_core_hints if h.severity == Severity.IMPORTANT
            )

            risk_level = _compute_risk_level(
                critical_count=critical_count,
                important_count=important_count,
                critical_threshold=config.critical_threshold,
                important_threshold=config.important_threshold,
            )

        else:
            # Standard finding-based risk dimensions
            counts = _count_findings_by_severity(
                findings, config.contributing_rule_categories
            )
            critical_count = counts[Severity.CRITICAL.value]
            important_count = counts[Severity.IMPORTANT.value]

            risk_level = _compute_risk_level(
                critical_count=critical_count,
                important_count=important_count,
                critical_threshold=config.critical_threshold,
                important_threshold=config.important_threshold,
            )

        description = _build_description(
            config, risk_level, critical_count, important_count, language
        )
        mitigation = _build_mitigation(config, risk_level, language)

        risk_notes.append(
            RiskNote(
                category=RiskCategory(config.category),
                description=description,
                severity=_risk_level_to_severity(risk_level),
                mitigation=mitigation,
            )
        )

    # Sort by severity (CRITICAL first)
    risk_notes.sort(key=lambda rn: _SEVERITY_ORDER.get(rn.severity.value, 99))

    return risk_notes
