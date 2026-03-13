"""Deep clean-core detection rules for the SAP ABAP/UI5 Review Assistant.

Provides 15 additional rules (CC-DEEP-001 through CC-DEEP-015) that cover
classic technology detection, released API enforcement, enhancement/modification
patterns, extension opportunities, and upgrade impact assessment.

Each rule is a frozen ``CleanCoreRule`` dataclass.  Complex rules that cannot
be expressed as a single regex expose a custom check function whose name is
stored in the rule's ``check_fn_name`` field (added via the base
``CleanCoreRule`` frozen dataclass).

Export
------
CLEAN_CORE_DEEP_RULES : tuple[CleanCoreRule, ...]
    All 15 deep clean-core rules.
CLEAN_CORE_DEEP_CHECK_FUNCTIONS : dict[str, Callable]
    Mapping of check-function names to their implementations.
"""

from __future__ import annotations

import re
from typing import Callable

from app.rules.clean_core_rules import CleanCoreRule

# ---------------------------------------------------------------------------
# Artifact types tuple shared by all deep rules
# ---------------------------------------------------------------------------

_ABAP_ARTIFACTS = (
    "ABAP_CLASS",
    "ABAP_METHOD",
    "ABAP_REPORT",
    "BEHAVIOR_IMPLEMENTATION",
    "MIXED_FULLSTACK",
)

# ===================================================================
# Classic Technology Detection
# ===================================================================

# ---------------------------------------------------------------------------
# CC-DEEP-001: Classic Dynpro usage (PBO/PAI flow logic)
# ---------------------------------------------------------------------------

CC_DEEP_001 = CleanCoreRule(
    rule_id="CC-DEEP-001",
    name="Classic Dynpro flow logic (PBO/PAI)",
    name_de="Klassische Dynpro-Ablauflogik (PBO/PAI)",
    pattern=(
        r"\b(?:"
        r"PROCESS\s+BEFORE\s+OUTPUT"
        r"|PROCESS\s+AFTER\s+INPUT"
        r"|MODULE\s+\w+\s+(?:OUTPUT|INPUT)"
        r")\b"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Classic Dynpro flow logic '{match}' detected. "
        "PROCESS BEFORE OUTPUT / PROCESS AFTER INPUT and MODULE blocks "
        "are not available in ABAP Cloud. Migrate to Fiori Elements or "
        "freestyle SAPUI5 applications."
    ),
    finding_template_de=(
        "Klassische Dynpro-Ablauflogik '{match}' erkannt. "
        "PROCESS BEFORE OUTPUT / PROCESS AFTER INPUT und MODULE-Bloecke "
        "stehen in ABAP Cloud nicht zur Verfuegung. Migration zu Fiori "
        "Elements oder Freestyle-SAPUI5-Anwendungen empfohlen."
    ),
    released_api_alternative=(
        "Replace Dynpro screens with Fiori Elements (RAP-based) or "
        "freestyle SAPUI5 applications."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-002: Classic ALV usage (non-SALV)
# ---------------------------------------------------------------------------

CC_DEEP_002 = CleanCoreRule(
    rule_id="CC-DEEP-002",
    name="Classic ALV without CL_SALV migration",
    name_de="Klassisches ALV ohne CL_SALV-Migration",
    pattern=(
        r"\b(?:"
        r"REUSE_ALV_GRID_DISPLAY"
        r"|REUSE_ALV_LIST_DISPLAY"
        r"|CL_GUI_ALV_GRID"
        r")\b"
        r"(?![\s\S]{0,200}\bCL_SALV\b)"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Classic ALV usage '{match}' without CL_SALV migration detected. "
        "REUSE_ALV_* function modules and CL_GUI_ALV_GRID are not available "
        "in ABAP Cloud. Use CL_SALV_TABLE or expose data via OData for "
        "Fiori consumption."
    ),
    finding_template_de=(
        "Klassische ALV-Nutzung '{match}' ohne CL_SALV-Migration erkannt. "
        "REUSE_ALV_*-Funktionsbausteine und CL_GUI_ALV_GRID stehen in ABAP "
        "Cloud nicht zur Verfuegung. CL_SALV_TABLE verwenden oder Daten "
        "via OData fuer Fiori bereitstellen."
    ),
    released_api_alternative=(
        "Use CL_SALV_TABLE (released) or expose data via RAP/OData for "
        "Fiori Elements."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-003: SAP Script usage (OPEN_FORM / WRITE_FORM / CLOSE_FORM)
# ---------------------------------------------------------------------------

CC_DEEP_003 = CleanCoreRule(
    rule_id="CC-DEEP-003",
    name="SAPscript form usage",
    name_de="SAPscript-Formularnutzung",
    pattern=(
        r"\bCALL\s+FUNCTION\s+'(?:OPEN_FORM|WRITE_FORM|CLOSE_FORM|START_FORM|END_FORM)'"
    ),
    severity="IMPORTANT",
    finding_template=(
        "SAPscript form call '{match}' detected. SAPscript (OPEN_FORM, "
        "WRITE_FORM, CLOSE_FORM) is obsolete technology not available in "
        "ABAP Cloud. Migrate to Adobe Forms or SAP Forms Service by Adobe."
    ),
    finding_template_de=(
        "SAPscript-Formularaufruf '{match}' erkannt. SAPscript (OPEN_FORM, "
        "WRITE_FORM, CLOSE_FORM) ist veraltete Technologie, die in ABAP "
        "Cloud nicht verfuegbar ist. Migration zu Adobe Forms oder SAP "
        "Forms Service by Adobe empfohlen."
    ),
    released_api_alternative=(
        "Migrate to Adobe Forms (XDP-based) or SAP Forms Service by Adobe "
        "on BTP."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-004: SAPConnect / BCS email sending
# ---------------------------------------------------------------------------

CC_DEEP_004 = CleanCoreRule(
    rule_id="CC-DEEP-004",
    name="SAPConnect BCS email sending",
    name_de="SAPConnect-BCS-E-Mail-Versand",
    pattern=(
        r"\b(?:"
        r"CL_BCS\b"
        r"|CL_CAM_ADDRESS_BCS\b"
        r"|CL_DOCUMENT_BCS\b"
        r"|IF_SENDER_BCS\b"
        r"|IF_RECIPIENT_BCS\b"
        r")"
    ),
    severity="IMPORTANT",
    finding_template=(
        "SAPConnect BCS usage '{match}' detected. CL_BCS and related "
        "Business Communication Services classes are not released for "
        "ABAP Cloud. Use CL_BCS_MAIL_MESSAGE (released) or SAP BTP "
        "mail service integration."
    ),
    finding_template_de=(
        "SAPConnect-BCS-Nutzung '{match}' erkannt. CL_BCS und zugehoerige "
        "Business Communication Services-Klassen sind in ABAP Cloud nicht "
        "freigegeben. CL_BCS_MAIL_MESSAGE (freigegeben) oder SAP-BTP-"
        "Mail-Service-Integration verwenden."
    ),
    released_api_alternative=(
        "Use CL_BCS_MAIL_MESSAGE (released API) or integrate with SAP BTP "
        "mail service."
    ),
)

# ===================================================================
# Released API Enforcement
# ===================================================================

# ---------------------------------------------------------------------------
# CC-DEEP-005: Direct SAP standard table access
# ---------------------------------------------------------------------------

# Well-known SAP standard tables that should be accessed via CDS views
_SAP_STANDARD_TABLES = (
    r"BUT\d{3}"  # Business partner tables
    r"|BSEG|BKPF|BSID|BSAD|BSIS|BSAS"  # FI documents
    r"|MARA|MARC|MARD|MAKT|MARM"  # Material master
    r"|VBAK|VBAP|VBEP|VBKD"  # Sales documents
    r"|EKKO|EKPO|EKET|EKES"  # Purchasing documents
    r"|KNA1|KNB1|KNVV"  # Customer master
    r"|LFA1|LFB1|LFM1"  # Vendor master
    r"|LIKP|LIPS"  # Delivery
    r"|MSEG|MKPF"  # Material documents
    r"|PRPS|PROJ"  # Project system
    r"|AFKO|AFPO|AUFK"  # Production orders
    r"|KONV|KONP"  # Pricing conditions
    r"|TCURR|T001|T001W|T005"  # Customizing tables
)


def _check_sap_table_access(code: str) -> list[tuple[str, int]]:
    """Detect direct SELECT from well-known SAP standard tables."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"\bSELECT\b[\s\S]*?\bFROM\s+("
        + _SAP_STANDARD_TABLES
        + r")\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(code):
        line_num = code[: m.start()].count("\n") + 1
        table_name = m.group(1).upper()
        results.append((f"Direct access to SAP table {table_name}", line_num))
    return results


CC_DEEP_005 = CleanCoreRule(
    rule_id="CC-DEEP-005",
    name="Direct SAP standard table access",
    name_de="Direkter Zugriff auf SAP-Standardtabelle",
    pattern=r"__CUSTOM_CHECK__",
    severity="IMPORTANT",
    finding_template=(
        "'{match}'. In clean-core development, access standard SAP data "
        "through released CDS views (I_* or C_*) instead of direct table "
        "access. Direct table access breaks on schema changes during upgrades."
    ),
    finding_template_de=(
        "'{match}'. In der Clean-Core-Entwicklung SAP-Standarddaten ueber "
        "freigegebene CDS-Views (I_* oder C_*) statt direktem Tabellenzugriff "
        "lesen. Direkter Tabellenzugriff bricht bei Schema-Aenderungen "
        "waehrend Upgrades."
    ),
    released_api_alternative=(
        "Use released CDS views such as I_Product, I_SalesDocument, "
        "I_PurchaseOrder, I_BusinessPartner instead of direct table access."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-006: Unreleased function module calls (common patterns)
# ---------------------------------------------------------------------------

CC_DEEP_006 = CleanCoreRule(
    rule_id="CC-DEEP-006",
    name="Common unreleased function module call",
    name_de="Haeufig nicht freigegebener Funktionsbausteinaufruf",
    pattern=(
        r"\bCALL\s+FUNCTION\s+'(?:"
        r"CONVERSION_EXIT_\w+"
        r"|POPUP_TO_CONFIRM(?:_STEP)?"
        r"|POPUP_TO_(?:DECIDE|INFORM|SELECT)"
        r"|REUSE_\w+"
        r"|F4IF_INT_TABLE_VALUE_REQUEST"
        r"|GUI_DOWNLOAD"
        r"|GUI_UPLOAD"
        r"|WS_FILENAME_GET"
        r"|SAPGUI_PROGRESS_INDICATOR"
        r"|CALL_BROWSER"
        r"|SO_NEW_DOCUMENT_ATT_SEND_API1"
        r")'"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Call to commonly unreleased function module '{match}' detected. "
        "These function modules are not released for ABAP Cloud (C1 contract). "
        "Replace with released ABAP Cloud APIs or modern alternatives."
    ),
    finding_template_de=(
        "Aufruf eines haeufig nicht freigegebenen Funktionsbausteins "
        "'{match}' erkannt. Diese Funktionsbausteine sind nicht fuer ABAP "
        "Cloud (C1-Vertrag) freigegeben. Durch freigegebene ABAP-Cloud-APIs "
        "oder moderne Alternativen ersetzen."
    ),
    released_api_alternative=(
        "CONVERSION_EXIT: use CDS cast/conversion. POPUP: use Fiori dialogs. "
        "GUI_DOWNLOAD/UPLOAD: use CL_GUI_FRONTEND_SERVICES (on-prem) or "
        "file handling APIs. REUSE_*: use CL_SALV_TABLE."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-007: Kernel method call
# ---------------------------------------------------------------------------

CC_DEEP_007 = CleanCoreRule(
    rule_id="CC-DEEP-007",
    name="ABAP kernel call",
    name_de="ABAP-Kernel-Aufruf",
    pattern=r"\bCALL\s+'[A-Z_][A-Z0-9_]*'\s+ID\b",
    severity="CRITICAL",
    finding_template=(
        "ABAP kernel call '{match}' detected. Direct kernel calls bypass "
        "the ABAP runtime layer and are strictly forbidden in ABAP Cloud. "
        "They create hard dependencies on internal SAP kernel functions "
        "that may change without notice."
    ),
    finding_template_de=(
        "ABAP-Kernel-Aufruf '{match}' erkannt. Direkte Kernel-Aufrufe "
        "umgehen die ABAP-Laufzeitschicht und sind in ABAP Cloud strikt "
        "verboten. Sie erzeugen harte Abhaengigkeiten zu internen "
        "SAP-Kernel-Funktionen, die sich ohne Vorankuendigung aendern koennen."
    ),
    released_api_alternative=(
        "Replace kernel calls with released ABAP classes or function modules. "
        "Consult the ABAP Cloud released object list."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-008: Table maintenance generator / SM30 patterns
# ---------------------------------------------------------------------------

CC_DEEP_008 = CleanCoreRule(
    rule_id="CC-DEEP-008",
    name="Table maintenance generator usage",
    name_de="Tabellenpflegegenerator-Nutzung",
    pattern=(
        r"\bCALL\s+FUNCTION\s+'(?:"
        r"VIEW_MAINTENANCE_CALL"
        r"|VIEWCLUSTER_MAINTENANCE_CALL"
        r"|TABLE_MAINTENANCE_CALL"
        r")'"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Table maintenance generator call '{match}' detected. "
        "VIEW_MAINTENANCE_CALL and related function modules rely on "
        "classic Dynpro technology and are not available in ABAP Cloud. "
        "Use Fiori-based maintenance apps or RAP-based CRUD services."
    ),
    finding_template_de=(
        "Tabellenpflegegenerator-Aufruf '{match}' erkannt. "
        "VIEW_MAINTENANCE_CALL und verwandte Funktionsbausteine basieren "
        "auf klassischer Dynpro-Technologie und stehen in ABAP Cloud nicht "
        "zur Verfuegung. Fiori-basierte Pflegeanwendungen oder RAP-basierte "
        "CRUD-Services verwenden."
    ),
    released_api_alternative=(
        "Create a RAP-based Fiori Elements Manage app or use custom "
        "Fiori application for table maintenance."
    ),
)

# ===================================================================
# Enhancement / Modification Detection
# ===================================================================

# ---------------------------------------------------------------------------
# CC-DEEP-009: BAdI implementation detection
# ---------------------------------------------------------------------------

CC_DEEP_009 = CleanCoreRule(
    rule_id="CC-DEEP-009",
    name="BAdI implementation detected",
    name_de="BAdI-Implementierung erkannt",
    pattern=(
        r"\b(?:"
        r"GET\s+BADI\b"
        r"|CALL\s+BADI\b"
        r"|IF_EX_[A-Z0-9_]+"
        r"|CL_EXITHANDLER\b"
        r")"
    ),
    severity="OPTIONAL",
    finding_template=(
        "BAdI usage '{match}' detected. BAdI implementations are a valid "
        "extension mechanism, but verify the BAdI is released for your "
        "target platform. Classic BAdIs (GET BADI/CALL BADI) should be "
        "evaluated for migration to new BAdI framework."
    ),
    finding_template_de=(
        "BAdI-Nutzung '{match}' erkannt. BAdI-Implementierungen sind ein "
        "valider Erweiterungsmechanismus, aber pruefen Sie, ob das BAdI "
        "fuer Ihre Zielplattform freigegeben ist. Klassische BAdIs "
        "(GET BADI/CALL BADI) sollten auf Migration zum neuen BAdI-Framework "
        "geprueft werden."
    ),
    released_api_alternative=(
        "Verify the BAdI is released. For classic BAdIs, evaluate migration "
        "to the new BAdI framework (Enhancement Spot based)."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-010: Implicit enhancement usage
# ---------------------------------------------------------------------------

CC_DEEP_010 = CleanCoreRule(
    rule_id="CC-DEEP-010",
    name="Implicit enhancement usage",
    name_de="Implizite Enhancement-Nutzung",
    pattern=(
        r"\b(?:"
        r"ENHANCEMENT\s+\d+\s+\w+"
        r"|ENHANCEMENT-SECTION\b"
        r"|END-ENHANCEMENT-SECTION\b"
        r")\b"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Implicit enhancement '{match}' detected. Implicit enhancements "
        "inject code into SAP standard objects and are not supported in "
        "ABAP Cloud. They create fragile dependencies that break during "
        "upgrades and are difficult to track."
    ),
    finding_template_de=(
        "Implizites Enhancement '{match}' erkannt. Implizite Enhancements "
        "fuegen Code in SAP-Standardobjekte ein und werden in ABAP Cloud "
        "nicht unterstuetzt. Sie erzeugen fragile Abhaengigkeiten, die bei "
        "Upgrades brechen und schwer nachzuverfolgen sind."
    ),
    released_api_alternative=(
        "Use released BAdIs, key-user extensibility, or side-by-side "
        "extensions on BTP."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-011: Modification assistant markers (SMOD/CMOD)
# ---------------------------------------------------------------------------

CC_DEEP_011 = CleanCoreRule(
    rule_id="CC-DEEP-011",
    name="Modification assistant / SMOD/CMOD pattern",
    name_de="Modifikationsassistent- / SMOD/CMOD-Muster",
    pattern=(
        r"\b(?:"
        r"SMOD\b"
        r"|CMOD\b"
        r"|MODIFICATION\s+ADJUSTMENT"
        r"|BEGIN\s+OF\s+MODIFICATION"
        r"|INSERT\s+REPORT\b[\s\S]*?\bFROM\b"
        r")\b"
    ),
    severity="IMPORTANT",
    finding_template=(
        "Modification assistant pattern '{match}' detected. SMOD/CMOD-based "
        "modifications directly alter SAP standard code and are strictly "
        "incompatible with clean-core principles. These modifications must "
        "be resolved before any cloud migration."
    ),
    finding_template_de=(
        "Modifikationsassistent-Muster '{match}' erkannt. SMOD/CMOD-basierte "
        "Modifikationen aendern direkt SAP-Standardcode und sind strikt "
        "inkompatibel mit Clean-Core-Prinzipien. Diese Modifikationen muessen "
        "vor jeder Cloud-Migration aufgeloest werden."
    ),
    released_api_alternative=(
        "Replace SMOD/CMOD modifications with BAdI implementations, "
        "Enhancement Spots, or side-by-side BTP extensions."
    ),
)

# ===================================================================
# Extension Patterns
# ===================================================================

# ---------------------------------------------------------------------------
# CC-DEEP-012: Side-by-side extension opportunity
# ---------------------------------------------------------------------------

CC_DEEP_012 = CleanCoreRule(
    rule_id="CC-DEEP-012",
    name="Side-by-side extension opportunity",
    name_de="Side-by-Side-Erweiterungsmoeglichkeit",
    pattern=(
        r"\bCALL\s+FUNCTION\s+'(?:BAPI_|RFC_)\w+'"
        r"\s+DESTINATION\b"
    ),
    severity="OPTIONAL",
    finding_template=(
        "Remote-capable function call '{match}' detected. This pattern "
        "could potentially be refactored into a side-by-side extension "
        "on BTP using RAP event-driven architecture or API-based "
        "integration instead of direct in-stack calls."
    ),
    finding_template_de=(
        "Remote-faehiger Funktionsaufruf '{match}' erkannt. Dieses Muster "
        "koennte potenziell in eine Side-by-Side-Erweiterung auf BTP "
        "umgebaut werden, unter Verwendung von RAP-Event-basierter "
        "Architektur oder API-basierter Integration statt direkter "
        "In-Stack-Aufrufe."
    ),
    released_api_alternative=(
        "Consider RAP business events, enterprise events on BTP, or "
        "API-based side-by-side integration patterns."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-013: Key user extensibility pattern (CI_INCLUDE / append)
# ---------------------------------------------------------------------------

CC_DEEP_013 = CleanCoreRule(
    rule_id="CC-DEEP-013",
    name="Classic key-user extensibility pattern",
    name_de="Klassisches Key-User-Erweiterungsmuster",
    pattern=(
        r"\b(?:"
        r"CI_[A-Z0-9_]+"
        r"|APPEND\s+STRUCTURE\b"
        r"|INCLUDE\s+STRUCTURE\s+CI_"
        r")\b"
    ),
    severity="OPTIONAL",
    finding_template=(
        "Classic extensibility pattern '{match}' detected (CI_INCLUDE or "
        "append structure). In S/4HANA Cloud, use the Custom Fields API "
        "or key-user extensibility tools instead of CI_INCLUDEs and "
        "append structures."
    ),
    finding_template_de=(
        "Klassisches Erweiterungsmuster '{match}' erkannt (CI_INCLUDE oder "
        "Append-Struktur). In S/4HANA Cloud die Custom-Fields-API oder "
        "Key-User-Erweiterungswerkzeuge anstelle von CI_INCLUDEs und "
        "Append-Strukturen verwenden."
    ),
    released_api_alternative=(
        "Use Custom Fields API (CL_CUST_FIELD_EXTENSIBILITY) or key-user "
        "extensibility tools in S/4HANA Cloud."
    ),
)

# ---------------------------------------------------------------------------
# CC-DEEP-014: Event-driven extension missing
# ---------------------------------------------------------------------------


def _check_missing_event_pattern(code: str) -> list[tuple[str, int]]:
    """Detect business operations without event raising."""
    results: list[tuple[str, int]] = []

    # Detect MODIFY/COMMIT patterns without RAISE EVENT nearby
    modify_pattern = re.compile(
        r"\b(?:MODIFY\s+(?:ENTITIES|ENTITY)\b|COMMIT\s+ENTITIES\b)",
        re.IGNORECASE,
    )
    event_pattern = re.compile(
        r"\b(?:RAISE\s+ENTITY\s+EVENT\b|RAISE\s+EVENT\b|CL_ABAP_EVENT\b)",
        re.IGNORECASE,
    )

    has_modify = modify_pattern.search(code)
    has_event = event_pattern.search(code)

    if has_modify and not has_event:
        for m in modify_pattern.finditer(code):
            line_num = code[: m.start()].count("\n") + 1
            results.append((
                f"Entity modification '{m.group().strip()}' without event raising",
                line_num,
            ))
            break  # Only report first occurrence
    return results


CC_DEEP_014 = CleanCoreRule(
    rule_id="CC-DEEP-014",
    name="Event-driven extension missing",
    name_de="Fehlende ereignisgesteuerte Erweiterung",
    pattern=r"__CUSTOM_CHECK__",
    severity="OPTIONAL",
    finding_template=(
        "'{match}'. Business entity modifications without event raising "
        "limit extensibility. Consider using RAISE ENTITY EVENT to enable "
        "decoupled side-by-side extensions and event-driven integration."
    ),
    finding_template_de=(
        "'{match}'. Geschaeftsentitaets-Modifikationen ohne Event-Ausloesung "
        "schraenken die Erweiterbarkeit ein. RAISE ENTITY EVENT verwenden, "
        "um entkoppelte Side-by-Side-Erweiterungen und ereignisgesteuerte "
        "Integration zu ermoeglichen."
    ),
    released_api_alternative=(
        "Add RAISE ENTITY EVENT after business entity modifications to "
        "enable RAP business events and BTP event mesh integration."
    ),
)

# ===================================================================
# Upgrade Impact
# ===================================================================

# ---------------------------------------------------------------------------
# CC-DEEP-015: SAP_BASIS dependent code
# ---------------------------------------------------------------------------

CC_DEEP_015 = CleanCoreRule(
    rule_id="CC-DEEP-015",
    name="SAP_BASIS release-dependent code",
    name_de="SAP_BASIS-releaseabhaengiger Code",
    pattern=(
        r"\b(?:"
        r"CL_GUI_FRONTEND_SERVICES\b"
        r"|CL_GUI_CFW\b"
        r"|CL_ABAP_BROWSER\b"
        r"|CL_GUI_DIALOGBOX_CONTAINER\b"
        r"|CL_GUI_CUSTOM_CONTAINER\b"
        r"|CL_GUI_DOCKING_CONTAINER\b"
        r"|CL_GUI_SPLITTER_CONTAINER\b"
        r"|CL_GUI_HTML_VIEWER\b"
        r"|CL_GUI_TEXTEDIT\b"
        r"|CL_GUI_PICTURE\b"
        r"|CL_ABAP_LIST_UTILITIES\b"
        r"|CL_WDR_\w+"
        r"|CL_FPM_\w+"
        r")"
    ),
    severity="IMPORTANT",
    finding_template=(
        "SAP_BASIS dependent class '{match}' detected. GUI container "
        "classes, Web Dynpro runtime classes (CL_WDR_*), and Floor Plan "
        "Manager classes (CL_FPM_*) are tightly coupled to specific "
        "SAP_BASIS releases and are not available in ABAP Cloud."
    ),
    finding_template_de=(
        "SAP_BASIS-abhaengige Klasse '{match}' erkannt. GUI-Container-"
        "Klassen, Web-Dynpro-Laufzeitklassen (CL_WDR_*) und Floor-Plan-"
        "Manager-Klassen (CL_FPM_*) sind eng an bestimmte SAP_BASIS-"
        "Releases gekoppelt und in ABAP Cloud nicht verfuegbar."
    ),
    released_api_alternative=(
        "Replace GUI containers with Fiori/SAPUI5 controls. Replace "
        "Web Dynpro (CL_WDR_*) and FPM (CL_FPM_*) with Fiori Elements "
        "or freestyle SAPUI5."
    ),
)

# ===================================================================
# Registries
# ===================================================================

CLEAN_CORE_DEEP_RULES: tuple[CleanCoreRule, ...] = (
    CC_DEEP_001,
    CC_DEEP_002,
    CC_DEEP_003,
    CC_DEEP_004,
    CC_DEEP_005,
    CC_DEEP_006,
    CC_DEEP_007,
    CC_DEEP_008,
    CC_DEEP_009,
    CC_DEEP_010,
    CC_DEEP_011,
    CC_DEEP_012,
    CC_DEEP_013,
    CC_DEEP_014,
    CC_DEEP_015,
)

CLEAN_CORE_DEEP_CHECK_FUNCTIONS: dict[str, Callable[..., list[tuple[str, int]]]] = {
    "check_sap_table_access": _check_sap_table_access,
    "check_missing_event_pattern": _check_missing_event_pattern,
}
