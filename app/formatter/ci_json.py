"""CI-friendly JSON formatter for the SAP ABAP/UI5 Review Assistant.

Produces a structured JSON output designed for CI/CD pipelines,
including a quality gate pass/fail decision, finding summaries,
and metadata for automated processing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.engines.quality_gate import QualityGateConfig, evaluate_quality_gate


def format_as_ci_json(
    response: dict[str, Any],
    gate_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert a ReviewResponse dict to CI-friendly JSON with quality gate.

    Parameters
    ----------
    response:
        The review response as a plain dict (from model_dump or JSON).
    gate_config:
        Optional quality gate config as a dict. Keys match
        ``QualityGateConfig`` fields. If None, uses default config
        (fail on any CRITICAL finding).

    Returns
    -------
    dict
        A CI-friendly JSON structure with quality gate result.
    """
    # Build QualityGateConfig from dict
    config = _build_gate_config(gate_config)
    gate_result = evaluate_quality_gate(response, config)

    # Count findings by severity
    findings = response.get("findings") or []
    by_severity: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "UNCLEAR")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Extract assessment info
    assessment = response.get("overall_assessment") or {}
    go_no_go = assessment.get("go_no_go", "GO")
    confidence = assessment.get("confidence", "MEDIUM")

    # Build simplified findings list
    simplified_findings = []
    for f in findings:
        simplified: dict[str, Any] = {
            "severity": f.get("severity", "UNCLEAR"),
            "title": f.get("title", ""),
            "rule_id": f.get("rule_id"),
            "line_reference": f.get("line_reference"),
            "recommendation": f.get("recommendation", ""),
        }
        simplified_findings.append(simplified)

    # Build test gaps
    test_gaps = []
    for gap in response.get("test_gaps") or []:
        test_gaps.append({
            "category": gap.get("category", ""),
            "description": gap.get("description", ""),
            "priority": gap.get("priority", "OPTIONAL"),
        })

    # Build risk notes
    risk_notes = []
    for note in response.get("risk_notes") or []:
        risk_notes.append({
            "category": note.get("category", ""),
            "description": note.get("description", ""),
            "severity": note.get("severity", "LOW"),
        })

    # Build clean core hints
    clean_core_hints = []
    for hint in response.get("clean_core_hints") or []:
        clean_core_hints.append({
            "finding": hint.get("finding", ""),
            "severity": hint.get("severity", "OPTIONAL"),
            "released_api_alternative": hint.get("released_api_alternative"),
        })

    return {
        "tool": "SAP ABAP/UI5 Review Assistant",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quality_gate": gate_result.to_dict(),
        "summary": {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "assessment": go_no_go,
            "confidence": confidence,
        },
        "findings": simplified_findings,
        "test_gaps": test_gaps,
        "risk_notes": risk_notes,
        "clean_core_hints": clean_core_hints,
    }


def _build_gate_config(
    config_dict: dict[str, Any] | None,
) -> QualityGateConfig:
    """Build a QualityGateConfig from a plain dict.

    Unknown keys are silently ignored.
    """
    if not config_dict:
        return QualityGateConfig()

    kwargs: dict[str, Any] = {}
    if "max_critical" in config_dict:
        kwargs["max_critical"] = int(config_dict["max_critical"])
    if "max_important" in config_dict:
        kwargs["max_important"] = int(config_dict["max_important"])
    if "max_total" in config_dict:
        kwargs["max_total"] = int(config_dict["max_total"])
    if "require_go" in config_dict:
        kwargs["require_go"] = bool(config_dict["require_go"])
    if "require_clean_core" in config_dict:
        kwargs["require_clean_core"] = bool(config_dict["require_clean_core"])
    if "custom_blocked_rules" in config_dict:
        kwargs["custom_blocked_rules"] = list(config_dict["custom_blocked_rules"])

    return QualityGateConfig(**kwargs)
