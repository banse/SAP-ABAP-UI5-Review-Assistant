"""Design review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance that checks solution design
documents for completeness, feasibility, and alignment with SAP best practices.

The rules use ``check_fn_name`` with custom check functions that analyse
free-form design text (not source code).
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule


# ---------------------------------------------------------------------------
# DESIGN-COMP: Design completeness rules
# ---------------------------------------------------------------------------

DESIGN_COMP_001 = ReviewRule(
    rule_id="DESIGN-COMP-001",
    name="Missing error handling strategy",
    name_de="Fehlende Fehlerbehandlungsstrategie",
    description=(
        "The solution design describes operations or processing logic but does "
        "not mention any error handling, exception management, or fallback strategy. "
        "A production-ready design must address how errors are caught, reported, "
        "and recovered from."
    ),
    description_de=(
        "Das Loesungsdesign beschreibt Operationen oder Verarbeitungslogik, erwaehnt "
        "jedoch keine Fehlerbehandlung, Ausnahmebehandlung oder Fallback-Strategie. "
        "Ein produktionsreifes Design muss beschreiben, wie Fehler abgefangen, "
        "gemeldet und behoben werden."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_error_handling",
    category="design_completeness",
    recommendation=(
        "Add an error handling section that covers exception types, retry logic, "
        "user notification, logging, and fallback behavior for each critical operation."
    ),
    recommendation_de=(
        "Einen Abschnitt zur Fehlerbehandlung ergaenzen, der Ausnahmetypen, "
        "Wiederholungslogik, Benutzerbenachrichtigung, Logging und Fallback-"
        "Verhalten fuer jede kritische Operation beschreibt."
    ),
)

DESIGN_COMP_002 = ReviewRule(
    rule_id="DESIGN-COMP-002",
    name="Missing authorization concept",
    name_de="Fehlendes Berechtigungskonzept",
    description=(
        "The solution design does not mention authorization, roles, or permissions. "
        "Every SAP application must define who can access which data and functions."
    ),
    description_de=(
        "Das Loesungsdesign erwaehnt keine Berechtigungen, Rollen oder Zugriffsrechte. "
        "Jede SAP-Anwendung muss definieren, wer auf welche Daten und Funktionen "
        "zugreifen darf."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_authorization",
    category="design_completeness",
    recommendation=(
        "Add an authorization concept section that defines roles, permission objects, "
        "access control lists, and data-level restrictions."
    ),
    recommendation_de=(
        "Einen Abschnitt zum Berechtigungskonzept ergaenzen, der Rollen, "
        "Berechtigungsobjekte, Zugriffssteuerungslisten und datenbasierte "
        "Einschraenkungen definiert."
    ),
)

DESIGN_COMP_003 = ReviewRule(
    rule_id="DESIGN-COMP-003",
    name="Missing test strategy",
    name_de="Fehlende Teststrategie",
    description=(
        "The solution design does not mention any test strategy, unit tests, "
        "integration tests, or quality assurance approach. Testability must be "
        "planned from the design phase."
    ),
    description_de=(
        "Das Loesungsdesign erwaehnt keine Teststrategie, Unit-Tests, "
        "Integrationstests oder Qualitaetssicherung. Testbarkeit muss ab der "
        "Designphase geplant werden."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_test_strategy",
    category="design_completeness",
    recommendation=(
        "Add a test strategy section covering unit tests, integration tests, "
        "end-to-end tests, test data management, and acceptance criteria."
    ),
    recommendation_de=(
        "Einen Abschnitt zur Teststrategie ergaenzen, der Unit-Tests, "
        "Integrationstests, End-to-End-Tests, Testdatenmanagement und "
        "Abnahmekriterien umfasst."
    ),
)

DESIGN_COMP_004 = ReviewRule(
    rule_id="DESIGN-COMP-004",
    name="Missing performance considerations",
    name_de="Fehlende Performance-Betrachtungen",
    description=(
        "The design mentions large data volumes or high throughput requirements "
        "but does not discuss performance strategy such as caching, pagination, "
        "indexing, or background processing."
    ),
    description_de=(
        "Das Design erwaehnt grosse Datenmengen oder hohe Durchsatzanforderungen, "
        "diskutiert jedoch keine Performance-Strategie wie Caching, Paginierung, "
        "Indizierung oder Hintergrundverarbeitung."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_performance",
    category="design_completeness",
    recommendation=(
        "Add a performance section that addresses data volume expectations, caching "
        "strategy, pagination, index design, and background processing for heavy "
        "operations."
    ),
    recommendation_de=(
        "Einen Performance-Abschnitt ergaenzen, der erwartete Datenmengen, "
        "Caching-Strategie, Paginierung, Index-Design und Hintergrundverarbeitung "
        "fuer aufwaendige Operationen behandelt."
    ),
)

DESIGN_COMP_005 = ReviewRule(
    rule_id="DESIGN-COMP-005",
    name="Missing migration/cutover plan",
    name_de="Fehlender Migrations-/Cutover-Plan",
    description=(
        "The design describes an extension or migration scenario but does not "
        "include a cutover plan, data migration strategy, or rollback approach."
    ),
    description_de=(
        "Das Design beschreibt ein Erweiterungs- oder Migrationsszenario, enthaelt "
        "aber keinen Cutover-Plan, keine Datenmigrationsstrategie oder Rollback-"
        "Vorgehensweise."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="OPTIONAL",
    pattern="",
    check_fn_name="check_design_missing_migration_plan",
    category="design_completeness",
    recommendation=(
        "Add a migration/cutover section covering data migration steps, downtime "
        "windows, rollback procedures, and validation checks."
    ),
    recommendation_de=(
        "Einen Migrations-/Cutover-Abschnitt ergaenzen, der Datenmigrationsschritte, "
        "Ausfallzeitfenster, Rollback-Verfahren und Validierungspruefungen beschreibt."
    ),
)

DESIGN_COMP_006 = ReviewRule(
    rule_id="DESIGN-COMP-006",
    name="Technology choice concern",
    name_de="Bedenken zur Technologiewahl",
    description=(
        "The design mentions OData V2 when V4 is available, classic Dynpro in new "
        "development, or other outdated technology choices that may limit the "
        "solution's future viability."
    ),
    description_de=(
        "Das Design erwaehnt OData V2 obwohl V4 verfuegbar ist, klassische Dynpros "
        "in Neuentwicklungen oder andere veraltete Technologieentscheidungen, die "
        "die Zukunftsfaehigkeit der Loesung einschraenken koennten."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="OPTIONAL",
    pattern="",
    check_fn_name="check_design_technology_concern",
    category="design_completeness",
    recommendation=(
        "Evaluate whether modern alternatives (OData V4, RAP, Fiori Elements) can "
        "replace the proposed technology. Document the rationale if legacy technology "
        "is intentionally chosen."
    ),
    recommendation_de=(
        "Pruefen, ob moderne Alternativen (OData V4, RAP, Fiori Elements) die "
        "vorgeschlagene Technologie ersetzen koennen. Begruendung dokumentieren, "
        "falls bewusst eine aeltere Technologie gewaehlt wird."
    ),
)

DESIGN_COMP_007 = ReviewRule(
    rule_id="DESIGN-COMP-007",
    name="Missing clean-core considerations",
    name_de="Fehlende Clean-Core-Betrachtungen",
    description=(
        "The design proposes custom development but does not mention clean core "
        "principles, released APIs, or upgrade safety. Custom code must be aligned "
        "with SAP clean core strategy."
    ),
    description_de=(
        "Das Design schlaegt kundenspezifische Entwicklung vor, erwaehnt aber weder "
        "Clean-Core-Prinzipien, freigegebene APIs noch Upgrade-Sicherheit. "
        "Eigenentwicklungen muessen mit der SAP Clean-Core-Strategie abgestimmt sein."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_clean_core",
    category="design_completeness",
    recommendation=(
        "Add a clean core section that explains which released APIs will be used, "
        "how custom code stays within the ABAP Cloud boundaries, and how upgrade "
        "safety is ensured."
    ),
    recommendation_de=(
        "Einen Clean-Core-Abschnitt ergaenzen, der erklaert, welche freigegebenen "
        "APIs verwendet werden, wie Eigenentwicklungen innerhalb der ABAP-Cloud-"
        "Grenzen bleiben und wie Upgrade-Sicherheit gewaehrleistet wird."
    ),
)

DESIGN_COMP_008 = ReviewRule(
    rule_id="DESIGN-COMP-008",
    name="Missing integration point documentation",
    name_de="Fehlende Dokumentation der Integrationspunkte",
    description=(
        "The design mentions integration or interfaces with other systems but does "
        "not specify protocols, data formats, authentication, or error handling for "
        "those integration points."
    ),
    description_de=(
        "Das Design erwaehnt Integration oder Schnittstellen zu anderen Systemen, "
        "spezifiziert aber keine Protokolle, Datenformate, Authentifizierung oder "
        "Fehlerbehandlung fuer diese Integrationspunkte."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="IMPORTANT",
    pattern="",
    check_fn_name="check_design_missing_integration_docs",
    category="design_completeness",
    recommendation=(
        "For each integration point, document the protocol (OData, RFC, REST, IDoc), "
        "data format, authentication method, error handling, and retry strategy."
    ),
    recommendation_de=(
        "Fuer jeden Integrationspunkt Protokoll (OData, RFC, REST, IDoc), Datenformat, "
        "Authentifizierungsmethode, Fehlerbehandlung und Wiederholungsstrategie "
        "dokumentieren."
    ),
)

DESIGN_COMP_009 = ReviewRule(
    rule_id="DESIGN-COMP-009",
    name="Incomplete entity model",
    name_de="Unvollstaendiges Entitaetsmodell",
    description=(
        "Entities are mentioned by name in the design but are not fully specified "
        "with fields, data types, relationships, or cardinalities."
    ),
    description_de=(
        "Entitaeten werden im Design namentlich erwaehnt, aber nicht vollstaendig "
        "mit Feldern, Datentypen, Beziehungen oder Kardinalitaeten spezifiziert."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="OPTIONAL",
    pattern="",
    check_fn_name="check_design_incomplete_entity_model",
    category="design_completeness",
    recommendation=(
        "Define each entity with its key fields, attributes, data types, "
        "associations, compositions, and cardinalities."
    ),
    recommendation_de=(
        "Jede Entitaet mit Schluesselfeldern, Attributen, Datentypen, "
        "Assoziationen, Kompositionen und Kardinalitaeten definieren."
    ),
)

DESIGN_COMP_010 = ReviewRule(
    rule_id="DESIGN-COMP-010",
    name="Missing UI pattern justification",
    name_de="Fehlende Begruendung des UI-Patterns",
    description=(
        "The design mentions a UI or Fiori application but does not justify the "
        "chosen UI pattern (list report, object page, overview page, freestyle) "
        "or explain why it fits the use case."
    ),
    description_de=(
        "Das Design erwaehnt eine UI- oder Fiori-Anwendung, begruendet aber nicht "
        "das gewaehlte UI-Pattern (List Report, Object Page, Overview Page, "
        "Freestyle) oder warum es zum Anwendungsfall passt."
    ),
    artifact_types=("SOLUTION_DESIGN",),
    default_severity="OPTIONAL",
    pattern="",
    check_fn_name="check_design_missing_ui_pattern_justification",
    category="design_completeness",
    recommendation=(
        "Document which Fiori floorplan or UI pattern is chosen and explain why "
        "it matches the user interaction model and business process."
    ),
    recommendation_de=(
        "Dokumentieren, welcher Fiori-Floorplan oder welches UI-Pattern gewaehlt "
        "wurde und warum es zum Benutzerinteraktionsmodell und Geschaeftsprozess "
        "passt."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions for design review
# ---------------------------------------------------------------------------


def check_design_missing_error_handling(code: str) -> list[tuple[str, int]]:
    """Fire if design discusses operations but has no error/exception/fallback mention."""
    text_lower = code.lower()
    has_operations = bool(re.search(
        r"\b(process|operation|creat|updat|delet|save|submit|post|execute|run|call|send|fetch|read|write|build|develop|implement|manag|handl|generat)\w*\b",
        text_lower,
    ))
    has_error_handling = bool(re.search(
        r"\b(error|exception|fallback|retry|catch|fault|failure|recovery|rollback|error.?handling)\b",
        text_lower,
    ))
    if has_operations and not has_error_handling:
        return [("Design lacks error handling strategy", 1)]
    return []


def check_design_missing_authorization(code: str) -> list[tuple[str, int]]:
    """Fire if design has no mention of auth/role/permission."""
    text_lower = code.lower()
    has_auth = bool(re.search(
        r"\b(auth|role|permission|access.?control|authorization|privilege|security.?model|rbac)\b",
        text_lower,
    ))
    if not has_auth:
        return [("Design lacks authorization concept", 1)]
    return []


def check_design_missing_test_strategy(code: str) -> list[tuple[str, int]]:
    """Fire if design has no mention of testing."""
    text_lower = code.lower()
    has_test = bool(re.search(
        r"\b(test|unit.?test|integration.?test|e2e|quality.?assur|qa|acceptance.?crit|test.?strateg|test.?plan)\b",
        text_lower,
    ))
    if not has_test:
        return [("Design lacks test strategy", 1)]
    return []


def check_design_missing_performance(code: str) -> list[tuple[str, int]]:
    """Fire if design mentions large data volumes but no performance strategy."""
    text_lower = code.lower()
    has_volume = bool(re.search(
        r"\b(large\s+(?:data\s+)?volume|high\s+throughput|million|hundred.?thousand|mass\s+(?:data|processing)|bulk|batch|heavy\s+load|\d{3,}[,.]?\d*\s*(?:record|order|item|document|entr|row|transaction)s?\s+per)\b",
        text_lower,
    ))
    has_perf_strategy = bool(re.search(
        r"\b(performance|caching|cache|pagination|paging|index|background.?process|async|parallel|batch.?process|optimi[sz])\b",
        text_lower,
    ))
    if has_volume and not has_perf_strategy:
        return [("Design mentions large data volumes without performance strategy", 1)]
    return []


def check_design_missing_migration_plan(code: str) -> list[tuple[str, int]]:
    """Fire if design describes migration/extension without cutover plan."""
    text_lower = code.lower()
    has_migration = bool(re.search(
        r"\b(migrat|extensi|convert|transition|legacy|replac|transform)\w*\b",
        text_lower,
    ))
    has_cutover = bool(re.search(
        r"\b(cutover|migration.?plan|rollback|data.?migration|downtime|go.?live|transition.?plan)\b",
        text_lower,
    ))
    if has_migration and not has_cutover:
        return [("Design describes migration/extension without cutover plan", 1)]
    return []


def check_design_technology_concern(code: str) -> list[tuple[str, int]]:
    """Fire if design mentions outdated technology choices."""
    text_lower = code.lower()
    results: list[tuple[str, int]] = []
    # OData V2 when not explicitly justified
    if re.search(r"\bodata\s*v2\b", text_lower) and not re.search(
        r"\b(legacy|backward|compat|reason|justif)\w*\b", text_lower
    ):
        results.append(("Design uses OData V2 — consider OData V4", 1))
    # Classic Dynpro in new development
    if re.search(r"\b(dynpro|screen\s+painter|module\s+pool)\b", text_lower) and not re.search(
        r"\b(legacy|exist|maintain|migrat)\w*\b", text_lower
    ):
        results.append(("Design uses classic Dynpro — consider Fiori/UI5", 1))
    # BSP in new development
    if re.search(r"\bbsp\b", text_lower) and re.search(r"\bnew\b", text_lower):
        results.append(("Design uses BSP for new development — consider Fiori/UI5", 1))
    return results


def check_design_missing_clean_core(code: str) -> list[tuple[str, int]]:
    """Fire if custom development is proposed without clean core mention."""
    text_lower = code.lower()
    has_custom = bool(re.search(
        r"\b(custom|z[_-]|bespoke|eigenentwicklung|kundenspezifisch|modify|enhancement|append|user.?exit|badi)\b",
        text_lower,
    ))
    has_clean_core = bool(re.search(
        r"\b(clean.?core|released.?api|abap.?cloud|tier.?1|upgrade.?safe|upgrade.?stab|key.?user)\b",
        text_lower,
    ))
    if has_custom and not has_clean_core:
        return [("Design proposes custom development without clean core considerations", 1)]
    return []


def check_design_missing_integration_docs(code: str) -> list[tuple[str, int]]:
    """Fire if design mentions integration without specifying details."""
    text_lower = code.lower()
    has_integration = bool(re.search(
        r"\b(integrat|interface|external.?system|third.?party|api\s+call|connect|downstream|upstream)\w*\b",
        text_lower,
    ))
    has_details = bool(re.search(
        r"\b(protocol|rest|odata|rfc|idoc|soap|format|json|xml|csv|authenticat|oauth|basic.?auth|certificate)\b",
        text_lower,
    ))
    if has_integration and not has_details:
        return [("Design mentions integration without protocol/format details", 1)]
    return []


def check_design_incomplete_entity_model(code: str) -> list[tuple[str, int]]:
    """Fire if entities are named but not specified with fields/relationships."""
    text_lower = code.lower()
    # Look for entity names mentioned (e.g., "Entities: X, Y, Z" or "entity SalesOrder")
    has_entities = bool(re.search(
        r"\b(entit(?:y|ies)|business\s+object|data\s+model|table|object\s+type)\b",
        text_lower,
    ))
    has_field_spec = bool(re.search(
        r"\b(field|attribute|column|property|association|composition|cardinality|relationship|foreign.?key|data.?type|key\s+field)\b",
        text_lower,
    ))
    if has_entities and not has_field_spec:
        return [("Entities mentioned but not fully specified with fields/relationships", 1)]
    return []


def check_design_missing_ui_pattern_justification(code: str) -> list[tuple[str, int]]:
    """Fire if UI/Fiori is mentioned but no pattern choice rationale is given."""
    text_lower = code.lower()
    has_ui = bool(re.search(
        r"\b(fiori|ui5|sapui5|frontend|user\s+interface|app|application|screen|dashboard)\b",
        text_lower,
    ))
    has_pattern_rationale = bool(re.search(
        r"\b(list\s+report|object\s+page|overview\s+page|worklist|analytical|freestyle|floorplan|pattern\s+chosen|pattern\s+select|ux\s+pattern|ui\s+pattern)\b",
        text_lower,
    ))
    if has_ui and not has_pattern_rationale:
        return [("Design mentions UI/Fiori without pattern justification", 1)]
    return []


# ---------------------------------------------------------------------------
# Registry — all design review rules
# ---------------------------------------------------------------------------

DESIGN_REVIEW_RULES: tuple[ReviewRule, ...] = (
    DESIGN_COMP_001,
    DESIGN_COMP_002,
    DESIGN_COMP_003,
    DESIGN_COMP_004,
    DESIGN_COMP_005,
    DESIGN_COMP_006,
    DESIGN_COMP_007,
    DESIGN_COMP_008,
    DESIGN_COMP_009,
    DESIGN_COMP_010,
)

# Map of check_fn_name -> callable
DESIGN_REVIEW_CHECK_FUNCTIONS: dict[str, object] = {
    "check_design_missing_error_handling": check_design_missing_error_handling,
    "check_design_missing_authorization": check_design_missing_authorization,
    "check_design_missing_test_strategy": check_design_missing_test_strategy,
    "check_design_missing_performance": check_design_missing_performance,
    "check_design_missing_migration_plan": check_design_missing_migration_plan,
    "check_design_technology_concern": check_design_technology_concern,
    "check_design_missing_clean_core": check_design_missing_clean_core,
    "check_design_missing_integration_docs": check_design_missing_integration_docs,
    "check_design_incomplete_entity_model": check_design_incomplete_entity_model,
    "check_design_missing_ui_pattern_justification": check_design_missing_ui_pattern_justification,
}
