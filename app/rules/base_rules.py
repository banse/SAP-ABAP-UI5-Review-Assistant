"""Base rule framework for the SAP ABAP/UI5 Review Assistant.

Provides ``ReviewRule`` (frozen dataclass) for defining review rules and
``RuleMatch`` for capturing regex matches against source code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReviewRule:
    """A single, immutable review rule that can be matched against source code."""

    rule_id: str  # e.g. "ABAP-READ-001"
    name: str
    name_de: str
    description: str
    description_de: str
    artifact_types: tuple[str, ...]  # ArtifactType values this rule applies to
    default_severity: str  # Severity value
    pattern: str  # regex pattern to detect the issue
    pattern_flags: int = re.IGNORECASE  # regex flags
    check_fn_name: str | None = None  # name of custom check function (complex rules)
    recommendation: str = ""
    recommendation_de: str = ""
    category: str = ""  # e.g. "readability", "error_handling", "performance"

    def compile_pattern(self) -> re.Pattern[str]:
        """Return a compiled regex for this rule's pattern."""
        return re.compile(self.pattern, self.pattern_flags)


@dataclass
class RuleMatch:
    """A match produced when a ``ReviewRule`` fires against source code."""

    rule: ReviewRule
    matched_text: str
    line_number: int | None = None
    context: str = ""
