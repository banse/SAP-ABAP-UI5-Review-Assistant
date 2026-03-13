"""CDS annotation review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance with bilingual metadata that
detects CDS annotation best-practice violations.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# CDS-ANN: Annotation best-practice rules
# ---------------------------------------------------------------------------

CDS_ANN_001 = ReviewRule(
    rule_id="CDS-ANN-001",
    name="Annotation overkill on interface view",
    name_de="Annotations-Ueberladung auf Interface View",
    description=(
        "UI annotations such as @UI.lineItem or @UI.selectionField should not "
        "be placed on interface (I_) views. They belong on consumption (C_) or "
        "projection views to keep the interface layer reusable."
    ),
    description_de=(
        "UI-Annotationen wie @UI.lineItem oder @UI.selectionField sollten nicht "
        "auf Interface- (I_-) Views platziert werden. Sie gehoeren auf "
        "Consumption- (C_-) oder Projection-Views, um die Interface-Schicht "
        "wiederverwendbar zu halten."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"define\s+(?:root\s+)?view\s+entity\s+\w*[Ii]_",
    check_fn_name="check_annotation_overkill_on_interface_view",
    category="annotations",
    recommendation="Move @UI annotations to the consumption/projection view layer.",
    recommendation_de="@UI-Annotationen auf die Consumption-/Projection-View-Schicht verschieben.",
)

CDS_ANN_002 = ReviewRule(
    rule_id="CDS-ANN-002",
    name="Missing @Semantics for currency/quantity fields",
    name_de="Fehlende @Semantics fuer Waehrungs-/Mengenfelder",
    description=(
        "Fields named like amount, currency, quantity, or unit should carry "
        "@Semantics.amount.currencyCode or @Semantics.quantity.unitOfMeasure "
        "annotations for correct Fiori rendering and aggregation."
    ),
    description_de=(
        "Felder mit Namen wie Amount, Currency, Quantity oder Unit sollten "
        "@Semantics.amount.currencyCode oder @Semantics.quantity.unitOfMeasure "
        "Annotationen tragen, damit Fiori korrekt rendern und aggregieren kann."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    check_fn_name="check_missing_semantics_currency_quantity",
    category="annotations",
    recommendation="Add @Semantics.amount.currencyCode or @Semantics.quantity.unitOfMeasure annotations.",
    recommendation_de="@Semantics.amount.currencyCode oder @Semantics.quantity.unitOfMeasure Annotationen hinzufuegen.",
)

CDS_ANN_003 = ReviewRule(
    rule_id="CDS-ANN-003",
    name="Missing @ObjectModel annotations",
    name_de="Fehlende @ObjectModel Annotationen",
    description=(
        "A CDS view entity used in RAP or analytical scenarios should have "
        "@ObjectModel annotations (e.g. modelCategory, representativeKey) to "
        "describe the business object semantics."
    ),
    description_de=(
        "Eine CDS View Entity, die in RAP oder analytischen Szenarien "
        "verwendet wird, sollte @ObjectModel-Annotationen (z.B. modelCategory, "
        "representativeKey) besitzen, um die Geschaeftsobjekt-Semantik zu beschreiben."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"define\s+(?:root\s+)?view\s+entity",
    check_fn_name="check_missing_object_model",
    category="annotations",
    recommendation="Add @ObjectModel.modelCategory or @ObjectModel.representativeKey annotation.",
    recommendation_de="@ObjectModel.modelCategory oder @ObjectModel.representativeKey Annotation hinzufuegen.",
)

CDS_ANN_004 = ReviewRule(
    rule_id="CDS-ANN-004",
    name="Value help annotation incomplete",
    name_de="Werthilfe-Annotation unvollstaendig",
    description=(
        "Fields that represent IDs or codes (ending in Id, Code, Type, Key, "
        "Number) on a projection or consumption view should have a "
        "@Consumption.valueHelpDefinition annotation for usability in Fiori UIs."
    ),
    description_de=(
        "Felder, die IDs oder Codes darstellen (endend auf Id, Code, Type, Key, "
        "Number), sollten auf Projection- oder Consumption-Views eine "
        "@Consumption.valueHelpDefinition Annotation besitzen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"as\s+projection\s+on",
    check_fn_name="check_missing_value_help",
    category="annotations",
    recommendation="Add @Consumption.valueHelpDefinition for ID/code fields.",
    recommendation_de="@Consumption.valueHelpDefinition fuer ID-/Code-Felder hinzufuegen.",
)

CDS_ANN_005 = ReviewRule(
    rule_id="CDS-ANN-005",
    name="CDS view layering violation",
    name_de="CDS View Schichtenverletzung",
    description=(
        "An interface (I_) view should not reference a consumption (C_) view. "
        "The correct dependency direction is C_ -> I_ -> base tables."
    ),
    description_de=(
        "Eine Interface- (I_-) View sollte keine Consumption- (C_-) View "
        "referenzieren. Die korrekte Abhaengigkeitsrichtung ist "
        "C_ -> I_ -> Basistabellen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"define\s+(?:root\s+)?view\s+entity\s+\w*[Ii]_",
    check_fn_name="check_layering_violation",
    category="structure",
    recommendation="Restructure so that interface views only depend on base tables or other interface views.",
    recommendation_de="Umstrukturieren, sodass Interface-Views nur von Basistabellen oder anderen Interface-Views abhaengen.",
)

CDS_ANN_006 = ReviewRule(
    rule_id="CDS-ANN-006",
    name="Missing @EndUserText for fields without alias",
    name_de="Fehlende @EndUserText fuer Felder ohne Alias",
    description=(
        "Fields exposed without a meaningful alias and without @EndUserText "
        "annotations result in poor labels in Fiori UIs."
    ),
    description_de=(
        "Felder, die ohne aussagekraeftigen Alias und ohne @EndUserText-"
        "Annotationen exponiert werden, fuehren zu schlechten Bezeichnungen in "
        "Fiori-UIs."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"define\s+(?:root\s+)?view\s+(?:entity\s+)?",
    check_fn_name="check_missing_end_user_text",
    category="annotations",
    recommendation="Add @EndUserText.label for fields without a readable alias.",
    recommendation_de="@EndUserText.label fuer Felder ohne lesbaren Alias hinzufuegen.",
)

CDS_ANN_007 = ReviewRule(
    rule_id="CDS-ANN-007",
    name="Missing @Metadata.allowExtensions on projection view",
    name_de="Fehlende @Metadata.allowExtensions auf Projection View",
    description=(
        "Projection views should have @Metadata.allowExtensions: true so that "
        "metadata extensions can be used to separate UI annotations."
    ),
    description_de=(
        "Projection Views sollten @Metadata.allowExtensions: true besitzen, "
        "damit Metadata Extensions zur Trennung von UI-Annotationen genutzt "
        "werden koennen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"as\s+projection\s+on",
    check_fn_name="check_missing_metadata_allow_extensions",
    category="annotations",
    recommendation="Add @Metadata.allowExtensions: true to the projection view.",
    recommendation_de="@Metadata.allowExtensions: true zur Projection View hinzufuegen.",
)

CDS_ANN_008 = ReviewRule(
    rule_id="CDS-ANN-008",
    name="Composition without to-parent association",
    name_de="Composition ohne to-parent Association",
    description=(
        "A child entity that is the target of a composition should have a "
        "to-parent association back to its parent entity for RAP draft and "
        "lock handling."
    ),
    description_de=(
        "Eine Kind-Entitaet, die Ziel einer Composition ist, sollte eine "
        "to-parent Association zurueck zur Eltern-Entitaet besitzen, damit "
        "RAP-Draft- und Lock-Handling funktionieren."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"\bcomposition\b",
    check_fn_name="check_composition_without_parent",
    category="structure",
    recommendation="Add an association to parent entity in the child view.",
    recommendation_de="Eine Association zur Eltern-Entitaet in der Kind-View hinzufuegen.",
)

CDS_ANN_009 = ReviewRule(
    rule_id="CDS-ANN-009",
    name="Missing @Consumption.filter annotation on projection view",
    name_de="Fehlende @Consumption.filter Annotation auf Projection View",
    description=(
        "Projection views intended for Fiori list reports should have "
        "@Consumption.filter annotations on key filter fields to enable "
        "efficient filtering."
    ),
    description_de=(
        "Projection Views, die fuer Fiori List Reports vorgesehen sind, "
        "sollten @Consumption.filter Annotationen auf Schluesselfilterfeldern "
        "besitzen, um effizientes Filtern zu ermoeglichen."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"as\s+projection\s+on",
    check_fn_name="check_missing_consumption_filter",
    category="annotations",
    recommendation="Add @Consumption.filter annotations to relevant fields.",
    recommendation_de="@Consumption.filter Annotationen auf relevante Felder setzen.",
)

CDS_ANN_010 = ReviewRule(
    rule_id="CDS-ANN-010",
    name="Redundant annotation override",
    name_de="Redundante Annotation-Ueberschreibung",
    description=(
        "The same annotation key appears multiple times at the same level, "
        "which may indicate a copy-paste error or unintended override."
    ),
    description_de=(
        "Derselbe Annotation-Schluessel erscheint mehrfach auf derselben Ebene, "
        "was auf einen Copy-Paste-Fehler oder eine unbeabsichtigte "
        "Ueberschreibung hindeuten kann."
    ),
    artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"@\w+\.\w+",
    check_fn_name="check_redundant_annotation",
    category="annotations",
    recommendation="Remove duplicate annotations and keep only the intended one.",
    recommendation_de="Doppelte Annotationen entfernen und nur die beabsichtigte behalten.",
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_annotation_overkill_on_interface_view(code: str) -> list[tuple[str, int]]:
    """Return a match if an I_ view carries @UI annotations."""
    is_interface = re.search(
        r"define\s+(?:root\s+)?view\s+entity\s+\w*[Ii]_", code, re.IGNORECASE
    )
    has_ui = re.search(r"@UI\.\w+", code, re.IGNORECASE)

    if is_interface and has_ui:
        return [(has_ui.group(), code[: has_ui.start()].count("\n") + 1)]
    return []


def check_missing_semantics_currency_quantity(code: str) -> list[tuple[str, int]]:
    """Return a match if amount/currency/quantity fields lack @Semantics."""
    has_view = re.search(
        r"define\s+(?:root\s+)?view\s+(?:entity\s+)?", code, re.IGNORECASE
    )
    if not has_view:
        return []

    # Look for field names suggesting currency/quantity/amount/unit
    has_amount_field = re.search(
        r"\b(?:as\s+)?(?:\w*(?:amount|currency|quantity|unit(?:of)?measure)\w*)\b",
        code, re.IGNORECASE,
    )
    has_semantics = re.search(r"@Semantics\.\w+", code, re.IGNORECASE)

    if has_amount_field and not has_semantics:
        return [(has_amount_field.group(), code[: has_amount_field.start()].count("\n") + 1)]
    return []


def check_missing_object_model(code: str) -> list[tuple[str, int]]:
    """Return a match if a view entity has no @ObjectModel annotation."""
    has_view_entity = re.search(
        r"define\s+(?:root\s+)?view\s+entity", code, re.IGNORECASE
    )
    has_object_model = re.search(r"@ObjectModel\b", code, re.IGNORECASE)

    if has_view_entity and not has_object_model:
        return [(has_view_entity.group(), code[: has_view_entity.start()].count("\n") + 1)]
    return []


def check_missing_value_help(code: str) -> list[tuple[str, int]]:
    """Return a match if a projection view has ID/code fields without value help."""
    has_projection = re.search(r"as\s+projection\s+on", code, re.IGNORECASE)
    if not has_projection:
        return []

    has_id_field = re.search(
        r"\b\w*(?:Id|Code|Type|Key|Number)\s*[,\n}]", code
    )
    has_value_help = re.search(
        r"@Consumption\.valueHelpDefinition", code, re.IGNORECASE
    )

    if has_id_field and not has_value_help:
        return [(has_id_field.group().strip().rstrip(","), code[: has_id_field.start()].count("\n") + 1)]
    return []


def check_layering_violation(code: str) -> list[tuple[str, int]]:
    """Return a match if an I_ view references a C_ view."""
    is_interface = re.search(
        r"define\s+(?:root\s+)?view\s+entity\s+\w*[Ii]_", code, re.IGNORECASE
    )
    if not is_interface:
        return []

    refs_consumption = re.search(
        r"(?:from|on|projection\s+on)\s+\w*[Cc]_\w+", code, re.IGNORECASE
    )
    if refs_consumption:
        return [(refs_consumption.group(), code[: refs_consumption.start()].count("\n") + 1)]
    return []


def check_missing_end_user_text(code: str) -> list[tuple[str, int]]:
    """Return a match if fields without alias lack @EndUserText."""
    has_view = re.search(
        r"define\s+(?:root\s+)?view\s+(?:entity\s+)?", code, re.IGNORECASE
    )
    if not has_view:
        return []

    # Look for technical field names (all lowercase, no alias) in the select list
    # e.g. "  vbeln," or "  key erdat,"
    tech_fields = re.findall(
        r"^\s*(?:key\s+)?([a-z][a-z0-9_]{2,})\s*[,\n}]", code, re.MULTILINE
    )
    has_end_user_text = re.search(r"@EndUserText\b", code, re.IGNORECASE)

    if tech_fields and not has_end_user_text:
        first_match = re.search(
            r"^\s*(?:key\s+)?([a-z][a-z0-9_]{2,})\s*[,\n}]", code, re.MULTILINE
        )
        if first_match:
            return [(first_match.group(1), code[: first_match.start()].count("\n") + 1)]
    return []


def check_missing_metadata_allow_extensions(code: str) -> list[tuple[str, int]]:
    """Return a match if a projection view lacks @Metadata.allowExtensions."""
    has_projection = re.search(r"as\s+projection\s+on", code, re.IGNORECASE)
    has_metadata = re.search(r"@Metadata\.allowExtensions", code, re.IGNORECASE)

    if has_projection and not has_metadata:
        return [(has_projection.group(), code[: has_projection.start()].count("\n") + 1)]
    return []


def check_composition_without_parent(code: str) -> list[tuple[str, int]]:
    """Return a match if a composition exists but no to-parent association."""
    has_composition = re.search(r"\bcomposition\b", code, re.IGNORECASE)
    has_to_parent = re.search(
        r"\bassociation\s+to\s+parent\b", code, re.IGNORECASE
    )

    if has_composition and not has_to_parent:
        return [(has_composition.group(), code[: has_composition.start()].count("\n") + 1)]
    return []


def check_missing_consumption_filter(code: str) -> list[tuple[str, int]]:
    """Return a match if a projection view has no @Consumption.filter."""
    has_projection = re.search(r"as\s+projection\s+on", code, re.IGNORECASE)
    has_filter = re.search(r"@Consumption\.filter", code, re.IGNORECASE)

    if has_projection and not has_filter:
        return [(has_projection.group(), code[: has_projection.start()].count("\n") + 1)]
    return []


def check_redundant_annotation(code: str) -> list[tuple[str, int]]:
    """Return a match if the same annotation key appears more than once."""
    annotations = re.findall(r"(@\w+\.\w+(?:\.\w+)?)", code, re.IGNORECASE)
    if not annotations:
        return []

    seen: dict[str, int] = {}
    for ann in annotations:
        key = ann.lower()
        seen[key] = seen.get(key, 0) + 1

    for key, count in seen.items():
        if count > 1:
            # Find the second occurrence
            first_pos = code.lower().find(key)
            second_pos = code.lower().find(key, first_pos + len(key))
            if second_pos >= 0:
                line = code[:second_pos].count("\n") + 1
                return [(key, line)]
    return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CDS_ANNOTATION_RULES: tuple[ReviewRule, ...] = (
    CDS_ANN_001,
    CDS_ANN_002,
    CDS_ANN_003,
    CDS_ANN_004,
    CDS_ANN_005,
    CDS_ANN_006,
    CDS_ANN_007,
    CDS_ANN_008,
    CDS_ANN_009,
    CDS_ANN_010,
)

CDS_ANNOTATION_CHECK_FUNCTIONS: dict[str, object] = {
    "check_annotation_overkill_on_interface_view": check_annotation_overkill_on_interface_view,
    "check_missing_semantics_currency_quantity": check_missing_semantics_currency_quantity,
    "check_missing_object_model": check_missing_object_model,
    "check_missing_value_help": check_missing_value_help,
    "check_layering_violation": check_layering_violation,
    "check_missing_end_user_text": check_missing_end_user_text,
    "check_missing_metadata_allow_extensions": check_missing_metadata_allow_extensions,
    "check_composition_without_parent": check_composition_without_parent,
    "check_missing_consumption_filter": check_missing_consumption_filter,
    "check_redundant_annotation": check_redundant_annotation,
}
