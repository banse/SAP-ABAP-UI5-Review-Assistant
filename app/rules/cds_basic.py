"""MVP CDS review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance with a regex pattern that
detects a common CDS view quality issue, plus bilingual metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# CDS-ANNO: Annotation rules
# ---------------------------------------------------------------------------

CDS_ANNO_001 = ReviewRule(
    rule_id="CDS-ANNO-001",
    name="Missing @AbapCatalog annotation",
    name_de="Fehlende @AbapCatalog Annotation",
    description=(
        "A CDS view entity should have an @AbapCatalog annotation to control "
        "SQL view generation and buffering behavior."
    ),
    description_de=(
        "Eine CDS View Entity sollte eine @AbapCatalog Annotation besitzen, um "
        "die SQL-View-Generierung und das Pufferverhalten zu steuern."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"define\s+(?:root\s+)?view\s+entity",
    check_fn_name="check_missing_abap_catalog",
    category="annotations",
    recommendation="Add @AbapCatalog.viewEnhancementCategory or similar annotation.",
    recommendation_de="@AbapCatalog.viewEnhancementCategory oder aehnliche Annotation hinzufuegen.",
)

CDS_ANNO_002 = ReviewRule(
    rule_id="CDS-ANNO-002",
    name="Missing @AccessControl annotation",
    name_de="Fehlende @AccessControl Annotation",
    description=(
        "Without @AccessControl.authorizationCheck the view does not enforce "
        "DCL-based authorization, which is a security risk."
    ),
    description_de=(
        "Ohne @AccessControl.authorizationCheck erzwingt die View keine DCL-"
        "basierte Berechtigung, was ein Sicherheitsrisiko darstellt."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    check_fn_name="check_missing_access_control",
    category="security",
    recommendation="Add @AccessControl.authorizationCheck: #CHECK (or #NOT_REQUIRED with justification).",
    recommendation_de=(
        "@AccessControl.authorizationCheck: #CHECK hinzufuegen (oder #NOT_REQUIRED "
        "mit Begruendung)."
    ),
)

CDS_ANNO_003 = ReviewRule(
    rule_id="CDS-ANNO-003",
    name="Missing @UI annotations on consumption view",
    name_de="Fehlende @UI Annotationen auf Consumption View",
    description=(
        "A consumption (C_) or projection view intended for Fiori UIs should "
        "carry @UI annotations to drive the UI rendering."
    ),
    description_de=(
        "Eine Consumption- (C_) oder Projection-View, die fuer Fiori UIs "
        "vorgesehen ist, sollte @UI Annotationen tragen."
    ),
    artifact_types=("CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"(?:as\s+projection\s+on|define\s+(?:root\s+)?view\s+entity\s+[Cc]_)",
    check_fn_name="check_missing_ui_annotations",
    category="annotations",
    recommendation="Add @UI.lineItem / @UI.identification / @UI.selectionField annotations.",
    recommendation_de="@UI.lineItem / @UI.identification / @UI.selectionField Annotationen hinzufuegen.",
)

CDS_ANNO_004 = ReviewRule(
    rule_id="CDS-ANNO-004",
    name="Missing @Search annotations on searchable fields",
    name_de="Fehlende @Search Annotationen auf suchbaren Feldern",
    description=(
        "Fields intended for free-text or value-help search should carry "
        "@Search.defaultSearchElement or @Search.fuzzinessThreshold annotations."
    ),
    description_de=(
        "Felder, die fuer Freitext- oder Werthilfesuche vorgesehen sind, sollten "
        "@Search.defaultSearchElement oder @Search.fuzzinessThreshold tragen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    check_fn_name="check_missing_search_annotations",
    category="annotations",
    recommendation="Add @Search.defaultSearchElement: true on fields relevant for search.",
    recommendation_de="@Search.defaultSearchElement: true auf suchrelevante Felder setzen.",
)

# ---------------------------------------------------------------------------
# CDS-STRUCT: Structural rules
# ---------------------------------------------------------------------------

CDS_STRUCT_001 = ReviewRule(
    rule_id="CDS-STRUCT-001",
    name="CDS view without key field",
    name_de="CDS View ohne Schluesselfeld",
    description=(
        "A CDS view without a key field cannot be consumed correctly by OData "
        "services or RAP, which require stable entity keys."
    ),
    description_de=(
        "Eine CDS View ohne Schluesselfeld kann von OData-Services oder RAP "
        "nicht korrekt konsumiert werden, da stabile Entity-Keys benoetigt werden."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    check_fn_name="check_missing_key_field",
    category="structure",
    recommendation="Define at least one key field in the select list.",
    recommendation_de="Mindestens ein Schluesselfeld in der Selektionsliste definieren.",
)

CDS_STRUCT_002 = ReviewRule(
    rule_id="CDS-STRUCT-002",
    name="Missing association in projection view",
    name_de="Fehlende Association in Projection View",
    description=(
        "A projection view should expose associations from its source for "
        "navigation in Fiori Elements apps and OData consumers."
    ),
    description_de=(
        "Eine Projection View sollte Associations der Quell-View exponieren, "
        "damit Fiori-Elements-Apps und OData-Consumer navigieren koennen."
    ),
    artifact_types=("CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"as\s+projection\s+on",
    check_fn_name="check_missing_association_in_projection",
    category="structure",
    recommendation="Expose relevant associations from the source view using use association syntax.",
    recommendation_de=(
        "Relevante Associations der Quell-View mit use-association-Syntax exponieren."
    ),
)

# ---------------------------------------------------------------------------
# CDS-PERF: Performance rules
# ---------------------------------------------------------------------------

CDS_PERF_001 = ReviewRule(
    rule_id="CDS-PERF-001",
    name="CDS view join without WHERE clause",
    name_de="CDS View Join ohne WHERE-Klausel",
    description=(
        "A CDS view that joins multiple tables without a WHERE clause may cause "
        "expensive full cross-joins at the database level."
    ),
    description_de=(
        "Eine CDS View, die mehrere Tabellen ohne WHERE-Klausel joint, kann "
        "teure Full-Cross-Joins auf Datenbankebene verursachen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\bjoin\b",
    check_fn_name="check_join_without_where",
    category="performance",
    recommendation="Add a WHERE clause to restrict the join result set.",
    recommendation_de="Eine WHERE-Klausel hinzufuegen, um die Join-Ergebnismenge einzuschraenken.",
)

# ---------------------------------------------------------------------------
# CDS-CONS: Consistency rules
# ---------------------------------------------------------------------------

CDS_CONS_001 = ReviewRule(
    rule_id="CDS-CONS-001",
    name="Inconsistent field naming (mixed case)",
    name_de="Inkonsistente Feldbezeichnung (gemischte Schreibweise)",
    description=(
        "Field aliases should follow a consistent naming convention, typically "
        "CamelCase. Mixing snake_case and CamelCase in the same view reduces "
        "readability."
    ),
    description_de=(
        "Feld-Aliase sollten einer konsistenten Namenskonvention folgen, "
        "typischerweise CamelCase. Die Mischung von snake_case und CamelCase "
        "in derselben View reduziert die Lesbarkeit."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\bas\s+[a-z]+_[a-z]+\b",
    category="readability",
    recommendation="Use consistent CamelCase for field aliases (SAP convention).",
    recommendation_de="Konsistentes CamelCase fuer Feld-Aliase verwenden (SAP-Konvention).",
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_missing_abap_catalog(code: str) -> list[tuple[str, int]]:
    """Return a match if the view entity has no @AbapCatalog annotation."""
    has_view_entity = re.search(
        r"define\s+(?:root\s+)?view\s+entity", code, re.IGNORECASE
    )
    has_annotation = re.search(r"@AbapCatalog\b", code, re.IGNORECASE)

    if has_view_entity and not has_annotation:
        return [(has_view_entity.group(), code[: has_view_entity.start()].count("\n") + 1)]
    return []


def check_missing_access_control(code: str) -> list[tuple[str, int]]:
    """Return a match if the view has no @AccessControl annotation."""
    has_view = re.search(
        r"define\s+(?:root\s+)?view\s+(?:entity\s+)?", code, re.IGNORECASE
    )
    has_annotation = re.search(r"@AccessControl\b", code, re.IGNORECASE)

    if has_view and not has_annotation:
        return [(has_view.group(), code[: has_view.start()].count("\n") + 1)]
    return []


def check_missing_key_field(code: str) -> list[tuple[str, int]]:
    """Return a match if the CDS view has no key field defined."""
    has_view = re.search(
        r"define\s+(?:root\s+)?view\s+(?:entity\s+)?", code, re.IGNORECASE
    )
    has_key = re.search(r"\bkey\s+\w+", code, re.IGNORECASE)

    if has_view and not has_key:
        return [(has_view.group(), code[: has_view.start()].count("\n") + 1)]
    return []


def check_missing_ui_annotations(code: str) -> list[tuple[str, int]]:
    """Return a match if a projection/consumption view lacks @UI annotations."""
    has_projection = re.search(
        r"(?:as\s+projection\s+on|define\s+(?:root\s+)?view\s+entity\s+[Cc]_)",
        code, re.IGNORECASE,
    )
    has_ui = re.search(r"@UI\.", code, re.IGNORECASE)

    if has_projection and not has_ui:
        return [(has_projection.group(), code[: has_projection.start()].count("\n") + 1)]
    return []


def check_missing_search_annotations(code: str) -> list[tuple[str, int]]:
    """Return a match if a view has no @Search annotations."""
    has_view = re.search(
        r"define\s+(?:root\s+)?view\s+(?:entity\s+)?", code, re.IGNORECASE
    )
    has_search = re.search(r"@Search\.", code, re.IGNORECASE)

    if has_view and not has_search:
        return [(has_view.group(), code[: has_view.start()].count("\n") + 1)]
    return []


def check_missing_association_in_projection(code: str) -> list[tuple[str, int]]:
    """Return a match if a projection view has no association exposure."""
    has_projection = re.search(r"as\s+projection\s+on", code, re.IGNORECASE)
    has_assoc = re.search(r"\b(?:_\w+|association)\b", code, re.IGNORECASE)

    if has_projection and not has_assoc:
        return [(has_projection.group(), code[: has_projection.start()].count("\n") + 1)]
    return []


def check_join_without_where(code: str) -> list[tuple[str, int]]:
    """Return a match if the CDS view has a join but no WHERE clause."""
    has_join = re.search(r"\bjoin\b", code, re.IGNORECASE)
    has_where = re.search(r"\bwhere\b", code, re.IGNORECASE)

    if has_join and not has_where:
        return [(has_join.group(), code[: has_join.start()].count("\n") + 1)]
    return []


# ---------------------------------------------------------------------------
# Registry — all CDS rules in one tuple
# ---------------------------------------------------------------------------

CDS_RULES: tuple[ReviewRule, ...] = (
    CDS_ANNO_001,
    CDS_ANNO_002,
    CDS_ANNO_003,
    CDS_ANNO_004,
    CDS_STRUCT_001,
    CDS_STRUCT_002,
    CDS_PERF_001,
    CDS_CONS_001,
)

# Map of check_fn_name -> callable
CDS_CHECK_FUNCTIONS: dict[str, object] = {
    "check_missing_abap_catalog": check_missing_abap_catalog,
    "check_missing_access_control": check_missing_access_control,
    "check_missing_key_field": check_missing_key_field,
    "check_missing_ui_annotations": check_missing_ui_annotations,
    "check_missing_search_annotations": check_missing_search_annotations,
    "check_missing_association_in_projection": check_missing_association_in_projection,
    "check_join_without_where": check_join_without_where,
}
