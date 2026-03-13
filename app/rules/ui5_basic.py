"""MVP UI5 review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance with a regex pattern that
detects a common SAPUI5 code quality issue, plus bilingual metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# UI5-I18N: Internationalization rules
# ---------------------------------------------------------------------------

UI5_I18N_001 = ReviewRule(
    rule_id="UI5-I18N-001",
    name="Hardcoded string in XML view",
    name_de="Hardcodierter Text in XML View",
    description=(
        "Hardcoded text strings in XML views are not translatable. All visible "
        "texts should come from the i18n model using {i18n>key} binding syntax."
    ),
    description_de=(
        "Hardcodierte Texte in XML Views sind nicht uebersetzbar. Alle sichtbaren "
        "Texte sollten ueber das i18n-Modell mit {i18n>key}-Binding kommen."
    ),
    artifact_types=("UI5_VIEW", "UI5_FRAGMENT", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r'(?:text|title|label|tooltip|placeholder)="(?!\{)[A-Z][a-zA-Z\s]{2,}"',
    category="internationalization",
    recommendation='Replace hardcoded text with i18n binding: text="{i18n>myKey}".',
    recommendation_de='Hardcodierten Text durch i18n-Binding ersetzen: text="{i18n>myKey}".',
)

# ---------------------------------------------------------------------------
# UI5-STRUCT: Structural rules
# ---------------------------------------------------------------------------

UI5_STRUCT_001 = ReviewRule(
    rule_id="UI5-STRUCT-001",
    name="Controller without onInit method",
    name_de="Controller ohne onInit-Methode",
    description=(
        "A UI5 controller without an onInit method misses the standard lifecycle "
        "hook for model initialization, routing setup, and event registration."
    ),
    description_de=(
        "Ein UI5 Controller ohne onInit-Methode verpasst den Standard-Lifecycle-"
        "Hook fuer Modellinitialisierung, Routing-Setup und Event-Registrierung."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"(?:Controller\.extend|sap\.ui\.controller|sap/ui/core/mvc/Controller)",
    check_fn_name="check_missing_on_init",
    category="structure",
    recommendation="Add an onInit method to the controller for lifecycle initialization.",
    recommendation_de="Eine onInit-Methode zum Controller fuer die Lifecycle-Initialisierung hinzufuegen.",
)

UI5_STRUCT_002 = ReviewRule(
    rule_id="UI5-STRUCT-002",
    name="Direct DOM manipulation in controller",
    name_de="Direkte DOM-Manipulation im Controller",
    description=(
        "Using jQuery or direct DOM manipulation (document.getElementById, $()) "
        "in a UI5 controller bypasses the framework's rendering lifecycle and "
        "causes fragile, hard-to-test code."
    ),
    description_de=(
        "jQuery oder direkte DOM-Manipulation (document.getElementById, $()) im "
        "UI5-Controller umgeht den Rendering-Lifecycle des Frameworks und fuehrt "
        "zu fragilem, schwer testbarem Code."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"(?:jQuery\s*\(|\$\s*\(|document\.getElementById|document\.querySelector)",
    category="structure",
    recommendation="Use this.byId() or the UI5 control API instead of direct DOM access.",
    recommendation_de="this.byId() oder die UI5 Control API anstelle von direktem DOM-Zugriff verwenden.",
)

UI5_STRUCT_003 = ReviewRule(
    rule_id="UI5-STRUCT-003",
    name="Complex expression in XML view binding",
    name_de="Komplexer Ausdruck in XML View Binding",
    description=(
        "Complex expression bindings with ternary operators or function calls "
        "in XML views should be moved to a formatter function for testability "
        "and readability."
    ),
    description_de=(
        "Komplexe Expression-Bindings mit ternaeren Operatoren oder Funktionsaufrufen "
        "in XML Views sollten in eine Formatter-Funktion ausgelagert werden."
    ),
    artifact_types=("UI5_VIEW", "UI5_FRAGMENT", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"=\s*\"?\{=\s*.*(?:\?|&&|\|\|).*\}\"?",
    category="readability",
    recommendation="Extract complex expressions into a formatter function.",
    recommendation_de="Komplexe Ausdruecke in eine Formatter-Funktion extrahieren.",
)

# ---------------------------------------------------------------------------
# UI5-ERR: Error handling
# ---------------------------------------------------------------------------

UI5_ERR_001 = ReviewRule(
    rule_id="UI5-ERR-001",
    name="OData call without error handler",
    name_de="OData-Aufruf ohne Fehlerbehandlung",
    description=(
        "An OData model read/create/update/remove call without an error callback "
        "or .fail()/.catch() handler leaves the user without feedback when the "
        "backend returns an error."
    ),
    description_de=(
        "Ein OData-Model read/create/update/remove-Aufruf ohne Error-Callback "
        "oder .fail()/.catch()-Handler laesst den Benutzer ohne Feedback, wenn "
        "das Backend einen Fehler liefert."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"\.(?:read|create|update|remove|callFunction)\s*\([^)]*\)\s*;",
    check_fn_name="check_odata_error_handler",
    category="error_handling",
    recommendation="Add an error callback or .catch()/.fail() handler to the OData call.",
    recommendation_de="Einen Error-Callback oder .catch()/.fail()-Handler zum OData-Aufruf hinzufuegen.",
)

# ---------------------------------------------------------------------------
# UI5-DEPR: Deprecation rules
# ---------------------------------------------------------------------------

UI5_DEPR_001 = ReviewRule(
    rule_id="UI5-DEPR-001",
    name="Deprecated sap.ui.getCore() usage",
    name_de="Veraltete sap.ui.getCore() Verwendung",
    description=(
        "sap.ui.getCore() is deprecated since UI5 1.118. Use dependency injection "
        "via sap/ui/core/Core or the Component / Controller APIs instead."
    ),
    description_de=(
        "sap.ui.getCore() ist seit UI5 1.118 deprecated. Dependency Injection "
        "ueber sap/ui/core/Core oder die Component / Controller APIs verwenden."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_FORMATTER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"sap\.ui\.getCore\s*\(",
    category="deprecation",
    recommendation=(
        "Replace sap.ui.getCore() with the appropriate module import "
        "(e.g., sap/ui/core/Messaging for message handling)."
    ),
    recommendation_de=(
        "sap.ui.getCore() durch den passenden Modulimport ersetzen "
        "(z.B. sap/ui/core/Messaging fuer Nachrichtenbehandlung)."
    ),
)

# ---------------------------------------------------------------------------
# UI5-PERF: Performance rules
# ---------------------------------------------------------------------------

UI5_PERF_001 = ReviewRule(
    rule_id="UI5-PERF-001",
    name="Missing busy indicator on async operation",
    name_de="Fehlender Busy-Indicator bei Async-Operation",
    description=(
        "Async operations (OData calls, promises) without setBusy/setBusyIndicatorDelay "
        "leave the user uncertain whether the app is processing."
    ),
    description_de=(
        "Async-Operationen (OData-Aufrufe, Promises) ohne setBusy/setBusyIndicatorDelay "
        "lassen den Benutzer unsicher, ob die App verarbeitet."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"(?:\.read\(|\.create\(|new\s+Promise|\.then\s*\()",
    check_fn_name="check_missing_busy_indicator",
    category="performance",
    recommendation="Set setBusy(true) before the async call and setBusy(false) in the callback.",
    recommendation_de=(
        "setBusy(true) vor dem Async-Aufruf und setBusy(false) im Callback setzen."
    ),
)

# ---------------------------------------------------------------------------
# UI5-BIND: Binding / model rules
# ---------------------------------------------------------------------------

UI5_BIND_001 = ReviewRule(
    rule_id="UI5-BIND-001",
    name="Hardcoded OData model path",
    name_de="Hardcodierter OData-Modellpfad",
    description=(
        "Hardcoded model paths like '/SalesOrderSet' scattered across controllers "
        "make refactoring difficult. Centralize paths as constants."
    ),
    description_de=(
        "Hardcodierte Modellpfade wie '/SalesOrderSet' verstreut ueber Controller "
        "erschweren Refactoring. Pfade als Konstanten zentralisieren."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"""(?:bindElement|bindProperty|read|create|update|remove)\s*\(\s*['"]\/\w+""",
    category="maintainability",
    recommendation="Define model paths as constants in a shared utility module.",
    recommendation_de="Modellpfade als Konstanten in einem gemeinsamen Utility-Modul definieren.",
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_missing_on_init(code: str) -> list[tuple[str, int]]:
    """Return a match if a controller has no onInit method."""
    is_controller = re.search(
        r"(?:Controller\.extend|sap\.ui\.controller|sap/ui/core/mvc/Controller)",
        code, re.IGNORECASE,
    )
    has_on_init = re.search(r"\bonInit\b", code)

    if is_controller and not has_on_init:
        return [(is_controller.group(), code[: is_controller.start()].count("\n") + 1)]
    return []


def check_odata_error_handler(code: str) -> list[tuple[str, int]]:
    """Return matches for OData calls without error/catch handlers nearby."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"\.(?:read|create|update|remove|callFunction)\s*\([^)]*\)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(code):
        # Check 200 chars after the call for error handling
        context_after = code[match.end(): match.end() + 200]
        has_error = re.search(r"(?:error|fail|catch|Error)", context_after, re.IGNORECASE)
        if not has_error:
            line_num = code[: match.start()].count("\n") + 1
            results.append((match.group(), line_num))
    return results


def check_missing_busy_indicator(code: str) -> list[tuple[str, int]]:
    """Return a match if async operations exist but no setBusy call found."""
    has_async = re.search(
        r"(?:\.read\(|\.create\(|new\s+Promise|\.then\s*\()", code, re.IGNORECASE,
    )
    has_busy = re.search(r"setBusy\s*\(", code)

    if has_async and not has_busy:
        return [(has_async.group(), code[: has_async.start()].count("\n") + 1)]
    return []


# ---------------------------------------------------------------------------
# Registry — all UI5 rules in one tuple
# ---------------------------------------------------------------------------

UI5_RULES: tuple[ReviewRule, ...] = (
    UI5_I18N_001,
    UI5_STRUCT_001,
    UI5_STRUCT_002,
    UI5_STRUCT_003,
    UI5_ERR_001,
    UI5_DEPR_001,
    UI5_PERF_001,
    UI5_BIND_001,
)

# Map of check_fn_name -> callable
UI5_CHECK_FUNCTIONS: dict[str, object] = {
    "check_missing_on_init": check_missing_on_init,
    "check_odata_error_handler": check_odata_error_handler,
    "check_missing_busy_indicator": check_missing_busy_indicator,
}
