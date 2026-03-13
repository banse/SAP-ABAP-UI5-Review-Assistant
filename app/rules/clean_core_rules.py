"""Clean-core detection rules for the SAP ABAP/UI5 Review Assistant.

Each ``CleanCoreRule`` is a frozen dataclass with a regex pattern that
identifies non-clean-core code patterns in ABAP source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CleanCoreRule:
    """A single, immutable clean-core detection rule.

    Parameters
    ----------
    rule_id:
        Unique identifier, e.g. ``CC-API-001``.
    name:
        English display name.
    name_de:
        German display name.
    pattern:
        Regex pattern that detects the non-compliant code.
    severity:
        ``Severity`` value (CRITICAL, IMPORTANT, OPTIONAL).
    finding_template:
        English finding message template.
    finding_template_de:
        German finding message template.
    released_api_alternative:
        Hint about which released API or pattern to use instead.
    pattern_flags:
        Regex flags (default: ``re.IGNORECASE``).
    """

    rule_id: str
    name: str
    name_de: str
    pattern: str
    severity: str
    finding_template: str
    finding_template_de: str
    released_api_alternative: str | None = None
    pattern_flags: int = re.IGNORECASE

    def compile_pattern(self) -> re.Pattern[str]:
        """Return a compiled regex for this rule's pattern."""
        return re.compile(self.pattern, self.pattern_flags)


# ---------------------------------------------------------------------------
# CC-API-001: Direct database table access
# ---------------------------------------------------------------------------

CC_API_001 = CleanCoreRule(
    rule_id="CC-API-001",
    name="Direct database table access",
    name_de="Direkter Datenbanktabellenzugriff",
    pattern=r"\bSELECT\b[\s\S]*?\bFROM\s+[z][a-z0-9_]+\b",
    severity="IMPORTANT",
    finding_template=(
        "Direct SELECT from custom table '{match}' detected. "
        "In a clean-core model, access business data through CDS views "
        "or released APIs instead of direct table access."
    ),
    finding_template_de=(
        "Direkter SELECT auf Custom-Tabelle '{match}' erkannt. "
        "Im Clean-Core-Modell Geschaeftsdaten ueber CDS-Views oder "
        "freigegebene APIs statt direktem Tabellenzugriff lesen."
    ),
    released_api_alternative="Use a CDS view entity (e.g. ZI_<Entity>) with proper annotations.",
)

# ---------------------------------------------------------------------------
# CC-API-002: Unreleased function module calls
# ---------------------------------------------------------------------------

CC_API_002 = CleanCoreRule(
    rule_id="CC-API-002",
    name="Unreleased function module call",
    name_de="Nicht freigegebener Funktionsbausteinaufruf",
    pattern=r"\bCALL\s+FUNCTION\s+'(?!BAPI_|RFC_|REUSE_)[A-Z][A-Z0-9_]*'",
    severity="IMPORTANT",
    finding_template=(
        "Call to potentially unreleased function module '{match}' detected. "
        "Verify the module is released for cloud development (C1 contract) "
        "or replace with a released API."
    ),
    finding_template_de=(
        "Aufruf eines moeglicherweise nicht freigegebenen Funktionsbausteins "
        "'{match}' erkannt. Pruefen, ob der Baustein fuer Cloud-Entwicklung "
        "(C1-Vertrag) freigegeben ist, oder durch eine freigegebene API ersetzen."
    ),
    released_api_alternative="Check the Released Objects list (transaction AOBJ) or use ABAP Cloud APIs.",
)

# ---------------------------------------------------------------------------
# CC-API-003: Modification markers (ENHANCEMENT-POINT / ENHANCEMENT-SECTION)
# ---------------------------------------------------------------------------

CC_API_003 = CleanCoreRule(
    rule_id="CC-API-003",
    name="Modification marker (Enhancement)",
    name_de="Modifikationsmarker (Enhancement)",
    pattern=r"\b(?:ENHANCEMENT-POINT|ENHANCEMENT-SECTION)\b",
    severity="CRITICAL",
    finding_template=(
        "Modification marker '{match}' detected. ENHANCEMENT-POINT and "
        "ENHANCEMENT-SECTION indicate direct modifications of SAP standard "
        "code, which break clean-core compliance and block upgrades."
    ),
    finding_template_de=(
        "Modifikationsmarker '{match}' erkannt. ENHANCEMENT-POINT und "
        "ENHANCEMENT-SECTION deuten auf direkte Modifikationen von SAP-"
        "Standard-Code hin, die Clean-Core-Compliance verletzen und "
        "Upgrades blockieren."
    ),
    released_api_alternative="Use BAdIs or the new extensibility framework (key-user / developer extensibility).",
)

# ---------------------------------------------------------------------------
# CC-API-004: User-exit / BAdI modification patterns
# ---------------------------------------------------------------------------

CC_API_004 = CleanCoreRule(
    rule_id="CC-API-004",
    name="User-exit / classic BAdI modification",
    name_de="User-Exit / klassische BAdI-Modifikation",
    pattern=r"\b(?:CUSTOMER-FUNCTION|USEREXIT_[A-Z0-9_]*|EXIT_[A-Z0-9_]+|CALL\s+CUSTOMER-FUNCTION)\b",
    severity="CRITICAL",
    finding_template=(
        "User-exit or classic modification pattern '{match}' detected. "
        "These patterns are not supported in ABAP Cloud and violate "
        "clean-core principles."
    ),
    finding_template_de=(
        "User-Exit oder klassisches Modifikationsmuster '{match}' erkannt. "
        "Diese Muster werden in ABAP Cloud nicht unterstuetzt und verletzen "
        "Clean-Core-Prinzipien."
    ),
    released_api_alternative="Migrate to new BAdI framework or side-by-side BTP extension.",
)

# ---------------------------------------------------------------------------
# CC-API-005: Classic dynpro usage
# ---------------------------------------------------------------------------

CC_API_005 = CleanCoreRule(
    rule_id="CC-API-005",
    name="Classic dynpro usage",
    name_de="Klassische Dynpro-Nutzung",
    pattern=r"\b(?:CALL\s+SCREEN|MODULE\s+\w+\s+(?:INPUT|OUTPUT)|SET\s+SCREEN)\b",
    severity="IMPORTANT",
    finding_template=(
        "Classic dynpro statement '{match}' detected. Dynpro technology "
        "is not available in ABAP Cloud. Use Fiori Elements or SAPUI5 "
        "for the UI layer."
    ),
    finding_template_de=(
        "Klassische Dynpro-Anweisung '{match}' erkannt. Dynpro-Technologie "
        "steht in ABAP Cloud nicht zur Verfuegung. Fiori Elements oder "
        "SAPUI5 fuer die UI-Schicht verwenden."
    ),
    released_api_alternative="Replace with Fiori Elements (RAP-based) or freestyle SAPUI5 application.",
)

# ---------------------------------------------------------------------------
# CC-API-006: Direct ABAP Dictionary access (TABLES statement)
# ---------------------------------------------------------------------------

CC_API_006 = CleanCoreRule(
    rule_id="CC-API-006",
    name="TABLES statement (global work area)",
    name_de="TABLES-Anweisung (globaler Arbeitsbereich)",
    pattern=r"^\s*TABLES\s*:?\s+\w+",
    severity="IMPORTANT",
    finding_template=(
        "TABLES statement '{match}' detected. The TABLES statement creates "
        "global work areas tied to ABAP Dictionary structures and is "
        "obsolete in modern ABAP / ABAP Cloud."
    ),
    finding_template_de=(
        "TABLES-Anweisung '{match}' erkannt. Die TABLES-Anweisung erzeugt "
        "globale Arbeitsbereiche, die an ABAP-Dictionary-Strukturen gebunden "
        "sind, und ist in modernem ABAP / ABAP Cloud veraltet."
    ),
    released_api_alternative="Use typed method parameters or local DATA declarations instead.",
    pattern_flags=re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# CC-API-007: Obsolete ALV technology
# ---------------------------------------------------------------------------

CC_API_007 = CleanCoreRule(
    rule_id="CC-API-007",
    name="Obsolete ALV technology",
    name_de="Veraltete ALV-Technologie",
    pattern=r"\b(?:REUSE_ALV_GRID_DISPLAY|REUSE_ALV_LIST_DISPLAY|REUSE_ALV_FIELDCATALOG_MERGE|CL_GUI_ALV_GRID)\b",
    severity="IMPORTANT",
    finding_template=(
        "Obsolete ALV usage '{match}' detected. Classic ALV function "
        "modules and CL_GUI_ALV_GRID are not available in ABAP Cloud. "
        "Use CL_SALV_TABLE or expose data via OData for Fiori consumption."
    ),
    finding_template_de=(
        "Veraltete ALV-Nutzung '{match}' erkannt. Klassische ALV-"
        "Funktionsbausteine und CL_GUI_ALV_GRID stehen in ABAP Cloud "
        "nicht zur Verfuegung. CL_SALV_TABLE verwenden oder Daten via "
        "OData fuer Fiori bereitstellen."
    ),
    released_api_alternative="Use CL_SALV_TABLE (released) or expose data via RAP/OData for Fiori Elements.",
)

# ---------------------------------------------------------------------------
# CC-API-008: Non-released CDS view access
# ---------------------------------------------------------------------------

CC_API_008 = CleanCoreRule(
    rule_id="CC-API-008",
    name="Potentially non-released CDS view access",
    name_de="Moeglicherweise nicht freigegebener CDS-View-Zugriff",
    pattern=r"\bFROM\s+(?!Z|z|I_|C_)[A-Z][A-Z0-9_]*(?:\s|\.|\b)",
    severity="OPTIONAL",
    finding_template=(
        "Access to CDS view or table '{match}' detected. Verify that the "
        "object is released for cloud development (C1 contract). Non-released "
        "objects may change or disappear during upgrades."
    ),
    finding_template_de=(
        "Zugriff auf CDS-View oder Tabelle '{match}' erkannt. Pruefen, ob "
        "das Objekt fuer Cloud-Entwicklung (C1-Vertrag) freigegeben ist. "
        "Nicht freigegebene Objekte koennen sich bei Upgrades aendern oder "
        "entfallen."
    ),
    released_api_alternative="Use I_* (interface) or C_* (consumption) released CDS views.",
)

# ---------------------------------------------------------------------------
# CC-API-009: Direct system field manipulation
# ---------------------------------------------------------------------------

CC_API_009 = CleanCoreRule(
    rule_id="CC-API-009",
    name="Direct system field manipulation",
    name_de="Direkte Systemfeld-Manipulation",
    pattern=r"\b(?:sy-msgid|sy-msgno|sy-msgty|sy-msgv[1-4])\s*=\s*",
    severity="OPTIONAL",
    finding_template=(
        "Direct manipulation of system message fields '{match}' detected. "
        "Setting sy-msg* fields directly is fragile and not recommended in "
        "modern ABAP. Use MESSAGE ... INTO or structured exception handling."
    ),
    finding_template_de=(
        "Direkte Manipulation von System-Nachrichtenfeldern '{match}' erkannt. "
        "Direktes Setzen von sy-msg*-Feldern ist fragil und in modernem ABAP "
        "nicht empfohlen. MESSAGE ... INTO oder strukturierte Ausnahmebehandlung "
        "verwenden."
    ),
    released_api_alternative="Use MESSAGE ... INTO DATA(lv_msg) or raise typed exceptions.",
)

# ---------------------------------------------------------------------------
# CC-API-010: ABAP SQL without inline declarations (old-style INTO wa)
# ---------------------------------------------------------------------------

CC_API_010 = CleanCoreRule(
    rule_id="CC-API-010",
    name="ABAP SQL without inline declarations",
    name_de="ABAP SQL ohne Inline-Deklarationen",
    pattern=r"\bSELECT\b[\s\S]*?\bINTO\s+(?!@|TABLE\s+@)(?:CORRESPONDING\s+FIELDS\s+OF\s+)?(?:TABLE\s+)?(?!@)\w+",
    severity="OPTIONAL",
    finding_template=(
        "Old-style SELECT ... INTO (without @ escape) '{match}' detected. "
        "Modern ABAP SQL requires host-variable escaping with @. Use "
        "inline declarations (INTO @DATA(...)) for cleaner, stricter code."
    ),
    finding_template_de=(
        "Alter SELECT ... INTO-Stil (ohne @-Escaping) '{match}' erkannt. "
        "Modernes ABAP SQL erfordert Host-Variable-Escaping mit @. "
        "Inline-Deklarationen (INTO @DATA(...)) fuer saubereren Code verwenden."
    ),
    released_api_alternative="Use SELECT ... INTO @DATA(ls_result) or INTO TABLE @DATA(lt_result).",
)

# ---------------------------------------------------------------------------
# Registry — all clean-core rules in one tuple
# ---------------------------------------------------------------------------

CLEAN_CORE_RULES: tuple[CleanCoreRule, ...] = (
    CC_API_001,
    CC_API_002,
    CC_API_003,
    CC_API_004,
    CC_API_005,
    CC_API_006,
    CC_API_007,
    CC_API_008,
    CC_API_009,
    CC_API_010,
)
