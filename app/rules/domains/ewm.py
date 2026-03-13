"""Domain-specific review rules for SAP EWM (Extended Warehouse Management).

Detects common issues in warehouse management ABAP code including warehouse
task handling, stock consistency, movement types, bin validation, and RF
transaction performance.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# Shared artifact types for domain rules
# ---------------------------------------------------------------------------

_DOMAIN_ARTIFACT_TYPES = (
    "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
    "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
)

# ---------------------------------------------------------------------------
# DOM-EWM-001: Warehouse task confirmation without HU validation
# ---------------------------------------------------------------------------

DOM_EWM_001 = ReviewRule(
    rule_id="DOM-EWM-001",
    name="Warehouse task confirmation without HU validation",
    name_de="Lageraufgabenbestaetigung ohne HU-Validierung",
    description=(
        "Warehouse task confirmations (wt_confirm, warehouse_task_confirm, "
        "confirm_warehouse_task) should validate the handling unit (HU) to "
        "ensure the correct unit is being processed and avoid stock mismatches."
    ),
    description_de=(
        "Lageraufgabenbestaetigungen (wt_confirm, warehouse_task_confirm, "
        "confirm_warehouse_task) sollten die Handling Unit (HU) validieren, "
        "um sicherzustellen, dass die richtige Einheit verarbeitet wird und "
        "Bestandsabweichungen vermieden werden."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\b(?:wt[_\-]?\s*confirm|warehouse[_\-]?\s*task[_\-]?\s*confirm|confirm[_\-]?\s*warehouse[_\-]?\s*task)\b",
    check_fn_name="check_ewm_wt_hu_validation",
    category="domain_ewm",
    recommendation=(
        "Validate the handling unit (HU) identifier before confirming the "
        "warehouse task. Check HU existence and content consistency."
    ),
    recommendation_de=(
        "Die Handling-Unit-(HU-)Kennung vor der Bestaetigung der "
        "Lageraufgabe validieren. HU-Existenz und Inhaltskonsistenz pruefen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-EWM-002: Large warehouse operation without batch processing
# ---------------------------------------------------------------------------

DOM_EWM_002 = ReviewRule(
    rule_id="DOM-EWM-002",
    name="Large warehouse operation without batch processing",
    name_de="Grosse Lageroperation ohne Stapelverarbeitung",
    description=(
        "Bulk warehouse operations (mass stock transfer, wave release, "
        "replenishment runs) without FOR ALL ENTRIES, batch/packet processing, "
        "or COMMIT WORK intervals risk timeouts and lock escalations."
    ),
    description_de=(
        "Massenlageroperationen (Massenumbuchung, Wellenfreigabe, "
        "Nachschubrunden) ohne FOR ALL ENTRIES, Paketverarbeitung oder "
        "COMMIT-WORK-Intervalle riskieren Timeouts und Lock-Eskalationen."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"(?:mass[_\-]?\s*stock|mass[_\-]?\s*transfer|mass[_\-]?\s*move|wave[_\-]?\s*release|replenishment[_\-]?\s*run|bulk[_\-]?\s*(?:pick|put|confirm))",
    check_fn_name="check_ewm_batch_processing",
    category="domain_ewm",
    recommendation=(
        "Process large warehouse operations in batches with COMMIT WORK "
        "intervals. Use FOR ALL ENTRIES or packeted processing."
    ),
    recommendation_de=(
        "Grosse Lageroperationen in Paketen mit COMMIT-WORK-Intervallen "
        "verarbeiten. FOR ALL ENTRIES oder Paketverarbeitung verwenden."
    ),
)

# ---------------------------------------------------------------------------
# DOM-EWM-003: Stock consistency check missing
# ---------------------------------------------------------------------------

DOM_EWM_003 = ReviewRule(
    rule_id="DOM-EWM-003",
    name="Stock consistency check missing",
    name_de="Bestandskonsistenzpruefung fehlt",
    description=(
        "Stock movement operations (goods_movement, stock_transfer, "
        "posting_change) should include consistency verification to "
        "detect and prevent negative stock or phantom quantities."
    ),
    description_de=(
        "Bestandsbewegungsoperationen (goods_movement, stock_transfer, "
        "posting_change) sollten eine Konsistenzpruefung enthalten, um "
        "negativen Bestand oder Phantommengen zu erkennen und zu verhindern."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\b(?:goods[_\-]?\s*movement|stock[_\-]?\s*transfer|posting[_\-]?\s*change|stock[_\-]?\s*update)\b",
    check_fn_name="check_ewm_stock_consistency",
    category="domain_ewm",
    recommendation=(
        "Add stock availability and consistency checks before executing "
        "stock movements. Verify available quantity and storage unit status."
    ),
    recommendation_de=(
        "Bestandsverfuegbarkeits- und Konsistenzpruefungen vor der "
        "Ausfuehrung von Bestandsbewegungen hinzufuegen. Verfuegbare "
        "Menge und Lagereinheitsstatus pruefen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-EWM-004: Movement type hardcoding
# ---------------------------------------------------------------------------

DOM_EWM_004 = ReviewRule(
    rule_id="DOM-EWM-004",
    name="Movement type hardcoding",
    name_de="Bewegungsart-Hardcodierung",
    description=(
        "Hardcoded movement type values (e.g., '101', '901', '311') instead "
        "of constants or configuration make the code fragile and harder to "
        "adapt to different warehouse processes or custom movement types."
    ),
    description_de=(
        "Hartcodierte Bewegungsartwerte (z.B. '101', '901', '311') statt "
        "Konstanten oder Konfiguration machen den Code fragil und schwerer "
        "anpassbar an verschiedene Lagerprozesse oder kundenspezifische "
        "Bewegungsarten."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\bbwart\b",
    check_fn_name="check_ewm_movement_type_hardcoding",
    category="domain_ewm",
    recommendation=(
        "Use constants or configuration tables for movement type values. "
        "Avoid hardcoding numeric movement type codes."
    ),
    recommendation_de=(
        "Konstanten oder Konfigurationstabellen fuer Bewegungsartwerte "
        "verwenden. Hartcodierte numerische Bewegungsartcodes vermeiden."
    ),
)

# ---------------------------------------------------------------------------
# DOM-EWM-005: Missing bin/storage location validation
# ---------------------------------------------------------------------------

DOM_EWM_005 = ReviewRule(
    rule_id="DOM-EWM-005",
    name="Missing bin/storage location validation",
    name_de="Fehlende Lagerplatz-/Lagerortvalidierung",
    description=(
        "Bin or storage location operations (bin_assign, storage_bin, "
        "lgpla, put_away) without existence validation can cause "
        "goods placement into non-existent or blocked locations."
    ),
    description_de=(
        "Lagerplatz- oder Lagerortoperationen (bin_assign, storage_bin, "
        "lgpla, put_away) ohne Existenzvalidierung koennen zu Warenplatzierung "
        "an nicht existierenden oder gesperrten Standorten fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\b(?:bin[_\-]?\s*assign|storage[_\-]?\s*bin|put[_\-]?\s*away|lgpla)\b",
    check_fn_name="check_ewm_bin_validation",
    category="domain_ewm",
    recommendation=(
        "Validate bin/storage location existence and availability status "
        "before assigning goods. Check for blocked or full bins."
    ),
    recommendation_de=(
        "Lagerplatz-/Lagerortexistenz und Verfuegbarkeitsstatus vor der "
        "Warenzuweisung validieren. Auf gesperrte oder volle Lagerplaetze "
        "pruefen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-EWM-006: RF transaction performance
# ---------------------------------------------------------------------------

DOM_EWM_006 = ReviewRule(
    rule_id="DOM-EWM-006",
    name="RF transaction performance",
    name_de="RF-Transaktionsperformance",
    description=(
        "RF screens in warehouse operations should minimize database calls "
        "for responsive scanning workflows. Multiple SELECT statements in "
        "RF processing context cause delays on handheld devices."
    ),
    description_de=(
        "RF-Bildschirme in Lageroperationen sollten Datenbankaufrufe "
        "minimieren fuer reaktionsschnelle Scan-Workflows. Mehrere "
        "SELECT-Anweisungen im RF-Verarbeitungskontext verursachen "
        "Verzoegerungen auf Handgeraeten."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="OPTIONAL",
    pattern=r"\b(?:rf[_\-]?\s*(?:screen|transaction|process)|itsmobile|sap_console)\b",
    check_fn_name="check_ewm_rf_performance",
    category="domain_ewm",
    recommendation=(
        "Minimize database calls in RF transaction context. Use buffered "
        "reads and combine queries where possible."
    ),
    recommendation_de=(
        "Datenbankaufrufe im RF-Transaktionskontext minimieren. Gepufferte "
        "Lesezugriffe verwenden und Abfragen wo moeglich zusammenfassen."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_ewm_wt_hu_validation(code: str) -> list[tuple[str, int]]:
    """Flag WT confirmations without HU validation nearby."""
    results: list[tuple[str, int]] = []
    wt_pattern = re.compile(
        r"\b(?:wt[_\-]?\s*confirm|warehouse[_\-]?\s*task[_\-]?\s*confirm|"
        r"confirm[_\-]?\s*warehouse[_\-]?\s*task)\b",
        re.IGNORECASE,
    )
    hu_pattern = re.compile(
        r"\b(?:handling[_\-]?\s*unit|hu[_\-]?\s*(?:valid|check|exist|verify)|"
        r"exidv|venum|huid)\b",
        re.IGNORECASE,
    )
    for m in wt_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not hu_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_ewm_batch_processing(code: str) -> list[tuple[str, int]]:
    """Flag bulk operations without batch/packet processing."""
    results: list[tuple[str, int]] = []
    bulk_pattern = re.compile(
        r"(?:mass[_\-]?\s*stock|mass[_\-]?\s*transfer|mass[_\-]?\s*move|"
        r"wave[_\-]?\s*release|replenishment[_\-]?\s*run|"
        r"bulk[_\-]?\s*(?:pick|put|confirm))",
        re.IGNORECASE,
    )
    batch_pattern = re.compile(
        r"\b(?:FOR\s+ALL\s+ENTRIES|COMMIT\s+WORK|packet|batch[_\-]?\s*size|"
        r"chunk|package[_\-]?\s*size)\b",
        re.IGNORECASE,
    )
    for m in bulk_pattern.finditer(code):
        start = max(0, m.start() - 600)
        end = min(len(code), m.end() + 600)
        window = code[start:end]
        if not batch_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_ewm_stock_consistency(code: str) -> list[tuple[str, int]]:
    """Flag stock movements without consistency verification."""
    results: list[tuple[str, int]] = []
    stock_pattern = re.compile(
        r"\b(?:goods[_\-]?\s*movement|stock[_\-]?\s*transfer|"
        r"posting[_\-]?\s*change|stock[_\-]?\s*update)\b",
        re.IGNORECASE,
    )
    check_pattern = re.compile(
        r"\b(?:consistency|available[_\-]?\s*(?:stock|qty|quantity)|"
        r"stock[_\-]?\s*check|verify[_\-]?\s*stock|negative[_\-]?\s*stock|"
        r"check[_\-]?\s*availability)\b",
        re.IGNORECASE,
    )
    for m in stock_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not check_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_ewm_movement_type_hardcoding(code: str) -> list[tuple[str, int]]:
    """Flag hardcoded movement type values near bwart references."""
    results: list[tuple[str, int]] = []
    bwart_pattern = re.compile(r"\bbwart\b", re.IGNORECASE)
    hardcode_pattern = re.compile(r"['\"]\d{3}['\"]")

    for m in bwart_pattern.finditer(code):
        start = max(0, m.start() - 100)
        end = min(len(code), m.end() + 100)
        window = code[start:end]
        if hardcode_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_ewm_bin_validation(code: str) -> list[tuple[str, int]]:
    """Flag bin operations without existence validation."""
    results: list[tuple[str, int]] = []
    bin_pattern = re.compile(
        r"\b(?:bin[_\-]?\s*assign|storage[_\-]?\s*bin|put[_\-]?\s*away|lgpla)\b",
        re.IGNORECASE,
    )
    valid_pattern = re.compile(
        r"\b(?:bin[_\-]?\s*(?:exist|valid|check|status|block)|"
        r"storage[_\-]?\s*(?:valid|check)|lgpla[_\-]?\s*(?:check|valid|exist)|"
        r"check[_\-]?\s*bin)\b",
        re.IGNORECASE,
    )
    for m in bin_pattern.finditer(code):
        start = max(0, m.start() - 400)
        end = min(len(code), m.end() + 400)
        window = code[start:end]
        if not valid_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_ewm_rf_performance(code: str) -> list[tuple[str, int]]:
    """Flag RF screens with too many SELECT statements nearby."""
    results: list[tuple[str, int]] = []
    rf_pattern = re.compile(
        r"\b(?:rf[_\-]?\s*(?:screen|transaction|process)|itsmobile|sap_console)\b",
        re.IGNORECASE,
    )
    for m in rf_pattern.finditer(code):
        start = max(0, m.start() - 800)
        end = min(len(code), m.end() + 800)
        window = code[start:end]
        select_count = len(re.findall(r"\bSELECT\b", window, re.IGNORECASE))
        if select_count > 3:
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

EWM_RULES: tuple[ReviewRule, ...] = (
    DOM_EWM_001,
    DOM_EWM_002,
    DOM_EWM_003,
    DOM_EWM_004,
    DOM_EWM_005,
    DOM_EWM_006,
)

EWM_CHECK_FUNCTIONS: dict[str, object] = {
    "check_ewm_wt_hu_validation": check_ewm_wt_hu_validation,
    "check_ewm_batch_processing": check_ewm_batch_processing,
    "check_ewm_stock_consistency": check_ewm_stock_consistency,
    "check_ewm_movement_type_hardcoding": check_ewm_movement_type_hardcoding,
    "check_ewm_bin_validation": check_ewm_bin_validation,
    "check_ewm_rf_performance": check_ewm_rf_performance,
}
