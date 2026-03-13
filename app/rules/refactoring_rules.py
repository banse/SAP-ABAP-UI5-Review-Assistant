"""Refactoring rules for the SAP ABAP/UI5 Review Assistant.

Each ``RefactoringRule`` is a frozen dataclass that defines a refactoring
suggestion that can be triggered by specific finding categories.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RefactoringRule:
    """A refactoring suggestion triggered by specific finding categories."""

    rule_id: str
    name: str
    name_de: str
    category: str  # RefactoringCategory value
    trigger_finding_categories: tuple[str, ...]
    description: str
    description_de: str
    benefit: str
    benefit_de: str
    effort_hint: str | None = None


# ---------------------------------------------------------------------------
# Pre-defined refactoring rules
# ---------------------------------------------------------------------------

R_EXTRACT_METHOD = RefactoringRule(
    rule_id="REF-001",
    name="Extract Method",
    name_de="Methode extrahieren",
    category="TARGETED_STRUCTURE_IMPROVEMENT",
    trigger_finding_categories=("structure", "readability", "maintainability"),
    description=(
        "Extract long or complex code blocks into dedicated methods with "
        "descriptive names. Methods should have a single responsibility."
    ),
    description_de=(
        "Lange oder komplexe Codebloecke in eigene Methoden mit "
        "aussagekraeftigen Namen extrahieren. Methoden sollten eine "
        "einzelne Verantwortung haben."
    ),
    benefit=(
        "Improved readability, easier unit testing, and reduced cognitive "
        "complexity."
    ),
    benefit_de=(
        "Bessere Lesbarkeit, einfacheres Unit-Testing und reduzierte "
        "kognitive Komplexitaet."
    ),
    effort_hint="medium",
)

R_ERROR_HANDLING = RefactoringRule(
    rule_id="REF-002",
    name="Introduce Error Handling Pattern",
    name_de="Fehlerbehandlungsmuster einfuehren",
    category="SMALL_FIX",
    trigger_finding_categories=("error_handling",),
    description=(
        "Replace empty CATCH blocks and missing exception handling with "
        "structured patterns: log, message, re-raise, or graceful fallback."
    ),
    description_de=(
        "Leere CATCH-Bloecke und fehlende Ausnahmebehandlung durch "
        "strukturierte Muster ersetzen: Loggen, Meldung, Re-Raise oder "
        "Graceful Fallback."
    ),
    benefit=(
        "Prevents silent failures, improves debuggability, and makes "
        "error flows explicit."
    ),
    benefit_de=(
        "Verhindert stille Fehler, verbessert Debuggability und macht "
        "Fehlerfluesse explizit."
    ),
    effort_hint="small",
)

R_SELECT_FIELD_LIST = RefactoringRule(
    rule_id="REF-003",
    name="Replace SELECT * with Field List",
    name_de="SELECT * durch Feldliste ersetzen",
    category="SMALL_FIX",
    trigger_finding_categories=("performance",),
    description=(
        "Replace SELECT * with an explicit field list to reduce data "
        "transfer and improve query performance."
    ),
    description_de=(
        "SELECT * durch eine explizite Feldliste ersetzen, um "
        "Datentransfer zu reduzieren und Query-Performance zu verbessern."
    ),
    benefit=(
        "Reduced network and memory overhead; makes the data contract "
        "explicit."
    ),
    benefit_de=(
        "Reduzierter Netzwerk- und Speicher-Overhead; macht den "
        "Datenvertrag explizit."
    ),
    effort_hint="small",
)

R_REPLACE_NESTED_SELECT = RefactoringRule(
    rule_id="REF-004",
    name="Replace Nested SELECT with JOIN or FOR ALL ENTRIES",
    name_de="Verschachtelte SELECT durch JOIN oder FOR ALL ENTRIES ersetzen",
    category="TARGETED_STRUCTURE_IMPROVEMENT",
    trigger_finding_categories=("performance",),
    description=(
        "Replace SELECT statements inside loops with JOIN-based queries "
        "or FOR ALL ENTRIES IN to avoid N+1 query patterns."
    ),
    description_de=(
        "SELECT-Anweisungen in Schleifen durch JOIN-basierte Abfragen "
        "oder FOR ALL ENTRIES IN ersetzen, um N+1-Abfragemuster zu vermeiden."
    ),
    benefit=(
        "Dramatic performance improvement by reducing database roundtrips "
        "from N+1 to 1."
    ),
    benefit_de=(
        "Dramatische Performance-Verbesserung durch Reduktion der "
        "Datenbank-Roundtrips von N+1 auf 1."
    ),
    effort_hint="medium",
)

R_I18N_MODEL = RefactoringRule(
    rule_id="REF-005",
    name="Introduce i18n Model for UI Texts",
    name_de="i18n-Modell fuer UI-Texte einfuehren",
    category="MEDIUM_TERM_REFACTORING_HINT",
    trigger_finding_categories=("i18n", "readability"),
    description=(
        "Replace hardcoded strings in UI5 views and controllers with "
        "i18n model references for proper translation support."
    ),
    description_de=(
        "Hartcodierte Strings in UI5-Views und -Controllern durch "
        "i18n-Modell-Referenzen ersetzen fuer korrekte Uebersetzungsunterstuetzung."
    ),
    benefit=(
        "Enables multi-language support and centralizes text maintenance."
    ),
    benefit_de=(
        "Ermoeglicht Mehrsprachigkeit und zentralisiert die Textpflege."
    ),
    effort_hint="medium",
)

R_EXTRACT_FORMATTER = RefactoringRule(
    rule_id="REF-006",
    name="Extract Formatter Functions",
    name_de="Formatter-Funktionen extrahieren",
    category="TARGETED_STRUCTURE_IMPROVEMENT",
    trigger_finding_categories=("readability", "structure", "maintainability"),
    description=(
        "Extract complex expression bindings and inline logic from XML "
        "views into dedicated formatter functions in a separate module."
    ),
    description_de=(
        "Komplexe Expression-Bindings und Inline-Logik aus XML-Views "
        "in dedizierte Formatter-Funktionen in einem separaten Modul extrahieren."
    ),
    benefit=(
        "Cleaner views, testable formatting logic, and reusable formatters "
        "across views."
    ),
    benefit_de=(
        "Sauberere Views, testbare Formatierungslogik und wiederverwendbare "
        "Formatter ueber Views hinweg."
    ),
    effort_hint="medium",
)

R_STRUCTURED_EXCEPTIONS = RefactoringRule(
    rule_id="REF-007",
    name="Add Structured Exception Handling",
    name_de="Strukturierte Ausnahmebehandlung ergaenzen",
    category="MEDIUM_TERM_REFACTORING_HINT",
    trigger_finding_categories=("error_handling", "security"),
    description=(
        "Introduce class-based exceptions (CX_ hierarchy) instead of "
        "SY-SUBRC checks or untyped CATCH blocks. Use dedicated exception "
        "classes per domain."
    ),
    description_de=(
        "Klassenbasierte Ausnahmen (CX_-Hierarchie) statt SY-SUBRC-Pruefungen "
        "oder untypisierter CATCH-Bloecke einfuehren. Dedizierte Ausnahmeklassen "
        "pro Domaene verwenden."
    ),
    benefit=(
        "Type-safe error handling, cleaner control flow, and better "
        "alignment with RAP and clean ABAP patterns."
    ),
    benefit_de=(
        "Typsichere Fehlerbehandlung, saubererer Kontrollfluss und bessere "
        "Ausrichtung an RAP- und Clean-ABAP-Mustern."
    ),
    effort_hint="large",
)

R_MODERNIZE_SYNTAX = RefactoringRule(
    rule_id="REF-008",
    name="Modernize ABAP Syntax (Inline Declarations)",
    name_de="ABAP-Syntax modernisieren (Inline-Deklarationen)",
    category="NOT_IMMEDIATE_REBUILD",
    trigger_finding_categories=("style", "readability", "maintainability"),
    description=(
        "Replace legacy DATA declarations with inline declarations "
        "(DATA(...), FINAL(...), VALUE #(...)) where the SAP release supports it."
    ),
    description_de=(
        "Legacy-DATA-Deklarationen durch Inline-Deklarationen "
        "(DATA(...), FINAL(...), VALUE #(...)) ersetzen, sofern das SAP-Release "
        "dies unterstuetzt."
    ),
    benefit=(
        "Reduced boilerplate, improved readability, and alignment with "
        "modern ABAP guidelines."
    ),
    benefit_de=(
        "Weniger Boilerplate, verbesserte Lesbarkeit und Ausrichtung an "
        "modernen ABAP-Richtlinien."
    ),
    effort_hint="large",
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_REFACTORING_RULES: tuple[RefactoringRule, ...] = (
    R_EXTRACT_METHOD,
    R_ERROR_HANDLING,
    R_SELECT_FIELD_LIST,
    R_REPLACE_NESTED_SELECT,
    R_I18N_MODEL,
    R_EXTRACT_FORMATTER,
    R_STRUCTURED_EXCEPTIONS,
    R_MODERNIZE_SYNTAX,
)
