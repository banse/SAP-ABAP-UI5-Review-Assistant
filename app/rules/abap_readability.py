"""ABAP readability and structure review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance that detects common ABAP
readability and structural issues, with bilingual EN/DE metadata.
"""

from __future__ import annotations

import re
from collections import Counter

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# ABAP-RDBL: Readability & Structure
# ---------------------------------------------------------------------------

ABAP_RDBL_001 = ReviewRule(
    rule_id="ABAP-RDBL-001",
    name="Naming convention violation",
    name_de="Namenskonventionsverletzung",
    description=(
        "Variable names should follow the standard ABAP prefix convention: "
        "lv_ for local variables, lt_ for local tables, ls_ for local "
        "structures, lo_ for local object references, and similar prefixes "
        "for global/instance scope (gv_, gt_, gs_, go_, mv_, mt_, ms_, mo_)."
    ),
    description_de=(
        "Variablennamen sollten der ABAP-Praefix-Konvention folgen: "
        "lv_ fuer lokale Variablen, lt_ fuer lokale Tabellen, ls_ fuer "
        "lokale Strukturen, lo_ fuer lokale Objektreferenzen und "
        "entsprechende Praefixe fuer globalen/Instanz-Scope "
        "(gv_, gt_, gs_, go_, mv_, mt_, ms_, mo_)."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"^\s*DATA\s+\w+",
    check_fn_name="check_naming_convention",
    category="readability",
    recommendation=(
        "Rename variables to follow the lv_/lt_/ls_/lo_ prefix convention "
        "for local scope, or mv_/mt_/ms_/mo_ for instance attributes."
    ),
    recommendation_de=(
        "Variablen nach der lv_/lt_/ls_/lo_-Praefix-Konvention fuer lokalen "
        "Scope bzw. mv_/mt_/ms_/mo_ fuer Instanzattribute umbenennen."
    ),
)

ABAP_RDBL_002 = ReviewRule(
    rule_id="ABAP-RDBL-002",
    name="Method has too many parameters",
    name_de="Methode hat zu viele Parameter",
    description=(
        "Methods with more than 5 IMPORTING, EXPORTING, or CHANGING "
        "parameters are hard to call, understand, and maintain. Consider "
        "grouping parameters into a structure or splitting the method."
    ),
    description_de=(
        "Methoden mit mehr als 5 IMPORTING-, EXPORTING- oder CHANGING-"
        "Parametern sind schwer aufrufbar, verstaendlich und wartbar. "
        "Parameter in eine Struktur gruppieren oder die Methode aufteilen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bMETHODS\b",
    check_fn_name="check_too_many_params",
    category="readability",
    recommendation=(
        "Reduce the number of parameters by grouping related ones into a "
        "structure or by splitting the method into smaller methods."
    ),
    recommendation_de=(
        "Die Parameteranzahl reduzieren, indem zusammengehoerige Parameter "
        "in einer Struktur gruppiert oder die Methode aufgeteilt wird."
    ),
)

ABAP_RDBL_003 = ReviewRule(
    rule_id="ABAP-RDBL-003",
    name="Commented-out code detected",
    name_de="Auskommentierter Code erkannt",
    description=(
        "Lines that appear to be commented-out ABAP statements clutter the "
        "code and reduce readability. Version control should be used instead "
        "of keeping old code as comments."
    ),
    description_de=(
        "Zeilen mit auskommentiertem ABAP-Code verschlechtern die "
        "Lesbarkeit. Versionskontrolle statt alter Code-Kommentare verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=(
        r"^\s*\*\s*(?:DATA|SELECT|IF|LOOP|CALL|METHOD|CLASS|WRITE|MOVE|"
        r"APPEND|INSERT|DELETE|MODIFY|READ|CLEAR|REFRESH|DO|WHILE|CASE|"
        r"TRY|CATCH|RAISE|CREATE|PERFORM|FORM|ENDFORM|ENDMETHOD|ENDIF|"
        r"ENDLOOP|ENDDO|ENDWHILE|ENDCASE|ENDTRY|ENDCLASS)\b"
    ),
    pattern_flags=re.IGNORECASE | re.MULTILINE,
    category="readability",
    recommendation=(
        "Remove commented-out code. Use version control to preserve "
        "historical code if needed."
    ),
    recommendation_de=(
        "Auskommentierten Code entfernen. Versionskontrolle verwenden, "
        "um historischen Code bei Bedarf aufzubewahren."
    ),
)

ABAP_RDBL_004 = ReviewRule(
    rule_id="ABAP-RDBL-004",
    name="Dead code after RETURN/RAISE",
    name_de="Toter Code nach RETURN/RAISE",
    description=(
        "Statements after an unconditional RETURN or RAISE EXCEPTION "
        "are unreachable and indicate a logic error or forgotten cleanup."
    ),
    description_de=(
        "Anweisungen nach einem unbedingten RETURN oder RAISE EXCEPTION "
        "sind unerreichbar und deuten auf einen Logikfehler oder vergessene "
        "Bereinigung hin."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bRETURN\b|\bRAISE\s+EXCEPTION\b",
    check_fn_name="check_dead_code_after_return",
    category="readability",
    recommendation=(
        "Remove unreachable statements after RETURN or RAISE EXCEPTION, "
        "or restructure the control flow."
    ),
    recommendation_de=(
        "Unerreichbare Anweisungen nach RETURN oder RAISE EXCEPTION "
        "entfernen oder den Kontrollfluss umstrukturieren."
    ),
)

ABAP_RDBL_005 = ReviewRule(
    rule_id="ABAP-RDBL-005",
    name="String literal duplication",
    name_de="Doppelte String-Literale",
    description=(
        "The same string literal appears multiple times. Repeated literals "
        "are error-prone when changes are needed and should be extracted "
        "into constants."
    ),
    description_de=(
        "Dasselbe String-Literal kommt mehrfach vor. Wiederholte Literale "
        "sind bei Aenderungen fehleranfaellig und sollten als Konstanten "
        "extrahiert werden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"'[^']{2,}'",
    check_fn_name="check_string_literal_duplication",
    category="readability",
    recommendation=(
        "Extract duplicated string literals into CONSTANTS declarations."
    ),
    recommendation_de=(
        "Doppelte String-Literale in CONSTANTS-Deklarationen extrahieren."
    ),
)

ABAP_RDBL_006 = ReviewRule(
    rule_id="ABAP-RDBL-006",
    name="Obsolete type usage in method signature",
    name_de="Veraltete Typverwendung in Methodensignatur",
    description=(
        "Using generic types like TYPE C, TYPE N, or TYPE P without "
        "length or decimal specification in method signatures leads to "
        "implicit type conversion and maintenance issues."
    ),
    description_de=(
        "Generische Typen wie TYPE C, TYPE N oder TYPE P ohne Laengen- "
        "oder Dezimalangabe in Methodensignaturen fuehren zu impliziten "
        "Typkonvertierungen und Wartungsproblemen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bTYPE\s+[CNP]\b(?!\s*LENGTH|\s*DECIMALS|\s*VALUE|\w)",
    pattern_flags=re.IGNORECASE | re.MULTILINE,
    category="readability",
    recommendation=(
        "Replace generic types with domain-specific types or add LENGTH "
        "and DECIMALS specifications."
    ),
    recommendation_de=(
        "Generische Typen durch domaenenspezifische Typen ersetzen oder "
        "LENGTH- und DECIMALS-Angaben ergaenzen."
    ),
)

ABAP_RDBL_007 = ReviewRule(
    rule_id="ABAP-RDBL-007",
    name="Missing method documentation",
    name_de="Fehlende Methodendokumentation",
    description=(
        "Public and protected methods should have ABAP Doc comments "
        "(lines starting with \"! ) before their definition to describe "
        "purpose, parameters, and return values."
    ),
    description_de=(
        "Oeffentliche und geschuetzte Methoden sollten ABAP-Doc-Kommentare "
        "(Zeilen mit \"! ) vor ihrer Definition haben, um Zweck, Parameter "
        "und Rueckgabewerte zu beschreiben."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bMETHODS\b",
    check_fn_name="check_missing_method_doc",
    category="readability",
    recommendation=(
        "Add ABAP Doc comments (\"! ) before each public/protected method "
        "definition to document its purpose."
    ),
    recommendation_de=(
        "ABAP-Doc-Kommentare (\"! ) vor jeder oeffentlichen/geschuetzten "
        "Methodendefinition hinzufuegen."
    ),
)

ABAP_RDBL_008 = ReviewRule(
    rule_id="ABAP-RDBL-008",
    name="Inline declaration opportunity",
    name_de="Moeglichkeit zur Inline-Deklaration",
    description=(
        "A DATA declaration followed immediately by an assignment on the "
        "next line could be simplified using inline declaration DATA(...)."
    ),
    description_de=(
        "Eine DATA-Deklaration, der unmittelbar eine Zuweisung folgt, "
        "koennte durch Inline-Deklaration DATA(...) vereinfacht werden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"^\s*DATA\s+\w+",
    check_fn_name="check_inline_declaration_opportunity",
    category="readability",
    recommendation=(
        "Use inline declarations like DATA(lv_var) = ... instead of "
        "separate DATA and assignment statements."
    ),
    recommendation_de=(
        "Inline-Deklarationen wie DATA(lv_var) = ... statt separater "
        "DATA- und Zuweisungsanweisungen verwenden."
    ),
)

ABAP_RDBL_009 = ReviewRule(
    rule_id="ABAP-RDBL-009",
    name="Magic number detected",
    name_de="Magische Zahl erkannt",
    description=(
        "Hardcoded numeric literals in IF, CASE, or WHEN conditions "
        "reduce readability and maintainability. Use named constants."
    ),
    description_de=(
        "Hartcodierte numerische Literale in IF-, CASE- oder WHEN-"
        "Bedingungen verschlechtern Lesbarkeit und Wartbarkeit. "
        "Benannte Konstanten verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"(?:^\s*(?:IF|ELSEIF|WHEN)\b.*\b(?:[2-9]\d{1,}|\d{3,})\b)",
    pattern_flags=re.IGNORECASE | re.MULTILINE,
    category="readability",
    recommendation=(
        "Replace magic numbers with named CONSTANTS that explain "
        "the business meaning."
    ),
    recommendation_de=(
        "Magische Zahlen durch benannte CONSTANTS ersetzen, die die "
        "fachliche Bedeutung erklaeren."
    ),
)

ABAP_RDBL_010 = ReviewRule(
    rule_id="ABAP-RDBL-010",
    name="CLASS-DATA (static attribute) overuse",
    name_de="CLASS-DATA (statisches Attribut) uebermaeßige Nutzung",
    description=(
        "Excessive use of CLASS-DATA introduces global mutable state "
        "into the class, making testing difficult and creating hidden "
        "dependencies between methods."
    ),
    description_de=(
        "Uebermaeßige Nutzung von CLASS-DATA fuehrt globalen veraenderbaren "
        "Zustand in die Klasse ein, erschwert Tests und erzeugt versteckte "
        "Abhaengigkeiten zwischen Methoden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bCLASS-DATA\b",
    check_fn_name="check_class_data_overuse",
    category="readability",
    recommendation=(
        "Minimize CLASS-DATA usage. Prefer instance attributes or method "
        "parameters to avoid shared mutable state."
    ),
    recommendation_de=(
        "CLASS-DATA-Nutzung minimieren. Instanzattribute oder "
        "Methodenparameter bevorzugen, um gemeinsamen veraenderbaren "
        "Zustand zu vermeiden."
    ),
)

ABAP_RDBL_011 = ReviewRule(
    rule_id="ABAP-RDBL-011",
    name="Too many local variables in method",
    name_de="Zu viele lokale Variablen in Methode",
    description=(
        "Methods with more than 10 DATA declarations are likely doing too "
        "much. Consider splitting into smaller methods."
    ),
    description_de=(
        "Methoden mit mehr als 10 DATA-Deklarationen machen wahrscheinlich "
        "zu viel. In kleinere Methoden aufteilen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bMETHOD\b",
    check_fn_name="check_too_many_local_vars",
    category="readability",
    recommendation=(
        "Reduce the number of local variables by extracting logic into "
        "helper methods or using inline declarations."
    ),
    recommendation_de=(
        "Anzahl lokaler Variablen reduzieren durch Extraktion von Logik "
        "in Hilfsmethoden oder Nutzung von Inline-Deklarationen."
    ),
)

ABAP_RDBL_012 = ReviewRule(
    rule_id="ABAP-RDBL-012",
    name="Missing FINAL for read-only variable",
    name_de="Fehlendes FINAL fuer schreibgeschuetzte Variable",
    description=(
        "Variables declared with DATA that are assigned only once could "
        "benefit from FINAL to signal immutability and prevent accidental "
        "reassignment."
    ),
    description_de=(
        "Variablen, die mit DATA deklariert und nur einmal zugewiesen "
        "werden, koennten von FINAL profitieren, um Unveraenderlichkeit "
        "zu signalisieren und versehentliche Neuzuweisung zu verhindern."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"^\s*DATA\s+\w+",
    check_fn_name="check_missing_final",
    category="readability",
    recommendation=(
        "Use FINAL(...) for variables that are assigned only once to "
        "signal immutability."
    ),
    recommendation_de=(
        "FINAL(...) fuer Variablen verwenden, die nur einmal zugewiesen "
        "werden, um Unveraenderlichkeit zu signalisieren."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions
# ---------------------------------------------------------------------------

_VALID_PREFIXES = {
    "lv_", "lt_", "ls_", "lo_", "lr_", "lx_",
    "gv_", "gt_", "gs_", "go_", "gr_", "gx_",
    "mv_", "mt_", "ms_", "mo_", "mr_", "mx_",
    "iv_", "it_", "is_", "io_", "ir_",
    "ev_", "et_", "es_", "eo_", "er_",
    "cv_", "ct_", "cs_", "co_", "cr_",
    "rv_", "rt_", "rs_", "ro_", "rr_",
}


def check_naming_convention(code: str) -> list[tuple[str, int]]:
    """Return matches for DATA declarations that violate prefix conventions."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(
        r"^\s*DATA\s+(\w+)\s+TYPE\b",
        re.IGNORECASE | re.MULTILINE,
    )
    for m in pattern.finditer(code):
        var_name = m.group(1).lower()
        # Skip inline DATA(...) declarations
        if var_name.startswith("("):
            continue
        # Check if any known prefix matches
        has_valid_prefix = any(var_name.startswith(p) for p in _VALID_PREFIXES)
        if not has_valid_prefix:
            line_num = code[: m.start()].count("\n") + 1
            results.append((m.group(0).strip(), line_num))
    return results


def check_too_many_params(code: str) -> list[tuple[str, int]]:
    """Return matches for method definitions with >5 parameters."""
    results: list[tuple[str, int]] = []
    # Find METHODS declarations that span multiple lines (ended by period)
    pattern = re.compile(
        r"\bMETHODS\s+(\w+)\b(.*?)\.",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(code):
        body = m.group(2)
        param_count = len(re.findall(
            r"^\s+(\w+)\s+TYPE\b",
            body,
            re.IGNORECASE | re.MULTILINE,
        ))
        if param_count > 5:
            line_num = code[: m.start()].count("\n") + 1
            results.append((f"METHODS {m.group(1)} ({param_count} parameters)", line_num))
    return results


def check_dead_code_after_return(code: str) -> list[tuple[str, int]]:
    """Return matches for statements after unconditional RETURN/RAISE."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    end_keywords = {"ENDMETHOD", "ENDIF", "ENDLOOP", "ENDDO", "ENDWHILE",
                    "ENDCASE", "ENDTRY", "ELSE", "ELSEIF", "WHEN", "CATCH",
                    "CLEANUP"}

    for i, line in enumerate(lines):
        stripped = line.strip().upper().rstrip(".")
        if stripped == "RETURN" or re.match(
            r"RAISE\s+EXCEPTION\s+TYPE\b", stripped, re.IGNORECASE
        ):
            # Check the next non-empty line
            for j in range(i + 1, min(i + 5, len(lines))):
                next_stripped = lines[j].strip().upper().rstrip(".")
                if not next_stripped or next_stripped.startswith("*") or next_stripped.startswith('"'):
                    continue
                first_word = next_stripped.split()[0] if next_stripped.split() else ""
                if first_word in end_keywords:
                    break
                # Found a statement after RETURN/RAISE that is not a block closer
                results.append((lines[j].strip(), j + 1))
                break
    return results


def check_string_literal_duplication(code: str) -> list[tuple[str, int]]:
    """Return matches for string literals that appear 3+ times."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(r"'([^']{2,})'")
    literals: list[tuple[str, int]] = []
    for m in pattern.finditer(code):
        line_num = code[: m.start()].count("\n") + 1
        literals.append((m.group(1), line_num))

    counts: Counter[str] = Counter(lit for lit, _ in literals)
    reported: set[str] = set()
    for lit, line_num in literals:
        if counts[lit] >= 3 and lit not in reported:
            results.append((f"'{lit}' (used {counts[lit]} times)", line_num))
            reported.add(lit)
    return results


def check_missing_method_doc(code: str) -> list[tuple[str, int]]:
    """Return matches for METHODS definitions without preceding ABAP Doc."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"\bMETHODS\s+\w+", stripped, re.IGNORECASE):
            # Check if preceding non-empty line is an ABAP Doc comment
            has_doc = False
            for j in range(i - 1, max(i - 5, -1), -1):
                prev = lines[j].strip()
                if not prev:
                    continue
                if prev.startswith('"!'):
                    has_doc = True
                break
            if not has_doc:
                results.append((stripped, i + 1))
    return results


def check_inline_declaration_opportunity(code: str) -> list[tuple[str, int]]:
    """Return matches where DATA decl is immediately followed by assignment."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^\s*DATA\s+(\w+)\s+TYPE\b.*\.", line, re.IGNORECASE)
        if m and i + 1 < len(lines):
            var_name = m.group(1)
            next_line = lines[i + 1].strip()
            # Check if next line is a direct assignment to this variable
            if re.match(
                rf"^\s*{re.escape(var_name)}\s*=\s*\S",
                next_line,
                re.IGNORECASE,
            ):
                results.append((line.strip(), i + 1))
    return results


def check_class_data_overuse(code: str) -> list[tuple[str, int]]:
    """Return a match if more than 3 CLASS-DATA declarations exist."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(r"^\s*CLASS-DATA\b", re.IGNORECASE | re.MULTILINE)
    matches = list(pattern.finditer(code))
    if len(matches) > 3:
        line_num = code[: matches[0].start()].count("\n") + 1
        results.append(
            (f"CLASS-DATA used {len(matches)} times (>3)", line_num)
        )
    return results


def check_too_many_local_vars(code: str) -> list[tuple[str, int]]:
    """Return matches for methods with >10 DATA declarations."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    method_start: int | None = None
    method_name = ""
    data_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            method_start = i
            method_name = line.strip()
            data_count = 0
        elif method_start is not None:
            if re.match(r"^\s*DATA\b", line, re.IGNORECASE):
                data_count += 1
            if stripped == "ENDMETHOD.":
                if data_count > 10:
                    results.append(
                        (f"{method_name} ({data_count} DATA declarations)",
                         method_start + 1)
                    )
                method_start = None
                method_name = ""
                data_count = 0
    return results


def check_missing_final(code: str) -> list[tuple[str, int]]:
    """Return matches for DATA variables assigned only once (FINAL candidate)."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    # Find DATA declarations with immediate inline assignment pattern:
    # DATA var TYPE ... .  followed by var = ... .  and no other var = later
    method_start: int | None = None
    declarations: list[tuple[str, int, str]] = []  # (var_name, line_num, line_text)

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            method_start = i
            declarations = []
        elif stripped == "ENDMETHOD." and method_start is not None:
            # Analyze the method body for single-assignment variables
            method_body = "\n".join(lines[method_start:i + 1])
            for var_name, decl_line, line_text in declarations:
                # Count assignments (var_name = ...) excluding the DATA line
                assign_pattern = re.compile(
                    rf"^\s*{re.escape(var_name)}\s*=",
                    re.IGNORECASE | re.MULTILINE,
                )
                assignments = assign_pattern.findall(method_body)
                if len(assignments) == 1:
                    results.append((line_text, decl_line))
            method_start = None
            declarations = []
        elif method_start is not None:
            m = re.match(r"^\s*DATA\s+(\w+)\s+TYPE\b", line, re.IGNORECASE)
            if m:
                declarations.append((m.group(1), i + 1, line.strip()))

    return results


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ABAP_READABILITY_RULES: tuple[ReviewRule, ...] = (
    ABAP_RDBL_001,
    ABAP_RDBL_002,
    ABAP_RDBL_003,
    ABAP_RDBL_004,
    ABAP_RDBL_005,
    ABAP_RDBL_006,
    ABAP_RDBL_007,
    ABAP_RDBL_008,
    ABAP_RDBL_009,
    ABAP_RDBL_010,
    ABAP_RDBL_011,
    ABAP_RDBL_012,
)

ABAP_READABILITY_CHECK_FUNCTIONS: dict[str, object] = {
    "check_naming_convention": check_naming_convention,
    "check_too_many_params": check_too_many_params,
    "check_dead_code_after_return": check_dead_code_after_return,
    "check_string_literal_duplication": check_string_literal_duplication,
    "check_missing_method_doc": check_missing_method_doc,
    "check_inline_declaration_opportunity": check_inline_declaration_opportunity,
    "check_class_data_overuse": check_class_data_overuse,
    "check_too_many_local_vars": check_too_many_local_vars,
    "check_missing_final": check_missing_final,
}
