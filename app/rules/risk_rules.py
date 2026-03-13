"""Risk aggregation rules for the SAP ABAP/UI5 Review Assistant.

Each ``RiskDimensionConfig`` is a frozen dataclass that defines how findings,
test gaps, and clean-core hints contribute to a specific risk dimension.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDimensionConfig:
    """Configuration for a single risk dimension.

    Parameters
    ----------
    category:
        ``RiskCategory`` value: FUNCTIONAL, MAINTAINABILITY, TESTABILITY,
        UPGRADE_CLEAN_CORE.
    name:
        English display name.
    name_de:
        German display name.
    description:
        English description of the risk dimension.
    description_de:
        German description of the risk dimension.
    contributing_rule_categories:
        Which finding categories (from ``ReviewRule.category``) feed into
        this risk dimension.
    critical_threshold:
        Number of CRITICAL-severity findings that trigger a HIGH risk level.
    important_threshold:
        Number of IMPORTANT-severity findings that trigger a MEDIUM risk level.
    weight:
        Relative importance of this dimension (0.0 -- 1.0).
    """

    category: str
    name: str
    name_de: str
    description: str
    description_de: str
    contributing_rule_categories: tuple[str, ...]
    critical_threshold: int
    important_threshold: int
    weight: float


# ---------------------------------------------------------------------------
# Pre-defined risk dimension configurations
# ---------------------------------------------------------------------------

RISK_FUNCTIONAL = RiskDimensionConfig(
    category="FUNCTIONAL",
    name="Functional Risk",
    name_de="Funktionales Risiko",
    description=(
        "Risk that the code contains functional defects such as missing error "
        "handling, security gaps, or performance problems that will manifest "
        "at runtime."
    ),
    description_de=(
        "Risiko, dass der Code funktionale Fehler enthaelt, z. B. fehlende "
        "Fehlerbehandlung, Sicherheitsluecken oder Performance-Probleme, die "
        "sich zur Laufzeit zeigen."
    ),
    contributing_rule_categories=("error_handling", "security", "performance"),
    critical_threshold=1,
    important_threshold=3,
    weight=1.0,
)

RISK_MAINTAINABILITY = RiskDimensionConfig(
    category="MAINTAINABILITY",
    name="Maintainability Risk",
    name_de="Wartbarkeitsrisiko",
    description=(
        "Risk that the code structure, readability, or style makes future "
        "changes expensive and error-prone."
    ),
    description_de=(
        "Risiko, dass Codestruktur, Lesbarkeit oder Stil zukuenftige "
        "Aenderungen teuer und fehleranfaellig machen."
    ),
    contributing_rule_categories=("readability", "structure", "style", "maintainability"),
    critical_threshold=2,
    important_threshold=4,
    weight=0.8,
)

RISK_TESTABILITY = RiskDimensionConfig(
    category="TESTABILITY",
    name="Testability Risk",
    name_de="Testbarkeitsrisiko",
    description=(
        "Risk that identified test gaps leave critical business logic or "
        "UI behaviour unverified."
    ),
    description_de=(
        "Risiko, dass identifizierte Testluecken kritische Geschaeftslogik "
        "oder UI-Verhalten unueberprueft lassen."
    ),
    contributing_rule_categories=(),
    critical_threshold=3,
    important_threshold=5,
    weight=0.7,
)

RISK_UPGRADE_CLEAN_CORE = RiskDimensionConfig(
    category="UPGRADE_CLEAN_CORE",
    name="Upgrade / Clean Core Risk",
    name_de="Upgrade- / Clean-Core-Risiko",
    description=(
        "Risk that the code uses non-released APIs, direct modifications, "
        "or obsolete technology that will break during S/4HANA upgrades."
    ),
    description_de=(
        "Risiko, dass der Code nicht freigegebene APIs, direkte Modifikationen "
        "oder veraltete Technologie nutzt, die bei S/4HANA-Upgrades brechen."
    ),
    contributing_rule_categories=(),
    critical_threshold=2,
    important_threshold=3,
    weight=0.9,
)

# ---------------------------------------------------------------------------
# Registry — all risk dimension configs in one tuple
# ---------------------------------------------------------------------------

RISK_DIMENSION_CONFIGS: tuple[RiskDimensionConfig, ...] = (
    RISK_FUNCTIONAL,
    RISK_MAINTAINABILITY,
    RISK_TESTABILITY,
    RISK_UPGRADE_CLEAN_CORE,
)
