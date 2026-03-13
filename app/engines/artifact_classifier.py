"""Artifact type classification engine.

Analyses submitted code to determine which ``ArtifactType`` it represents.
"""

from __future__ import annotations

import re

from app.models.enums import ArtifactType


# ---------------------------------------------------------------------------
# Pattern groups — order matters (more specific patterns first)
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[ArtifactType, list[str]]] = [
    # RAP / Service layer (check before generic CDS/ABAP)
    (ArtifactType.SERVICE_BINDING, [
        r"\bbind\s+service\b",
    ]),
    (ArtifactType.SERVICE_DEFINITION, [
        r"\bdefine\s+service\b",
    ]),
    (ArtifactType.BEHAVIOR_IMPLEMENTATION, [
        r"\bMETHOD\s+\w+\s+FOR\s+(?:MODIFY|READ|ACTION|VALIDATE|DETERMINE)\b",
    ]),
    (ArtifactType.BEHAVIOR_DEFINITION, [
        r"\bmanaged\s+implementation\s+in\s+class\b",
        r"\bunmanaged\s+implementation\s+in\s+class\b",
        r"\bdefine\s+behavior\s+for\b",
    ]),

    # CDS (check before ABAP because "define view" is distinctive)
    (ArtifactType.CDS_ANNOTATION, [
        r"\bannotate\s+view\b",
    ]),
    (ArtifactType.CDS_PROJECTION, [
        r"\bdefine\s+(?:root\s+)?view\s+entity\s+\S+\s+as\s+projection\s+on\b",
    ]),
    (ArtifactType.CDS_VIEW, [
        r"\bdefine\s+(?:root\s+)?view\s+entity\b",
        r"\bdefine\s+view\s+\S+\s+as\s+select\s+from\b",
    ]),

    # UI5
    (ArtifactType.UI5_FRAGMENT, [
        r"<core:FragmentDefinition\b",
    ]),
    (ArtifactType.UI5_VIEW, [
        r"<mvc:View\b",
        r"<XMLView\b",
    ]),
    (ArtifactType.UI5_CONTROLLER, [
        r"sap\.ui\.define\s*\(.*Controller",
        r"Controller\.extend\s*\(",
        r"sap\.ui\.controller\s*\(",
        r'sap/ui/core/mvc/Controller',
    ]),

    # ABAP (broadest patterns last)
    (ArtifactType.ABAP_REPORT, [
        r"^\s*REPORT\s+\w+",
    ]),
    (ArtifactType.ABAP_CLASS, [
        r"\bCLASS\s+\w+\s+DEFINITION\b",
        r"\bCLASS\s+\w+\s+IMPLEMENTATION\b",
    ]),
    (ArtifactType.ABAP_METHOD, [
        r"\bMETHOD\s+\w+\.",
        r"\bENDMETHOD\.",
    ]),
]


def _count_type_matches(code: str) -> dict[ArtifactType, int]:
    """Count how many distinct artifact types match in the code."""
    matched: dict[ArtifactType, int] = {}
    for artifact_type, patterns in _PATTERNS:
        for pat in patterns:
            if re.search(pat, code, re.IGNORECASE | re.MULTILINE):
                matched[artifact_type] = matched.get(artifact_type, 0) + 1
                break  # one match per type group is enough
    return matched


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_artifact(
    code: str,
    provided_type: ArtifactType | None = None,
) -> ArtifactType:
    """Classify the artifact type of the submitted code.

    If *provided_type* is given and is not ``None``, it is returned directly.
    Otherwise heuristics are applied.
    """
    if provided_type is not None:
        return provided_type

    if not code or not code.strip():
        return ArtifactType.ABAP_CLASS  # safe default

    matched = _count_type_matches(code)

    if not matched:
        return ArtifactType.ABAP_CLASS  # safe default

    # If multiple distinct *groups* of artifact types matched, call it mixed
    # Group: ABAP = {ABAP_CLASS, ABAP_METHOD, ABAP_REPORT}
    # Group: CDS  = {CDS_VIEW, CDS_PROJECTION, CDS_ANNOTATION}
    # Group: UI5  = {UI5_VIEW, UI5_CONTROLLER, UI5_FRAGMENT, UI5_FORMATTER}
    # Group: RAP  = {BEHAVIOR_DEFINITION, BEHAVIOR_IMPLEMENTATION,
    #                SERVICE_DEFINITION, SERVICE_BINDING}
    groups_hit: set[str] = set()
    abap_types = {ArtifactType.ABAP_CLASS, ArtifactType.ABAP_METHOD, ArtifactType.ABAP_REPORT}
    cds_types = {ArtifactType.CDS_VIEW, ArtifactType.CDS_PROJECTION, ArtifactType.CDS_ANNOTATION}
    ui5_types = {ArtifactType.UI5_VIEW, ArtifactType.UI5_CONTROLLER, ArtifactType.UI5_FRAGMENT}
    rap_types = {
        ArtifactType.BEHAVIOR_DEFINITION, ArtifactType.BEHAVIOR_IMPLEMENTATION,
        ArtifactType.SERVICE_DEFINITION, ArtifactType.SERVICE_BINDING,
    }

    for at in matched:
        if at in abap_types:
            groups_hit.add("ABAP")
        elif at in cds_types:
            groups_hit.add("CDS")
        elif at in ui5_types:
            groups_hit.add("UI5")
        elif at in rap_types:
            # RAP behavior implementation is still ABAP-based, not a separate
            # technology group.  Only count as a separate group when mixed with
            # CDS/UI5 artefacts — achieved by grouping RAP + ABAP together.
            groups_hit.add("ABAP")

    if len(groups_hit) >= 2:
        return ArtifactType.MIXED_FULLSTACK

    # Return the first (most specific) match — _PATTERNS is ordered by specificity
    for artifact_type, patterns in _PATTERNS:
        if artifact_type in matched:
            return artifact_type

    return ArtifactType.ABAP_CLASS
