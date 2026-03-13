"""Template-based output formatters for the SAP ABAP/UI5 Review Assistant.

Provides Markdown, ticket comment, and clipboard export formats
for review results.
"""

from __future__ import annotations

from typing import Any


def format_as_markdown(response: dict, language: str = "EN") -> str:
    """Generate a full structured Markdown review document.

    Parameters
    ----------
    response:
        The review response as a plain dict (from model_dump or JSON).
    language:
        ``"DE"`` or ``"EN"`` for bilingual output.

    Returns
    -------
    str
        A complete Markdown review report.
    """
    is_de = language.upper() == "DE"
    lines: list[str] = []

    # Title
    lines.append("# " + ("Review-Bericht" if is_de else "Review Report"))
    lines.append("")

    # Overall Assessment
    assessment = response.get("overall_assessment") or {}
    if assessment:
        lines.append("## " + ("Gesamtbewertung" if is_de else "Overall Assessment"))
        lines.append("")

        go_no_go = assessment.get("go_no_go", "GO")
        verdict_map = {
            "GO": "GO",
            "CONDITIONAL_GO": "CONDITIONAL GO",
            "NO_GO": "NO-GO",
        }
        verdict = verdict_map.get(go_no_go, go_no_go)
        confidence = assessment.get("confidence", "")

        lines.append(f"**{verdict}**" + (f" ({('Konfidenz' if is_de else 'Confidence')}: {confidence})" if confidence else ""))
        lines.append("")

        summary = assessment.get("summary", "")
        if summary:
            lines.append(summary)
            lines.append("")

        counts = []
        critical = assessment.get("critical_count", 0)
        important = assessment.get("important_count", 0)
        optional = assessment.get("optional_count", 0)
        if critical:
            counts.append(f"{critical} Critical")
        if important:
            counts.append(f"{important} Important")
        if optional:
            counts.append(f"{optional} Optional")
        if counts:
            lines.append(" | ".join(counts))
            lines.append("")

    # Review Summary
    review_summary = response.get("review_summary", "")
    if review_summary:
        lines.append("## " + ("Zusammenfassung" if is_de else "Summary"))
        lines.append("")
        lines.append(review_summary)
        lines.append("")

    # Findings
    findings = response.get("findings") or []
    if findings:
        lines.append("## " + ("Befunde" if is_de else "Findings"))
        lines.append("")

        if is_de:
            lines.append("| # | Schweregrad | Titel | Empfehlung |")
        else:
            lines.append("| # | Severity | Title | Recommendation |")
        lines.append("|---|-----------|-------|--------------|")

        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "UNCLEAR")
            title = (f.get("title") or "").replace("|", "\\|")
            rec = (f.get("recommendation") or "").replace("|", "\\|")
            if len(rec) > 120:
                rec = rec[:117] + "..."
            lines.append(f"| {i} | {sev} | {title} | {rec} |")
        lines.append("")

        # Detailed findings
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            lines.append(f"### {i}. [{sev}] {title}")
            lines.append("")
            if f.get("observation"):
                lines.append(f"**{('Beobachtung' if is_de else 'Observation')}:** {f['observation']}")
                lines.append("")
            if f.get("reasoning"):
                lines.append(f"**{('Begruendung' if is_de else 'Reasoning')}:** {f['reasoning']}")
                lines.append("")
            if f.get("impact"):
                lines.append(f"**{('Auswirkung' if is_de else 'Impact')}:** {f['impact']}")
                lines.append("")
            if f.get("recommendation"):
                lines.append(f"**{('Empfehlung' if is_de else 'Recommendation')}:** {f['recommendation']}")
                lines.append("")
            refs = []
            if f.get("rule_id"):
                refs.append(f"Rule: {f['rule_id']}")
            if f.get("line_reference"):
                refs.append(f"Line: {f['line_reference']}")
            if refs:
                lines.append("_" + " | ".join(refs) + "_")
                lines.append("")

    # Test Gaps
    test_gaps = response.get("test_gaps") or []
    if test_gaps:
        lines.append("## " + ("Testluecken" if is_de else "Test Gaps"))
        lines.append("")
        for gap in test_gaps:
            prio = gap.get("priority", "OPTIONAL")
            cat = gap.get("category", "")
            desc = gap.get("description", "")
            lines.append(f"- **[{prio}]** {cat}: {desc}")
            if gap.get("suggested_test"):
                lines.append(f"  - {gap['suggested_test']}")
        lines.append("")

    # Risk Dashboard
    risk_notes = response.get("risk_notes") or []
    if risk_notes:
        lines.append("## " + ("Risiko-Dashboard" if is_de else "Risk Dashboard"))
        lines.append("")
        for note in risk_notes:
            sev = note.get("severity", "LOW")
            cat = note.get("category", "")
            desc = note.get("description", "")
            lines.append(f"- **{cat}** [{sev}]: {desc}")
            if note.get("mitigation"):
                lines.append(f"  - {('Massnahme' if is_de else 'Mitigation')}: {note['mitigation']}")
        lines.append("")

    # Clean-Core Hints
    cc_hints = response.get("clean_core_hints") or []
    if cc_hints:
        lines.append("## " + ("Clean-Core-Hinweise" if is_de else "Clean-Core Hints"))
        lines.append("")
        for hint in cc_hints:
            sev = hint.get("severity", "OPTIONAL")
            finding = hint.get("finding", "")
            lines.append(f"- **[{sev}]** {finding}")
            if hint.get("released_api_alternative"):
                lines.append(f"  - Alternative: {hint['released_api_alternative']}")
        lines.append("")

    # Refactoring Hints
    refactoring = response.get("refactoring_hints") or []
    if refactoring:
        lines.append("## " + ("Refactoring-Hinweise" if is_de else "Refactoring Hints"))
        lines.append("")
        for hint in refactoring:
            effort = f" ({('Aufwand' if is_de else 'Effort')}: {hint['effort_hint']})" if hint.get("effort_hint") else ""
            lines.append(f"- **{hint.get('category', '')}**: {hint.get('title', '')}{effort}")
            if hint.get("description"):
                lines.append(f"  - {hint['description']}")
            if hint.get("benefit"):
                lines.append(f"  - {('Nutzen' if is_de else 'Benefit')}: {hint['benefit']}")
        lines.append("")

    # Recommended Actions
    actions = response.get("recommended_actions") or []
    if actions:
        lines.append("## " + ("Empfohlene Massnahmen" if is_de else "Recommended Actions"))
        lines.append("")
        for action in actions:
            order = action.get("order", "")
            title = action.get("title", "")
            effort = f" [{action['effort_hint']}]" if action.get("effort_hint") else ""
            lines.append(f"{order}. **{title}**{effort}")
            if action.get("description"):
                lines.append(f"   {action['description']}")
        lines.append("")

    # Open Questions
    missing = response.get("missing_information") or []
    if missing:
        lines.append("## " + ("Offene Fragen" if is_de else "Open Questions"))
        lines.append("")
        for info in missing:
            lines.append(f"- {info.get('question', '')}")
            if info.get("why_it_matters"):
                lines.append(f"  - {info['why_it_matters']}")
            if info.get("default_assumption"):
                label = "Standardannahme" if is_de else "Default assumption"
                lines.append(f"  - {label}: {info['default_assumption']}")
        lines.append("")

    return "\n".join(lines)


def format_as_ticket_comment(response: dict, language: str = "EN") -> str:
    """Generate a condensed format suitable for JIRA/ServiceNow ticket comments.

    Includes assessment verdict, top findings (title + severity + recommendation),
    and action items. No detailed reasoning. Target: under 2000 characters.

    Parameters
    ----------
    response:
        The review response as a plain dict.
    language:
        ``"DE"`` or ``"EN"``.

    Returns
    -------
    str
        A concise ticket-friendly review comment.
    """
    is_de = language.upper() == "DE"
    lines: list[str] = []

    # Assessment
    assessment = response.get("overall_assessment") or {}
    go_no_go = assessment.get("go_no_go", "GO")
    verdict_map = {"GO": "GO", "CONDITIONAL_GO": "CONDITIONAL GO", "NO_GO": "NO-GO"}
    verdict = verdict_map.get(go_no_go, go_no_go)

    lines.append(f"[{verdict}] " + ("Code-Review Ergebnis" if is_de else "Code Review Result"))
    lines.append("")

    summary = assessment.get("summary", "")
    if summary:
        lines.append(summary)
        lines.append("")

    # Top findings (max 5)
    findings = response.get("findings") or []
    if findings:
        lines.append(("Befunde:" if is_de else "Findings:"))
        for f in findings[:5]:
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            rec = f.get("recommendation", "")
            if len(rec) > 80:
                rec = rec[:77] + "..."
            lines.append(f"- [{sev}] {title}")
            if rec:
                lines.append(f"  -> {rec}")
        if len(findings) > 5:
            remaining = len(findings) - 5
            lines.append(f"  (+{remaining} " + ("weitere" if is_de else "more") + ")")
        lines.append("")

    # Action items (max 3)
    actions = response.get("recommended_actions") or []
    if actions:
        lines.append(("Naechste Schritte:" if is_de else "Next Steps:"))
        for a in actions[:3]:
            title = a.get("title", "")
            lines.append(f"- {title}")
        lines.append("")

    return "\n".join(lines)


def format_as_clipboard(response: dict, language: str = "EN") -> str:
    """Generate a plain text summary for clipboard copy.

    One-line assessment, bullet list of findings, action items.

    Parameters
    ----------
    response:
        The review response as a plain dict.
    language:
        ``"DE"`` or ``"EN"``.

    Returns
    -------
    str
        A plain text summary suitable for clipboard.
    """
    is_de = language.upper() == "DE"
    lines: list[str] = []

    # One-line assessment
    assessment = response.get("overall_assessment") or {}
    go_no_go = assessment.get("go_no_go", "GO")
    verdict_map = {"GO": "GO", "CONDITIONAL_GO": "CONDITIONAL GO", "NO_GO": "NO-GO"}
    verdict = verdict_map.get(go_no_go, go_no_go)
    confidence = assessment.get("confidence", "")
    summary_text = assessment.get("summary", "")

    assessment_line = f"{verdict}"
    if confidence:
        assessment_line += f" ({confidence})"
    if summary_text:
        assessment_line += f" - {summary_text}"
    lines.append(assessment_line)
    lines.append("")

    # Findings as bullets
    findings = response.get("findings") or []
    if findings:
        lines.append(("Befunde:" if is_de else "Findings:"))
        for f in findings:
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            lines.append(f"  [{sev}] {title}")
        lines.append("")

    # Action items
    actions = response.get("recommended_actions") or []
    if actions:
        lines.append(("Massnahmen:" if is_de else "Actions:"))
        for a in actions:
            order = a.get("order", "")
            title = a.get("title", "")
            lines.append(f"  {order}. {title}")
        lines.append("")

    return "\n".join(lines)
