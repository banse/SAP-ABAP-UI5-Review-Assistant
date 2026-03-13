"""ABAP error handling and testability review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance that detects common ABAP
error handling and testability issues, with bilingual EN/DE metadata.
"""

from __future__ import annotations

import re
from collections import Counter

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# ABAP-ERRH: Error Handling & Testability
# ---------------------------------------------------------------------------

ABAP_ERRH_001 = ReviewRule(
    rule_id="ABAP-ERRH-001",
    name="Missing CLEANUP block in TRY/CATCH",
    name_de="Fehlender CLEANUP-Block in TRY/CATCH",
    description=(
        "When resources (files, locks, memory) are acquired before or "
        "inside a TRY block, a CLEANUP block should be used to ensure "
        "proper resource release even when exceptions propagate."
    ),
    description_de=(
        "Wenn Ressourcen (Dateien, Sperren, Speicher) vor oder innerhalb "
        "eines TRY-Blocks erworben werden, sollte ein CLEANUP-Block "
        "verwendet werden, um die Freigabe auch bei Ausnahmen sicherzustellen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bTRY\b",
    check_fn_name="check_missing_cleanup",
    category="error_handling",
    recommendation=(
        "Add a CLEANUP block to the TRY statement to release resources "
        "(locks, open files, memory) when exceptions propagate."
    ),
    recommendation_de=(
        "Einen CLEANUP-Block zur TRY-Anweisung hinzufuegen, um Ressourcen "
        "(Sperren, offene Dateien, Speicher) bei Ausnahmen freizugeben."
    ),
)

ABAP_ERRH_002 = ReviewRule(
    rule_id="ABAP-ERRH-002",
    name="RAISE EXCEPTION without message",
    name_de="RAISE EXCEPTION ohne Nachricht",
    description=(
        "Raising an exception without a MESSAGE makes it difficult to "
        "diagnose issues in production. Always include a meaningful "
        "exception message."
    ),
    description_de=(
        "Das Ausloesen einer Ausnahme ohne MESSAGE erschwert die "
        "Fehlerdiagnose in der Produktion. Immer eine aussagekraeftige "
        "Ausnahmenachricht angeben."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bRAISE\s+EXCEPTION\s+TYPE\b",
    check_fn_name="check_raise_without_message",
    category="error_handling",
    recommendation=(
        "Add a MESSAGE or EXPORTING clause to RAISE EXCEPTION TYPE to "
        "provide diagnostic information."
    ),
    recommendation_de=(
        "Eine MESSAGE- oder EXPORTING-Klausel zu RAISE EXCEPTION TYPE "
        "hinzufuegen, um Diagnoseinformationen bereitzustellen."
    ),
)

ABAP_ERRH_003 = ReviewRule(
    rule_id="ABAP-ERRH-003",
    name="Missing RESUMABLE exception handling",
    name_de="Fehlende RESUMABLE-Ausnahmebehandlung",
    description=(
        "When a method signature declares RAISING a resumable exception, "
        "callers should handle it with RESUME to allow graceful recovery."
    ),
    description_de=(
        "Wenn eine Methodensignatur eine resumable Ausnahme deklariert, "
        "sollten Aufrufer sie mit RESUME behandeln, um eine graceful "
        "Recovery zu ermoeglichen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bRAISING\s+RESUMABLE\b",
    pattern_flags=re.IGNORECASE,
    category="error_handling",
    recommendation=(
        "Handle RESUMABLE exceptions with CATCH ... BEFORE UNWIND and "
        "RESUME where appropriate."
    ),
    recommendation_de=(
        "RESUMABLE-Ausnahmen mit CATCH ... BEFORE UNWIND und RESUME "
        "behandeln, wo angemessen."
    ),
)

ABAP_ERRH_004 = ReviewRule(
    rule_id="ABAP-ERRH-004",
    name="Method signature unfriendly to test doubles",
    name_de="Methodensignatur ungeeignet fuer Test-Doubles",
    description=(
        "Using concrete class references (TYPE REF TO zcl_*) instead of "
        "interfaces (TYPE REF TO zif_*) in method signatures prevents "
        "injection of test doubles and mocks."
    ),
    description_de=(
        "Die Verwendung konkreter Klassenreferenzen (TYPE REF TO zcl_*) "
        "statt Interfaces (TYPE REF TO zif_*) in Methodensignaturen "
        "verhindert die Injection von Test-Doubles und Mocks."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bTYPE\s+REF\s+TO\s+zcl_\w+",
    pattern_flags=re.IGNORECASE,
    category="testability",
    recommendation=(
        "Use interface references (TYPE REF TO zif_*) instead of concrete "
        "class references to enable test double injection."
    ),
    recommendation_de=(
        "Interface-Referenzen (TYPE REF TO zif_*) statt konkreter "
        "Klassenreferenzen verwenden, um Test-Double-Injection zu "
        "ermoeglichen."
    ),
)

ABAP_ERRH_005 = ReviewRule(
    rule_id="ABAP-ERRH-005",
    name="Global data dependency in instance method",
    name_de="Globale Datenabhaengigkeit in Instanzmethode",
    description=(
        "Instance methods that directly read or write CLASS-DATA (static "
        "attributes) create hidden global state dependencies that make "
        "testing and reasoning about behavior difficult."
    ),
    description_de=(
        "Instanzmethoden, die direkt CLASS-DATA (statische Attribute) "
        "lesen oder schreiben, erzeugen versteckte globale "
        "Zustandsabhaengigkeiten, die Tests und Nachvollziehbarkeit "
        "erschweren."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bCLASS-DATA\b",
    check_fn_name="check_global_data_dependency",
    category="testability",
    recommendation=(
        "Avoid reading or writing CLASS-DATA from instance methods. "
        "Pass state through method parameters or instance attributes."
    ),
    recommendation_de=(
        "CLASS-DATA nicht aus Instanzmethoden lesen oder schreiben. "
        "Zustand ueber Methodenparameter oder Instanzattribute uebergeben."
    ),
)

ABAP_ERRH_006 = ReviewRule(
    rule_id="ABAP-ERRH-006",
    name="Missing constructor injection",
    name_de="Fehlende Konstruktor-Injection",
    description=(
        "Creating dependencies directly with CREATE OBJECT or NEW inside "
        "methods instead of injecting them through the constructor makes "
        "the class hard to test and tightly coupled."
    ),
    description_de=(
        "Das direkte Erstellen von Abhaengigkeiten mit CREATE OBJECT oder "
        "NEW in Methoden statt Injection ueber den Konstruktor macht die "
        "Klasse schwer testbar und eng gekoppelt."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bCREATE\s+OBJECT\b|\bNEW\s+zcl_\w+\s*\(",
    check_fn_name="check_missing_constructor_injection",
    category="testability",
    recommendation=(
        "Inject dependencies through the constructor and store them "
        "as instance attributes. Use CREATE OBJECT / NEW only in "
        "factory methods."
    ),
    recommendation_de=(
        "Abhaengigkeiten ueber den Konstruktor injizieren und als "
        "Instanzattribute speichern. CREATE OBJECT / NEW nur in "
        "Factory-Methoden verwenden."
    ),
)

ABAP_ERRH_007 = ReviewRule(
    rule_id="ABAP-ERRH-007",
    name="Factory pattern absence",
    name_de="Fehlendes Factory-Pattern",
    description=(
        "Multiple CREATE OBJECT or NEW statements for the same class "
        "in different methods indicate a missing factory pattern, leading "
        "to duplicated instantiation logic."
    ),
    description_de=(
        "Mehrfache CREATE OBJECT- oder NEW-Anweisungen fuer dieselbe "
        "Klasse in verschiedenen Methoden deuten auf ein fehlendes "
        "Factory-Pattern hin."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bCREATE\s+OBJECT\b|\bNEW\s+\w+\s*\(",
    check_fn_name="check_factory_pattern_absence",
    category="testability",
    recommendation=(
        "Extract object creation into a factory method or use "
        "constructor injection to centralize instantiation."
    ),
    recommendation_de=(
        "Objekterzeugung in eine Factory-Methode extrahieren oder "
        "Konstruktor-Injection verwenden."
    ),
)

ABAP_ERRH_008 = ReviewRule(
    rule_id="ABAP-ERRH-008",
    name="CATCH without INTO",
    name_de="CATCH ohne INTO",
    description=(
        "Catching an exception without INTO discards the exception "
        "object, making it impossible to inspect the error message, "
        "previous exceptions, or the call stack."
    ),
    description_de=(
        "Das Abfangen einer Ausnahme ohne INTO verwirft das "
        "Ausnahmeobjekt, sodass Fehlermeldung, vorherige Ausnahmen "
        "und Aufrufstack nicht inspiziert werden koennen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bCATCH\s+\w+",
    check_fn_name="check_catch_without_into",
    category="error_handling",
    recommendation=(
        "Add INTO DATA(lx_error) to the CATCH statement to capture "
        "the exception object for logging or re-raising."
    ),
    recommendation_de=(
        "INTO DATA(lx_error) zur CATCH-Anweisung hinzufuegen, um das "
        "Ausnahmeobjekt fuer Logging oder erneutes Ausloesen zu erfassen."
    ),
)

ABAP_ERRH_009 = ReviewRule(
    rule_id="ABAP-ERRH-009",
    name="Missing precondition check in public method",
    name_de="Fehlende Vorbedingungspruefung in oeffentlicher Methode",
    description=(
        "Public methods should validate their input parameters early "
        "with ASSERT or RAISE EXCEPTION to fail fast and provide clear "
        "error messages."
    ),
    description_de=(
        "Oeffentliche Methoden sollten ihre Eingabeparameter fruehzeitig "
        "mit ASSERT oder RAISE EXCEPTION validieren, um schnell zu "
        "fehlschlagen und klare Fehlermeldungen zu liefern."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bMETHOD\b",
    check_fn_name="check_missing_precondition",
    category="error_handling",
    recommendation=(
        "Add parameter validation using ASSERT or RAISE EXCEPTION at "
        "the beginning of public methods."
    ),
    recommendation_de=(
        "Parametervalidierung mit ASSERT oder RAISE EXCEPTION am Anfang "
        "oeffentlicher Methoden hinzufuegen."
    ),
)

ABAP_ERRH_010 = ReviewRule(
    rule_id="ABAP-ERRH-010",
    name="Missing sy-subrc check after internal table operation",
    name_de="Fehlende sy-subrc-Pruefung nach interner Tabellenoperation",
    description=(
        "Operations like READ TABLE and LOOP AT set sy-subrc to indicate "
        "whether an entry was found. Not checking sy-subrc can lead to "
        "processing invalid or initial data."
    ),
    description_de=(
        "Operationen wie READ TABLE und LOOP AT setzen sy-subrc als "
        "Indikator, ob ein Eintrag gefunden wurde. Ohne Pruefung koennen "
        "ungueltige oder initiale Daten verarbeitet werden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bREAD\s+TABLE\b",
    check_fn_name="check_read_table_without_subrc",
    category="error_handling",
    recommendation=(
        "Check sy-subrc immediately after READ TABLE or use inline "
        "expressions like VALUE #( itab[ key = val ] OPTIONAL )."
    ),
    recommendation_de=(
        "sy-subrc direkt nach READ TABLE pruefen oder Inline-Ausdruecke "
        "wie VALUE #( itab[ key = val ] OPTIONAL ) verwenden."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------


def check_missing_cleanup(code: str) -> list[tuple[str, int]]:
    """Return matches for TRY blocks that have resource ops but no CLEANUP."""
    results: list[tuple[str, int]] = []
    resource_pattern = re.compile(
        r"(?:ENQUEUE_|DEQUEUE_|OPEN\s+DATASET|'ENQUEUE)",
        re.IGNORECASE,
    )
    # Find TRY ... ENDTRY blocks
    try_pattern = re.compile(
        r"\bTRY\b(.*?)\bENDTRY\b",
        re.IGNORECASE | re.DOTALL,
    )
    for m in try_pattern.finditer(code):
        block = m.group(1)
        has_resource = resource_pattern.search(block)
        has_cleanup = re.search(r"\bCLEANUP\b", block, re.IGNORECASE)
        if has_resource and not has_cleanup:
            line_num = code[: m.start()].count("\n") + 1
            results.append(("TRY without CLEANUP (resources acquired)", line_num))
    return results


def check_raise_without_message(code: str) -> list[tuple[str, int]]:
    """Return matches for RAISE EXCEPTION TYPE without MESSAGE or EXPORTING."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"\bRAISE\s+EXCEPTION\s+TYPE\s+\w+(.*?)\.",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(code):
        remainder = m.group(1)
        has_message = re.search(r"\bMESSAGE\b", remainder, re.IGNORECASE)
        has_exporting = re.search(r"\bEXPORTING\b", remainder, re.IGNORECASE)
        if not has_message and not has_exporting:
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(0).split("\n")[0].strip(), line_num))
    return results


def check_global_data_dependency(code: str) -> list[tuple[str, int]]:
    """Return matches for instance methods accessing CLASS-DATA."""
    results: list[tuple[str, int]] = []
    # Collect CLASS-DATA names
    class_data_names: set[str] = set()
    for m in re.finditer(
        r"^\s*CLASS-DATA\s+(\w+)\b", code, re.IGNORECASE | re.MULTILINE
    ):
        class_data_names.add(m.group(1).lower())

    if not class_data_names:
        return []

    # Find instance methods and check if they reference CLASS-DATA vars
    lines = code.split("\n")
    in_method = False
    method_name = ""
    method_start = 0
    is_class_method = False

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            in_method = True
            method_name = line.strip()
            method_start = i
            # If it is a class-method, skip
            is_class_method = False
        elif stripped == "ENDMETHOD." and in_method:
            in_method = False
        elif in_method and not is_class_method:
            for var in class_data_names:
                if re.search(rf"\b{re.escape(var)}\b", line, re.IGNORECASE):
                    results.append(
                        (f"{method_name} accesses CLASS-DATA {var}", method_start + 1)
                    )
                    break
            if results and results[-1][1] == method_start + 1:
                in_method = False  # only report once per method
    return results


def check_missing_constructor_injection(code: str) -> list[tuple[str, int]]:
    """Return matches for CREATE OBJECT/NEW in non-constructor methods."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    in_method = False
    method_name = ""
    is_constructor = False

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            in_method = True
            method_name = stripped.replace("METHOD ", "").rstrip(".")
            is_constructor = method_name.upper() == "CONSTRUCTOR"
        elif stripped == "ENDMETHOD.":
            in_method = False
            is_constructor = False
        elif in_method and not is_constructor:
            if re.search(
                r"\bCREATE\s+OBJECT\s+\w+\s+TYPE\s+zcl_\w+",
                line, re.IGNORECASE
            ) or re.search(
                r"\bNEW\s+zcl_\w+\s*\(", line, re.IGNORECASE
            ):
                results.append((line.strip(), i + 1))
    return results


def check_factory_pattern_absence(code: str) -> list[tuple[str, int]]:
    """Return matches when the same class is instantiated in multiple methods."""
    results: list[tuple[str, int]] = []
    # Find all CREATE OBJECT TYPE <class> or NEW <class>(
    create_pattern = re.compile(
        r"\bCREATE\s+OBJECT\s+\w+\s+TYPE\s+(\w+)",
        re.IGNORECASE,
    )
    new_pattern = re.compile(
        r"\bNEW\s+(\w+)\s*\(",
        re.IGNORECASE,
    )

    classes: list[tuple[str, int]] = []
    for m in create_pattern.finditer(code):
        line_num = code[: m.start()].count("\n") + 1
        classes.append((m.group(1).lower(), line_num))
    for m in new_pattern.finditer(code):
        line_num = code[: m.start()].count("\n") + 1
        classes.append((m.group(1).lower(), line_num))

    counts: Counter[str] = Counter(cls for cls, _ in classes)
    reported: set[str] = set()
    for cls, line_num in classes:
        if counts[cls] >= 3 and cls not in reported:
            results.append(
                (f"{cls} instantiated {counts[cls]} times", line_num)
            )
            reported.add(cls)
    return results


def check_catch_without_into(code: str) -> list[tuple[str, int]]:
    """Return matches for CATCH without INTO (exception not captured)."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"\bCATCH\s+([\w\s]+)\.",
        re.IGNORECASE,
    )
    for m in pattern.finditer(code):
        catch_text = m.group(0)
        if not re.search(r"\bINTO\b", catch_text, re.IGNORECASE):
            # Check it's not an empty catch (already covered by ABAP-ERR-001)
            # We only flag non-empty catches without INTO
            line_num = code[: m.start()].count("\n") + 1
            # Look ahead for content between this CATCH and ENDTRY/next CATCH
            after = code[m.end():]
            next_boundary = re.search(
                r"\b(?:ENDTRY|CATCH|CLEANUP)\b", after, re.IGNORECASE
            )
            if next_boundary:
                between = after[:next_boundary.start()].strip()
                if between:  # has statements = non-empty catch
                    results.append((catch_text.strip(), line_num))
    return results


def check_missing_precondition(code: str) -> list[tuple[str, int]]:
    """Return matches for methods with IMPORTING params but no validation."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    in_method = False
    method_name = ""
    method_start = 0
    has_importing_param = False
    has_validation = False

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            # Check if previous method had issues
            if in_method and has_importing_param and not has_validation:
                results.append((method_name, method_start + 1))
            in_method = True
            method_name = line.strip()
            method_start = i
            has_importing_param = False
            has_validation = False
        elif stripped == "ENDMETHOD.":
            if in_method and has_importing_param and not has_validation:
                results.append((method_name, method_start + 1))
            in_method = False
        elif in_method:
            if re.search(r"\biv_\w+\b|\bis_\w+\b|\bit_\w+\b|\bio_\w+\b",
                         line, re.IGNORECASE):
                has_importing_param = True
            if re.search(
                r"\b(?:ASSERT|RAISE\s+EXCEPTION)\b",
                line, re.IGNORECASE,
            ):
                has_validation = True
            # Also accept IF checks on importing params as validation
            if re.search(
                r"\bIF\s+iv_\w+\s+IS\s+(?:INITIAL|NOT\s+BOUND)\b",
                line, re.IGNORECASE,
            ):
                has_validation = True
    return results


def check_read_table_without_subrc(code: str) -> list[tuple[str, int]]:
    """Return matches for READ TABLE without subsequent sy-subrc check."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"\bREAD\s+TABLE\b[^.]*\.",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(code):
        stmt = m.group(0)
        # Skip if using TRANSPORTING NO FIELDS with inline (index-like)
        # or REFERENCE/ASSIGNING (still should check subrc)
        after = code[m.end(): m.end() + 200]
        has_subrc_check = re.match(
            r"\s*IF\s+sy-subrc\b",
            after,
            re.IGNORECASE,
        )
        if not has_subrc_check:
            line_num = code[: m.start()].count("\n") + 1
            results.append((stmt.split("\n")[0].strip(), line_num))
    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ABAP_ERROR_HANDLING_RULES: tuple[ReviewRule, ...] = (
    ABAP_ERRH_001,
    ABAP_ERRH_002,
    ABAP_ERRH_003,
    ABAP_ERRH_004,
    ABAP_ERRH_005,
    ABAP_ERRH_006,
    ABAP_ERRH_007,
    ABAP_ERRH_008,
    ABAP_ERRH_009,
    ABAP_ERRH_010,
)

ABAP_ERROR_HANDLING_CHECK_FUNCTIONS: dict[str, object] = {
    "check_missing_cleanup": check_missing_cleanup,
    "check_raise_without_message": check_raise_without_message,
    "check_global_data_dependency": check_global_data_dependency,
    "check_missing_constructor_injection": check_missing_constructor_injection,
    "check_factory_pattern_absence": check_factory_pattern_absence,
    "check_catch_without_into": check_catch_without_into,
    "check_missing_precondition": check_missing_precondition,
    "check_read_table_without_subrc": check_read_table_without_subrc,
}
