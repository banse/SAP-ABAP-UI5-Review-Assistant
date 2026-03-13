"""Overall assessment engine for the SAP ABAP/UI5 Review Assistant.

Aggregates findings, test gaps, and risk notes into a go/no-go verdict
with confidence and bilingual summary.
"""

from __future__ import annotations

from app.models.enums import (
    Confidence,
    GoNoGo,
    Language,
    RiskLevel,
    Severity,
)
from app.models.schemas import (
    Finding,
    OverallAssessment,
    RiskNote,
    TestGap,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_RISK_LEVEL_MAP: dict[Severity, str] = {
    Severity.CRITICAL: RiskLevel.CRITICAL.value,
    Severity.IMPORTANT: RiskLevel.HIGH.value,
    Severity.OPTIONAL: RiskLevel.MEDIUM.value,
    Severity.UNCLEAR: RiskLevel.LOW.value,
}


def _count_by_severity(findings: list[Finding]) -> dict[str, int]:
    """Count findings by severity level."""
    counts = {
        Severity.CRITICAL.value: 0,
        Severity.IMPORTANT.value: 0,
        Severity.OPTIONAL.value: 0,
        Severity.UNCLEAR.value: 0,
    }
    for f in findings:
        counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
    return counts


def _has_critical_risk_dimension(risk_notes: list[RiskNote]) -> bool:
    """Check if any risk dimension is at CRITICAL level."""
    return any(rn.severity == Severity.CRITICAL for rn in risk_notes)


def _determine_go_no_go(
    critical_count: int,
    important_count: int,
    has_critical_risk: bool,
) -> GoNoGo:
    """Determine the go/no-go verdict."""
    # NO_GO: any CRITICAL finding AND risk dimension at CRITICAL level
    if critical_count > 0 and has_critical_risk:
        return GoNoGo.NO_GO

    # CONDITIONAL_GO: any CRITICAL findings OR more than 3 IMPORTANT findings
    if critical_count > 0 or important_count > 3:
        return GoNoGo.CONDITIONAL_GO

    # GO: no CRITICAL findings AND 3 or fewer IMPORTANT findings
    return GoNoGo.GO


def _determine_confidence(unclear_count: int, total_count: int) -> Confidence:
    """Determine confidence based on UNCLEAR finding ratio."""
    if total_count == 0:
        return Confidence.HIGH

    ratio = unclear_count / total_count

    if ratio > 0.3:
        return Confidence.LOW
    if ratio > 0.1:
        return Confidence.MEDIUM
    return Confidence.HIGH


def _build_summary(
    go_no_go: GoNoGo,
    critical_count: int,
    important_count: int,
    optional_count: int,
    language: Language,
) -> str:
    """Build a bilingual summary of the assessment."""
    is_de = language == Language.DE

    if go_no_go == GoNoGo.GO:
        if is_de:
            summary = (
                "Der Code kann freigegeben werden. "
                f"{important_count} wichtige(s) und {optional_count} optionale(s) "
                "Finding(s) wurden identifiziert, aber keine kritischen Probleme."
            )
        else:
            summary = (
                "The code can be released. "
                f"{important_count} important and {optional_count} optional "
                "finding(s) were identified, but no critical issues."
            )
    elif go_no_go == GoNoGo.CONDITIONAL_GO:
        if is_de:
            summary = (
                "Der Code kann unter Bedingungen freigegeben werden. "
                f"{critical_count} kritische(s) und {important_count} wichtige(s) "
                "Finding(s) muessen vor dem Merge adressiert werden."
            )
        else:
            summary = (
                "The code can be conditionally released. "
                f"{critical_count} critical and {important_count} important "
                "finding(s) must be addressed before merge."
            )
    else:
        if is_de:
            summary = (
                "Der Code kann NICHT freigegeben werden. "
                f"{critical_count} kritische(s) Finding(s) und kritische "
                "Risikodimensionen erfordern sofortige Aufmerksamkeit."
            )
        else:
            summary = (
                "The code can NOT be released. "
                f"{critical_count} critical finding(s) and critical risk "
                "dimensions require immediate attention."
            )

    return summary


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_assessment(
    findings: list[Finding],
    test_gaps: list[TestGap],
    risk_notes: list[RiskNote],
    language: Language,
) -> OverallAssessment:
    """Generate the overall go/no-go assessment.

    Parameters
    ----------
    findings:
        Findings produced by the findings engine.
    test_gaps:
        Test gaps identified during review.
    risk_notes:
        Risk notes from the risk engine.
    language:
        Output language (EN or DE).

    Returns
    -------
    OverallAssessment
        The overall assessment with verdict, confidence, and summary.
    """
    counts = _count_by_severity(findings)
    critical_count = counts[Severity.CRITICAL.value]
    important_count = counts[Severity.IMPORTANT.value]
    optional_count = counts[Severity.OPTIONAL.value]
    unclear_count = counts[Severity.UNCLEAR.value]
    total_count = len(findings)

    has_critical_risk = _has_critical_risk_dimension(risk_notes)

    go_no_go = _determine_go_no_go(critical_count, important_count, has_critical_risk)
    confidence = _determine_confidence(unclear_count, total_count)
    summary = _build_summary(
        go_no_go, critical_count, important_count, optional_count, language
    )

    return OverallAssessment(
        go_no_go=go_no_go,
        confidence=confidence,
        summary=summary,
        critical_count=critical_count,
        important_count=important_count,
        optional_count=optional_count,
    )
