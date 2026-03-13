"""Cross-artifact consistency rules for the SAP ABAP/UI5 Review Assistant.

Detects inconsistencies between multiple SAP artifacts when reviewed together
in a change package (e.g., CDS view + Behavior Definition + UI5 controller).

Each rule is a frozen ``CrossArtifactRule`` dataclass with bilingual metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.engines.multi_artifact_handler import ArtifactSection
from app.models.enums import Language, Severity
from app.models.schemas import Finding


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrossArtifactRule:
    """A single cross-artifact consistency rule."""

    rule_id: str
    name: str
    name_de: str
    description: str
    description_de: str
    source_artifact_types: tuple[str, ...]  # artifact types that trigger this rule
    target_artifact_types: tuple[str, ...]  # artifact types to check against
    default_severity: str
    check_fn_name: str
    recommendation: str
    recommendation_de: str
    category: str = "cross_artifact_consistency"


# ---------------------------------------------------------------------------
# XART rules
# ---------------------------------------------------------------------------

XART_001 = CrossArtifactRule(
    rule_id="XART-001",
    name="CDS field added but not exposed in Behavior Definition",
    name_de="CDS-Feld hinzugefuegt aber nicht in Behavior Definition exponiert",
    description=(
        "A field defined in the CDS view entity is not referenced or mapped "
        "in the corresponding Behavior Definition, which may indicate an "
        "incomplete change package."
    ),
    description_de=(
        "Ein in der CDS-View-Entity definiertes Feld wird in der zugehoerigen "
        "Behavior Definition nicht referenziert oder gemappt, was auf ein "
        "unvollstaendiges Aenderungspaket hindeuten kann."
    ),
    source_artifact_types=("CDS_VIEW", "CDS_PROJECTION"),
    target_artifact_types=("BEHAVIOR_DEFINITION",),
    default_severity="IMPORTANT",
    check_fn_name="check_cds_field_not_in_bdef",
    recommendation=(
        "Ensure new CDS fields are reflected in the Behavior Definition "
        "(e.g., field mapping, use in validations or determinations)."
    ),
    recommendation_de=(
        "Sicherstellen, dass neue CDS-Felder in der Behavior Definition "
        "beruecksichtigt werden (z.B. Feld-Mapping, Verwendung in Validierungen "
        "oder Determinations)."
    ),
)

XART_002 = CrossArtifactRule(
    rule_id="XART-002",
    name="Action defined in BDEF but no UI annotation for it",
    name_de="Action in BDEF definiert aber keine UI-Annotation dafuer",
    description=(
        "An action is defined in the Behavior Definition but the CDS projection "
        "or annotation layer does not contain a corresponding @UI.lineItem or "
        "@UI.identification annotation with type #FOR_ACTION, so the action "
        "will not be visible in the Fiori UI."
    ),
    description_de=(
        "Eine Action ist in der Behavior Definition definiert, aber die CDS-Projection "
        "oder Annotation-Schicht enthaelt keine entsprechende @UI.lineItem- oder "
        "@UI.identification-Annotation mit type #FOR_ACTION, sodass die Action "
        "in der Fiori-UI nicht sichtbar sein wird."
    ),
    source_artifact_types=("BEHAVIOR_DEFINITION",),
    target_artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION"),
    default_severity="IMPORTANT",
    check_fn_name="check_bdef_action_no_ui_annotation",
    recommendation=(
        "Add @UI.lineItem or @UI.identification annotation with type: "
        "#FOR_ACTION for the action in the CDS projection or annotation layer."
    ),
    recommendation_de=(
        "@UI.lineItem- oder @UI.identification-Annotation mit type: "
        "#FOR_ACTION fuer die Action in der CDS-Projection oder Annotation-Schicht "
        "hinzufuegen."
    ),
)

XART_003 = CrossArtifactRule(
    rule_id="XART-003",
    name="UI5 binding path references non-existent OData property",
    name_de="UI5-Binding-Pfad referenziert nicht-existente OData-Eigenschaft",
    description=(
        "A UI5 view or controller binds to a property path that does not appear "
        "as a field in any CDS view entity or service definition in the change "
        "package, indicating a potential binding mismatch."
    ),
    description_de=(
        "Eine UI5-View oder ein Controller bindet an einen Eigenschaftspfad, der "
        "in keiner CDS-View-Entity oder Service-Definition im Aenderungspaket als "
        "Feld erscheint, was auf einen moeglichen Binding-Fehler hinweist."
    ),
    source_artifact_types=("UI5_VIEW", "UI5_CONTROLLER", "UI5_FRAGMENT"),
    target_artifact_types=("CDS_VIEW", "CDS_PROJECTION", "SERVICE_DEFINITION"),
    default_severity="CRITICAL",
    check_fn_name="check_ui5_binding_not_in_cds",
    recommendation=(
        "Verify that all UI5 binding paths correspond to fields exposed in "
        "the CDS view or service definition."
    ),
    recommendation_de=(
        "Sicherstellen, dass alle UI5-Binding-Pfade den in der CDS-View oder "
        "Service-Definition exponierten Feldern entsprechen."
    ),
)

XART_004 = CrossArtifactRule(
    rule_id="XART-004",
    name="CDS association added but not exposed in service definition",
    name_de="CDS-Assoziation hinzugefuegt aber nicht in Service-Definition exponiert",
    description=(
        "An association is defined in a CDS view entity but the service "
        "definition in the change package does not expose the associated entity, "
        "meaning the association cannot be navigated via OData."
    ),
    description_de=(
        "Eine Assoziation ist in einer CDS-View-Entity definiert, aber die "
        "Service-Definition im Aenderungspaket exponiert die assoziierte "
        "Entitaet nicht, sodass die Assoziation nicht per OData navigiert "
        "werden kann."
    ),
    source_artifact_types=("CDS_VIEW", "CDS_PROJECTION"),
    target_artifact_types=("SERVICE_DEFINITION",),
    default_severity="IMPORTANT",
    check_fn_name="check_cds_association_not_in_service",
    recommendation=(
        "Add an 'expose' statement for the associated entity in the service "
        "definition."
    ),
    recommendation_de=(
        "Ein 'expose'-Statement fuer die assoziierte Entitaet in der "
        "Service-Definition hinzufuegen."
    ),
)

XART_005 = CrossArtifactRule(
    rule_id="XART-005",
    name="Authorization changed in BDEF but UI feature control not updated",
    name_de="Autorisierung in BDEF geaendert aber UI Feature Control nicht aktualisiert",
    description=(
        "The Behavior Definition contains authorization master changes but "
        "there is no corresponding UI5 feature control or dynamic visibility "
        "update, which may leave the UI inconsistent with backend permissions."
    ),
    description_de=(
        "Die Behavior Definition enthaelt Aenderungen an authorization master, "
        "aber es gibt kein entsprechendes UI5 Feature Control oder dynamisches "
        "Sichtbarkeits-Update, was die UI inkonsistent mit den Backend-"
        "Berechtigungen lassen koennte."
    ),
    source_artifact_types=("BEHAVIOR_DEFINITION",),
    target_artifact_types=("UI5_VIEW", "UI5_CONTROLLER", "CDS_PROJECTION", "CDS_ANNOTATION"),
    default_severity="IMPORTANT",
    check_fn_name="check_bdef_auth_no_ui_feature_control",
    recommendation=(
        "Update the UI layer to reflect authorization changes, e.g., via "
        "dynamic feature control or @UI.hidden annotations."
    ),
    recommendation_de=(
        "Die UI-Schicht aktualisieren, um Autorisierungsaenderungen widerzuspiegeln, "
        "z.B. ueber dynamisches Feature Control oder @UI.hidden-Annotationen."
    ),
)

XART_006 = CrossArtifactRule(
    rule_id="XART-006",
    name="Draft table defined in BDEF but no draft actions exposed",
    name_de="Draft-Tabelle in BDEF definiert aber keine Draft-Aktionen exponiert",
    description=(
        "The Behavior Definition declares 'with draft' or a draft table but "
        "does not include draft determine action or draft prepare action, "
        "which are required for a working draft scenario."
    ),
    description_de=(
        "Die Behavior Definition deklariert 'with draft' oder eine Draft-Tabelle, "
        "enthaelt aber keine draft determine action oder draft prepare action, "
        "die fuer ein funktionierendes Draft-Szenario erforderlich sind."
    ),
    source_artifact_types=("BEHAVIOR_DEFINITION",),
    target_artifact_types=("BEHAVIOR_DEFINITION",),
    default_severity="CRITICAL",
    check_fn_name="check_draft_table_no_draft_actions",
    recommendation=(
        "Add 'draft determine action Prepare;' and other required draft "
        "actions to the Behavior Definition."
    ),
    recommendation_de=(
        "'draft determine action Prepare;' und andere erforderliche Draft-"
        "Aktionen zur Behavior Definition hinzufuegen."
    ),
)

XART_007 = CrossArtifactRule(
    rule_id="XART-007",
    name="Value help CDS view referenced but not in change package",
    name_de="Wertehilfe-CDS-View referenziert aber nicht im Aenderungspaket",
    description=(
        "A @Consumption.valueHelpDefinition annotation references an entity "
        "that is not present in the change package. While the entity may exist "
        "in the system, any changes to it should be reviewed together."
    ),
    description_de=(
        "Eine @Consumption.valueHelpDefinition-Annotation referenziert eine "
        "Entitaet, die nicht im Aenderungspaket enthalten ist. Obwohl die "
        "Entitaet im System existieren kann, sollten Aenderungen daran "
        "gemeinsam reviewed werden."
    ),
    source_artifact_types=("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION"),
    target_artifact_types=("CDS_VIEW", "CDS_PROJECTION"),
    default_severity="OPTIONAL",
    check_fn_name="check_value_help_not_in_package",
    recommendation=(
        "Include the referenced value help entity in the change package for "
        "a complete review, or confirm it is unchanged."
    ),
    recommendation_de=(
        "Die referenzierte Wertehilfe-Entitaet im Aenderungspaket einschliessen "
        "fuer ein vollstaendiges Review, oder bestaetigen, dass sie unveraendert ist."
    ),
)

XART_008 = CrossArtifactRule(
    rule_id="XART-008",
    name="CDS field type changed but UI formatter not updated",
    name_de="CDS-Feldtyp geaendert aber UI-Formatter nicht aktualisiert",
    description=(
        "A CDS field uses a specific data type (e.g., abap.curr, abap.dats) "
        "but the corresponding UI5 binding does not include an appropriate "
        "formatter or type constraint, which may cause display issues."
    ),
    description_de=(
        "Ein CDS-Feld verwendet einen spezifischen Datentyp (z.B. abap.curr, "
        "abap.dats), aber das entsprechende UI5-Binding enthaelt keinen "
        "passenden Formatter oder Type-Constraint, was zu Anzeigeproblemen "
        "fuehren kann."
    ),
    source_artifact_types=("CDS_VIEW", "CDS_PROJECTION"),
    target_artifact_types=("UI5_VIEW", "UI5_CONTROLLER", "UI5_FRAGMENT"),
    default_severity="OPTIONAL",
    check_fn_name="check_cds_type_no_ui_formatter",
    recommendation=(
        "Add appropriate UI5 type or formatter for the CDS field type "
        "(e.g., sap.ui.model.type.Currency for abap.curr)."
    ),
    recommendation_de=(
        "Passenden UI5-Type oder Formatter fuer den CDS-Feldtyp hinzufuegen "
        "(z.B. sap.ui.model.type.Currency fuer abap.curr)."
    ),
)

XART_009 = CrossArtifactRule(
    rule_id="XART-009",
    name="BDEF validation added but no ABAP implementation method",
    name_de="BDEF-Validation hinzugefuegt aber keine ABAP-Implementierungsmethode",
    description=(
        "A validation is defined in the Behavior Definition but the ABAP "
        "implementation class in the change package does not contain a "
        "corresponding METHOD ... FOR VALIDATE, meaning the validation "
        "will fail at runtime."
    ),
    description_de=(
        "Eine Validation ist in der Behavior Definition definiert, aber die "
        "ABAP-Implementierungsklasse im Aenderungspaket enthaelt keine "
        "entsprechende METHOD ... FOR VALIDATE, was bedeutet, dass die "
        "Validation zur Laufzeit fehlschlaegt."
    ),
    source_artifact_types=("BEHAVIOR_DEFINITION",),
    target_artifact_types=("ABAP_CLASS", "BEHAVIOR_IMPLEMENTATION"),
    default_severity="CRITICAL",
    check_fn_name="check_bdef_validation_no_abap_impl",
    recommendation=(
        "Add a METHOD <validation_name> FOR VALIDATE in the behavior "
        "implementation class."
    ),
    recommendation_de=(
        "Eine METHOD <validation_name> FOR VALIDATE in der Behavior-"
        "Implementierungsklasse hinzufuegen."
    ),
)

XART_010 = CrossArtifactRule(
    rule_id="XART-010",
    name="Service definition exposes entity not in CDS model",
    name_de="Service-Definition exponiert Entitaet die nicht im CDS-Modell ist",
    description=(
        "The service definition contains an 'expose' statement for an entity "
        "name that does not appear in any CDS view entity definition in the "
        "change package, indicating a possible typo or missing artifact."
    ),
    description_de=(
        "Die Service-Definition enthaelt ein 'expose'-Statement fuer einen "
        "Entitaetsnamen, der in keiner CDS-View-Entity-Definition im "
        "Aenderungspaket erscheint, was auf einen moeglichen Tippfehler "
        "oder ein fehlendes Artefakt hinweist."
    ),
    source_artifact_types=("SERVICE_DEFINITION",),
    target_artifact_types=("CDS_VIEW", "CDS_PROJECTION"),
    default_severity="CRITICAL",
    check_fn_name="check_service_exposes_unknown_entity",
    recommendation=(
        "Verify that all exposed entity names match CDS view entity definitions, "
        "or include the missing CDS artifacts in the change package."
    ),
    recommendation_de=(
        "Sicherstellen, dass alle exponierten Entitaetsnamen mit CDS-View-Entity-"
        "Definitionen uebereinstimmen, oder die fehlenden CDS-Artefakte im "
        "Aenderungspaket einschliessen."
    ),
)


# ---------------------------------------------------------------------------
# Check functions — each receives a list of ArtifactSection objects
# ---------------------------------------------------------------------------


def _get_sections_by_types(
    sections: list[ArtifactSection],
    artifact_types: tuple[str, ...],
) -> list[ArtifactSection]:
    """Filter sections matching any of the given artifact type values."""
    return [s for s in sections if s.artifact_type.value in artifact_types]


def _extract_cds_fields(code: str) -> set[str]:
    """Extract field names/aliases from a CDS view entity definition."""
    fields: set[str] = set()
    # Match "fieldname as Alias" or just "fieldname" in select list
    # Look inside the { ... } block
    block_match = re.search(r"\{(.*?)\}", code, re.DOTALL)
    if not block_match:
        return fields
    block = block_match.group(1)
    for line in block.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.startswith("//") or line.startswith("*"):
            continue
        # "key field as Alias" or "field as Alias" or just "field"
        m = re.match(
            r"(?:key\s+)?(?:\w+\.)?(\w+)\s+as\s+(\w+)",
            line, re.IGNORECASE,
        )
        if m:
            fields.add(m.group(1).lower())
            fields.add(m.group(2).lower())
        else:
            # Simple field reference like "key order_id,"
            m2 = re.match(r"(?:key\s+)?(?:\w+\.)?(\w+)", line, re.IGNORECASE)
            if m2:
                token = m2.group(1).lower()
                # Skip association references
                if token not in ("association", "composition", "_"):
                    fields.add(token)
    return fields


def _extract_cds_entity_names(sections: list[ArtifactSection]) -> set[str]:
    """Extract all CDS view entity names from given sections."""
    names: set[str] = set()
    for s in sections:
        m = re.search(
            r"\bdefine\s+(?:root\s+)?view\s+entity\s+(\w+)",
            s.code, re.IGNORECASE,
        )
        if m:
            names.add(m.group(1).lower())
        # Also match projection syntax
        m2 = re.search(
            r"\bdefine\s+(?:root\s+)?view\s+entity\s+(\w+)\s+as\s+projection",
            s.code, re.IGNORECASE,
        )
        if m2:
            names.add(m2.group(1).lower())
    return names


def _extract_bdef_actions(code: str) -> set[str]:
    """Extract action names from a Behavior Definition."""
    actions: set[str] = set()
    for m in re.finditer(r"\baction\s+(\w+)", code, re.IGNORECASE):
        actions.add(m.group(1).lower())
    return actions


def _extract_bdef_validations(code: str) -> set[str]:
    """Extract validation names from a Behavior Definition."""
    validations: set[str] = set()
    for m in re.finditer(r"\bvalidation\s+(\w+)", code, re.IGNORECASE):
        validations.add(m.group(1).lower())
    return validations


def _extract_associations(code: str) -> set[str]:
    """Extract association target entity names from CDS code."""
    assocs: set[str] = set()
    for m in re.finditer(
        r"(?:association|composition)\s+\[.*?\]\s+of\s+(\w+)",
        code, re.IGNORECASE,
    ):
        assocs.add(m.group(1).lower())
    return assocs


def _extract_ui5_binding_paths(code: str) -> set[str]:
    """Extract property binding paths from UI5 view/controller code."""
    paths: set[str] = set()
    # XML binding: {PropertyName} or {path: 'PropertyName'} or {/PropertyName}
    for m in re.finditer(r"\{(?:path\s*:\s*['\"])?/?(\w+)['\"]?\}", code):
        path = m.group(1)
        # Filter out common non-property tokens
        if path.lower() not in (
            "parts", "formatter", "type", "constraints", "model",
            "i18n", "view", "device", "this", "true", "false",
            "sap", "mvc", "core", "m", "f", "table", "layout",
        ):
            paths.add(path.lower())
    return paths


def _extract_exposed_entities(code: str) -> set[str]:
    """Extract entity names from service definition expose statements."""
    entities: set[str] = set()
    for m in re.finditer(r"\bexpose\s+(\w+)", code, re.IGNORECASE):
        entities.add(m.group(1).lower())
    return entities


def _extract_value_help_entities(code: str) -> set[str]:
    """Extract entity names from @Consumption.valueHelpDefinition annotations."""
    entities: set[str] = set()
    for m in re.finditer(
        r"@Consumption\.valueHelpDefinition\s*:\s*\[\s*\{[^}]*entity\s*:\s*\{[^}]*name\s*:\s*['\"](\w+)['\"]",
        code, re.IGNORECASE,
    ):
        entities.add(m.group(1).lower())
    # Simpler pattern: entity.name: 'ZI_Something'
    for m in re.finditer(
        r"valueHelpDefinition.*?name\s*:\s*['\"](\w+)['\"]",
        code, re.IGNORECASE | re.DOTALL,
    ):
        entities.add(m.group(1).lower())
    return entities


# ---------------------------------------------------------------------------
# Check function implementations
# ---------------------------------------------------------------------------


def check_cds_field_not_in_bdef(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-001: CDS field added but not in BDEF."""
    cds_sections = _get_sections_by_types(sections, ("CDS_VIEW", "CDS_PROJECTION"))
    bdef_sections = _get_sections_by_types(sections, ("BEHAVIOR_DEFINITION",))
    if not cds_sections or not bdef_sections:
        return []

    # Collect CDS fields
    all_cds_fields: set[str] = set()
    for s in cds_sections:
        all_cds_fields |= _extract_cds_fields(s.code)

    # Collect all text from BDEF for simple reference check
    bdef_text = " ".join(s.code.lower() for s in bdef_sections)

    # Find fields not mentioned anywhere in BDEF
    unreferenced = {f for f in all_cds_fields if f not in bdef_text}

    # Only report if there are fields genuinely missing (ignore key fields and common ones)
    # and the BDEF has field-level constructs (mapping, validation, determination)
    has_field_constructs = bool(re.search(
        r"\b(?:mapping|field|validation|determination)\b", bdef_text, re.IGNORECASE
    ))

    if unreferenced and has_field_constructs and len(unreferenced) <= len(all_cds_fields):
        # Only flag if a meaningful portion of fields are unreferenced
        findings = []
        is_de = language == Language.DE
        rule = XART_001
        for field_name in sorted(unreferenced)[:3]:  # Limit to top 3
            findings.append(Finding(
                severity=Severity(rule.default_severity),
                title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
                observation=(
                    f"Field '{field_name}' found in CDS but not referenced in "
                    f"Behavior Definition."
                    if not is_de else
                    f"Feld '{field_name}' in CDS gefunden aber nicht in der "
                    f"Behavior Definition referenziert."
                ),
                reasoning=rule.description_de if is_de else rule.description,
                impact="Category: cross_artifact_consistency",
                recommendation=rule.recommendation_de if is_de else rule.recommendation,
                rule_id=rule.rule_id,
                artifact_reference=", ".join(
                    s.artifact_name for s in cds_sections + bdef_sections
                ),
            ))
        return findings
    return []


def check_bdef_action_no_ui_annotation(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-002: Action in BDEF but no UI annotation."""
    bdef_sections = _get_sections_by_types(sections, ("BEHAVIOR_DEFINITION",))
    cds_sections = _get_sections_by_types(
        sections, ("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION")
    )
    if not bdef_sections or not cds_sections:
        return []

    # Extract actions from BDEF
    all_actions: set[str] = set()
    for s in bdef_sections:
        all_actions |= _extract_bdef_actions(s.code)

    if not all_actions:
        return []

    # Check CDS for #FOR_ACTION annotations
    cds_text = " ".join(s.code.lower() for s in cds_sections)

    findings = []
    is_de = language == Language.DE
    rule = XART_002

    for action_name in sorted(all_actions):
        # Check if action is referenced in UI annotations
        # Matches patterns like: #FOR_ACTION, dataAction: 'confirmOrder'
        # or: type: #FOR_ACTION ... confirmOrder
        has_annotation = bool(re.search(
            r"#for_action.*?" + re.escape(action_name),
            cds_text, re.IGNORECASE,
        )) or bool(re.search(
            r"dataaction\s*:\s*['\"]?" + re.escape(action_name),
            cds_text, re.IGNORECASE,
        ))
        if not has_annotation:
            findings.append(Finding(
                severity=Severity(rule.default_severity),
                title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
                observation=(
                    f"Action '{action_name}' defined in Behavior Definition but no "
                    f"@UI annotation with #FOR_ACTION found in CDS artifacts."
                    if not is_de else
                    f"Action '{action_name}' in Behavior Definition definiert aber keine "
                    f"@UI-Annotation mit #FOR_ACTION in CDS-Artefakten gefunden."
                ),
                reasoning=rule.description_de if is_de else rule.description,
                impact="Category: cross_artifact_consistency",
                recommendation=rule.recommendation_de if is_de else rule.recommendation,
                rule_id=rule.rule_id,
                artifact_reference=", ".join(
                    s.artifact_name for s in bdef_sections + cds_sections
                ),
            ))
    return findings


def check_ui5_binding_not_in_cds(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-003: UI5 binding path not in CDS."""
    ui5_sections = _get_sections_by_types(
        sections, ("UI5_VIEW", "UI5_CONTROLLER", "UI5_FRAGMENT")
    )
    cds_sections = _get_sections_by_types(
        sections, ("CDS_VIEW", "CDS_PROJECTION", "SERVICE_DEFINITION")
    )
    if not ui5_sections or not cds_sections:
        return []

    # Collect all CDS fields and entity text
    all_cds_fields: set[str] = set()
    cds_text_lower = ""
    for s in cds_sections:
        all_cds_fields |= _extract_cds_fields(s.code)
        cds_text_lower += " " + s.code.lower()

    # Extract UI5 bindings
    all_bindings: set[str] = set()
    for s in ui5_sections:
        all_bindings |= _extract_ui5_binding_paths(s.code)

    if not all_bindings or not all_cds_fields:
        return []

    # Find bindings not in CDS fields
    missing = {b for b in all_bindings if b not in all_cds_fields and b not in cds_text_lower}

    findings = []
    is_de = language == Language.DE
    rule = XART_003

    for binding in sorted(missing)[:5]:  # Limit to top 5
        findings.append(Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                f"UI5 binding path '{binding}' not found in any CDS artifact "
                f"in the change package."
                if not is_de else
                f"UI5-Binding-Pfad '{binding}' in keinem CDS-Artefakt im "
                f"Aenderungspaket gefunden."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(
                s.artifact_name for s in ui5_sections + cds_sections
            ),
        ))
    return findings


def check_cds_association_not_in_service(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-004: CDS association not exposed in service definition."""
    cds_sections = _get_sections_by_types(sections, ("CDS_VIEW", "CDS_PROJECTION"))
    svc_sections = _get_sections_by_types(sections, ("SERVICE_DEFINITION",))
    if not cds_sections or not svc_sections:
        return []

    # Extract associations from CDS
    all_assocs: set[str] = set()
    for s in cds_sections:
        all_assocs |= _extract_associations(s.code)

    if not all_assocs:
        return []

    # Extract exposed entities from service
    all_exposed: set[str] = set()
    for s in svc_sections:
        all_exposed |= _extract_exposed_entities(s.code)

    # Find associations whose target is not exposed
    missing = {a for a in all_assocs if a not in all_exposed}

    findings = []
    is_de = language == Language.DE
    rule = XART_004

    for assoc_target in sorted(missing):
        findings.append(Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                f"Association target entity '{assoc_target}' in CDS is not "
                f"exposed in the service definition."
                if not is_de else
                f"Assoziationsziel-Entitaet '{assoc_target}' in CDS wird nicht "
                f"in der Service-Definition exponiert."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(
                s.artifact_name for s in cds_sections + svc_sections
            ),
        ))
    return findings


def check_bdef_auth_no_ui_feature_control(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-005: Auth changed in BDEF but UI not updated."""
    bdef_sections = _get_sections_by_types(sections, ("BEHAVIOR_DEFINITION",))
    ui_sections = _get_sections_by_types(
        sections,
        ("UI5_VIEW", "UI5_CONTROLLER", "CDS_PROJECTION", "CDS_ANNOTATION"),
    )
    if not bdef_sections or not ui_sections:
        return []

    # Check if BDEF has authorization master
    bdef_text = " ".join(s.code for s in bdef_sections)
    has_auth = bool(re.search(
        r"\bauthorization\s+master\b", bdef_text, re.IGNORECASE
    ))
    if not has_auth:
        return []

    # Check if any UI artifact references feature control
    ui_text = " ".join(s.code for s in ui_sections)
    has_feature_control = bool(re.search(
        r"(?:feature.?control|visible\s*=|enabled\s*=|@UI\.hidden|"
        r"operationAvailable|insertRestrictions|updateRestrictions|"
        r"deleteRestrictions)",
        ui_text, re.IGNORECASE,
    ))

    if not has_feature_control:
        is_de = language == Language.DE
        rule = XART_005
        return [Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                "Behavior Definition contains authorization master but no "
                "feature control or visibility handling found in UI artifacts."
                if not is_de else
                "Behavior Definition enthaelt authorization master aber kein "
                "Feature Control oder Sichtbarkeitshandling in UI-Artefakten gefunden."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(
                s.artifact_name for s in bdef_sections + ui_sections
            ),
        )]
    return []


def check_draft_table_no_draft_actions(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-006: Draft table defined but no draft actions."""
    bdef_sections = _get_sections_by_types(sections, ("BEHAVIOR_DEFINITION",))
    if not bdef_sections:
        return []

    bdef_text = " ".join(s.code for s in bdef_sections)

    has_draft = bool(re.search(
        r"\b(?:with\s+draft|draft\s+table)\b", bdef_text, re.IGNORECASE
    ))
    if not has_draft:
        return []

    has_draft_determine = bool(re.search(
        r"\bdraft\s+(?:determine\s+action|action\s+\w+)", bdef_text, re.IGNORECASE
    ))

    if not has_draft_determine:
        is_de = language == Language.DE
        rule = XART_006
        return [Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                "Behavior Definition declares draft table / 'with draft' but "
                "no draft determine action or draft prepare action found."
                if not is_de else
                "Behavior Definition deklariert Draft-Tabelle / 'with draft' aber "
                "keine draft determine action oder draft prepare action gefunden."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(s.artifact_name for s in bdef_sections),
        )]
    return []


def check_value_help_not_in_package(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-007: Value help entity not in change package."""
    cds_source = _get_sections_by_types(
        sections, ("CDS_VIEW", "CDS_PROJECTION", "CDS_ANNOTATION")
    )
    if not cds_source:
        return []

    # All CDS entity names in the package
    all_entity_names = _extract_cds_entity_names(sections)

    # Value help entity references
    vh_entities: set[str] = set()
    for s in cds_source:
        vh_entities |= _extract_value_help_entities(s.code)

    if not vh_entities:
        return []

    # Find value help entities not in package
    missing = {e for e in vh_entities if e not in all_entity_names}

    findings = []
    is_de = language == Language.DE
    rule = XART_007

    for entity in sorted(missing):
        findings.append(Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                f"Value help entity '{entity}' referenced in annotation but "
                f"not included in the change package."
                if not is_de else
                f"Wertehilfe-Entitaet '{entity}' in Annotation referenziert aber "
                f"nicht im Aenderungspaket enthalten."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(s.artifact_name for s in cds_source),
        ))
    return findings


def check_cds_type_no_ui_formatter(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-008: CDS field type changed but UI formatter not updated."""
    cds_sections = _get_sections_by_types(sections, ("CDS_VIEW", "CDS_PROJECTION"))
    ui5_sections = _get_sections_by_types(
        sections, ("UI5_VIEW", "UI5_CONTROLLER", "UI5_FRAGMENT")
    )
    if not cds_sections or not ui5_sections:
        return []

    # Check for typed fields in CDS (abap.curr, abap.dats, abap.tims, abap.dec)
    typed_fields: list[tuple[str, str]] = []  # (field_name, type)
    type_pattern = re.compile(
        r"(\w+)\s*:\s*(abap\.(?:curr|dats|tims|dec|quan|unit))",
        re.IGNORECASE,
    )
    for s in cds_sections:
        for m in type_pattern.finditer(s.code):
            typed_fields.append((m.group(1).lower(), m.group(2).lower()))

    if not typed_fields:
        return []

    # Check if UI5 has formatters or type constraints
    ui5_text = " ".join(s.code for s in ui5_sections)

    findings = []
    is_de = language == Language.DE
    rule = XART_008

    for field_name, field_type in typed_fields:
        # Check if field is referenced in UI5 with any formatter/type
        # Use DOTALL to match across lines (formatter/type may be on different line)
        has_formatter = bool(re.search(
            r"(?:formatter|type\s*:).*?" + re.escape(field_name),
            ui5_text, re.IGNORECASE | re.DOTALL,
        )) or bool(re.search(
            re.escape(field_name) + r".*?(?:formatter|type\s*:)",
            ui5_text, re.IGNORECASE | re.DOTALL,
        ))
        if not has_formatter:
            findings.append(Finding(
                severity=Severity(rule.default_severity),
                title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
                observation=(
                    f"CDS field '{field_name}' has type '{field_type}' but no "
                    f"corresponding UI5 formatter or type constraint found."
                    if not is_de else
                    f"CDS-Feld '{field_name}' hat Typ '{field_type}' aber kein "
                    f"entsprechender UI5-Formatter oder Type-Constraint gefunden."
                ),
                reasoning=rule.description_de if is_de else rule.description,
                impact="Category: cross_artifact_consistency",
                recommendation=rule.recommendation_de if is_de else rule.recommendation,
                rule_id=rule.rule_id,
                artifact_reference=", ".join(
                    s.artifact_name for s in cds_sections + ui5_sections
                ),
            ))
    return findings[:3]  # Limit output


def check_bdef_validation_no_abap_impl(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-009: BDEF validation without ABAP implementation."""
    bdef_sections = _get_sections_by_types(sections, ("BEHAVIOR_DEFINITION",))
    abap_sections = _get_sections_by_types(
        sections, ("ABAP_CLASS", "BEHAVIOR_IMPLEMENTATION")
    )
    if not bdef_sections or not abap_sections:
        return []

    # Extract validations from BDEF
    all_validations: set[str] = set()
    for s in bdef_sections:
        all_validations |= _extract_bdef_validations(s.code)

    if not all_validations:
        return []

    # Check ABAP implementation for METHOD ... FOR VALIDATE
    abap_text = " ".join(s.code.lower() for s in abap_sections)

    findings = []
    is_de = language == Language.DE
    rule = XART_009

    for val_name in sorted(all_validations):
        has_impl = bool(re.search(
            r"\bmethod\s+" + re.escape(val_name) + r"\b",
            abap_text, re.IGNORECASE,
        ))
        if not has_impl:
            findings.append(Finding(
                severity=Severity(rule.default_severity),
                title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
                observation=(
                    f"Validation '{val_name}' defined in Behavior Definition but "
                    f"no corresponding METHOD found in ABAP implementation."
                    if not is_de else
                    f"Validation '{val_name}' in Behavior Definition definiert aber "
                    f"keine entsprechende METHOD in ABAP-Implementierung gefunden."
                ),
                reasoning=rule.description_de if is_de else rule.description,
                impact="Category: cross_artifact_consistency",
                recommendation=rule.recommendation_de if is_de else rule.recommendation,
                rule_id=rule.rule_id,
                artifact_reference=", ".join(
                    s.artifact_name for s in bdef_sections + abap_sections
                ),
            ))
    return findings


def check_service_exposes_unknown_entity(
    sections: list[ArtifactSection],
    language: Language,
) -> list[Finding]:
    """XART-010: Service definition exposes entity not in CDS model."""
    svc_sections = _get_sections_by_types(sections, ("SERVICE_DEFINITION",))
    cds_sections = _get_sections_by_types(sections, ("CDS_VIEW", "CDS_PROJECTION"))
    if not svc_sections or not cds_sections:
        return []

    # Exposed entities from service
    all_exposed: set[str] = set()
    for s in svc_sections:
        all_exposed |= _extract_exposed_entities(s.code)

    if not all_exposed:
        return []

    # CDS entity names
    all_entities = _extract_cds_entity_names(cds_sections)

    # Find exposed entities not in CDS
    missing = {e for e in all_exposed if e not in all_entities}

    findings = []
    is_de = language == Language.DE
    rule = XART_010

    for entity in sorted(missing):
        findings.append(Finding(
            severity=Severity(rule.default_severity),
            title=f"(Cross-Artifact) {rule.name_de if is_de else rule.name}",
            observation=(
                f"Service definition exposes '{entity}' but no matching CDS "
                f"view entity found in the change package."
                if not is_de else
                f"Service-Definition exponiert '{entity}' aber keine passende "
                f"CDS-View-Entity im Aenderungspaket gefunden."
            ),
            reasoning=rule.description_de if is_de else rule.description,
            impact="Category: cross_artifact_consistency",
            recommendation=rule.recommendation_de if is_de else rule.recommendation,
            rule_id=rule.rule_id,
            artifact_reference=", ".join(
                s.artifact_name for s in svc_sections + cds_sections
            ),
        ))
    return findings


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CROSS_ARTIFACT_RULES: tuple[CrossArtifactRule, ...] = (
    XART_001, XART_002, XART_003, XART_004, XART_005,
    XART_006, XART_007, XART_008, XART_009, XART_010,
)

CROSS_ARTIFACT_CHECK_FUNCTIONS: dict[str, object] = {
    "check_cds_field_not_in_bdef": check_cds_field_not_in_bdef,
    "check_bdef_action_no_ui_annotation": check_bdef_action_no_ui_annotation,
    "check_ui5_binding_not_in_cds": check_ui5_binding_not_in_cds,
    "check_cds_association_not_in_service": check_cds_association_not_in_service,
    "check_bdef_auth_no_ui_feature_control": check_bdef_auth_no_ui_feature_control,
    "check_draft_table_no_draft_actions": check_draft_table_no_draft_actions,
    "check_value_help_not_in_package": check_value_help_not_in_package,
    "check_cds_type_no_ui_formatter": check_cds_type_no_ui_formatter,
    "check_bdef_validation_no_abap_impl": check_bdef_validation_no_abap_impl,
    "check_service_exposes_unknown_entity": check_service_exposes_unknown_entity,
}
