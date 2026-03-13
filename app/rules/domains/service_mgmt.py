"""Domain-specific review rules for SAP Service Management.

Detects common issues in service management ABAP code including service
order approvals, SLA/warranty handling, notification workflows, technician
assignments, and spare part reservations.
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
# DOM-SVC-001: Service order approval flow incomplete
# ---------------------------------------------------------------------------

DOM_SVC_001 = ReviewRule(
    rule_id="DOM-SVC-001",
    name="Service order approval flow incomplete",
    name_de="Serviceauftrags-Genehmigungsfluss unvollstaendig",
    description=(
        "Service order approval logic that handles the 'approve' path but "
        "not the 'reject' path creates a dead-end workflow. Orders stuck in "
        "pending approval status block service execution."
    ),
    description_de=(
        "Serviceauftrags-Genehmigungslogik, die den 'Genehmigen'-Pfad "
        "behandelt, aber nicht den 'Ablehnen'-Pfad, erzeugt einen Workflow-"
        "Stillstand. Auftraege im Status 'Genehmigung ausstehend' blockieren "
        "die Serviceausfuehrung."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"(?:service[_\-]?\s*(?:order[_\-]?\s*)?approv|order[_\-]?\s*approv|approval[_\-]?\s*flow)",
    check_fn_name="check_svc_approval_flow",
    category="domain_service",
    recommendation=(
        "Implement both approve and reject paths in the service order "
        "approval flow. Include escalation or timeout handling."
    ),
    recommendation_de=(
        "Sowohl Genehmigungs- als auch Ablehnungspfade im Serviceauftrags-"
        "Genehmigungsfluss implementieren. Eskalation oder Timeout-"
        "Behandlung einschliessen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-SVC-002: Missing warranty/SLA calculation
# ---------------------------------------------------------------------------

DOM_SVC_002 = ReviewRule(
    rule_id="DOM-SVC-002",
    name="Missing warranty/SLA calculation",
    name_de="Fehlende Garantie-/SLA-Berechnung",
    description=(
        "Service order creation or processing without SLA or warranty "
        "reference can lead to missed response times, incorrect billing, "
        "and customer dissatisfaction."
    ),
    description_de=(
        "Serviceauftragserstellung oder -verarbeitung ohne SLA- oder "
        "Garantiereferenz kann zu verpassten Reaktionszeiten, falscher "
        "Abrechnung und Kundenunzufriedenheit fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"(?:service[_\-]?\s*order|create[_\-]?\s*service|sm[_\-]?\s*order)",
    check_fn_name="check_svc_warranty_sla",
    category="domain_service",
    recommendation=(
        "Include SLA determination and warranty check during service order "
        "creation. Reference the appropriate service contract or warranty."
    ),
    recommendation_de=(
        "SLA-Ermittlung und Garantiepruefung bei der Serviceauftragserstellung "
        "einschliessen. Den passenden Servicevertrag oder die Garantie referenzieren."
    ),
)

# ---------------------------------------------------------------------------
# DOM-SVC-003: Notification workflow gap
# ---------------------------------------------------------------------------

DOM_SVC_003 = ReviewRule(
    rule_id="DOM-SVC-003",
    name="Notification workflow gap",
    name_de="Benachrichtigungs-Workflow-Luecke",
    description=(
        "Service notification creation without a follow-up action (task, "
        "service order, or escalation) leaves notifications in an open state "
        "without resolution tracking."
    ),
    description_de=(
        "Servicemeldungserstellung ohne Folgeaktion (Aufgabe, Serviceauftrag "
        "oder Eskalation) laesst Meldungen in einem offenen Status ohne "
        "Loesungsverfolgung."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"\b(?:notification[_\-]?\s*(?:create|new|generate)|create[_\-]?\s*notification|qm[_\-]?\s*notification)\b",
    check_fn_name="check_svc_notification_workflow",
    category="domain_service",
    recommendation=(
        "Ensure notification creation includes follow-up action generation "
        "(task assignment, service order creation, or escalation trigger)."
    ),
    recommendation_de=(
        "Sicherstellen, dass die Meldungserstellung die Generierung von "
        "Folgeaktionen umfasst (Aufgabenzuweisung, Serviceauftragserstellung "
        "oder Eskalationsausloesung)."
    ),
)

# ---------------------------------------------------------------------------
# DOM-SVC-004: Technician assignment without availability check
# ---------------------------------------------------------------------------

DOM_SVC_004 = ReviewRule(
    rule_id="DOM-SVC-004",
    name="Technician assignment without availability check",
    name_de="Technikerzuweisung ohne Verfuegbarkeitspruefung",
    description=(
        "Assigning a technician to a service order without checking "
        "availability, skills, or current workload can lead to scheduling "
        "conflicts and SLA breaches."
    ),
    description_de=(
        "Zuweisung eines Technikers zu einem Serviceauftrag ohne Pruefung "
        "der Verfuegbarkeit, Faehigkeiten oder aktuellen Arbeitslast kann "
        "zu Planungskonflikten und SLA-Verletzungen fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="OPTIONAL",
    pattern=r"\b(?:technician[_\-]?\s*assign|assign[_\-]?\s*technician|resource[_\-]?\s*assign|field[_\-]?\s*engineer[_\-]?\s*assign)\b",
    check_fn_name="check_svc_technician_availability",
    category="domain_service",
    recommendation=(
        "Check technician availability, skills, and workload before "
        "assignment. Consider geographic proximity and SLA requirements."
    ),
    recommendation_de=(
        "Technikerverfuegbarkeit, Faehigkeiten und Arbeitslast vor der "
        "Zuweisung pruefen. Geografische Naehe und SLA-Anforderungen "
        "beruecksichtigen."
    ),
)

# ---------------------------------------------------------------------------
# DOM-SVC-005: Spare part reservation without stock check
# ---------------------------------------------------------------------------

DOM_SVC_005 = ReviewRule(
    rule_id="DOM-SVC-005",
    name="Spare part reservation without stock check",
    name_de="Ersatzteilreservierung ohne Bestandspruefung",
    description=(
        "Reserving spare parts for a service order without checking current "
        "stock availability can lead to unfulfillable reservations and "
        "delayed service execution."
    ),
    description_de=(
        "Reservierung von Ersatzteilen fuer einen Serviceauftrag ohne "
        "Pruefung der aktuellen Bestandsverfuegbarkeit kann zu nicht "
        "erfuellbaren Reservierungen und verzoegerter Serviceausfuehrung "
        "fuehren."
    ),
    artifact_types=_DOMAIN_ARTIFACT_TYPES,
    default_severity="IMPORTANT",
    pattern=r"(?:spare[_\-]?\s*part[_\-]?\s*reserv|part[_\-]?\s*reserv|material[_\-]?\s*reserv|component[_\-]?\s*reserv)",
    check_fn_name="check_svc_spare_part_stock",
    category="domain_service",
    recommendation=(
        "Check stock availability (ATP or warehouse stock) before creating "
        "spare part reservations. Provide alternatives if stock is insufficient."
    ),
    recommendation_de=(
        "Bestandsverfuegbarkeit (ATP oder Lagerbestand) vor der Erstellung "
        "von Ersatzteilreservierungen pruefen. Alternativen anbieten, wenn "
        "der Bestand nicht ausreicht."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_svc_approval_flow(code: str) -> list[tuple[str, int]]:
    """Flag approval logic without reject path."""
    results: list[tuple[str, int]] = []
    approve_pattern = re.compile(
        r"(?:service[_\-]?\s*(?:order[_\-]?\s*)?approv|order[_\-]?\s*approv|"
        r"approval[_\-]?\s*flow)",
        re.IGNORECASE,
    )
    reject_pattern = re.compile(
        r"\b(?:reject|decline|deny|disapprov|refus)\b",
        re.IGNORECASE,
    )
    has_reject = reject_pattern.search(code)
    if not has_reject:
        for m in approve_pattern.finditer(code):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_svc_warranty_sla(code: str) -> list[tuple[str, int]]:
    """Flag service order creation without SLA/warranty reference."""
    results: list[tuple[str, int]] = []
    order_pattern = re.compile(
        r"(?:service[_\-]?\s*order|create[_\-]?\s*service|sm[_\-]?\s*order)",
        re.IGNORECASE,
    )
    sla_pattern = re.compile(
        r"(?:sla|warranty|guarantee|service[_\-]?\s*contract|"
        r"response[_\-]?\s*time|service[_\-]?\s*level)",
        re.IGNORECASE,
    )
    for m in order_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not sla_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_svc_notification_workflow(code: str) -> list[tuple[str, int]]:
    """Flag notification creation without follow-up action."""
    results: list[tuple[str, int]] = []
    notif_pattern = re.compile(
        r"\b(?:notification[_\-]?\s*(?:create|new|generate)|"
        r"create[_\-]?\s*notification|qm[_\-]?\s*notification)\b",
        re.IGNORECASE,
    )
    followup_pattern = re.compile(
        r"\b(?:follow[_\-]?\s*up|task[_\-]?\s*(?:create|assign)|"
        r"service[_\-]?\s*order|escalat|action[_\-]?\s*(?:create|trigger))\b",
        re.IGNORECASE,
    )
    for m in notif_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not followup_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_svc_technician_availability(code: str) -> list[tuple[str, int]]:
    """Flag technician assignment without availability check."""
    results: list[tuple[str, int]] = []
    assign_pattern = re.compile(
        r"\b(?:technician[_\-]?\s*assign|assign[_\-]?\s*technician|"
        r"resource[_\-]?\s*assign|field[_\-]?\s*engineer[_\-]?\s*assign)\b",
        re.IGNORECASE,
    )
    avail_pattern = re.compile(
        r"(?:availab|capacity|workload|schedule[_\-]?\s*check|"
        r"skill[_\-]?\s*(?:check|match)|calendar)",
        re.IGNORECASE,
    )
    for m in assign_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not avail_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


def check_svc_spare_part_stock(code: str) -> list[tuple[str, int]]:
    """Flag spare part reservation without stock check."""
    results: list[tuple[str, int]] = []
    reserv_pattern = re.compile(
        r"(?:spare[_\-]?\s*part[_\-]?\s*reserv|part[_\-]?\s*reserv|"
        r"material[_\-]?\s*reserv|component[_\-]?\s*reserv)",
        re.IGNORECASE,
    )
    stock_pattern = re.compile(
        r"(?:stock[_\-]?\s*(?:check|avail|verify)|atp|"
        r"available[_\-]?\s*(?:stock|qty|quantity)|"
        r"check[_\-]?\s*(?:stock|avail)|inventory[_\-]?\s*check)",
        re.IGNORECASE,
    )
    for m in reserv_pattern.finditer(code):
        start = max(0, m.start() - 500)
        end = min(len(code), m.end() + 500)
        window = code[start:end]
        if not stock_pattern.search(window):
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(), line_num))
    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SERVICE_MGMT_RULES: tuple[ReviewRule, ...] = (
    DOM_SVC_001,
    DOM_SVC_002,
    DOM_SVC_003,
    DOM_SVC_004,
    DOM_SVC_005,
)

SERVICE_MGMT_CHECK_FUNCTIONS: dict[str, object] = {
    "check_svc_approval_flow": check_svc_approval_flow,
    "check_svc_warranty_sla": check_svc_warranty_sla,
    "check_svc_notification_workflow": check_svc_notification_workflow,
    "check_svc_technician_availability": check_svc_technician_availability,
    "check_svc_spare_part_stock": check_svc_spare_part_stock,
}
