"""Multi-artifact input handler for the SAP ABAP/UI5 Review Assistant.

Splits change packages containing multiple artifacts into sections,
reviews each independently, and consolidates results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.engines.artifact_classifier import classify_artifact
from app.models.enums import ArtifactType


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ArtifactSection:
    """A single artifact section within a change package."""

    artifact_type: ArtifactType
    artifact_name: str
    code: str
    section_index: int


# ---------------------------------------------------------------------------
# Section header patterns for explicit separator-delimited format
# ---------------------------------------------------------------------------

# Matches separator lines: "---", "===", "------- ", etc.
_SEPARATOR_RE = re.compile(r"^[-=]{3,}\s*$")

# Matches optional headers like:
#   // CDS View: ZI_Order
#   * Class: ZCL_ORDER
#   // Behavior Definition: ZI_ORDER
#   * ABAP Report: ZREPORT
_HEADER_RE = re.compile(
    r"^(?://|\*)\s*(?:CDS\s+View|CDS\s+Projection|CDS\s+Annotation|"
    r"Class|Report|Method|Behavior\s+Definition|Behavior\s+Implementation|"
    r"Service\s+Definition|Service\s+Binding|"
    r"UI5\s+View|UI5\s+Controller|UI5\s+Fragment|"
    r"Fiori\s+Elements|OData\s+Service|Mixed):\s*(\S+.*)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Auto-detection boundary patterns
# ---------------------------------------------------------------------------

_BOUNDARY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("CDS", re.compile(
        r"^(?:@\w|define\s+(?:root\s+)?view\s+entity|"
        r"define\s+view\s+\S+\s+as\s+select|"
        r"annotate\s+view)",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("BEHAVIOR", re.compile(
        r"^(?:managed\s+implementation|unmanaged\s+implementation|"
        r"define\s+behavior\s+for)",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("UI5_XML", re.compile(
        r"^<(?:mvc:View|core:FragmentDefinition|XMLView)\b",
        re.MULTILINE,
    )),
    ("UI5_JS", re.compile(
        r"^sap\.ui\.define\s*\(",
        re.MULTILINE,
    )),
    ("ABAP_CLASS", re.compile(
        r"^CLASS\s+\w+\s+(?:DEFINITION|IMPLEMENTATION)\b",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("ABAP_REPORT", re.compile(
        r"^\s*REPORT\s+\w+",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("SERVICE_DEF", re.compile(
        r"^define\s+service\b",
        re.IGNORECASE | re.MULTILINE,
    )),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_change_package(text: str) -> list[ArtifactSection]:
    """Split a change package into individual artifact sections.

    Supports two formats:

    1. **Separator-delimited**: sections separated by ``---`` or ``===``
       lines with optional header like ``// CDS View: ZI_Order`` or
       ``* Class: ZCL_ORDER``.

    2. **Auto-detection**: if no separators are found, attempts to detect
       multiple artifact types and split at boundaries (e.g.,
       ``define view entity`` starts a CDS section, ``CLASS zcl_``
       starts an ABAP section).

    Parameters
    ----------
    text:
        The raw change package text.

    Returns
    -------
    list[ArtifactSection]
        One section per detected artifact.  Empty sections are skipped.
    """
    if not text or not text.strip():
        return []

    # Try separator-delimited first
    sections = _try_separator_split(text)
    if sections is not None:
        return sections

    # Fall back to auto-detection
    sections = _try_auto_detect_split(text)
    if sections:
        return sections

    # Single artifact — treat the whole text as one section
    artifact_type = classify_artifact(text)
    return [
        ArtifactSection(
            artifact_type=artifact_type,
            artifact_name=_derive_name(text, artifact_type),
            code=text.strip(),
            section_index=0,
        )
    ]


# ---------------------------------------------------------------------------
# Separator-delimited splitting
# ---------------------------------------------------------------------------


def _try_separator_split(text: str) -> list[ArtifactSection] | None:
    """Attempt separator-delimited splitting.

    Returns ``None`` if no separators are found, signalling that
    auto-detection should be tried instead.
    """
    lines = text.splitlines(keepends=True)

    # Check if there are separator lines
    separator_indices: list[int] = []
    for idx, line in enumerate(lines):
        if _SEPARATOR_RE.match(line.strip()):
            separator_indices.append(idx)

    if not separator_indices:
        return None

    # Split into raw blocks between separators
    raw_blocks: list[str] = []
    prev = 0
    for sep_idx in separator_indices:
        block = "".join(lines[prev:sep_idx])
        if block.strip():
            raw_blocks.append(block)
        prev = sep_idx + 1
    # Remaining text after last separator
    remaining = "".join(lines[prev:])
    if remaining.strip():
        raw_blocks.append(remaining)

    if not raw_blocks:
        return None

    sections: list[ArtifactSection] = []
    for idx, block in enumerate(raw_blocks):
        block_stripped = block.strip()
        if not block_stripped:
            continue

        # Check for header line at start of block
        name = ""
        code = block_stripped
        block_lines = block_stripped.splitlines()
        if block_lines:
            header_match = _HEADER_RE.match(block_lines[0].strip())
            if header_match:
                name = header_match.group(1).strip()
                code = "\n".join(block_lines[1:]).strip()
                if not code:
                    continue

        artifact_type = classify_artifact(code)
        if not name:
            name = _derive_name(code, artifact_type)

        sections.append(
            ArtifactSection(
                artifact_type=artifact_type,
                artifact_name=name,
                code=code,
                section_index=idx,
            )
        )

    return sections if sections else None


# ---------------------------------------------------------------------------
# Auto-detection splitting
# ---------------------------------------------------------------------------


def _try_auto_detect_split(text: str) -> list[ArtifactSection]:
    """Attempt to auto-detect artifact boundaries in the text."""
    # Find all boundary match positions
    boundaries: list[tuple[int, str, str]] = []  # (pos, label, matched_name)

    for _label, pattern in _BOUNDARY_PATTERNS:
        for m in pattern.finditer(text):
            # Extract entity name if possible (for dedup)
            matched_name = _extract_boundary_name(m.group(), _label)
            boundaries.append((m.start(), _label, matched_name))

    if len(boundaries) <= 1:
        return []

    # Sort by position
    boundaries.sort(key=lambda b: b[0])

    # Deduplicate: merge boundaries of the same type+name (e.g., CLASS zcl_x
    # DEFINITION and CLASS zcl_x IMPLEMENTATION are the same artifact).
    # Also filter out boundaries that are very close together.
    filtered: list[tuple[int, str, str]] = [boundaries[0]]
    for pos, label, name in boundaries[1:]:
        prev_pos, prev_label, prev_name = filtered[-1]
        # Same artifact type and same name — merge (keep the first occurrence)
        if label == prev_label and name and name.lower() == (prev_name or "").lower():
            continue
        if pos - prev_pos > 20:
            filtered.append((pos, label, name))

    if len(filtered) <= 1:
        return []

    # Check that we have at least 2 distinct labels (different artifact groups)
    distinct_labels = {label for _, label, _ in filtered}
    if len(distinct_labels) < 2:
        return []

    # Split text at boundary positions
    sections: list[ArtifactSection] = []
    for idx, (pos, _label, _name) in enumerate(filtered):
        end_pos = filtered[idx + 1][0] if idx + 1 < len(filtered) else len(text)
        code = text[pos:end_pos].strip()
        if not code:
            continue

        artifact_type = classify_artifact(code)
        name = _derive_name(code, artifact_type)

        sections.append(
            ArtifactSection(
                artifact_type=artifact_type,
                artifact_name=name,
                code=code,
                section_index=idx,
            )
        )

    return sections


def _extract_boundary_name(matched_text: str, label: str) -> str:
    """Extract the artifact name from a boundary match."""
    m = re.search(r"\b(?:CLASS|REPORT|view\s+entity|view|behavior\s+for|service)\s+(\w+)", matched_text, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_name(code: str, artifact_type: ArtifactType) -> str:
    """Try to derive a meaningful name from the code."""
    # Try ABAP class name
    m = re.search(r"\bCLASS\s+(\w+)\s+", code, re.IGNORECASE)
    if m:
        return m.group(1)

    # Try CDS view entity name
    m = re.search(
        r"\bdefine\s+(?:root\s+)?view\s+entity\s+(\w+)", code, re.IGNORECASE
    )
    if m:
        return m.group(1)

    # Try view name from old-style CDS
    m = re.search(r"\bdefine\s+view\s+(\w+)", code, re.IGNORECASE)
    if m:
        return m.group(1)

    # Try behavior definition
    m = re.search(r"\bdefine\s+behavior\s+for\s+(\w+)", code, re.IGNORECASE)
    if m:
        return m.group(1)

    # Try service definition
    m = re.search(r"\bdefine\s+service\s+(\w+)", code, re.IGNORECASE)
    if m:
        return m.group(1)

    # Try ABAP report
    m = re.search(r"\bREPORT\s+(\w+)", code, re.IGNORECASE)
    if m:
        return m.group(1)

    # Fall back to artifact type
    return artifact_type.value
