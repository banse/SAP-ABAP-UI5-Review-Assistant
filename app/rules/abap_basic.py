"""MVP ABAP review rules for the SAP ABAP/UI5 Review Assistant.

Each rule is a frozen ``ReviewRule`` instance with a regex pattern that
detects a common ABAP code quality issue, plus bilingual metadata.
"""

from __future__ import annotations

import re

from app.rules.base_rules import ReviewRule

# ---------------------------------------------------------------------------
# ABAP-READ: Data-access / read patterns
# ---------------------------------------------------------------------------

ABAP_READ_001 = ReviewRule(
    rule_id="ABAP-READ-001",
    name="SELECT * usage",
    name_de="SELECT * Verwendung",
    description=(
        "SELECT * retrieves all columns from the database table, which wastes "
        "network bandwidth and prevents the database optimizer from using covering "
        "indexes. Always select only the fields you actually need."
    ),
    description_de=(
        "SELECT * liest alle Spalten der Datenbanktabelle, verschwendet Netzwerk-"
        "bandbreite und verhindert die Nutzung von Covering-Indexes. Immer nur die "
        "benoetigten Felder selektieren."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bSELECT\s+\*\s+FROM\b",
    category="performance",
    recommendation="Replace SELECT * with an explicit field list.",
    recommendation_de="SELECT * durch eine explizite Feldliste ersetzen.",
)

ABAP_READ_002 = ReviewRule(
    rule_id="ABAP-READ-002",
    name="SELECT without WHERE clause",
    name_de="SELECT ohne WHERE-Klausel",
    description=(
        "A SELECT statement without a WHERE clause causes a full table scan, "
        "which is a severe performance risk on large production tables."
    ),
    description_de=(
        "Ein SELECT ohne WHERE-Klausel fuehrt zu einem Full-Table-Scan, was bei "
        "grossen Produktionstabellen ein erhebliches Performance-Risiko darstellt."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="CRITICAL",
    pattern=r"\bSELECT\b",
    category="performance",
    check_fn_name="check_select_without_where",
    recommendation="Add a WHERE clause to restrict the result set.",
    recommendation_de="Eine WHERE-Klausel hinzufuegen, um die Ergebnismenge einzuschraenken.",
)

ABAP_READ_003 = ReviewRule(
    rule_id="ABAP-READ-003",
    name="Nested SELECT in loop",
    name_de="SELECT innerhalb einer Schleife",
    description=(
        "Executing a SELECT inside a LOOP/DO/WHILE creates an N+1 query pattern "
        "that scales poorly. Collect keys first, then use a single SELECT with "
        "FOR ALL ENTRIES or a range table."
    ),
    description_de=(
        "Ein SELECT innerhalb von LOOP/DO/WHILE erzeugt ein N+1-Query-Muster, das "
        "schlecht skaliert. Schluessel erst sammeln, dann ein einzelnes SELECT mit "
        "FOR ALL ENTRIES oder Ranges verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="CRITICAL",
    pattern=r"(?:LOOP\s+AT|DO\b|WHILE\b)[\s\S]{0,500}?\bSELECT\b",
    pattern_flags=re.IGNORECASE | re.DOTALL,
    category="performance",
    recommendation=(
        "Move the SELECT out of the loop. Collect keys first, then use "
        "FOR ALL ENTRIES IN or a range table."
    ),
    recommendation_de=(
        "Das SELECT aus der Schleife verschieben. Schluessel sammeln und "
        "FOR ALL ENTRIES IN oder eine Range-Tabelle verwenden."
    ),
)

# ---------------------------------------------------------------------------
# ABAP-ERR: Error handling
# ---------------------------------------------------------------------------

ABAP_ERR_001 = ReviewRule(
    rule_id="ABAP-ERR-001",
    name="Empty CATCH block",
    name_de="Leerer CATCH-Block",
    description=(
        "An empty CATCH block silently swallows exceptions, hiding errors from "
        "support teams and making production issues impossible to diagnose."
    ),
    description_de=(
        "Ein leerer CATCH-Block verschluckt Ausnahmen stillschweigend. Fehler "
        "werden unsichtbar und Produktionsprobleme schwer diagnostizierbar."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"CATCH\s+\w[\w\s]*\.\s*(?:ENDTRY|CATCH)",
    pattern_flags=re.IGNORECASE | re.DOTALL,
    category="error_handling",
    recommendation=(
        "Log the exception or re-raise it. At minimum, capture the message text "
        "for operational traceability."
    ),
    recommendation_de=(
        "Die Ausnahme loggen oder erneut ausloesen. Mindestens den Nachrichtentext "
        "fuer die Betriebsueberwachung erfassen."
    ),
)

ABAP_ERR_002 = ReviewRule(
    rule_id="ABAP-ERR-002",
    name="CATCH cx_root (overly broad)",
    name_de="CATCH cx_root (zu allgemein)",
    description=(
        "Catching cx_root captures every possible exception including system "
        "errors and programming bugs. Catch the most specific exception class."
    ),
    description_de=(
        "CATCH cx_root faengt jede moegliche Ausnahme ab, einschliesslich "
        "Systemfehler und Programmierfehler. Die spezifischste Ausnahmeklasse verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bCATCH\s+cx_root\b",
    category="error_handling",
    recommendation="Replace cx_root with a more specific exception class.",
    recommendation_de="cx_root durch eine spezifischere Ausnahmeklasse ersetzen.",
)

ABAP_ERR_003 = ReviewRule(
    rule_id="ABAP-ERR-003",
    name="Missing sy-subrc check after CALL FUNCTION",
    name_de="Fehlende sy-subrc Pruefung nach CALL FUNCTION",
    description=(
        "CALL FUNCTION sets sy-subrc to indicate success or failure. Not checking "
        "it means errors pass silently and corrupt downstream processing."
    ),
    description_de=(
        "CALL FUNCTION setzt sy-subrc als Erfolgs-/Fehlerindikator. Ohne Pruefung "
        "gehen Fehler stillschweigend durch und koennen nachfolgende Verarbeitung korrumpieren."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"CALL\s+FUNCTION\b[^.]*\.(?!\s*IF\s+sy-subrc)",
    pattern_flags=re.IGNORECASE | re.DOTALL,
    category="error_handling",
    recommendation="Check sy-subrc immediately after CALL FUNCTION.",
    recommendation_de="sy-subrc direkt nach CALL FUNCTION pruefen.",
)

# ---------------------------------------------------------------------------
# ABAP-STRUCT: Structural / complexity
# ---------------------------------------------------------------------------

ABAP_STRUCT_001 = ReviewRule(
    rule_id="ABAP-STRUCT-001",
    name="Method exceeds 100 lines",
    name_de="Methode ueberschreitet 100 Zeilen",
    description=(
        "Methods longer than 100 lines are hard to understand, test, and "
        "maintain. Consider extracting helper methods."
    ),
    description_de=(
        "Methoden mit mehr als 100 Zeilen sind schwer verstaendlich, testbar und "
        "wartbar. Hilfsmethoden extrahieren."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"METHOD\s+\w+\.",
    check_fn_name="check_method_length",
    category="readability",
    recommendation="Extract parts of the method into smaller, focused helper methods.",
    recommendation_de="Teile der Methode in kleinere, fokussierte Hilfsmethoden extrahieren.",
)

ABAP_STRUCT_002 = ReviewRule(
    rule_id="ABAP-STRUCT-002",
    name="Deep nesting (> 4 levels)",
    name_de="Tiefe Verschachtelung (> 4 Ebenen)",
    description=(
        "Nesting deeper than four levels makes control flow hard to follow. "
        "Use guard clauses or extract methods to flatten the structure."
    ),
    description_de=(
        "Verschachtelungen tiefer als vier Ebenen machen den Kontrollfluss schwer "
        "nachvollziehbar. Guard-Clauses oder Methodenextraktion verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"(?:IF|LOOP|DO|WHILE|CASE)\b",
    check_fn_name="check_nesting_depth",
    category="readability",
    recommendation="Reduce nesting with guard clauses (early RETURN/CONTINUE) or extract methods.",
    recommendation_de=(
        "Verschachtelung mit Guard-Clauses (fruehes RETURN/CONTINUE) reduzieren "
        "oder Methoden extrahieren."
    ),
)

# ---------------------------------------------------------------------------
# ABAP-STYLE: Obsolete / stylistic patterns
# ---------------------------------------------------------------------------

ABAP_STYLE_001 = ReviewRule(
    rule_id="ABAP-STYLE-001",
    name="WRITE statement in OO context",
    name_de="WRITE-Anweisung im OO-Kontext",
    description=(
        "The WRITE statement targets the classic list screen and has no effect "
        "in OData, Fiori, or API-based architectures. Use messages, logging, or "
        "return parameters instead."
    ),
    description_de=(
        "Die WRITE-Anweisung zielt auf den klassischen Listbildschirm und hat in "
        "OData-, Fiori- oder API-Architekturen keine Wirkung. Nachrichten, Logging "
        "oder Rueckgabeparameter verwenden."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK"),
    default_severity="OPTIONAL",
    pattern=r"^\s*WRITE[\s:/]",
    pattern_flags=re.IGNORECASE | re.MULTILINE,
    category="readability",
    recommendation="Replace WRITE with structured messages or return parameters.",
    recommendation_de="WRITE durch strukturierte Nachrichten oder Rueckgabeparameter ersetzen.",
)

ABAP_STYLE_002 = ReviewRule(
    rule_id="ABAP-STYLE-002",
    name="Obsolete MOVE / COMPUTE statement",
    name_de="Veraltete MOVE / COMPUTE Anweisung",
    description=(
        "MOVE ... TO and COMPUTE are obsolete ABAP statements. Use inline "
        "assignments (=) instead."
    ),
    description_de=(
        "MOVE ... TO und COMPUTE sind veraltete ABAP-Anweisungen. Inline-"
        "Zuweisungen (=) verwenden."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"^\s*(?:MOVE\b|COMPUTE\b)",
    pattern_flags=re.IGNORECASE | re.MULTILINE,
    category="readability",
    recommendation="Replace MOVE/COMPUTE with the modern assignment operator (=).",
    recommendation_de="MOVE/COMPUTE durch den modernen Zuweisungsoperator (=) ersetzen.",
)

# ---------------------------------------------------------------------------
# ABAP-SEC: Security
# ---------------------------------------------------------------------------

ABAP_SEC_001 = ReviewRule(
    rule_id="ABAP-SEC-001",
    name="Missing AUTHORITY-CHECK",
    name_de="Fehlende AUTHORITY-CHECK",
    description=(
        "Code that reads or modifies business data without an AUTHORITY-CHECK "
        "may expose sensitive data or allow unauthorized operations."
    ),
    description_de=(
        "Code, der Geschaeftsdaten ohne AUTHORITY-CHECK liest oder aendert, kann "
        "sensible Daten offenlegen oder unautorisierte Aktionen ermoeglichen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\bSELECT\b",
    check_fn_name="check_missing_authority",
    category="security",
    recommendation=(
        "Add AUTHORITY-CHECK OBJECT with the appropriate authorization object "
        "before accessing business data."
    ),
    recommendation_de=(
        "AUTHORITY-CHECK OBJECT mit dem passenden Berechtigungsobjekt vor dem "
        "Zugriff auf Geschaeftsdaten hinzufuegen."
    ),
)

# ---------------------------------------------------------------------------
# ABAP-PERF: Performance
# ---------------------------------------------------------------------------

ABAP_PERF_001 = ReviewRule(
    rule_id="ABAP-PERF-001",
    name="SELECT without ORDER BY when processing depends on order",
    name_de="SELECT ohne ORDER BY bei reihenfolgeabhaengiger Verarbeitung",
    description=(
        "Without ORDER BY the database may return rows in an unpredictable order. "
        "If downstream logic depends on the sequence, results become unreliable."
    ),
    description_de=(
        "Ohne ORDER BY kann die Datenbank Zeilen in unvorhersehbarer Reihenfolge "
        "liefern. Wenn die Folgelogik auf die Reihenfolge angewiesen ist, werden "
        "Ergebnisse unzuverlaessig."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="OPTIONAL",
    pattern=r"\bSELECT\b",
    check_fn_name="check_select_without_order_by",
    category="performance",
    recommendation="Add ORDER BY PRIMARY KEY or an explicit ORDER BY clause if processing is order-dependent.",
    recommendation_de=(
        "ORDER BY PRIMARY KEY oder eine explizite ORDER-BY-Klausel hinzufuegen, "
        "wenn die Verarbeitung reihenfolgeabhaengig ist."
    ),
)

# ---------------------------------------------------------------------------
# ABAP-MOD: Modification / extension markers
# ---------------------------------------------------------------------------

ABAP_MOD_001 = ReviewRule(
    rule_id="ABAP-MOD-001",
    name="Direct modification marker detected",
    name_de="Direkte Modifikationsmarkierung erkannt",
    description=(
        "ENHANCEMENT-POINT, ENHANCEMENT-SECTION, or user-exit markers indicate "
        "a direct modification of SAP standard code. This is a Clean Core risk "
        "and complicates upgrades."
    ),
    description_de=(
        "ENHANCEMENT-POINT, ENHANCEMENT-SECTION oder User-Exit-Marker deuten auf "
        "eine direkte Modifikation von SAP-Standard-Code hin. Dies ist ein Clean-"
        "Core-Risiko und erschwert Upgrades."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_IMPLEMENTATION", "MIXED_FULLSTACK",
    ),
    default_severity="IMPORTANT",
    pattern=r"\b(?:ENHANCEMENT-POINT|ENHANCEMENT-SECTION|user-exit)\b",
    category="maintainability",
    recommendation=(
        "Evaluate whether a BAdI, new extension point, or side-by-side extension "
        "can replace the direct modification."
    ),
    recommendation_de=(
        "Pruefen, ob ein BAdI, ein neuer Extension-Point oder eine Side-by-Side-"
        "Erweiterung die direkte Modifikation ersetzen kann."
    ),
)


# ---------------------------------------------------------------------------
# Custom check functions (for rules with check_fn_name)
# ---------------------------------------------------------------------------


def check_method_length(code: str) -> list[tuple[str, int]]:
    """Return (matched_text, line_number) for methods exceeding 100 lines."""
    results: list[tuple[str, int]] = []
    lines = code.split("\n")
    method_start: int | None = None
    method_name = ""

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("METHOD ") and stripped.endswith("."):
            method_start = i
            method_name = line.strip()
        elif stripped == "ENDMETHOD." and method_start is not None:
            length = i - method_start + 1
            if length > 100:
                results.append((method_name, method_start + 1))
            method_start = None
            method_name = ""

    return results


def check_nesting_depth(code: str) -> list[tuple[str, int]]:
    """Return (matched_text, line_number) for lines exceeding 4 nesting levels."""
    results: list[tuple[str, int]] = []
    depth = 0
    openers = {"IF", "LOOP", "DO", "WHILE", "CASE", "TRY"}
    closers = {"ENDIF", "ENDLOOP", "ENDDO", "ENDWHILE", "ENDCASE", "ENDTRY"}

    for i, line in enumerate(code.split("\n")):
        first_word = line.strip().split()[0].upper().rstrip(".") if line.strip() else ""
        if first_word in openers:
            depth += 1
            if depth > 4:
                results.append((line.strip(), i + 1))
        elif first_word in closers:
            depth = max(0, depth - 1)

    return results


def check_select_without_order_by(code: str) -> list[tuple[str, int]]:
    """Return matches for SELECT ... INTO TABLE without ORDER BY."""
    results: list[tuple[str, int]] = []
    pattern = re.compile(r"\bSELECT\b(.*?)\.", re.IGNORECASE | re.DOTALL)
    for m in pattern.finditer(code):
        stmt = m.group(0)
        if not re.search(r"\bINTO\s+TABLE\b", stmt, re.IGNORECASE):
            continue
        if not re.search(r"\bORDER\s+BY\b", stmt, re.IGNORECASE):
            line_num = code[: m.start()].count("\n") + 1
            results.append((stmt.split("\n")[0].strip(), line_num))
    return results


def check_select_without_where(code: str) -> list[tuple[str, int]]:
    """Return matches for SELECT ... FROM ... statements that lack a WHERE clause."""
    results: list[tuple[str, int]] = []
    # Find each SELECT statement (terminated by a period)
    pattern = re.compile(
        r"\bSELECT\b(.*?)\.",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(code):
        stmt = m.group(0)
        # Must have FROM to be a real SELECT
        if not re.search(r"\bFROM\b", stmt, re.IGNORECASE):
            continue
        # Check for WHERE
        if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
            line_num = code[: m.start()].count("\n") + 1
            results.append((stmt.split("\n")[0].strip(), line_num))
    return results


def check_missing_authority(code: str) -> list[tuple[str, int]]:
    """Return a match if code has SELECT but no AUTHORITY-CHECK anywhere."""
    has_select = re.search(r"\bSELECT\b", code, re.IGNORECASE)
    has_authority = re.search(r"\bAUTHORITY-CHECK\b", code, re.IGNORECASE)

    if has_select and not has_authority:
        match = re.search(r"\bSELECT\b", code, re.IGNORECASE)
        if match:
            line_num = code[: match.start()].count("\n") + 1
            return [(match.group(), line_num)]
    return []


# ---------------------------------------------------------------------------
# Registry — all ABAP rules in one tuple
# ---------------------------------------------------------------------------

ABAP_RULES: tuple[ReviewRule, ...] = (
    ABAP_READ_001,
    ABAP_READ_002,
    ABAP_READ_003,
    ABAP_ERR_001,
    ABAP_ERR_002,
    ABAP_ERR_003,
    ABAP_STRUCT_001,
    ABAP_STRUCT_002,
    ABAP_STYLE_001,
    ABAP_STYLE_002,
    ABAP_SEC_001,
    ABAP_PERF_001,
    ABAP_MOD_001,
)

# Map of check_fn_name -> callable
ABAP_CHECK_FUNCTIONS: dict[str, object] = {
    "check_method_length": check_method_length,
    "check_nesting_depth": check_nesting_depth,
    "check_select_without_where": check_select_without_where,
    "check_select_without_order_by": check_select_without_order_by,
    "check_missing_authority": check_missing_authority,
}
