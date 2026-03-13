"""Quality gate engine for CI/CD integration.

Evaluates review results against configurable thresholds to produce
a pass/fail decision suitable for automated pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QualityGateConfig:
    """Configuration for quality gate thresholds.

    Attributes
    ----------
    max_critical:
        Maximum allowed CRITICAL findings. 0 = fail on any. -1 = unlimited.
    max_important:
        Maximum allowed IMPORTANT findings. -1 = unlimited.
    max_total:
        Maximum allowed total findings. -1 = unlimited.
    require_go:
        If True, fail unless assessment is GO.
    require_clean_core:
        If True, fail if any clean-core hints are present.
    custom_blocked_rules:
        Specific rule_ids that cause immediate failure.
    """

    max_critical: int = 0
    max_important: int = -1
    max_total: int = -1
    require_go: bool = False
    require_clean_core: bool = False
    custom_blocked_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a plain dict."""
        return {
            "max_critical": self.max_critical,
            "max_important": self.max_important,
            "max_total": self.max_total,
            "require_go": self.require_go,
            "require_clean_core": self.require_clean_core,
            "custom_blocked_rules": list(self.custom_blocked_rules),
        }


@dataclass
class QualityGateResult:
    """Result of a quality gate evaluation.

    Attributes
    ----------
    passed:
        Whether the quality gate passed.
    reason:
        Human-readable explanation of why it passed or failed.
    violations:
        List of specific violations that caused failure.
    config:
        The config that was used for evaluation.
    """

    passed: bool
    reason: str
    violations: list[str]
    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a plain dict."""
        return {
            "passed": self.passed,
            "reason": self.reason,
            "violations": list(self.violations),
            "config": dict(self.config),
        }


def evaluate_quality_gate(
    response: dict[str, Any],
    config: QualityGateConfig | None = None,
) -> QualityGateResult:
    """Evaluate review results against quality gate thresholds.

    Parameters
    ----------
    response:
        The review response as a plain dict (from model_dump or JSON).
    config:
        Quality gate configuration. If None, uses default config
        which fails on any CRITICAL finding (max_critical=0).

    Returns
    -------
    QualityGateResult
        The pass/fail result with details.
    """
    if config is None:
        config = QualityGateConfig()

    violations: list[str] = []
    findings = response.get("findings") or []

    # Count findings by severity
    severity_counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "UNCLEAR")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    critical_count = severity_counts.get("CRITICAL", 0)
    important_count = severity_counts.get("IMPORTANT", 0)
    total_count = len(findings)

    # Check max_critical threshold
    if config.max_critical >= 0 and critical_count > config.max_critical:
        violations.append(
            f"CRITICAL findings: {critical_count} (max allowed: {config.max_critical})"
        )

    # Check max_important threshold
    if config.max_important >= 0 and important_count > config.max_important:
        violations.append(
            f"IMPORTANT findings: {important_count} (max allowed: {config.max_important})"
        )

    # Check max_total threshold
    if config.max_total >= 0 and total_count > config.max_total:
        violations.append(
            f"Total findings: {total_count} (max allowed: {config.max_total})"
        )

    # Check require_go
    if config.require_go:
        assessment = response.get("overall_assessment") or {}
        go_no_go = assessment.get("go_no_go", "GO")
        if go_no_go != "GO":
            violations.append(
                f"Assessment is {go_no_go}, but GO is required"
            )

    # Check require_clean_core
    if config.require_clean_core:
        clean_core_hints = response.get("clean_core_hints") or []
        if clean_core_hints:
            violations.append(
                f"Clean-core hints found: {len(clean_core_hints)} "
                f"(clean-core compliance required)"
            )

    # Check custom_blocked_rules
    if config.custom_blocked_rules:
        blocked_found: list[str] = []
        for f in findings:
            rule_id = f.get("rule_id")
            if rule_id and rule_id in config.custom_blocked_rules:
                blocked_found.append(rule_id)
        if blocked_found:
            unique_blocked = sorted(set(blocked_found))
            violations.append(
                f"Blocked rules found: {', '.join(unique_blocked)}"
            )

    passed = len(violations) == 0

    if passed:
        reason = "All quality gate checks passed"
    else:
        reason = f"Quality gate failed: {len(violations)} violation(s)"

    return QualityGateResult(
        passed=passed,
        reason=reason,
        violations=violations,
        config=config.to_dict(),
    )
