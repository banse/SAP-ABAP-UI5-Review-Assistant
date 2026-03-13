"""Template-based output formatters for the SAP ABAP/UI5 Review Assistant.

Provides Markdown, ticket comment, and clipboard export formats
for review results.
"""

from __future__ import annotations

from typing import Any


def _resolution_label(finding_index: int, resolutions: list[dict]) -> str:
    """Build a resolution label string for a finding, e.g. '[ACCEPTED]' or '[DEFERRED by John: reason]'."""
    for r in resolutions:
        if r.get("finding_index") == finding_index and r.get("status", "OPEN") != "OPEN":
            status = r["status"]
            parts = [status]
            if r.get("reviewer_name"):
                parts.append(f"by {r['reviewer_name']}")
            if r.get("comment"):
                parts.append(r["comment"])
            return "[" + " ".join(parts) + "] " if len(parts) == 1 else "[" + parts[0] + " " + ": ".join(parts[1:]) + "] "
    return ""


def _completion_summary(resolutions: list[dict], total_findings: int, is_de: bool) -> list[str]:
    """Generate a completion summary block."""
    if not resolutions and total_findings == 0:
        return []

    lines: list[str] = []
    by_status: dict[str, int] = {}
    resolved = 0
    for r in resolutions:
        st = r.get("status", "OPEN")
        by_status[st] = by_status.get(st, 0) + 1
        if st != "OPEN":
            resolved += 1

    pct = (resolved / total_findings * 100.0) if total_findings > 0 else 0.0
    lines.append("## " + ("Abschluss-Status" if is_de else "Completion Status"))
    lines.append("")
    lines.append(
        f"{'Fortschritt' if is_de else 'Progress'}: {resolved}/{total_findings} ({pct:.0f}%)"
    )

    if by_status:
        status_parts = [f"{k}: {v}" for k, v in sorted(by_status.items())]
        lines.append(" | ".join(status_parts))
    lines.append("")
    return lines


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
    resolutions = response.get("resolutions") or []
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
            res_label = _resolution_label(i - 1, resolutions)
            title = (res_label + (f.get("title") or "")).replace("|", "\\|")
            rec = (f.get("recommendation") or "").replace("|", "\\|")
            if len(rec) > 120:
                rec = rec[:117] + "..."
            lines.append(f"| {i} | {sev} | {title} | {rec} |")
        lines.append("")

        # Detailed findings
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            res_label = _resolution_label(i - 1, resolutions)
            lines.append(f"### {i}. [{sev}] {res_label}{title}")
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

    # Completion summary (when resolutions are present)
    if resolutions:
        total = len(findings)
        lines.extend(_completion_summary(resolutions, total, is_de))

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
    resolutions = response.get("resolutions") or []
    if findings:
        lines.append(("Befunde:" if is_de else "Findings:"))
        for idx, f in enumerate(findings[:5]):
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            res_label = _resolution_label(idx, resolutions)
            rec = f.get("recommendation", "")
            if len(rec) > 80:
                rec = rec[:77] + "..."
            lines.append(f"- [{sev}] {res_label}{title}")
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

    # Completion summary
    if resolutions:
        total = len(findings)
        lines.extend(_completion_summary(resolutions, total, is_de))

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
    resolutions = response.get("resolutions") or []
    if findings:
        lines.append(("Befunde:" if is_de else "Findings:"))
        for idx, f in enumerate(findings):
            sev = f.get("severity", "UNCLEAR")
            title = f.get("title", "")
            res_label = _resolution_label(idx, resolutions)
            lines.append(f"  [{sev}] {res_label}{title}")
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

    # Completion summary
    if resolutions:
        total = len(findings)
        lines.extend(_completion_summary(resolutions, total, is_de))

    return "\n".join(lines)
