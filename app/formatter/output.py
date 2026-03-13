"""Markdown export formatter for the SAP ABAP/UI5 Review Assistant.

Converts a ``ReviewResponse`` into a well-structured Markdown document.
"""

from __future__ import annotations

from app.models.enums import Language
from app.models.schemas import ReviewResponse


def format_review_as_markdown(response: ReviewResponse) -> str:
    """Generate a structured Markdown review report.

    Parameters
    ----------
    response:
        The complete review response.

    Returns
    -------
    str
        A Markdown-formatted review report.
    """
    is_de = response.language == Language.DE
    lines: list[str] = []

    # Header
    if is_de:
        lines.append("# Review-Bericht")
    else:
        lines.append("# Review Report")
    lines.append("")

    # Summary section
    if is_de:
        lines.append("## Zusammenfassung")
    else:
        lines.append("## Summary")
    lines.append("")
    lines.append(response.review_summary)
    lines.append("")

    # Findings table
    if response.findings:
        if is_de:
            lines.append("## Findings")
        else:
            lines.append("## Findings")
        lines.append("")

        if is_de:
            lines.append("| # | Schweregrad | Titel | Empfehlung |")
        else:
            lines.append("| # | Severity | Title | Recommendation |")
        lines.append("|---|-----------|-------|--------------|")

        for i, finding in enumerate(response.findings, 1):
            sev = finding.severity.value
            title = finding.title.replace("|", "\\|")
            rec = finding.recommendation.replace("|", "\\|")
            if len(rec) > 120:
                rec = rec[:117] + "..."
            lines.append(f"| {i} | {sev} | {title} | {rec} |")
        lines.append("")

    # Test Gaps section
    if response.test_gaps:
        if is_de:
            lines.append("## Testluecken")
        else:
            lines.append("## Test Gaps")
        lines.append("")

        for gap in response.test_gaps:
            prio = gap.priority.value
            lines.append(f"- **[{prio}]** {gap.category.value}: {gap.description}")
            if gap.suggested_test:
                lines.append(f"  - {gap.suggested_test}")
        lines.append("")

    # Risk Dashboard section
    if response.risk_notes:
        if is_de:
            lines.append("## Risiko-Dashboard")
        else:
            lines.append("## Risk Dashboard")
        lines.append("")

        for note in response.risk_notes:
            sev = note.severity.value
            lines.append(f"- **{note.category.value}** [{sev}]: {note.description}")
            if note.mitigation:
                if is_de:
                    lines.append(f"  - Mitigation: {note.mitigation}")
                else:
                    lines.append(f"  - Mitigation: {note.mitigation}")
        lines.append("")

    # Clean-Core Hints
    if response.clean_core_hints:
        if is_de:
            lines.append("## Clean-Core-Hinweise")
        else:
            lines.append("## Clean-Core Hints")
        lines.append("")

        for hint in response.clean_core_hints:
            sev = hint.severity.value
            lines.append(f"- **[{sev}]** {hint.finding}")
            if hint.released_api_alternative:
                if is_de:
                    lines.append(f"  - Alternative: {hint.released_api_alternative}")
                else:
                    lines.append(f"  - Alternative: {hint.released_api_alternative}")
        lines.append("")

    # Refactoring Hints
    if response.refactoring_hints:
        if is_de:
            lines.append("## Refactoring-Hinweise")
        else:
            lines.append("## Refactoring Hints")
        lines.append("")

        for hint in response.refactoring_hints:
            effort = f" (Aufwand: {hint.effort_hint})" if hint.effort_hint else ""
            if not is_de:
                effort = f" (Effort: {hint.effort_hint})" if hint.effort_hint else ""
            lines.append(
                f"- **{hint.category.value}**: {hint.title}{effort}"
            )
            lines.append(f"  - {hint.description}")
            if is_de:
                lines.append(f"  - Nutzen: {hint.benefit}")
            else:
                lines.append(f"  - Benefit: {hint.benefit}")
        lines.append("")

    # Recommended Actions
    if response.recommended_actions:
        if is_de:
            lines.append("## Empfohlene Massnahmen")
        else:
            lines.append("## Recommended Actions")
        lines.append("")

        for action in response.recommended_actions:
            effort = f" [{action.effort_hint}]" if action.effort_hint else ""
            lines.append(f"{action.order}. **{action.title}**{effort}")
            lines.append(f"   {action.description}")
        lines.append("")

    # Overall Assessment
    if is_de:
        lines.append("## Gesamtbewertung")
    else:
        lines.append("## Overall Assessment")
    lines.append("")

    assessment = response.overall_assessment
    verdict_icon = {
        "GO": "GO",
        "CONDITIONAL_GO": "CONDITIONAL GO",
        "NO_GO": "NO-GO",
    }.get(assessment.go_no_go.value, assessment.go_no_go.value)

    lines.append(f"**{verdict_icon}** (Confidence: {assessment.confidence.value})")
    lines.append("")
    lines.append(assessment.summary)
    lines.append("")

    # Missing Information (if any)
    if response.missing_information:
        if is_de:
            lines.append("## Offene Fragen")
        else:
            lines.append("## Open Questions")
        lines.append("")

        for info in response.missing_information:
            lines.append(f"- {info.question}")
            lines.append(f"  - {info.why_it_matters}")
            if info.default_assumption:
                if is_de:
                    lines.append(f"  - Standardannahme: {info.default_assumption}")
                else:
                    lines.append(f"  - Default assumption: {info.default_assumption}")
        lines.append("")

    return "\n".join(lines)
