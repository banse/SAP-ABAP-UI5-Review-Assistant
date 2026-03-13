"""UI5 Freestyle review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance that detects common SAPUI5
freestyle development issues, with bilingual EN/DE metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# UI5-FS-001: Missing model destroy in onExit
# ---------------------------------------------------------------------------

UI5_FS_001 = ReviewRule(
    rule_id="UI5-FS-001",
    name="Missing model destroy in onExit",
    name_de="Fehlende Model-Zerstoerung in onExit",
    description=(
        "The controller creates a model in onInit but does not implement onExit "
        "to destroy it. This can cause memory leaks in long-running applications."
    ),
    description_de=(
        "Der Controller erstellt ein Model in onInit, implementiert aber kein onExit "
        "um es zu zerstoeren. Dies kann zu Speicherlecks in langlebigen Anwendungen fuehren."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"new\s+JSONModel\s*\(",
    check_fn_name="check_missing_model_destroy",
    category="memory_management",
    recommendation="Add an onExit method that destroys models created in onInit.",
    recommendation_de="Eine onExit-Methode hinzufuegen, die in onInit erstellte Models zerstoert.",
)

# ---------------------------------------------------------------------------
# UI5-FS-002: Synchronous XMLHttpRequest usage
# ---------------------------------------------------------------------------

UI5_FS_002 = ReviewRule(
    rule_id="UI5-FS-002",
    name="Synchronous XMLHttpRequest usage",
    name_de="Synchrone XMLHttpRequest-Verwendung",
    description=(
        "Synchronous XMLHttpRequest or jQuery.ajax with async:false blocks the "
        "main thread and causes a poor user experience. Use asynchronous calls."
    ),
    description_de=(
        "Synchrone XMLHttpRequest oder jQuery.ajax mit async:false blockiert den "
        "Hauptthread und fuehrt zu einer schlechten Benutzererfahrung. Asynchrone Aufrufe verwenden."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_FORMATTER", "MIXED_FULLSTACK"),
    default_severity="CRITICAL",
    pattern=r"(?:new\s+XMLHttpRequest\s*\(\s*\)|async\s*:\s*false)",
    category="performance",
    recommendation="Use asynchronous requests (fetch, jQuery.ajax with async:true, or OData model).",
    recommendation_de="Asynchrone Requests verwenden (fetch, jQuery.ajax mit async:true oder OData-Model).",
)

# ---------------------------------------------------------------------------
# UI5-FS-003: Missing formatter for date/currency display
# ---------------------------------------------------------------------------

UI5_FS_003 = ReviewRule(
    rule_id="UI5-FS-003",
    name="Missing formatter for date/currency display",
    name_de="Fehlender Formatter fuer Datum/Waehrungsanzeige",
    description=(
        "A binding for a date or currency field does not use a type or formatter. "
        "Raw values without formatting lead to inconsistent display across locales."
    ),
    description_de=(
        "Ein Binding fuer ein Datum- oder Waehrungsfeld verwendet keinen Typ oder Formatter. "
        "Rohwerte ohne Formatierung fuehren zu inkonsistenter Anzeige ueber Sprachversionen hinweg."
    ),
    artifact_types=("UI5_VIEW", "UI5_FRAGMENT", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"(?:date|Date|datum|currency|Currency|amount|Amount|betrag|price|Price)",
    check_fn_name="check_missing_date_currency_formatter",
    category="internationalization",
    recommendation="Use sap.ui.model.type.Date or sap.ui.model.type.Currency types in bindings.",
    recommendation_de="sap.ui.model.type.Date oder sap.ui.model.type.Currency Typen in Bindings verwenden.",
)

# ---------------------------------------------------------------------------
# UI5-FS-004: Deprecated control usage
# ---------------------------------------------------------------------------

UI5_FS_004 = ReviewRule(
    rule_id="UI5-FS-004",
    name="Deprecated control library usage",
    name_de="Verwendung veralteter Control-Bibliothek",
    description=(
        "References to deprecated SAP UI5 libraries such as sap.ui.commons, "
        "sap.viz, or sap.ca are detected. These libraries are no longer maintained."
    ),
    description_de=(
        "Referenzen auf veraltete SAP UI5 Bibliotheken wie sap.ui.commons, "
        "sap.viz oder sap.ca wurden erkannt. Diese Bibliotheken werden nicht mehr gepflegt."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_VIEW", "UI5_FRAGMENT", "UI5_FORMATTER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"(?:sap\.ui\.commons|sap\.viz|sap\.ca\.\w+|sap/ui/commons|sap/viz|sap/ca/)",
    category="deprecation",
    recommendation="Migrate to sap.m, sap.f, or sap.ui.unified control libraries.",
    recommendation_de="Auf sap.m, sap.f oder sap.ui.unified Control-Bibliotheken migrieren.",
)

# ---------------------------------------------------------------------------
# UI5-FS-005: Event handler not unregistered
# ---------------------------------------------------------------------------

UI5_FS_005 = ReviewRule(
    rule_id="UI5-FS-005",
    name="Event handler not unregistered",
    name_de="Event-Handler nicht abgemeldet",
    description=(
        "An event handler is registered with attachPress, attachEvent, or similar "
        "but no corresponding detach call is found. This may cause memory leaks "
        "or unexpected behavior when the view is destroyed and recreated."
    ),
    description_de=(
        "Ein Event-Handler wird mit attachPress, attachEvent oder aehnlichem registriert, "
        "aber es gibt keinen entsprechenden detach-Aufruf. Dies kann zu Speicherlecks "
        "oder unerwartetem Verhalten fuehren, wenn die View zerstoert und neu erstellt wird."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\.attach\w+\s*\(",
    check_fn_name="check_event_handler_not_unregistered",
    category="memory_management",
    recommendation="Add matching detach calls in onExit for every attach in onInit.",
    recommendation_de="Passende detach-Aufrufe in onExit fuer jeden attach in onInit hinzufuegen.",
)

# ---------------------------------------------------------------------------
# UI5-FS-006: Missing accessibility attributes
# ---------------------------------------------------------------------------

UI5_FS_006 = ReviewRule(
    rule_id="UI5-FS-006",
    name="Missing accessibility attributes",
    name_de="Fehlende Barrierefreiheits-Attribute",
    description=(
        "Interactive controls such as Button, Input, or Icon without ariaLabelledBy, "
        "ariaLabel, or tooltip reduce accessibility for screen reader users."
    ),
    description_de=(
        "Interaktive Controls wie Button, Input oder Icon ohne ariaLabelledBy, "
        "ariaLabel oder tooltip reduzieren die Barrierefreiheit fuer Screenreader-Nutzer."
    ),
    artifact_types=("UI5_VIEW", "UI5_FRAGMENT", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"<(?:Icon|IconTabFilter)\s+[^>]*src\s*=",
    check_fn_name="check_missing_accessibility",
    category="accessibility",
    recommendation="Add tooltip, ariaLabel, or ariaLabelledBy to interactive controls.",
    recommendation_de="tooltip, ariaLabel oder ariaLabelledBy zu interaktiven Controls hinzufuegen.",
)

# ---------------------------------------------------------------------------
# UI5-FS-007: Routing without parameter validation
# ---------------------------------------------------------------------------

UI5_FS_007 = ReviewRule(
    rule_id="UI5-FS-007",
    name="Routing without parameter validation",
    name_de="Routing ohne Parametervalidierung",
    description=(
        "getRouter().navTo() is called without validating route parameters. "
        "Missing or undefined parameters cause navigation failures."
    ),
    description_de=(
        "getRouter().navTo() wird ohne Validierung der Route-Parameter aufgerufen. "
        "Fehlende oder undefinierte Parameter fuehren zu Navigationsfehlern."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"(?:getRouter|this\.oRouter)\s*\(\s*\)\s*\.navTo\s*\(",
    category="robustness",
    recommendation="Validate route parameters before calling navTo.",
    recommendation_de="Route-Parameter vor dem Aufruf von navTo validieren.",
)

# ---------------------------------------------------------------------------
# UI5-FS-008: Global variable in controller
# ---------------------------------------------------------------------------

UI5_FS_008 = ReviewRule(
    rule_id="UI5-FS-008",
    name="Global variable in controller module",
    name_de="Globale Variable im Controller-Modul",
    description=(
        "Variables declared at module scope (outside sap.ui.define callback or "
        "controller methods) become global state shared across instances, causing "
        "unpredictable behavior in multi-instance scenarios."
    ),
    description_de=(
        "Variablen, die auf Modul-Ebene deklariert werden (ausserhalb sap.ui.define "
        "Callback oder Controller-Methoden), werden globaler Zustand, der zwischen "
        "Instanzen geteilt wird und unvorhersehbares Verhalten verursacht."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"sap\.ui\.define",
    check_fn_name="check_global_variable_in_controller",
    category="maintainability",
    recommendation="Move variable declarations inside controller methods or onInit.",
    recommendation_de="Variablendeklarationen in Controller-Methoden oder onInit verschieben.",
)

# ---------------------------------------------------------------------------
# UI5-FS-009: Console.log left in production code
# ---------------------------------------------------------------------------

UI5_FS_009 = ReviewRule(
    rule_id="UI5-FS-009",
    name="Console.log left in production code",
    name_de="Console.log im Produktionscode vorhanden",
    description=(
        "console.log, console.warn, or console.debug statements should be removed "
        "before deploying to production. Use jQuery.sap.log or sap/base/Log instead."
    ),
    description_de=(
        "console.log, console.warn oder console.debug Anweisungen sollten vor dem "
        "Deployment entfernt werden. jQuery.sap.log oder sap/base/Log stattdessen verwenden."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_FORMATTER", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"\bconsole\s*\.\s*(?:log|warn|debug|info)\s*\(",
    category="quality",
    recommendation="Remove console statements or replace with sap/base/Log.",
    recommendation_de="Console-Anweisungen entfernen oder durch sap/base/Log ersetzen.",
)

# ---------------------------------------------------------------------------
# UI5-FS-010: Missing fragment reuse (duplicate XML structures)
# ---------------------------------------------------------------------------

UI5_FS_010 = ReviewRule(
    rule_id="UI5-FS-010",
    name="Missing fragment reuse opportunity",
    name_de="Fehlende Fragment-Wiederverwendung",
    description=(
        "Duplicate or very similar XML structures detected that could be extracted "
        "into a reusable fragment to reduce duplication and improve maintainability."
    ),
    description_de=(
        "Doppelte oder sehr aehnliche XML-Strukturen erkannt, die in ein wiederverwendbares "
        "Fragment ausgelagert werden koennten, um Duplikation zu reduzieren."
    ),
    artifact_types=("UI5_VIEW", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"<(?:VBox|HBox|form:SimpleForm)",
    check_fn_name="check_duplicate_xml_structures",
    category="maintainability",
    recommendation="Extract repeated UI structures into reusable XML fragments.",
    recommendation_de="Wiederholte UI-Strukturen in wiederverwendbare XML-Fragmente extrahieren.",
)

# ---------------------------------------------------------------------------
# UI5-FS-011: Synchronous module loading
# ---------------------------------------------------------------------------

UI5_FS_011 = ReviewRule(
    rule_id="UI5-FS-011",
    name="Synchronous module loading",
    name_de="Synchrones Modulladen",
    description=(
        "jQuery.sap.require or sap.ui.requireSync are synchronous module loading "
        "APIs that block the main thread and are deprecated. Use sap.ui.define or "
        "sap.ui.require with callbacks."
    ),
    description_de=(
        "jQuery.sap.require oder sap.ui.requireSync sind synchrone Modulladeaufrufe, "
        "die den Hauptthread blockieren und deprecated sind. sap.ui.define oder "
        "sap.ui.require mit Callbacks verwenden."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_FORMATTER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"(?:jQuery\.sap\.require\s*\(|sap\.ui\.requireSync\s*\()",
    category="deprecation",
    recommendation="Replace with sap.ui.define or asynchronous sap.ui.require.",
    recommendation_de="Durch sap.ui.define oder asynchrones sap.ui.require ersetzen.",
)

# ---------------------------------------------------------------------------
# UI5-FS-012: Missing metadata section in Component.js
# ---------------------------------------------------------------------------

UI5_FS_012 = ReviewRule(
    rule_id="UI5-FS-012",
    name="Missing metadata section in Component.js",
    name_de="Fehlende Metadata-Sektion in Component.js",
    description=(
        "A UI5 Component that extends UIComponent without a metadata section "
        "misses essential configuration such as manifest reference, routing, "
        "and model definitions."
    ),
    description_de=(
        "Eine UI5 Component, die UIComponent erweitert ohne Metadata-Sektion, "
        "verpasst essentielle Konfiguration wie Manifest-Referenz, Routing "
        "und Model-Definitionen."
    ),
    artifact_types=("UI5_CONTROLLER", "MIXED_FULLSTACK"),
    default_severity="IMPORTANT",
    pattern=r"UIComponent\.extend\s*\(",
    check_fn_name="check_missing_component_metadata",
    category="structure",
    recommendation='Add a metadata section with at least manifest: "json" to your Component.',
    recommendation_de='Eine Metadata-Sektion mit mindestens manifest: "json" zur Component hinzufuegen.',
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_missing_model_destroy(code: str) -> list[tuple[str, int]]:
    """Return a match if controller creates model in onInit but has no onExit."""
    has_model_creation = re.search(
        r"new\s+(?:JSONModel|ODataModel|ResourceModel)\s*\(", code
    )
    has_on_exit = re.search(r"\bonExit\b", code)

    if has_model_creation and not has_on_exit:
        return [(has_model_creation.group(), code[: has_model_creation.start()].count("\n") + 1)]
    return []


def check_missing_date_currency_formatter(code: str) -> list[tuple[str, int]]:
    """Return matches for date/currency bindings without type or formatter."""
    results: list[tuple[str, int]] = []
    # Look for XML attribute bindings that reference date/currency-like paths
    # without a type or formatter specification
    pattern = re.compile(
        r"""(?:text|value|number)\s*=\s*"\{[^}]*?"""
        r"""(?:[Dd]ate|[Cc]urrency|[Aa]mount|[Pp]rice|[Bb]etrag)[^}]*?\}""",
    )
    for match in pattern.finditer(code):
        context = match.group()
        # Skip if it already has type or formatter
        if re.search(r"(?:type|formatter)\s*:", context, re.IGNORECASE):
            continue
        line_num = code[: match.start()].count("\n") + 1
        results.append((match.group(), line_num))
    return results


def check_event_handler_not_unregistered(code: str) -> list[tuple[str, int]]:
    """Return matches for attach calls without corresponding detach calls."""
    results: list[tuple[str, int]] = []
    attach_pattern = re.compile(r"\.(attach(\w+))\s*\(")

    for match in attach_pattern.finditer(code):
        event_name = match.group(2)
        detach_name = f"detach{event_name}"
        if detach_name not in code:
            line_num = code[: match.start()].count("\n") + 1
            results.append((match.group(1), line_num))
    return results


def check_missing_accessibility(code: str) -> list[tuple[str, int]]:
    """Return matches for Icon controls without accessibility attributes."""
    results: list[tuple[str, int]] = []
    # Match Icon tags with optional namespace prefix (e.g., core:Icon)
    pattern = re.compile(
        r"<(?:\w+:)?(?:Icon|IconTabFilter)\s+[^>]*?/>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(code):
        tag_content = match.group()
        has_a11y = re.search(
            r"(?:ariaLabel|ariaLabelledBy|tooltip)", tag_content, re.IGNORECASE
        )
        if not has_a11y:
            line_num = code[: match.start()].count("\n") + 1
            results.append((match.group(), line_num))
    return results


def check_global_variable_in_controller(code: str) -> list[tuple[str, int]]:
    """Return matches for variable declarations before sap.ui.define."""
    results: list[tuple[str, int]] = []
    define_match = re.search(r"sap\.ui\.define\s*\(", code)
    if not define_match:
        return []

    # Check code before sap.ui.define for var/let/const declarations
    preamble = code[: define_match.start()]
    var_pattern = re.compile(r"^\s*(?:var|let|const)\s+\w+", re.MULTILINE)
    for match in var_pattern.finditer(preamble):
        line_num = preamble[: match.start()].count("\n") + 1
        results.append((match.group().strip(), line_num))
    return results


def check_duplicate_xml_structures(code: str) -> list[tuple[str, int]]:
    """Return a match if duplicate XML container structures are detected."""
    results: list[tuple[str, int]] = []
    # Look for repeated VBox/HBox/SimpleForm patterns (3+ occurrences)
    for tag in ("VBox", "HBox", "form:SimpleForm"):
        occurrences = [(m.start(), m.group()) for m in re.finditer(f"<{tag}[\\s>]", code)]
        if len(occurrences) >= 3:
            start = occurrences[0][0]
            line_num = code[:start].count("\n") + 1
            results.append((f"<{tag}> repeated {len(occurrences)} times", line_num))
    return results


def check_missing_component_metadata(code: str) -> list[tuple[str, int]]:
    """Return a match if UIComponent.extend is used without metadata."""
    extend_match = re.search(r"UIComponent\.extend\s*\(", code)
    if not extend_match:
        return []

    has_metadata = re.search(r"\bmetadata\s*:", code)
    if not has_metadata:
        return [(extend_match.group(), code[: extend_match.start()].count("\n") + 1)]
    return []


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

UI5_FREESTYLE_RULES: tuple[ReviewRule, ...] = (
    UI5_FS_001,
    UI5_FS_002,
    UI5_FS_003,
    UI5_FS_004,
    UI5_FS_005,
    UI5_FS_006,
    UI5_FS_007,
    UI5_FS_008,
    UI5_FS_009,
    UI5_FS_010,
    UI5_FS_011,
    UI5_FS_012,
)

UI5_FREESTYLE_CHECK_FUNCTIONS: dict[str, object] = {
    "check_missing_model_destroy": check_missing_model_destroy,
    "check_missing_date_currency_formatter": check_missing_date_currency_formatter,
    "check_event_handler_not_unregistered": check_event_handler_not_unregistered,
    "check_missing_accessibility": check_missing_accessibility,
    "check_global_variable_in_controller": check_global_variable_in_controller,
    "check_duplicate_xml_structures": check_duplicate_xml_structures,
    "check_missing_component_metadata": check_missing_component_metadata,
}
