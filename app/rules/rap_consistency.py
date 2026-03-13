"""RAP Behavior Definition consistency rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance with bilingual metadata that
detects RAP behavior definition consistency issues.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# RAP-CONS: RAP Behavior Definition consistency rules
# ---------------------------------------------------------------------------

RAP_CONS_001 = ReviewRule(
    rule_id="RAP-CONS-001",
    name="Behavior definition references non-existent entity",
    name_de="Behavior Definition referenziert nicht-existente Entitaet",
    description=(
        "The behavior definition references an entity name that does not match "
        "any define statement in the same code unit, suggesting a mismatch "
        "between BDEF and CDS view."
    ),
    description_de=(
        "Die Behavior Definition referenziert einen Entitaetsnamen, der keinem "
        "define-Statement in derselben Code-Einheit entspricht, was auf eine "
        "Diskrepanz zwischen BDEF und CDS View hindeutet."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"\bdefine\s+behavior\s+for\b",
    check_fn_name="check_bdef_entity_mismatch",
    category="consistency",
    recommendation="Ensure the entity name in the BDEF matches the CDS view entity name.",
    recommendation_de="Sicherstellen, dass der Entitaetsname in der BDEF mit dem CDS-View-Entity-Namen uebereinstimmt.",
)

RAP_CONS_002 = ReviewRule(
    rule_id="RAP-CONS-002",
    name="Action defined but no implementation class binding",
    name_de="Action definiert aber keine Implementierungsklasse gebunden",
    description=(
        "An action or determination is defined in the behavior definition but "
        "there is no implementation class binding, so the runtime cannot "
        "dispatch the action."
    ),
    description_de=(
        "Eine Action oder Determination ist in der Behavior Definition definiert, "
        "aber es gibt keine Implementierungsklassen-Bindung, sodass die Laufzeit "
        "die Action nicht dispatchen kann."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"\baction\b",
    check_fn_name="check_action_without_implementation",
    category="consistency",
    recommendation="Add an 'implementation in class <classname> unique' binding.",
    recommendation_de="Eine 'implementation in class <Klassenname> unique' Bindung hinzufuegen.",
)

RAP_CONS_003 = ReviewRule(
    rule_id="RAP-CONS-003",
    name="Validation on save without field trigger list",
    name_de="Validation on save ohne Feld-Trigger-Liste",
    description=(
        "A validation triggered on save should specify which fields trigger it "
        "to avoid unnecessary execution on every save operation."
    ),
    description_de=(
        "Eine Validation, die on save ausgeloest wird, sollte angeben, welche "
        "Felder sie triggern, um unnoetige Ausfuehrung bei jedem Speichervorgang "
        "zu vermeiden."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\bvalidation\b",
    check_fn_name="check_validation_without_trigger_fields",
    category="consistency",
    recommendation="Add 'on save { field Field1, Field2; }' to the validation definition.",
    recommendation_de="'on save { field Field1, Field2; }' zur Validation-Definition hinzufuegen.",
)

RAP_CONS_004 = ReviewRule(
    rule_id="RAP-CONS-004",
    name="Determination on wrong trigger",
    name_de="Determination mit falschem Trigger",
    description=(
        "A determination triggered on create that modifies non-key fields may "
        "indicate that it should be triggered on modify instead, to also handle "
        "updates."
    ),
    description_de=(
        "Eine Determination, die on create ausgeloest wird und Nicht-Schluessel-"
        "Felder aendert, deutet darauf hin, dass sie auf on modify getriggert "
        "werden sollte, um auch Updates zu behandeln."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\bdetermination\b",
    check_fn_name="check_determination_trigger",
    category="consistency",
    recommendation="Review whether the determination should be triggered on modify instead of create.",
    recommendation_de="Pruefen, ob die Determination auf on modify statt on create getriggert werden sollte.",
)

RAP_CONS_005 = ReviewRule(
    rule_id="RAP-CONS-005",
    name="Incomplete draft handling",
    name_de="Unvollstaendiges Draft Handling",
    description=(
        "A draft table is defined but the behavior definition is missing "
        "standard draft actions (Edit, Activate, Discard, Resume)."
    ),
    description_de=(
        "Eine Draft-Tabelle ist definiert, aber der Behavior Definition fehlen "
        "Standard-Draft-Aktionen (Edit, Activate, Discard, Resume)."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"\bdraft\s+table\b",
    check_fn_name="check_incomplete_draft",
    category="consistency",
    recommendation="Add draft actions: Edit, Activate, Discard, Resume.",
    recommendation_de="Draft-Aktionen hinzufuegen: Edit, Activate, Discard, Resume.",
)

RAP_CONS_006 = ReviewRule(
    rule_id="RAP-CONS-006",
    name="Managed implementation with unmanaged patterns",
    name_de="Managed-Implementierung mit Unmanaged-Mustern",
    description=(
        "The behavior definition uses 'managed' implementation but also "
        "contains keywords typical of unmanaged scenarios (e.g. 'with "
        "unmanaged save'), which may indicate a configuration conflict."
    ),
    description_de=(
        "Die Behavior Definition verwendet 'managed'-Implementierung, enthaelt "
        "aber auch Schluesselwoerter fuer Unmanaged-Szenarien (z.B. 'with "
        "unmanaged save'), was auf einen Konfigurationskonflikt hindeuten kann."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"\bmanaged\b",
    check_fn_name="check_managed_unmanaged_conflict",
    category="consistency",
    recommendation="Use either managed or unmanaged implementation consistently.",
    recommendation_de="Entweder managed oder unmanaged Implementierung konsistent verwenden.",
)

RAP_CONS_007 = ReviewRule(
    rule_id="RAP-CONS-007",
    name="Missing authorization master/instance",
    name_de="Fehlende authorization master/instance",
    description=(
        "A behavior definition without authorization master or authorization "
        "instance declarations cannot enforce proper access control at the "
        "RAP level."
    ),
    description_de=(
        "Eine Behavior Definition ohne authorization master oder authorization "
        "instance Deklarationen kann keine korrekte Zugriffskontrolle auf "
        "RAP-Ebene durchsetzen."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\bdefine\s+behavior\s+for\b",
    check_fn_name="check_missing_authorization",
    category="security",
    recommendation="Add 'authorization master ( instance )' or similar authorization declaration.",
    recommendation_de="'authorization master ( instance )' oder aehnliche Autorisierungsdeklaration hinzufuegen.",
)

RAP_CONS_008 = ReviewRule(
    rule_id="RAP-CONS-008",
    name="Missing feature control for conditional actions",
    name_de="Fehlende Feature Control fuer bedingte Aktionen",
    description=(
        "Actions that should only be available under certain conditions need "
        "feature control (static or instance) to be declared in the BDEF."
    ),
    description_de=(
        "Aktionen, die nur unter bestimmten Bedingungen verfuegbar sein sollen, "
        "benoetigen Feature Control (statisch oder instanzbasiert) in der BDEF."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\baction\b",
    check_fn_name="check_missing_feature_control",
    category="consistency",
    recommendation="Add instance or static feature control for conditional actions.",
    recommendation_de="Instanz- oder statische Feature Control fuer bedingte Aktionen hinzufuegen.",
)

RAP_CONS_009 = ReviewRule(
    rule_id="RAP-CONS-009",
    name="Missing side-effects annotation for actions",
    name_de="Fehlende Side-Effects-Annotation fuer Aktionen",
    description=(
        "Actions that modify data should have side-effects annotations so that "
        "the Fiori UI can refresh affected fields and associations automatically."
    ),
    description_de=(
        "Aktionen, die Daten aendern, sollten Side-Effects-Annotationen besitzen, "
        "damit die Fiori-UI betroffene Felder und Assoziationen automatisch "
        "aktualisieren kann."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\baction\b",
    check_fn_name="check_missing_side_effects",
    category="annotations",
    recommendation="Add side-effects annotations for actions that modify data.",
    recommendation_de="Side-Effects-Annotationen fuer datenveraendernde Aktionen hinzufuegen.",
)

RAP_CONS_010 = ReviewRule(
    rule_id="RAP-CONS-010",
    name="Numbering inconsistency",
    name_de="Nummerierungs-Inkonsistenz",
    description=(
        "A managed scenario with early numbering or a missing numbering "
        "declaration may cause key generation issues at runtime."
    ),
    description_de=(
        "Ein managed-Szenario mit early numbering oder einer fehlenden "
        "Nummerierungs-Deklaration kann Probleme bei der Schluesselgenerierung "
        "zur Laufzeit verursachen."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\bmanaged\b",
    check_fn_name="check_numbering_inconsistency",
    category="consistency",
    recommendation="Use 'late numbering' with managed or declare numbering explicitly.",
    recommendation_de="'late numbering' mit managed verwenden oder Nummerierung explizit deklarieren.",
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_bdef_entity_mismatch(code: str) -> list[tuple[str, int]]:
    """Return a match if BDEF references entity but no matching define view entity."""
    bdef_match = re.search(
        r"\bdefine\s+behavior\s+for\s+(\w+)", code, re.IGNORECASE
    )
    if not bdef_match:
        return []

    entity_name = bdef_match.group(1)
    # Check if there is a corresponding CDS define statement
    has_define = re.search(
        r"define\s+(?:root\s+)?view\s+entity\s+" + re.escape(entity_name),
        code, re.IGNORECASE,
    )
    # Only flag when both BDEF and CDS are in same code but entity names mismatch
    has_any_view = re.search(
        r"define\s+(?:root\s+)?view\s+entity\s+(\w+)", code, re.IGNORECASE
    )
    if has_any_view and not has_define:
        return [(bdef_match.group(), code[: bdef_match.start()].count("\n") + 1)]
    return []


def check_action_without_implementation(code: str) -> list[tuple[str, int]]:
    """Return a match if actions exist but no implementation class binding."""
    has_action = re.search(r"\baction\s+\w+", code, re.IGNORECASE)
    has_impl = re.search(r"\bimplementation\s+in\s+class\b", code, re.IGNORECASE)

    if has_action and not has_impl:
        return [(has_action.group(), code[: has_action.start()].count("\n") + 1)]
    return []


def check_validation_without_trigger_fields(code: str) -> list[tuple[str, int]]:
    """Return a match if a validation on save has no field trigger list."""
    # Find validations
    validation_match = re.search(
        r"\bvalidation\s+(\w+)\s+on\s+save\b", code, re.IGNORECASE
    )
    if not validation_match:
        return []

    # Check if there is a field list after the validation
    # Pattern: validation X on save { field ... }
    after_validation = code[validation_match.end():]
    has_field_list = re.search(r"\{\s*field\b", after_validation, re.IGNORECASE)

    if not has_field_list:
        return [(validation_match.group(), code[: validation_match.start()].count("\n") + 1)]
    return []


def check_determination_trigger(code: str) -> list[tuple[str, int]]:
    """Return a match if a determination on create modifies non-key fields."""
    det_match = re.search(
        r"\bdetermination\s+(\w+)\s+on\s+(?:save|modify)\s*\{\s*create\s*;\s*\}",
        code, re.IGNORECASE,
    )
    if not det_match:
        return []

    # Heuristic: if the determination name suggests it sets status/description/amount
    det_name = det_match.group(1).lower()
    non_key_hints = ("status", "description", "amount", "total", "text", "date", "calc")
    for hint in non_key_hints:
        if hint in det_name:
            return [(det_match.group(), code[: det_match.start()].count("\n") + 1)]
    return []


def check_incomplete_draft(code: str) -> list[tuple[str, int]]:
    """Return a match if draft table is defined but draft actions are missing."""
    has_draft_table = re.search(r"\bdraft\s+table\b", code, re.IGNORECASE)
    if not has_draft_table:
        return []

    has_draft_action = re.search(
        r"\bdraft\s+action\b", code, re.IGNORECASE
    )
    if not has_draft_action:
        return [(has_draft_table.group(), code[: has_draft_table.start()].count("\n") + 1)]
    return []


def check_managed_unmanaged_conflict(code: str) -> list[tuple[str, int]]:
    """Return a match if both managed and unmanaged keywords are present."""
    has_managed = re.search(r"\bmanaged\b(?!\s+save)", code, re.IGNORECASE)
    has_unmanaged = re.search(r"\bunmanaged\s+save\b", code, re.IGNORECASE)

    if has_managed and has_unmanaged:
        return [(has_unmanaged.group(), code[: has_unmanaged.start()].count("\n") + 1)]
    return []


def check_missing_authorization(code: str) -> list[tuple[str, int]]:
    """Return a match if a BDEF has no authorization declaration."""
    has_bdef = re.search(
        r"\bdefine\s+behavior\s+for\b", code, re.IGNORECASE
    )
    has_auth = re.search(r"\bauthorization\s+master\b", code, re.IGNORECASE)

    if has_bdef and not has_auth:
        return [(has_bdef.group(), code[: has_bdef.start()].count("\n") + 1)]
    return []


def check_missing_feature_control(code: str) -> list[tuple[str, int]]:
    """Return a match if actions exist but no feature control is declared."""
    has_action = re.search(r"\baction\s+\w+", code, re.IGNORECASE)
    has_feature_control = re.search(
        r"\b(?:instance\s+)?feature\s+control\b", code, re.IGNORECASE
    )

    if has_action and not has_feature_control:
        return [(has_action.group(), code[: has_action.start()].count("\n") + 1)]
    return []


def check_missing_side_effects(code: str) -> list[tuple[str, int]]:
    """Return a match if actions exist but no side-effects are declared."""
    has_action = re.search(r"\baction\s+\w+", code, re.IGNORECASE)
    has_side_effects = re.search(r"\bside\s*effects\b", code, re.IGNORECASE)

    if has_action and not has_side_effects:
        return [(has_action.group(), code[: has_action.start()].count("\n") + 1)]
    return []


def check_numbering_inconsistency(code: str) -> list[tuple[str, int]]:
    """Return a match if managed with early numbering or missing numbering."""
    has_managed = re.search(r"\bmanaged\b", code, re.IGNORECASE)
    if not has_managed:
        return []

    has_early = re.search(r"\bearly\s+numbering\b", code, re.IGNORECASE)
    has_any_numbering = re.search(
        r"\b(?:early|late)\s+numbering\b", code, re.IGNORECASE
    )

    # Flag if managed + early numbering (unusual combo)
    if has_early:
        return [(has_early.group(), code[: has_early.start()].count("\n") + 1)]

    # Flag if managed with no numbering declaration at all
    if not has_any_numbering:
        # Only flag if there is actually a BDEF structure (not just the word managed)
        has_bdef = re.search(r"\bdefine\s+behavior\b", code, re.IGNORECASE)
        if has_bdef:
            return [(has_managed.group(), code[: has_managed.start()].count("\n") + 1)]
    return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RAP_CONSISTENCY_RULES: tuple[ReviewRule, ...] = (
    RAP_CONS_001,
    RAP_CONS_002,
    RAP_CONS_003,
    RAP_CONS_004,
    RAP_CONS_005,
    RAP_CONS_006,
    RAP_CONS_007,
    RAP_CONS_008,
    RAP_CONS_009,
    RAP_CONS_010,
)

RAP_CONSISTENCY_CHECK_FUNCTIONS: dict[str, object] = {
    "check_bdef_entity_mismatch": check_bdef_entity_mismatch,
    "check_action_without_implementation": check_action_without_implementation,
    "check_validation_without_trigger_fields": check_validation_without_trigger_fields,
    "check_determination_trigger": check_determination_trigger,
    "check_incomplete_draft": check_incomplete_draft,
    "check_managed_unmanaged_conflict": check_managed_unmanaged_conflict,
    "check_missing_authorization": check_missing_authorization,
    "check_missing_feature_control": check_missing_feature_control,
    "check_missing_side_effects": check_missing_side_effects,
    "check_numbering_inconsistency": check_numbering_inconsistency,
}
