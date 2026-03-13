"""Review type detection engine.

Analyses submitted code or text to determine the appropriate ``ReviewType``.
"""

from __future__ import annotations

import re

from app.models.enums import ReviewType


# ---------------------------------------------------------------------------
# Detection heuristics
# ---------------------------------------------------------------------------

_DIFF_MARKERS = (r"^\+\+\+\s", r"^---\s", r"^@@\s")

_CODE_INDICATORS = (
    # ABAP
    r"\bSELECT\b.*\bFROM\b",
    r"\bCLASS\s+\w+\s+(?:DEFINITION|IMPLEMENTATION)\b",
    r"\bMETHOD\s+\w+\.",
    r"\bENDMETHOD\.",
    r"\bREPORT\s+\w+",
    r"\bFUNCTION\s+\w+",
    r"\bDATA\s+\w+\s+TYPE\b",
    # CDS
    r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    r"as\s+(?:select|projection)\s+(?:from|on)\b",
    r"@AbapCatalog\b",
    r"@AccessControl\b",
    # UI5
    r"sap\.ui\.define\s*\(",
    r"Controller\.extend\s*\(",
    r"<mvc:View\b",
    r"<core:FragmentDefinition\b",
    r"sap\.ui\.getCore\s*\(",
    # RAP behavior
    r"define\s+behavior\s+for\b",
    r"managed\s+implementation\s+in\s+class\b",
    r"define\s+service\b",
    r"bind\s+service\b",
)

_DESIGN_KEYWORDS = (
    r"\bsolution\b", r"\bapproach\b", r"\barchitecture\b",
    r"\bdesign\b", r"\bproposal\b", r"\bevaluat(?:e|ion)\b",
    r"\bstrategy\b", r"\bconcept\b",
)

_TICKET_PATTERN = re.compile(
    r"(?:JIRA|INC|CHG|CR|SNOW|REQ|TASK)[-\s]?\d{3,}",
    re.IGNORECASE,
)


def _has_diff_markers(text: str) -> bool:
    for pattern in _DIFF_MARKERS:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False


def _has_code_patterns(text: str) -> bool:
    for pattern in _CODE_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _is_design_text(text: str) -> bool:
    """Check if the text looks like solution/design prose without code."""
    design_hits = sum(
        1 for pat in _DESIGN_KEYWORDS if re.search(pat, text, re.IGNORECASE)
    )
    return design_hits >= 2 and not _has_code_patterns(text)


def _is_ticket_reference(text: str) -> bool:
    """Check if the text is short and contains a ticket reference."""
    stripped = text.strip()
    has_ticket = bool(_TICKET_PATTERN.search(stripped))
    is_short = len(stripped.split()) < 60
    return has_ticket and is_short and not _has_code_patterns(stripped)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_review_type(
    code: str,
    provided_type: ReviewType | None = None,
) -> ReviewType:
    """Detect the review type from the submitted code / text.

    If *provided_type* is given and is not ``None``, it is returned directly
    (the caller has already decided).  Otherwise heuristics are applied.
    """
    if provided_type is not None:
        return provided_type

    if not code or not code.strip():
        return ReviewType.SNIPPET_REVIEW

    if _has_diff_markers(code):
        return ReviewType.DIFF_REVIEW

    if _is_design_text(code):
        return ReviewType.SOLUTION_DESIGN_REVIEW

    if _is_ticket_reference(code):
        return ReviewType.TICKET_BASED_PRE_REVIEW

    # Default: if it contains code or we cannot tell, treat as snippet
    return ReviewType.SNIPPET_REVIEW
