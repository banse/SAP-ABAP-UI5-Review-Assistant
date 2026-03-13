"""SARIF v2.1.0 formatter for the SAP ABAP/UI5 Review Assistant.

Converts a ReviewResponse dict to SARIF (Static Analysis Results
Interchange Format) v2.1.0 for integration with GitHub Code Scanning,
Azure DevOps, and other SARIF-compatible tools.

No external dependencies -- produces a pure dict structure.
"""

from __future__ import annotations

from typing import Any

_SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
    "master/Schemata/sarif-schema-2.1.0.json"
)
_SARIF_VERSION = "2.1.0"

# Mapping from internal severity to SARIF level.
# SARIF levels: "error", "warning", "note", "none"
_SEVERITY_TO_LEVEL: dict[str, str] = {
    "CRITICAL": "error",
    "IMPORTANT": "error",
    "OPTIONAL": "warning",
    "UNCLEAR": "note",
}


def _parse_start_line(line_reference: str | None) -> int | None:
    """Extract a numeric start line from a line_reference string.

    Handles formats like ``"42"``, ``"10-15"``, ``"Line 42"``.
    Returns None if the reference cannot be parsed.
    """
    if not line_reference:
        return None

    # Strip common prefixes
    cleaned = line_reference.strip()
    for prefix in ("Line ", "line ", "L", "l"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    # Take the first number (before any dash or separator)
    number_part = ""
    for ch in cleaned:
        if ch.isdigit():
            number_part += ch
        elif number_part:
            break  # Stop at first non-digit after digits

    if number_part:
        try:
            return int(number_part)
        except ValueError:
            return None
    return None


def format_as_sarif(
    response: dict[str, Any],
    tool_name: str = "SAP ABAP/UI5 Review Assistant",
    tool_version: str = "2.0.0",
) -> dict[str, Any]:
    """Convert a ReviewResponse dict to SARIF v2.1.0 format.

    Parameters
    ----------
    response:
        The review response as a plain dict (from model_dump or JSON).
    tool_name:
        Name of the tool for the SARIF driver section.
    tool_version:
        Version string for the SARIF driver section.

    Returns
    -------
    dict
        A SARIF v2.1.0 compliant dict ready for JSON serialization.

    Notes
    -----
    Mapping rules:
    - Each Finding becomes a SARIF result.
    - severity CRITICAL/IMPORTANT -> level "error"
    - severity OPTIONAL -> level "warning"
    - severity UNCLEAR -> level "note"
    - rule_id maps to SARIF ruleId
    - line_reference maps to region.startLine
    - observation maps to message.text
    - recommendation maps to help.text in the rule definition
    """
    findings = response.get("findings") or []

    # Build rule definitions and results
    rules: list[dict[str, Any]] = []
    rule_index_map: dict[str, int] = {}
    results: list[dict[str, Any]] = []

    for finding in findings:
        rule_id = finding.get("rule_id") or _generate_rule_id(finding)
        severity = finding.get("severity", "UNCLEAR")
        level = _SEVERITY_TO_LEVEL.get(severity, "note")

        # Register rule if not seen before
        if rule_id not in rule_index_map:
            rule_index_map[rule_id] = len(rules)
            rule_def: dict[str, Any] = {
                "id": rule_id,
                "shortDescription": {
                    "text": finding.get("title", ""),
                },
                "defaultConfiguration": {
                    "level": level,
                },
            }
            # Add help text from recommendation
            recommendation = finding.get("recommendation")
            if recommendation:
                rule_def["help"] = {"text": recommendation}

            # Add full description from reasoning
            reasoning = finding.get("reasoning")
            if reasoning:
                rule_def["fullDescription"] = {"text": reasoning}

            rules.append(rule_def)

        # Build result
        result: dict[str, Any] = {
            "ruleId": rule_id,
            "ruleIndex": rule_index_map[rule_id],
            "level": level,
            "message": {
                "text": finding.get("observation", finding.get("title", "")),
            },
        }

        # Build location from line_reference and artifact_reference
        location = _build_location(finding)
        if location:
            result["locations"] = [location]

        results.append(result)

    # Assemble SARIF document
    sarif: dict[str, Any] = {
        "$schema": _SARIF_SCHEMA,
        "version": _SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "rules": rules,
                    },
                },
                "results": results,
            },
        ],
    }

    return sarif


def _generate_rule_id(finding: dict[str, Any]) -> str:
    """Generate a stable rule ID for findings without an explicit rule_id.

    Uses a simplified hash of the title to create a reproducible ID.
    """
    title = finding.get("title", "unknown")
    # Simple hash-based ID
    hash_val = 0
    for ch in title:
        hash_val = (hash_val * 31 + ord(ch)) & 0xFFFFFFFF
    return f"REVIEW-{hash_val:08x}"


def _build_location(finding: dict[str, Any]) -> dict[str, Any] | None:
    """Build a SARIF location object from finding references."""
    line = _parse_start_line(finding.get("line_reference"))
    artifact_ref = finding.get("artifact_reference")

    if line is None and not artifact_ref:
        return None

    physical_location: dict[str, Any] = {}

    if artifact_ref:
        physical_location["artifactLocation"] = {
            "uri": artifact_ref,
        }

    if line is not None:
        physical_location["region"] = {
            "startLine": line,
        }

    return {"physicalLocation": physical_location}
