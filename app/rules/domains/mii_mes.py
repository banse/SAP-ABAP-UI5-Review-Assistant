"""Domain-specific review rules for SAP MII/MES (Manufacturing Integration/Execution).

Detects common issues in manufacturing execution ABAP code including
production order confirmations, shopfloor communication, real-time data
handling, operator UI complexity, and order status checks.
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
# DOM-MII-001: Production order confirmation timing
# ---------------------------------------------------------------------------

DOM_MII_001 = ReviewRule(
    rule_id="DOM-MII-001",
    name="Production order confirmation timing",
    name_de="Fertigungsauftragsbestaetigung ohne Zeitpruefung",
    description=(
        "Production order confirmations (prod_confirm, order_confirm, "
        "co_confirm) without timestamp validation can result in backdated "
        "or future-dated confirmations, distorting production reporting."
    ),
    description_de=(
        "Fertigungsauftragsbestaetigungen (prod_confirm, order_confirm, "
        "co_confirm) ohne Zeitstempelvalidierung koennen zu rueckdatierten "
        "oder zukuenftig datierten Bestaetigungen fuehren und die "
        "Produktionsberichterstattung verfaelschen."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\b(?:prod[_\-]?\s*confirm|order[_\-]?\s*confirm|co[_\-]?\s*confirm|confirmation[_\-]?\s*post)\b",
    check_fn_name="check_mii_confirm_timing",
    category="domain_mii",
    recommendation=(
        "Validate confirmation timestamps against the current system time "
        "and production order schedule. Reject backdated confirmations "
        "beyond a configurable tolerance."
    ),
    recommendation_de=(
        "Bestaetigungszeitstempel gegen die aktuelle Systemzeit und den "
        "Fertigungsauftragsplan validieren. Rueckdatierte Bestaetigungen "
        "ueber eine konfigurierbare Toleranz hinaus ablehnen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-MII-002: Shopfloor communication without retry logic
# ---------------------------------------------------------------------------

DOM_MII_002 = ReviewRule(
    rule_id="DOM-MII-002",
    name="Shopfloor communication without retry logic",
    name_de="Shopfloor-Kommunikation ohne Retry-Logik",
    description=(
        "MES/PLC/shopfloor integration calls (mes_send, plc_call, "
        "shopfloor_interface, opc_read) without retry or error recovery "
        "logic can cause silent data loss in production environments."
    ),
    description_de=(
        "MES-/PLC-/Shopfloor-Integrationsaufrufe (mes_send, plc_call, "
        "shopfloor_interface, opc_read) ohne Retry- oder Fehlerbehebungs-"
        "Logik koennen zu stillem Datenverlust in Produktionsumgebungen "
        "fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\b(?:mes[_\-]?\s*(?:send|call|interface)|plc[_\-]?\s*(?:call|read|write)|shopfloor[_\-]?\s*interface|opc[_\-]?\s*(?:read|write))\b",
    check_fn_name="check_mii_shopfloor_retry",
    category="domain_mii",
    recommendation=(
        "Implement retry logic with configurable attempts and backoff for "
        "shopfloor communication. Log failures and provide alerting."
    ),
    recommendation_de=(
        "Retry-Logik mit konfigurierbaren Versuchen und Backoff fuer "
        "Shopfloor-Kommunikation implementieren. Fehler protokollieren "
        "und Alarmierung bereitstellen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-MII-003: Real-time data handling without buffer
# ---------------------------------------------------------------------------

DOM_MII_003 = ReviewRule(
    rule_id="DOM-MII-003",
    name="Real-time data handling without buffer",
    name_de="Echtzeitdatenverarbeitung ohne Puffer",
    description=(
        "Direct processing of high-frequency production data (sensor_data, "
        "machine_signal, realtime_feed, process_data) without buffering or "
        "aggregation can overload the backend and cause data loss."
    ),
    description_de=(
        "Direkte Verarbeitung von hochfrequenten Produktionsdaten "
        "(sensor_data, machine_signal, realtime_feed, process_data) ohne "
        "Pufferung oder Aggregation kann das Backend ueberlasten und "
        "Datenverlust verursachen."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\b(?:sensor[_\-]?\s*data|machine[_\-]?\s*signal|realtime[_\-]?\s*feed|process[_\-]?\s*data[_\-]?\s*collect)\b",
    check_fn_name="check_mii_realtime_buffer",
    category="domain_mii",
    recommendation=(
        "Implement a buffer or aggregation layer for high-frequency data. "
        "Process in batches and use asynchronous handling where possible."
    ),
    recommendation_de=(
        "Einen Puffer oder eine Aggregationsschicht fuer hochfrequente Daten "
        "implementieren. In Paketen verarbeiten und wo moeglich asynchrone "
        "Behandlung verwenden."
    ),
)

# ---------------------------------------------------------------------------
# DOM-MII-004: Operator UI complexity
# ---------------------------------------------------------------------------

DOM_MII_004 = ReviewRule(
    rule_id="DOM-MII-004",
    name="Operator UI complexity",
    name_de="Bediener-UI-Komplexitaet",
    description=(
        "Shopfloor operator interfaces (operator_screen, shop_ui, "
        "production_screen) with too many input fields increase error rates "
        "and slow down production workflows on the shop floor."
    ),
    description_de=(
        "Shopfloor-Bedieneroberflaechen (operator_screen, shop_ui, "
        "production_screen) mit zu vielen Eingabefeldern erhoehen die "
        "Fehlerrate und verlangsamen Produktions-Workflows auf dem Shopfloor."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="OPTIONAL",
    pattern=r"(?:operator[_\-]?\s*screen|shop[_\-]?\s*ui|production[_\-]?\s*screen|shopfloor[_\-]?\s*ui)",
    check_fn_name="check_mii_operator_ui",
    category="domain_mii",
    recommendation=(
        "Limit operator screens to essential input fields. Use barcode "
        "scanning and defaults to reduce manual entry."
    ),
    recommendation_de=(
        "Bedienerbildschirme auf wesentliche Eingabefelder beschraenken. "
        "Barcode-Scanning und Standardwerte verwenden, um manuelle "
        "Eingaben zu reduzieren."
    ),
)

# ---------------------------------------------------------------------------
# DOM-MII-005: Missing production order status check before confirmation
# ---------------------------------------------------------------------------

DOM_MII_005 = ReviewRule(
    rule_id="DOM-MII-005",
    name="Missing production order status check before confirmation",
    name_de="Fehlende Fertigungsauftragsstatus-Pruefung vor Bestaetigung",
    description=(
        "Confirming production operations without checking the production "
        "order status (released, partially confirmed, technically complete) "
        "can lead to invalid confirmations against closed or locked orders."
    ),
    description_de=(
        "Bestaetigung von Fertigungsoperationen ohne Pruefung des "
        "Fertigungsauftragsstatus (freigegeben, teilbestaetigt, technisch "
        "abgeschlossen) kann zu ungueltigen Bestaetigungen gegen "
        "geschlossene oder gesperrte Auftraege fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\b(?:prod[_\-]?\s*confirm|order[_\-]?\s*confirm|co[_\-]?\s*confirm|confirmation[_\-]?\s*post|bapi[_\-]?\s*prodord[_\-]?\s*confirm)\b",
    check_fn_name="check_mii_order_status",
    category="domain_mii",
    recommendation=(
        "Check the production order status (AUFNR status field or "
        "BAPI_PRODORD_GET_DETAIL) before posting confirmations. "
        "Reject confirmations against locked or closed orders."
    ),
    recommendation_de=(
        "Den Fertigungsauftragsstatus (AUFNR-Statusfeld oder "
        "BAPI_PRODORD_GET_DETAIL) vor der Buchung von Bestaetigungen "
        "pruefen. Bestaetigungen gegen gesperrte oder geschlossene "
        "Auftraege ablehnen."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_mii_confirm_timing(code: str) -> list[tuple[str, int]]:
    """Flag production confirmations without timestamp validation."""
    results: list[tuple[str, int]] = []
    confirm_pattern = re.compile(
        r"\b(?:prod[_\-]?\s*confirm|order[_\-]?\s*confirm|co[_\-]?\s*confirm|"
        r"confirmation[_\-]?\s*post)\b",
        re.IGNORECASE,
    )
    time_pattern = re.compile(
        r"\b(?:sy-datum|sy-uzeit|timestamp|time_stamp|convert\s+time\s+stamp|"
        r"cl_abap_tstmp|confirm_date|confirm_time|posting_date)\b",
        re.IGNORECASE,
    )
    for m in confirm_pattern.finditer(code):
        start = max(0, m.start() - 400)
        end = min(len(code), m.end() + 400)
        window = code[start:end]
        if not time_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_mii_shopfloor_retry(code: str) -> list[tuple[str, int]]:
    """Flag shopfloor calls without retry/error recovery."""
    results: list[tuple[str, int]] = []
    sf_pattern = re.compile(
        r"\b(?:mes[_\-]?\s*(?:send|call|interface)|plc[_\-]?\s*(?:call|read|write)|"
        r"shopfloor[_\-]?\s*interface|opc[_\-]?\s*(?:read|write))\b",
        re.IGNORECASE,
    )
    retry_pattern = re.compile(
        r"(?:retry|retries|max[_\-]?\s*attempts|backoff|"
        r"reconnect|recovery|fallback|DO\s+\d+\s+TIMES)",
        re.IGNORECASE,
    )
    for m in sf_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not retry_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_mii_realtime_buffer(code: str) -> list[tuple[str, int]]:
    """Flag real-time data processing without buffering."""
    results: list[tuple[str, int]] = []
    rt_pattern = re.compile(
        r"\b(?:sensor[_\-]?\s*data|machine[_\-]?\s*signal|"
        r"realtime[_\-]?\s*feed|process[_\-]?\s*data[_\-]?\s*collect)\b",
        re.IGNORECASE,
    )
    buffer_pattern = re.compile(
        r"\b(?:buffer|queue|aggregat|batch|accumul|collect[_\-]?\s*data|"
        r"staging[_\-]?\s*table|async)\b",
        re.IGNORECASE,
    )
    for m in rt_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not buffer_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_mii_operator_ui(code: str) -> list[tuple[str, int]]:
    """Flag operator screens with too many input fields."""
    results: list[tuple[str, int]] = []
    ui_pattern = re.compile(
        r"(?:operator[_\-]?\s*screen|shop[_\-]?\s*ui|"
        r"production[_\-]?\s*screen|shopfloor[_\-]?\s*ui)",
        re.IGNORECASE,
    )
    for m in ui_pattern.finditer(code):
        start = max(0, m.start() - 800)
        end = min(len(code), m.end() + 800)
        window = code[start:end]
        field_count = len(re.findall(
            r"\b(?:PARAMETERS|SELECT-OPTIONS|SELECTION-SCREEN|input[_\-]?\s*field)\b",
            window, re.IGNORECASE,
        ))
        if field_count > 5:
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_mii_order_status(code: str) -> list[tuple[str, int]]:
    """Flag production confirmations without order status check."""
    results: list[tuple[str, int]] = []
    confirm_pattern = re.compile(
        r"\b(?:prod[_\-]?\s*confirm|order[_\-]?\s*confirm|co[_\-]?\s*confirm|"
        r"confirmation[_\-]?\s*post|bapi[_\-]?\s*prodord[_\-]?\s*confirm)\b",
        re.IGNORECASE,
    )
    status_pattern = re.compile(
        r"\b(?:order[_\-]?\s*status|status[_\-]?\s*check|aufnr[_\-]?\s*status|"
        r"prod[_\-]?\s*order[_\-]?\s*status|get[_\-]?\s*status|"
        r"bapi_prodord_get_detail|i_status|released|teco)\b",
        re.IGNORECASE,
    )
    for m in confirm_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not status_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

MII_MES_RULES: tuple[ReviewRule, ...] = (
    DOM_MII_001,
    DOM_MII_002,
    DOM_MII_003,
    DOM_MII_004,
    DOM_MII_005,
)

MII_MES_CHECK_FUNCTIONS: dict[str, object] = {
    "check_mii_confirm_timing": check_mii_confirm_timing,
    "check_mii_shopfloor_retry": check_mii_shopfloor_retry,
    "check_mii_realtime_buffer": check_mii_realtime_buffer,
    "check_mii_operator_ui": check_mii_operator_ui,
    "check_mii_order_status": check_mii_order_status,
}
