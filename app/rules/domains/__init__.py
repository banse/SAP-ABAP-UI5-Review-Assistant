"""Domain-specific rule packs for the SAP ABAP/UI5 Review Assistant.

Aggregates rules from all supported SAP domains (Yard Logistics, EWM,
Service Management, MII/MES) and provides domain auto-detection.
"""

from __future__ import annotations

import re

from app.rules.domains.ewm import EWM_CHECK_FUNCTIONS, EWM_RULES
from app.rules.domains.mii_mes import MII_MES_CHECK_FUNCTIONS, MII_MES_RULES
from app.rules.domains.service_mgmt import (
    SERVICE_MGMT_CHECK_FUNCTIONS,
    SERVICE_MGMT_RULES,
)
from app.rules.domains.yard import YARD_CHECK_FUNCTIONS, YARD_RULES

# ---------------------------------------------------------------------------
# Combined domain registries
# ---------------------------------------------------------------------------

DOMAIN_RULES = YARD_RULES + EWM_RULES + SERVICE_MGMT_RULES + MII_MES_RULES

DOMAIN_CHECK_FUNCTIONS: dict[str, object] = {
    **YARD_CHECK_FUNCTIONS,
    **EWM_CHECK_FUNCTIONS,
    **SERVICE_MGMT_CHECK_FUNCTIONS,
    **MII_MES_CHECK_FUNCTIONS,
}

# ---------------------------------------------------------------------------
# Domain detection patterns
# ---------------------------------------------------------------------------

_YARD_PATTERNS = re.compile(
    r"(?:yard[_\-]?\s*(?:management|task|gate|dock|slot)|"
    r"gate[_\-]?\s*(?:in|out|process)\b|check[_\-]?\s*(?:in|out)\b|"
    r"dock[_\-]?\s*(?:assign|schedule|door)|"
    r"carrier[_\-]?\s*(?:api|service|notification)|"
    r"\bscac\b|\btrailer\b|shipment[_\-]?\s*yard|"
    r"\bytask\b|yard_order|/scwm/yard)",
    re.IGNORECASE,
)

_EWM_PATTERNS = re.compile(
    r"(?:warehouse[_\-]?\s*task|warehouse[_\-]?\s*order|"
    r"warehouse[_\-]?\s*management|warehouse[_\-]?\s*process|"
    r"wt[_\-]?\s*confirm|wt[_\-]?\s*create|handling[_\-]?\s*unit|"
    r"storage[_\-]?\s*bin|\blgpla\b|\blgnum\b|\blgtyp\b|"
    r"put[_\-]?\s*away|pick[_\-]?\s*(?:list|wave)|"
    r"goods[_\-]?\s*movement|stock[_\-]?\s*transfer|"
    r"\breplenishment\b|wave[_\-]?\s*release|"
    r"/scwm/|ewm[_\-]|\bbwart\b|hu[_\-]?\s*(?:valid|check))",
    re.IGNORECASE,
)

_SERVICE_PATTERNS = re.compile(
    r"(?:service[_\-]?\s*order|service[_\-]?\s*contract|"
    r"service[_\-]?\s*notification|service[_\-]?\s*management|"
    r"create[_\-]?\s*service|sm[_\-]?\s*order|technician[_\-]?\s*assign|"
    r"spare[_\-]?\s*part|\bwarranty\b|\bsla\b|"
    r"field[_\-]?\s*service|notification[_\-]?\s*(?:create|workflow)|"
    r"service[_\-]?\s*(?:approv|level)|"
    r"\biw3[1-9]\b|\biw2[0-9]\b|pm[_\-]?\s*order)",
    re.IGNORECASE,
)

_MII_MES_PATTERNS = re.compile(
    r"(?:production[_\-]?\s*(?:order|confirm|screen)|"
    r"prod[_\-]?\s*confirm|prod[_\-]?\s*order|co[_\-]?\s*confirm|"
    r"mes[_\-]?\s*(?:send|call|interface)|"
    r"plc[_\-]?\s*(?:call|read|write)|opc[_\-]?\s*(?:read|write)|"
    r"shopfloor[_\-]?\s*(?:interface|ui)|shopfloor_ui|"
    r"operator[_\-]?\s*screen|sensor[_\-]?\s*data|"
    r"machine[_\-]?\s*signal|realtime[_\-]?\s*feed|"
    r"mii[_\-]|manufacturing[_\-]?\s*execution|"
    r"bapi[_\-]?\s*prodord|\bco1[1-5]\b)",
    re.IGNORECASE,
)


def detect_domain(code: str, context_summary: str = "") -> str | None:
    """Auto-detect the SAP domain from code patterns and context text.

    Parameters
    ----------
    code:
        The ABAP source code to analyse.
    context_summary:
        Optional context text (e.g., ticket description, commit message).

    Returns
    -------
    str | None
        One of ``"YARD"``, ``"EWM"``, ``"SERVICE"``, ``"MII_MES"``,
        or ``None`` if no domain is detected.
    """
    combined = f"{code}\n{context_summary}" if context_summary else code

    # Count matches per domain to pick the strongest signal
    scores: dict[str, int] = {
        "YARD": len(_YARD_PATTERNS.findall(combined)),
        "EWM": len(_EWM_PATTERNS.findall(combined)),
        "SERVICE": len(_SERVICE_PATTERNS.findall(combined)),
        "MII_MES": len(_MII_MES_PATTERNS.findall(combined)),
    }

    best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best_domain] > 0:
        return best_domain
    return None
