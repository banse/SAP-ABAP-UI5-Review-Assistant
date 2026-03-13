"""Domain-specific review rules for SAP Yard Logistics.

Detects common issues in yard management ABAP code including gate
processes, carrier integration, slot management, RF device handling,
task sequencing, and check-in/check-out flows.
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
# DOM-YARD-001: Gate process without timing check
# ---------------------------------------------------------------------------

DOM_YARD_001 = ReviewRule(
    rule_id="DOM-YARD-001",
    name="Gate process without timing check",
    name_de="Gate-Prozess ohne Zeitpruefung",
    description=(
        "Yard gate operations (gate_in, gate_out, gate_process) should validate "
        "timestamps to prevent backdated or future-dated movements. Missing "
        "timestamp validation can lead to incorrect yard occupancy tracking."
    ),
    description_de=(
        "Yard-Gate-Operationen (gate_in, gate_out, gate_process) sollten "
        "Zeitstempel validieren, um rueckdatierte oder zukuenftige Bewegungen "
        "zu verhindern. Fehlende Zeitstempelvalidierung kann zu falscher "
        "Yard-Belegungsverfolgung fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\bgate[_\-]?\s*(?:in|out|process)\b",
    check_fn_name="check_yard_gate_timing",
    category="domain_yard",
    recommendation=(
        "Add timestamp validation (sy-datum/sy-uzeit or CONVERT TIME STAMP) "
        "near gate operations to ensure accurate yard tracking."
    ),
    recommendation_de=(
        "Zeitstempelvalidierung (sy-datum/sy-uzeit oder CONVERT TIME STAMP) "
        "in der Naehe von Gate-Operationen hinzufuegen, um eine genaue "
        "Yard-Verfolgung sicherzustellen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-YARD-002: Missing carrier integration error handling
# ---------------------------------------------------------------------------

DOM_YARD_002 = ReviewRule(
    rule_id="DOM-YARD-002",
    name="Missing carrier integration error handling",
    name_de="Fehlende Fehlerbehandlung bei Carrier-Integration",
    description=(
        "Carrier API calls (carrier_api, carrier_service, scac_lookup, "
        "carrier_notification) without proper exception handling can cause "
        "uncontrolled failures in yard gate and dock scheduling processes."
    ),
    description_de=(
        "Carrier-API-Aufrufe (carrier_api, carrier_service, scac_lookup, "
        "carrier_notification) ohne Fehlerbehandlung koennen unkontrollierte "
        "Ausfaelle in Yard-Gate- und Dock-Planungsprozessen verursachen."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\bcarrier[_\-]?\s*(?:api|service|notification)\b|\bscac[_\-]?\s*lookup\b",
    check_fn_name="check_yard_carrier_error_handling",
    category="domain_yard",
    recommendation=(
        "Wrap carrier API calls in TRY/CATCH with specific exception handling "
        "and implement a retry or fallback mechanism."
    ),
    recommendation_de=(
        "Carrier-API-Aufrufe in TRY/CATCH mit spezifischer Ausnahmebehandlung "
        "einschliessen und einen Retry- oder Fallback-Mechanismus implementieren."
    ),
)

# ---------------------------------------------------------------------------
# DOM-YARD-003: Slot management without concurrency control
# ---------------------------------------------------------------------------

DOM_YARD_003 = ReviewRule(
    rule_id="DOM-YARD-003",
    name="Slot management without concurrency control",
    name_de="Slot-Verwaltung ohne Parallelitaetskontrolle",
    description=(
        "Slot booking or dock assignment operations without lock/enqueue "
        "mechanisms risk double-booking when multiple users schedule "
        "simultaneously."
    ),
    description_de=(
        "Slot-Buchungs- oder Dock-Zuweisungsoperationen ohne Sperr-/Enqueue-"
        "Mechanismen riskieren Doppelbuchungen bei gleichzeitiger Planung "
        "durch mehrere Benutzer."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="CRITICAL",
    pattern=r"\b(?:slot[_\-]?\s*(?:book|assign|reserve|alloc)|dock[_\-]?\s*(?:assign|schedule|reserve))\b",
    check_fn_name="check_yard_slot_concurrency",
    category="domain_yard",
    recommendation=(
        "Use ENQUEUE/DEQUEUE or a database lock before slot/dock assignment "
        "to prevent concurrent booking conflicts."
    ),
    recommendation_de=(
        "ENQUEUE/DEQUEUE oder eine Datenbanksperre vor der Slot-/Dock-Zuweisung "
        "verwenden, um gleichzeitige Buchungskonflikte zu verhindern."
    ),
)

# ---------------------------------------------------------------------------
# DOM-YARD-004: RF device UI complexity
# ---------------------------------------------------------------------------

DOM_YARD_004 = ReviewRule(
    rule_id="DOM-YARD-004",
    name="RF device UI complexity",
    name_de="RF-Geraet UI-Komplexitaet",
    description=(
        "RF transaction screens used in yard operations should be kept simple "
        "for handheld devices. Too many fields or complex conditional logic "
        "in RF context leads to operator errors and slow scanning workflows."
    ),
    description_de=(
        "RF-Transaktionsbildschirme fuer Yard-Operationen sollten fuer "
        "Handgeraete einfach gehalten werden. Zu viele Felder oder komplexe "
        "bedingte Logik im RF-Kontext fuehrt zu Bedienerfehlern und "
        "langsamen Scan-Workflows."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="OPTIONAL",
    pattern=r"\b(?:rf[_\-]?\s*(?:screen|transaction|display|input)|itsmobile|sap_console)\b",
    check_fn_name="check_yard_rf_complexity",
    category="domain_yard",
    recommendation=(
        "Limit RF screens to essential fields only. Move complex validation "
        "to backend logic and keep the RF interaction linear."
    ),
    recommendation_de=(
        "RF-Bildschirme auf wesentliche Felder beschraenken. Komplexe "
        "Validierungen in die Backend-Logik verlagern und die RF-Interaktion "
        "linear halten."
    ),
)

# ---------------------------------------------------------------------------
# DOM-YARD-005: Yard task sequencing gap
# ---------------------------------------------------------------------------

DOM_YARD_005 = ReviewRule(
    rule_id="DOM-YARD-005",
    name="Yard task sequencing gap",
    name_de="Yard-Aufgaben-Sequenzierungsluecke",
    description=(
        "Yard task creation (yard_task, yt_create, create_yard_task) without "
        "predecessor or dependency checking can lead to out-of-order execution "
        "and dock conflicts."
    ),
    description_de=(
        "Yard-Aufgabenerstellung (yard_task, yt_create, create_yard_task) ohne "
        "Vorgaenger- oder Abhaengigkeitspruefung kann zu ungeordneter "
        "Ausfuehrung und Dock-Konflikten fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\b(?:yard[_\-]?\s*task|yt[_\-]?\s*create|create[_\-]?\s*yard[_\-]?\s*task)\b",
    check_fn_name="check_yard_task_sequencing",
    category="domain_yard",
    recommendation=(
        "Check predecessor task status before creating new yard tasks. "
        "Validate that required prior operations are complete."
    ),
    recommendation_de=(
        "Vorgaenger-Aufgabenstatus vor der Erstellung neuer Yard-Aufgaben "
        "pruefen. Validieren, dass erforderliche vorherige Operationen "
        "abgeschlossen sind."
    ),
)

# ---------------------------------------------------------------------------
# DOM-YARD-006: Check-in/check-out flow incomplete
# ---------------------------------------------------------------------------

DOM_YARD_006 = ReviewRule(
    rule_id="DOM-YARD-006",
    name="Check-in/check-out flow incomplete",
    name_de="Check-in/Check-out-Fluss unvollstaendig",
    description=(
        "A check_in reference without a corresponding check_out in the same "
        "scope indicates an incomplete yard vehicle lifecycle. Vehicles may "
        "remain in 'checked-in' status indefinitely."
    ),
    description_de=(
        "Eine check_in-Referenz ohne entsprechendes check_out im selben "
        "Geltungsbereich deutet auf einen unvollstaendigen Yard-Fahrzeug-"
        "Lebenszyklus hin. Fahrzeuge koennen unbegrenzt im Status "
        "'eingecheckt' verbleiben."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\bcheck[_\-]?\s*in\b",
    check_fn_name="check_yard_checkin_checkout",
    category="domain_yard",
    recommendation=(
        "Ensure every check_in operation has a corresponding check_out path. "
        "Consider implementing a timeout or cleanup mechanism for stale check-ins."
    ),
    recommendation_de=(
        "Sicherstellen, dass jede check_in-Operation einen entsprechenden "
        "check_out-Pfad hat. Einen Timeout- oder Bereinigungsmechanismus "
        "fuer veraltete Check-ins implementieren."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_yard_gate_timing(code: str) -> list[tuple[str, int]]:
    """Flag gate operations without timestamp validation nearby."""
    results: list[tuple[str, int]] = []
    gate_pattern = re.compile(
        r"\bgate[_\-]?\s*(?:in|out|process)\b", re.IGNORECASE,
    )
    time_pattern = re.compile(
        r"\b(?:sy-datum|sy-uzeit|timestamp|time_stamp|convert\s+time\s+stamp|"
        r"cl_abap_tstmp|tzone|gate_time|arrival_time|departure_time)\b",
        re.IGNORECASE,
    )
    for m in gate_pattern.finditer(code):
        # Check a window of 600 chars around the match for timing references
        start = max(0, m.start() - 300)
        end = min(len(code), m.end() + 300)
        window = code[start:end]
        if not time_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_yard_carrier_error_handling(code: str) -> list[tuple[str, int]]:
    """Flag carrier API calls without TRY/CATCH nearby."""
    results: list[tuple[str, int]] = []
    carrier_pattern = re.compile(
        r"\bcarrier[_\-]?\s*(?:api|service|notification)\b|\bscac[_\-]?\s*lookup\b",
        re.IGNORECASE,
    )
    for m in carrier_pattern.finditer(code):
        start = max(0, m.start() - 400)
        end = min(len(code), m.end() + 400)
        window = code[start:end]
        if not re.search(r"\bTRY\b", window, re.IGNORECASE):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_yard_slot_concurrency(code: str) -> list[tuple[str, int]]:
    """Flag slot/dock operations without enqueue/lock nearby."""
    results: list[tuple[str, int]] = []
    slot_pattern = re.compile(
        r"\b(?:slot[_\-]?\s*(?:book|assign|reserve|alloc)|"
        r"dock[_\-]?\s*(?:assign|schedule|reserve))\b",
        re.IGNORECASE,
    )
    lock_pattern = re.compile(
        r"(?:enqueue|dequeue|lock|cl_abap_lock|locking)",
        re.IGNORECASE,
    )
    for m in slot_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not lock_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_yard_rf_complexity(code: str) -> list[tuple[str, int]]:
    """Flag RF screen references with too many PARAMETERS/SELECT-OPTIONS."""
    results: list[tuple[str, int]] = []
    rf_pattern = re.compile(
        r"\b(?:rf[_\-]?\s*(?:screen|transaction|display|input)|itsmobile|sap_console)\b",
        re.IGNORECASE,
    )
    for m in rf_pattern.finditer(code):
        start = max(0, m.start() - 800)
        end = min(len(code), m.end() + 800)
        window = code[start:end]
        field_count = len(re.findall(
            r"\b(?:PARAMETERS|SELECT-OPTIONS|SELECTION-SCREEN|screen-input)\b",
            window, re.IGNORECASE,
        ))
        if field_count > 5:
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_yard_task_sequencing(code: str) -> list[tuple[str, int]]:
    """Flag yard task creation without predecessor/dependency check nearby."""
    results: list[tuple[str, int]] = []
    task_pattern = re.compile(
        r"\b(?:yard[_\-]?\s*task|yt[_\-]?\s*create|create[_\-]?\s*yard[_\-]?\s*task)\b",
        re.IGNORECASE,
    )
    pred_pattern = re.compile(
        r"(?:predecessor|dependency|depends_on|sequence|prior_task|"
        r"prev_task|task_order|task_status)",
        re.IGNORECASE,
    )
    for m in task_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not pred_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_yard_checkin_checkout(code: str) -> list[tuple[str, int]]:
    """Flag check_in references without check_out in the same code."""
    results: list[tuple[str, int]] = []
    checkin_pattern = re.compile(r"\bcheck[_\-]?\s*in\b", re.IGNORECASE)
    checkout_pattern = re.compile(r"\bcheck[_\-]?\s*out\b", re.IGNORECASE)

    has_checkout = checkout_pattern.search(code)
    if not has_checkout:
        for m in checkin_pattern.finditer(code):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

YARD_RULES: tuple[ReviewRule, ...] = (
    DOM_YARD_001,
    DOM_YARD_002,
    DOM_YARD_003,
    DOM_YARD_004,
    DOM_YARD_005,
    DOM_YARD_006,
)

YARD_CHECK_FUNCTIONS: dict[str, object] = {
    "check_yard_gate_timing": check_yard_gate_timing,
    "check_yard_carrier_error_handling": check_yard_carrier_error_handling,
    "check_yard_slot_concurrency": check_yard_slot_concurrency,
    "check_yard_rf_complexity": check_yard_rf_complexity,
    "check_yard_task_sequencing": check_yard_task_sequencing,
    "check_yard_checkin_checkout": check_yard_checkin_checkout,
}
