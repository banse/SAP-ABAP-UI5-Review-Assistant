"""Fiori Elements review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance that detects common Fiori Elements
configuration issues, with bilingual EN/DE metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# FE-CFG-001: Incomplete List Report configuration
# ---------------------------------------------------------------------------

FE_CFG_001 = ReviewRule(
    rule_id="FE-CFG-001",
    name="Incomplete List Report configuration",
    name_de="Unvollstaendige List-Report-Konfiguration",
    description=(
        "A CDS projection or annotation file for a List Report is missing "
        "@UI.selectionField annotations. Without SelectionFields, the filter bar "
        "has no default filter criteria."
    ),
    description_de=(
        "Eine CDS-Projection oder Annotationsdatei fuer einen List Report hat "
        "keine @UI.selectionField Annotationen. Ohne SelectionFields hat die "
        "Filterleiste keine Standard-Filterkriterien."
    ),
    artifact_types=("CDS_PROJECTION", "CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"@UI\.lineItem",
    check_fn_name="check_missing_selection_fields",
    category="configuration",
    recommendation="Add @UI.selectionField annotations for key filter fields.",
    recommendation_de="@UI.selectionField Annotationen fuer wichtige Filterfelder hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-002: Object Page without header info
# ---------------------------------------------------------------------------

FE_CFG_002 = ReviewRule(
    rule_id="FE-CFG-002",
    name="Object Page without header info",
    name_de="Object Page ohne Header-Info",
    description=(
        "A CDS entity used in an Object Page is missing @UI.headerInfo annotation. "
        "This annotation defines the title, subtitle, and image shown in the header."
    ),
    description_de=(
        "Eine CDS-Entitaet fuer eine Object Page hat keine @UI.headerInfo Annotation. "
        "Diese Annotation definiert Titel, Untertitel und Bild im Header."
    ),
    artifact_types=("CDS_PROJECTION", "CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"@UI\.identification",
    check_fn_name="check_missing_header_info",
    category="configuration",
    recommendation="Add @UI.headerInfo annotation with typeName and typeNamePlural.",
    recommendation_de="@UI.headerInfo Annotation mit typeName und typeNamePlural hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-003: Missing criticality on status fields
# ---------------------------------------------------------------------------

FE_CFG_003 = ReviewRule(
    rule_id="FE-CFG-003",
    name="Missing criticality on status fields",
    name_de="Fehlende Criticality bei Statusfeldern",
    description=(
        "A field with 'status' or 'Status' in its name or alias lacks a "
        "@UI.lineItem.criticality or @UI.fieldGroup.criticality annotation. "
        "Status fields should have visual criticality indicators."
    ),
    description_de=(
        "Ein Feld mit 'status' oder 'Status' im Namen oder Alias hat keine "
        "@UI.lineItem.criticality oder @UI.fieldGroup.criticality Annotation. "
        "Statusfelder sollten visuelle Criticality-Indikatoren haben."
    ),
    artifact_types=("CDS_PROJECTION", "CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"(?i)(?:as\s+\w*status\w*|(?:overall|order|delivery|processing)_?status)",
    check_fn_name="check_missing_status_criticality",
    category="ux",
    recommendation="Add criticality or criticalityRepresentation annotation to status fields.",
    recommendation_de="criticality oder criticalityRepresentation Annotation zu Statusfeldern hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-004: Action annotation missing DataFieldForAction type
# ---------------------------------------------------------------------------

FE_CFG_004 = ReviewRule(
    rule_id="FE-CFG-004",
    name="Action annotation missing DataFieldForAction",
    name_de="Action-Annotation ohne DataFieldForAction",
    description=(
        "An action is defined in the behavior definition or CDS but not exposed "
        "in UI annotations with type #FOR_ACTION or DataFieldForAction. The action "
        "will not appear in the Fiori Elements UI."
    ),
    description_de=(
        "Eine Aktion ist im Behavior Definition oder CDS definiert, aber nicht "
        "in UI-Annotationen mit type #FOR_ACTION oder DataFieldForAction exponiert. "
        "Die Aktion erscheint nicht in der Fiori Elements Oberflaeche."
    ),
    artifact_types=("CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\baction\s+\w+",
    check_fn_name="check_missing_action_annotation",
    category="configuration",
    recommendation="Add @UI.lineItem or @UI.identification with type: #FOR_ACTION.",
    recommendation_de="@UI.lineItem oder @UI.identification mit type: #FOR_ACTION hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-005: Missing navigation configuration
# ---------------------------------------------------------------------------

FE_CFG_005 = ReviewRule(
    rule_id="FE-CFG-005",
    name="Missing intent-based navigation in list",
    name_de="Fehlende Intent-basierte Navigation in Liste",
    description=(
        "A List Report entity has lineItem annotations but no navigation "
        "configuration via DataFieldWithIntentBasedNavigation or "
        "DataFieldWithNavigationPath for cross-app navigation."
    ),
    description_de=(
        "Eine List-Report-Entitaet hat lineItem-Annotationen, aber keine "
        "Navigationskonfiguration via DataFieldWithIntentBasedNavigation oder "
        "DataFieldWithNavigationPath fuer App-uebergreifende Navigation."
    ),
    artifact_types=("CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"@UI\.lineItem",
    check_fn_name="check_missing_navigation",
    category="configuration",
    recommendation="Add DataFieldWithIntentBasedNavigation for cross-app navigation.",
    recommendation_de="DataFieldWithIntentBasedNavigation fuer App-uebergreifende Navigation hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-006: Missing i18n for annotation labels
# ---------------------------------------------------------------------------

FE_CFG_006 = ReviewRule(
    rule_id="FE-CFG-006",
    name="Missing i18n for annotation labels",
    name_de="Fehlende i18n fuer Annotations-Labels",
    description=(
        "Inline text is used directly in CDS annotations (label, typeName, "
        "description) instead of i18n references. This prevents translation."
    ),
    description_de=(
        "Inline-Text wird direkt in CDS-Annotationen (label, typeName, "
        "description) verwendet anstatt i18n-Referenzen. Dies verhindert Uebersetzung."
    ),
    artifact_types=("CDS_PROJECTION", "CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"""(?:label|typeName|typeNamePlural|title|description)\s*:\s*'[A-Z][a-zA-Z\s]{2,}'""",
    category="internationalization",
    recommendation="Use i18n references: label: '{i18n>myLabel}' instead of inline text.",
    recommendation_de="i18n-Referenzen verwenden: label: '{i18n>myLabel}' statt Inline-Text.",
)

# ---------------------------------------------------------------------------
# FE-CFG-007: Extension point misuse
# ---------------------------------------------------------------------------

FE_CFG_007 = ReviewRule(
    rule_id="FE-CFG-007",
    name="Extension point misuse in manifest.json",
    name_de="Fehlverwendung von Extension Points in manifest.json",
    description=(
        "The manifest.json contains Fiori Elements extension overrides that "
        "replace standard controllers or views. This breaks standard upgrade "
        "paths and should use controlled extension points instead."
    ),
    description_de=(
        "Die manifest.json enthaelt Fiori Elements Extension-Overrides, die "
        "Standard-Controller oder Views ersetzen. Dies bricht Standard-Upgrade-"
        "Pfade und sollte kontrollierte Extension Points verwenden."
    ),
    artifact_types=("FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"""(?:"controllerName"\s*:\s*"(?!sap\.)[^"]+"|"viewName"\s*:\s*"(?!sap\.)[^"]+")""",
    check_fn_name="check_extension_point_misuse",
    category="upgrade_safety",
    recommendation="Use official extension points (e.g., controllerExtensions) instead of full overrides.",
    recommendation_de="Offizielle Extension Points (z.B. controllerExtensions) statt vollstaendiger Overrides verwenden.",
)

# ---------------------------------------------------------------------------
# FE-CFG-008: Missing variant management configuration
# ---------------------------------------------------------------------------

FE_CFG_008 = ReviewRule(
    rule_id="FE-CFG-008",
    name="Missing variant management configuration",
    name_de="Fehlende Variant-Management-Konfiguration",
    description=(
        "A Fiori Elements application manifest does not configure variant "
        "management. Users cannot save personalized filter and table settings."
    ),
    description_de=(
        "Eine Fiori Elements Anwendungsmanifest konfiguriert kein Variant "
        "Management. Benutzer koennen personalisierte Filter- und Tabelleneinstellungen "
        "nicht speichern."
    ),
    artifact_types=("FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"sap\.ui\.generic\.app|sap\.fe\.templates",
    check_fn_name="check_missing_variant_management",
    category="ux",
    recommendation='Add variantManagement configuration in manifest.json settings.',
    recommendation_de='variantManagement-Konfiguration in manifest.json-Einstellungen hinzufuegen.',
)

# ---------------------------------------------------------------------------
# FE-CFG-009: Filter bar without default values
# ---------------------------------------------------------------------------

FE_CFG_009 = ReviewRule(
    rule_id="FE-CFG-009",
    name="Filter bar without default values",
    name_de="Filterleiste ohne Standardwerte",
    description=(
        "The filter bar has selectionField annotations but no default values "
        "configured. Users see an empty filter bar and must set values manually "
        "before loading data."
    ),
    description_de=(
        "Die Filterleiste hat selectionField-Annotationen, aber keine Standardwerte "
        "konfiguriert. Benutzer sehen eine leere Filterleiste und muessen Werte "
        "manuell setzen, bevor Daten geladen werden."
    ),
    artifact_types=("CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"@UI\.selectionField",
    check_fn_name="check_filter_bar_default_values",
    category="ux",
    recommendation="Add @Consumption.filter.defaultValue or Common.FilterDefaultValue annotations.",
    recommendation_de="@Consumption.filter.defaultValue oder Common.FilterDefaultValue Annotationen hinzufuegen.",
)

# ---------------------------------------------------------------------------
# FE-CFG-010: Table without initial sort order
# ---------------------------------------------------------------------------

FE_CFG_010 = ReviewRule(
    rule_id="FE-CFG-010",
    name="Table without initial sort order",
    name_de="Tabelle ohne initiale Sortierung",
    description=(
        "A List Report or Object Page table has lineItem annotations but no "
        "@UI.presentationVariant with sortOrder. Data appears in arbitrary order."
    ),
    description_de=(
        "Eine List-Report- oder Object-Page-Tabelle hat lineItem-Annotationen, aber "
        "kein @UI.presentationVariant mit sortOrder. Daten erscheinen in beliebiger Reihenfolge."
    ),
    artifact_types=("CDS_PROJECTION", "CDS_ANNOTATION", "FIORI_ELEMENTS_APP", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"@UI\.lineItem",
    check_fn_name="check_missing_sort_order",
    category="ux",
    recommendation="Add @UI.presentationVariant with sortOrder for consistent data display.",
    recommendation_de="@UI.presentationVariant mit sortOrder fuer konsistente Datenanzeige hinzufuegen.",
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_missing_selection_fields(code: str) -> list[tuple[str, int]]:
    """Return a match if lineItem annotations exist but no selectionField."""
    has_line_item = re.search(r"@UI\.lineItem", code, re.IGNORECASE)
    has_selection_field = re.search(r"(?:selectionField|SelectionFields)", code, re.IGNORECASE)

    if has_line_item and not has_selection_field:
        return [(has_line_item.group(), code[: has_line_item.start()].count("\n") + 1)]
    return []


def check_missing_header_info(code: str) -> list[tuple[str, int]]:
    """Return a match if identification annotations exist but no headerInfo."""
    has_identification = re.search(r"@UI\.identification", code, re.IGNORECASE)
    has_header_info = re.search(r"(?:headerInfo|HeaderInfo)", code, re.IGNORECASE)

    if has_identification and not has_header_info:
        return [(has_identification.group(), code[: has_identification.start()].count("\n") + 1)]
    return []


def check_missing_status_criticality(code: str) -> list[tuple[str, int]]:
    """Return a match if status fields lack criticality annotations."""
    results: list[tuple[str, int]] = []
    status_pattern = re.compile(
        r"(?:as\s+\w*[Ss]tatus\w*|(?:overall|order|delivery|processing)[_]?[Ss]tatus)",
        re.IGNORECASE,
    )

    for match in status_pattern.finditer(code):
        # Check 300 chars around the match for criticality
        start = max(0, match.start() - 150)
        end = min(len(code), match.end() + 150)
        context = code[start:end]
        has_criticality = re.search(r"criticality", context, re.IGNORECASE)
        if not has_criticality:
            line_num = code[: match.start()].count("\n") + 1
            results.append((match.group(), line_num))
    return results


def check_missing_action_annotation(code: str) -> list[tuple[str, int]]:
    """Return a match if actions are defined but not exposed in UI annotations."""
    has_action = re.search(r"\baction\s+\w+", code, re.IGNORECASE)
    has_for_action = re.search(r"(?:#FOR_ACTION|DataFieldForAction)", code, re.IGNORECASE)

    if has_action and not has_for_action:
        return [(has_action.group(), code[: has_action.start()].count("\n") + 1)]
    return []


def check_missing_navigation(code: str) -> list[tuple[str, int]]:
    """Return a match if lineItem exists but no navigation configuration."""
    has_line_item = re.search(r"@UI\.lineItem", code, re.IGNORECASE)
    has_navigation = re.search(
        r"(?:IntentBasedNavigation|NavigationPath|DataFieldWithUrl|semanticObject)",
        code, re.IGNORECASE,
    )

    if has_line_item and not has_navigation:
        return [(has_line_item.group(), code[: has_line_item.start()].count("\n") + 1)]
    return []


def check_extension_point_misuse(code: str) -> list[tuple[str, int]]:
    """Return a match if manifest overrides standard controllers/views."""
    results: list[tuple[str, int]] = []
    # Look for extends/overrides in a manifest-like structure
    override_pattern = re.compile(
        r'"(?:controllerName|viewName)"\s*:\s*"(?!sap\.)[^"]+"',
    )
    for match in override_pattern.finditer(code):
        # Only flag if we also see extension-related context
        context_start = max(0, match.start() - 300)
        context = code[context_start:match.start()]
        if re.search(r"(?:extends|extension|templateName|component)", context, re.IGNORECASE):
            line_num = code[: match.start()].count("\n") + 1
            results.append((match.group(), line_num))
    return results


def check_missing_variant_management(code: str) -> list[tuple[str, int]]:
    """Return a match if FE app config exists but no variant management."""
    has_fe_template = re.search(
        r"(?:sap\.ui\.generic\.app|sap\.fe\.templates)", code
    )
    has_variant = re.search(r"(?:variantManagement|VariantManagement)", code, re.IGNORECASE)

    if has_fe_template and not has_variant:
        return [(has_fe_template.group(), code[: has_fe_template.start()].count("\n") + 1)]
    return []


def check_filter_bar_default_values(code: str) -> list[tuple[str, int]]:
    """Return a match if selectionFields exist but no default values."""
    has_selection = re.search(r"@UI\.selectionField", code, re.IGNORECASE)
    has_defaults = re.search(
        r"(?:defaultValue|FilterDefaultValue|filter\.default)", code, re.IGNORECASE
    )

    if has_selection and not has_defaults:
        return [(has_selection.group(), code[: has_selection.start()].count("\n") + 1)]
    return []


def check_missing_sort_order(code: str) -> list[tuple[str, int]]:
    """Return a match if lineItem exists but no presentationVariant with sortOrder."""
    has_line_item = re.search(r"@UI\.lineItem", code, re.IGNORECASE)
    has_sort = re.search(
        r"(?:presentationVariant|sortOrder|PresentationVariant)", code, re.IGNORECASE
    )

    if has_line_item and not has_sort:
        return [(has_line_item.group(), code[: has_line_item.start()].count("\n") + 1)]
    return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

FIORI_ELEMENTS_RULES: tuple[ReviewRule, ...] = (
    FE_CFG_001,
    FE_CFG_002,
    FE_CFG_003,
    FE_CFG_004,
    FE_CFG_005,
    FE_CFG_006,
    FE_CFG_007,
    FE_CFG_008,
    FE_CFG_009,
    FE_CFG_010,
)

FIORI_ELEMENTS_CHECK_FUNCTIONS: dict[str, object] = {
    "check_missing_selection_fields": check_missing_selection_fields,
    "check_missing_header_info": check_missing_header_info,
    "check_missing_status_criticality": check_missing_status_criticality,
    "check_missing_action_annotation": check_missing_action_annotation,
    "check_missing_navigation": check_missing_navigation,
    "check_extension_point_misuse": check_extension_point_misuse,
    "check_missing_variant_management": check_missing_variant_management,
    "check_filter_bar_default_values": check_filter_bar_default_values,
    "check_missing_sort_order": check_missing_sort_order,
}
