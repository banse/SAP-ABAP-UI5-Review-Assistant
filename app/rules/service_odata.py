"""Service Definition and OData Binding review rules.

Each rule is a frozen ``ReviewRule`` instance that detects common service
definition, service binding, and OData exposure quality issues, with
bilingual (EN/DE) metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# SRV-EXP-001: Service Definition exposing interface views directly
# ---------------------------------------------------------------------------

SRV_EXP_001 = ReviewRule(
    rule_id="SRV-EXP-001",
    name="Service definition exposes interface view directly",
    name_de="Service Definition exponiert Interface-View direkt",
    description=(
        "A service definition should expose consumption (C_) or projection views, "
        "not interface (I_) views directly. Exposing I_ views breaks the clean "
        "separation between interface and consumption layer."
    ),
    description_de=(
        "Eine Service Definition sollte Consumption- (C_) oder Projection-Views "
        "exponieren, nicht direkt Interface- (I_) Views. Das direkte Exponieren "
        "von I_ Views bricht die saubere Trennung zwischen Interface- und "
        "Consumption-Schicht."
    ),
    artifact_types=("SERVICE_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_expose_interface_view",
    category="architecture",
    recommendation=(
        "Expose a consumption projection (C_ or ZC_) view instead of the "
        "interface (I_ or ZI_) view directly."
    ),
    recommendation_de=(
        "Eine Consumption-Projection (C_ oder ZC_) View anstelle der Interface- "
        "(I_ oder ZI_) View direkt exponieren."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-002: Excessive entity exposure
# ---------------------------------------------------------------------------

SRV_EXP_002 = ReviewRule(
    rule_id="SRV-EXP-002",
    name="Excessive entity exposure in service definition",
    name_de="Uebermassige Entity-Exponierung in Service Definition",
    description=(
        "A service definition with more than 10 expose statements may indicate "
        "a too-broad service scope. Consider splitting into focused services."
    ),
    description_de=(
        "Eine Service Definition mit mehr als 10 expose-Anweisungen kann auf "
        "einen zu breiten Service-Scope hinweisen. Erwaegen Sie die Aufteilung "
        "in fokussierte Services."
    ),
    artifact_types=("SERVICE_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"",
    check_fn_name="check_excessive_expose",
    category="architecture",
    recommendation=(
        "Split the service definition into smaller, domain-focused services "
        "with fewer than 10 exposed entities each."
    ),
    recommendation_de=(
        "Die Service Definition in kleinere, domaenenfokussierte Services "
        "mit jeweils weniger als 10 exponierten Entities aufteilen."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-003: Missing service binding authorization
# ---------------------------------------------------------------------------

SRV_EXP_003 = ReviewRule(
    rule_id="SRV-EXP-003",
    name="Missing authorization in service binding",
    name_de="Fehlende Autorisierung in Service Binding",
    description=(
        "A service binding should reference authorization checks. Without "
        "explicit authorization handling, the service may be accessible "
        "without proper permission enforcement."
    ),
    description_de=(
        "Ein Service Binding sollte Autorisierungspruefungen referenzieren. "
        "Ohne explizite Autorisierungsbehandlung kann der Service ohne "
        "ordnungsgemaesse Berechtigungspruefung erreichbar sein."
    ),
    artifact_types=("SERVICE_BINDING", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_missing_binding_authorization",
    category="security",
    recommendation=(
        "Ensure that the underlying CDS views have @AccessControl.authorizationCheck "
        "and that the service binding enforces authorization at the service level."
    ),
    recommendation_de=(
        "Sicherstellen, dass die zugrundeliegenden CDS Views "
        "@AccessControl.authorizationCheck haben und das Service Binding "
        "Autorisierung auf Service-Ebene erzwingt."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-004: Missing etag handling
# ---------------------------------------------------------------------------

SRV_EXP_004 = ReviewRule(
    rule_id="SRV-EXP-004",
    name="Missing ETag handling on exposed entity",
    name_de="Fehlende ETag-Behandlung auf exponierter Entity",
    description=(
        "An exposed entity without ETag annotation (@ObjectModel.semanticKey or "
        "etag master) may cause optimistic concurrency issues in OData consumers."
    ),
    description_de=(
        "Eine exponierte Entity ohne ETag-Annotation (@ObjectModel.semanticKey "
        "oder etag master) kann zu Problemen mit optimistischer Nebenlaeufigkeit "
        "bei OData-Consumern fuehren."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_missing_etag",
    category="data_integrity",
    recommendation=(
        "Add etag master annotation or @ObjectModel.semanticKey to entities "
        "exposed for update operations."
    ),
    recommendation_de=(
        "etag master Annotation oder @ObjectModel.semanticKey zu Entities "
        "hinzufuegen, die fuer Update-Operationen exponiert werden."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-005: OData V2 patterns used with V4 intent
# ---------------------------------------------------------------------------

SRV_EXP_005 = ReviewRule(
    rule_id="SRV-EXP-005",
    name="OData V2 patterns used with V4 intent",
    name_de="OData V2 Muster bei V4-Absicht verwendet",
    description=(
        "The service definition uses V2-specific annotations (e.g. "
        "@OData.publish, @sap.label) together with a V4-style service "
        "definition (define service), indicating a version mismatch."
    ),
    description_de=(
        "Die Service Definition verwendet V2-spezifische Annotationen "
        "(z.B. @OData.publish, @sap.label) zusammen mit einer V4-artigen "
        "Service Definition (define service), was auf einen Versionsmismatch "
        "hinweist."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_v2_v4_mismatch",
    category="compatibility",
    recommendation=(
        "Remove V2-specific annotations (@OData.publish, @sap.label) and use "
        "V4-compatible annotations in the service definition."
    ),
    recommendation_de=(
        "V2-spezifische Annotationen (@OData.publish, @sap.label) entfernen "
        "und V4-kompatible Annotationen in der Service Definition verwenden."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-006: Missing filter restrictions
# ---------------------------------------------------------------------------

SRV_EXP_006 = ReviewRule(
    rule_id="SRV-EXP-006",
    name="Missing filter restrictions on exposed entity",
    name_de="Fehlende Filtereinschraenkungen auf exponierter Entity",
    description=(
        "An exposed entity without @Capabilities.FilterRestrictions may allow "
        "unfiltered requests that cause performance degradation on large datasets."
    ),
    description_de=(
        "Eine exponierte Entity ohne @Capabilities.FilterRestrictions kann "
        "ungefilterte Anfragen ermoeglichen, die bei grossen Datenmengen zu "
        "Leistungseinbussen fuehren."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"",
    check_fn_name="check_missing_filter_restrictions",
    category="performance",
    recommendation=(
        "Add @Capabilities.FilterRestrictions to define required and optional "
        "filter fields on the exposed entity."
    ),
    recommendation_de=(
        "@Capabilities.FilterRestrictions hinzufuegen, um erforderliche und "
        "optionale Filterfelder auf der exponierten Entity zu definieren."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-007: Deep insert/update not configured
# ---------------------------------------------------------------------------

SRV_EXP_007 = ReviewRule(
    rule_id="SRV-EXP-007",
    name="Composition exposed without deep operation support",
    name_de="Komposition ohne Deep-Operation-Unterstuetzung exponiert",
    description=(
        "A composition relationship is exposed in the service but draft or "
        "deep insert/update operations are not configured, which may prevent "
        "correct child entity handling."
    ),
    description_de=(
        "Eine Kompositionsbeziehung wird im Service exponiert, aber Draft- "
        "oder Deep-Insert/Update-Operationen sind nicht konfiguriert, was "
        "die korrekte Behandlung von Child-Entities verhindern kann."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_composition_without_deep_ops",
    category="functionality",
    recommendation=(
        "Enable draft handling or configure deep insert/update for entities "
        "with composition relationships."
    ),
    recommendation_de=(
        "Draft-Handling aktivieren oder Deep-Insert/Update fuer Entities "
        "mit Kompositionsbeziehungen konfigurieren."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-008: Missing service description
# ---------------------------------------------------------------------------

SRV_EXP_008 = ReviewRule(
    rule_id="SRV-EXP-008",
    name="Missing service description",
    name_de="Fehlende Service-Beschreibung",
    description=(
        "A service definition without a description or @EndUserText annotation "
        "makes it difficult to understand the purpose of the service in "
        "service catalogs and documentation."
    ),
    description_de=(
        "Eine Service Definition ohne Beschreibung oder @EndUserText-Annotation "
        "erschwert das Verstaendnis des Service-Zwecks in Service-Katalogen "
        "und der Dokumentation."
    ),
    artifact_types=("SERVICE_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"",
    check_fn_name="check_missing_service_description",
    category="readability",
    recommendation=(
        "Add an @EndUserText.label annotation or a descriptive comment before "
        "the service definition."
    ),
    recommendation_de=(
        "Eine @EndUserText.label-Annotation oder einen beschreibenden Kommentar "
        "vor die Service Definition setzen."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-009: Cross-service entity reference
# ---------------------------------------------------------------------------

SRV_EXP_009 = ReviewRule(
    rule_id="SRV-EXP-009",
    name="Cross-service entity reference detected",
    name_de="Dienstueber­greifende Entity-Referenz erkannt",
    description=(
        "The service definition references entities from another service "
        "namespace, which may create tight coupling between services and "
        "break service isolation."
    ),
    description_de=(
        "Die Service Definition referenziert Entities aus einem anderen "
        "Service-Namespace, was zu enger Kopplung zwischen Services fuehren "
        "und die Service-Isolation brechen kann."
    ),
    artifact_types=("SERVICE_DEFINITION", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_cross_service_reference",
    category="architecture",
    recommendation=(
        "Keep entity references within the same service namespace. If "
        "cross-service access is needed, use associations or API composition."
    ),
    recommendation_de=(
        "Entity-Referenzen innerhalb desselben Service-Namespace halten. "
        "Bei dienstueber­greifendem Zugriff Associations oder API-Komposition "
        "verwenden."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-010: Missing pagination support
# ---------------------------------------------------------------------------

SRV_EXP_010 = ReviewRule(
    rule_id="SRV-EXP-010",
    name="Missing pagination support on exposed entity",
    name_de="Fehlende Paginierungsunterstuetzung auf exponierter Entity",
    description=(
        "An exposed entity without @Capabilities.TopSupported or "
        "@Capabilities.SkipSupported may return unbounded result sets, "
        "causing performance and memory issues."
    ),
    description_de=(
        "Eine exponierte Entity ohne @Capabilities.TopSupported oder "
        "@Capabilities.SkipSupported kann unbegrenzte Ergebnismengen liefern, "
        "was zu Leistungs- und Speicherproblemen fuehrt."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"",
    check_fn_name="check_missing_pagination",
    category="performance",
    recommendation=(
        "Add @Capabilities.TopSupported and @Capabilities.SkipSupported "
        "annotations to enable proper pagination."
    ),
    recommendation_de=(
        "@Capabilities.TopSupported und @Capabilities.SkipSupported "
        "Annotationen hinzufuegen, um ordnungsgemaesse Paginierung zu "
        "ermoeglichen."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-011: Draft-enabled entity without draft actions in service
# ---------------------------------------------------------------------------

SRV_EXP_011 = ReviewRule(
    rule_id="SRV-EXP-011",
    name="Draft-enabled entity exposed without draft actions",
    name_de="Draft-faehige Entity ohne Draft-Aktionen exponiert",
    description=(
        "An entity with draft indication is exposed in the service but "
        "the service definition does not include draft action handling "
        "(e.g. with draft or draft actions). This may lead to incomplete "
        "draft lifecycle support."
    ),
    description_de=(
        "Eine Entity mit Draft-Kennzeichen wird im Service exponiert, aber "
        "die Service Definition enthaelt keine Draft-Aktionsbehandlung "
        "(z.B. with draft oder Draft-Aktionen). Dies kann zu unvollstaendiger "
        "Draft-Lifecycle-Unterstuetzung fuehren."
    ),
    artifact_types=("SERVICE_DEFINITION", "ODATA_SERVICE", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"",
    check_fn_name="check_draft_without_actions",
    category="functionality",
    recommendation=(
        "Add draft action handling (with draft) to the service definition "
        "when exposing draft-enabled entities."
    ),
    recommendation_de=(
        "Draft-Aktionsbehandlung (with draft) zur Service Definition "
        "hinzufuegen, wenn Draft-faehige Entities exponiert werden."
    ),
)

# ---------------------------------------------------------------------------
# SRV-EXP-012: Service binding without /sap/ prefix
# ---------------------------------------------------------------------------

SRV_EXP_012 = ReviewRule(
    rule_id="SRV-EXP-012",
    name="Service binding without /sap/ prefix in URL path",
    name_de="Service Binding ohne /sap/-Praefix im URL-Pfad",
    description=(
        "The service binding URL path does not follow the SAP standard "
        "/sap/ prefix pattern. Non-standard URL paths may cause routing "
        "and gateway configuration issues."
    ),
    description_de=(
        "Der URL-Pfad des Service Bindings folgt nicht dem SAP-Standard "
        "/sap/-Praefix-Muster. Nicht-standardmaessige URL-Pfade koennen "
        "Routing- und Gateway-Konfigurationsprobleme verursachen."
    ),
    artifact_types=("SERVICE_BINDING", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"",
    check_fn_name="check_binding_url_prefix",
    category="standards",
    recommendation=(
        "Use the standard /sap/ prefix in the service binding URL path "
        "(e.g. /sap/opu/odata4/sap/)."
    ),
    recommendation_de=(
        "Den Standard /sap/-Praefix im Service-Binding-URL-Pfad verwenden "
        "(z.B. /sap/opu/odata4/sap/)."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_expose_interface_view(code: str) -> list[tuple[str, int]]:
    """Detect expose statements that reference I_ or ZI_ views directly."""
    results: list[tuple[str, int]] = []
    for m in re.finditer(
        r"\bexpose\s+(Z?I_\w+)", code, re.IGNORECASE
    ):
        line = code[: m.start()].count("\n") + 1
        results.append((m.group(), line))
    return results


def check_excessive_expose(code: str) -> list[tuple[str, int]]:
    """Flag if more than 10 expose statements exist in a single service."""
    expose_matches = list(re.finditer(r"\bexpose\b", code, re.IGNORECASE))
    if len(expose_matches) > 10:
        first = expose_matches[0]
        line = code[: first.start()].count("\n") + 1
        return [(f"expose (found {len(expose_matches)} expose statements)", line)]
    return []


def check_missing_binding_authorization(code: str) -> list[tuple[str, int]]:
    """Flag service binding without authorization reference."""
    has_binding = re.search(
        r"\bservice\s+binding\b", code, re.IGNORECASE
    )
    if not has_binding:
        # Also match bind-style syntax
        has_binding = re.search(r"\bbinding\b.*\bservice\b", code, re.IGNORECASE)
    if not has_binding:
        return []

    has_auth = re.search(
        r"(?:@AccessControl|authorization|auth\s*check|authorizationCheck)",
        code, re.IGNORECASE,
    )
    if not has_auth:
        line = code[: has_binding.start()].count("\n") + 1
        return [(has_binding.group(), line)]
    return []


def check_missing_etag(code: str) -> list[tuple[str, int]]:
    """Flag exposed entities without ETag or semanticKey annotations."""
    has_expose = re.search(r"\bexpose\b", code, re.IGNORECASE)
    if not has_expose:
        return []

    has_etag = re.search(
        r"(?:@ObjectModel\.semanticKey|etag\s+master|\betag\b)",
        code, re.IGNORECASE,
    )
    if not has_etag:
        line = code[: has_expose.start()].count("\n") + 1
        return [(has_expose.group(), line)]
    return []


def check_v2_v4_mismatch(code: str) -> list[tuple[str, int]]:
    """Flag V2-specific annotations in a V4-style service definition."""
    has_define_service = re.search(
        r"\bdefine\s+service\b", code, re.IGNORECASE
    )
    if not has_define_service:
        return []

    v2_pattern = re.search(
        r"@OData\.publish|@sap\.label|@sap\.aggregation|@sap\.text",
        code, re.IGNORECASE,
    )
    if v2_pattern:
        line = code[: v2_pattern.start()].count("\n") + 1
        return [(v2_pattern.group(), line)]
    return []


def check_missing_filter_restrictions(code: str) -> list[tuple[str, int]]:
    """Flag exposed entities without filter restriction annotations."""
    has_expose = re.search(r"\bexpose\b", code, re.IGNORECASE)
    if not has_expose:
        return []

    has_filter = re.search(
        r"@Capabilities\.FilterRestrictions", code, re.IGNORECASE
    )
    if not has_filter:
        line = code[: has_expose.start()].count("\n") + 1
        return [(has_expose.group(), line)]
    return []


def check_composition_without_deep_ops(code: str) -> list[tuple[str, int]]:
    """Flag compositions exposed without draft or deep operation config."""
    has_composition = re.search(r"\bcomposition\b", code, re.IGNORECASE)
    if not has_composition:
        return []

    has_deep = re.search(
        r"(?:with\s+draft|deep\s+(?:insert|update)|@Capabilities\.Deep)",
        code, re.IGNORECASE,
    )
    if not has_deep:
        line = code[: has_composition.start()].count("\n") + 1
        return [(has_composition.group(), line)]
    return []


def check_missing_service_description(code: str) -> list[tuple[str, int]]:
    """Flag service definition without description or EndUserText."""
    has_define_service = re.search(
        r"\bdefine\s+service\b", code, re.IGNORECASE
    )
    if not has_define_service:
        return []

    has_description = re.search(
        r"(?:@EndUserText\.label|//\s*\w+.*service|/\*.*service)",
        code, re.IGNORECASE,
    )
    if not has_description:
        line = code[: has_define_service.start()].count("\n") + 1
        return [(has_define_service.group(), line)]
    return []


def check_cross_service_reference(code: str) -> list[tuple[str, int]]:
    """Flag references to entities from a different service namespace."""
    # Extract the service name from 'define service <NAME>'
    svc_match = re.search(
        r"\bdefine\s+service\s+(\w+)", code, re.IGNORECASE
    )
    if not svc_match:
        return []

    svc_name = svc_match.group(1)
    # Look for expose statements that reference a different service prefix
    # e.g. expose OtherService.Entity
    results: list[tuple[str, int]] = []
    for m in re.finditer(
        r"\bexpose\s+(\w+)\.(\w+)", code, re.IGNORECASE
    ):
        ref_namespace = m.group(1)
        if ref_namespace.lower() != svc_name.lower():
            line = code[: m.start()].count("\n") + 1
            results.append((m.group(), line))
    return results


def check_missing_pagination(code: str) -> list[tuple[str, int]]:
    """Flag exposed entities without pagination annotations."""
    has_expose = re.search(r"\bexpose\b", code, re.IGNORECASE)
    if not has_expose:
        return []

    has_pagination = re.search(
        r"@Capabilities\.(?:TopSupported|SkipSupported|CountRestrictions)",
        code, re.IGNORECASE,
    )
    if not has_pagination:
        line = code[: has_expose.start()].count("\n") + 1
        return [(has_expose.group(), line)]
    return []


def check_draft_without_actions(code: str) -> list[tuple[str, int]]:
    """Flag draft-enabled entities exposed without draft action config."""
    has_draft_ref = re.search(
        r"(?:draft\s+enabled|@ObjectModel\.draft\.enabled|draft_enabled|with\s+draft)",
        code, re.IGNORECASE,
    )
    if not has_draft_ref:
        return []

    has_expose = re.search(r"\bexpose\b", code, re.IGNORECASE)
    if not has_expose:
        return []

    has_draft_actions = re.search(
        r"(?:with\s+draft|draftPrepare|draftActivate|draftEdit|DraftAdministrativeData)",
        code, re.IGNORECASE,
    )
    if not has_draft_actions:
        line = code[: has_draft_ref.start()].count("\n") + 1
        return [(has_draft_ref.group(), line)]
    return []


def check_binding_url_prefix(code: str) -> list[tuple[str, int]]:
    """Flag service bindings without /sap/ prefix in URL path."""
    # Look for URL path patterns in binding definitions
    url_match = re.search(
        r"(?:path|url|endpoint)\s*[:=]\s*['\"]?(/[^'\"\s]+)",
        code, re.IGNORECASE,
    )
    if url_match:
        path = url_match.group(1)
        if not path.startswith("/sap/"):
            line = code[: url_match.start()].count("\n") + 1
            return [(url_match.group(), line)]
        return []

    # Also flag service bindings that have a binding keyword but
    # reference a non-standard path
    has_binding = re.search(
        r"\bservice\s+binding\b", code, re.IGNORECASE
    )
    if has_binding:
        # Check for any path definition
        path_match = re.search(r"/\w+/\w+", code)
        if path_match:
            path_text = path_match.group()
            if not path_text.startswith("/sap/"):
                line = code[: path_match.start()].count("\n") + 1
                return [(path_match.group(), line)]
    return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SERVICE_ODATA_RULES: tuple[ReviewRule, ...] = (
    SRV_EXP_001,
    SRV_EXP_002,
    SRV_EXP_003,
    SRV_EXP_004,
    SRV_EXP_005,
    SRV_EXP_006,
    SRV_EXP_007,
    SRV_EXP_008,
    SRV_EXP_009,
    SRV_EXP_010,
    SRV_EXP_011,
    SRV_EXP_012,
)

SERVICE_ODATA_CHECK_FUNCTIONS: dict[str, object] = {
    "check_expose_interface_view": check_expose_interface_view,
    "check_excessive_expose": check_excessive_expose,
    "check_missing_binding_authorization": check_missing_binding_authorization,
    "check_missing_etag": check_missing_etag,
    "check_v2_v4_mismatch": check_v2_v4_mismatch,
    "check_missing_filter_restrictions": check_missing_filter_restrictions,
    "check_composition_without_deep_ops": check_composition_without_deep_ops,
    "check_missing_service_description": check_missing_service_description,
    "check_cross_service_reference": check_cross_service_reference,
    "check_missing_pagination": check_missing_pagination,
    "check_draft_without_actions": check_draft_without_actions,
    "check_binding_url_prefix": check_binding_url_prefix,
}
