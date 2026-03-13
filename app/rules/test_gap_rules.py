"""Test gap detection rules for the SAP ABAP/UI5 Review Assistant.

Each ``TestGapRule`` is a frozen dataclass that describes a specific kind of
missing test coverage and provides a detection regex plus bilingual suggested
test templates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TestGapRule:
    """A single, immutable rule that detects a gap in test coverage."""

    rule_id: str  # e.g. "TG-ABAP-001"
    name: str
    name_de: str
    description: str
    description_de: str
    artifact_types: tuple[str, ...]  # applicable ArtifactType values
    category: str  # TestGapCategory value
    default_priority: str  # Severity value
    detection_pattern: str  # regex to find testable code
    detection_flags: int = re.IGNORECASE | re.MULTILINE
    suggested_test_template: str = ""
    suggested_test_template_de: str = ""

    def compile_pattern(self) -> re.Pattern[str]:
        """Return a compiled regex for this rule's detection pattern."""
        return re.compile(self.detection_pattern, self.detection_flags)


# ---------------------------------------------------------------------------
# ABAP Unit test gaps
# ---------------------------------------------------------------------------

TG_ABAP_001 = TestGapRule(
    rule_id="TG-ABAP-001",
    name="Public method without ABAP Unit test",
    name_de="Oeffentliche Methode ohne ABAP-Unit-Test",
    description=(
        "A public method was found but no corresponding test class or "
        "test method reference exists in the code. Public methods represent "
        "the contract of the class and must have explicit unit tests."
    ),
    description_de=(
        "Eine oeffentliche Methode wurde gefunden, aber keine zugehoerige "
        "Testklasse oder Testmethode ist im Code referenziert. Oeffentliche "
        "Methoden stellen den Vertrag der Klasse dar und muessen explizite "
        "Unit-Tests haben."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD"),
    category="ABAP_UNIT",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"^\s*(?:CLASS-)?METHODS\s+(\w+)"
    ),
    suggested_test_template=(
        "CLASS ltcl_{class}_test DEFINITION FINAL FOR TESTING\n"
        "  DURATION SHORT RISK LEVEL HARMLESS.\n"
        "  PRIVATE SECTION.\n"
        "    DATA mo_cut TYPE REF TO {class}.\n"
        "    METHODS setup.\n"
        "    METHODS test_{method} FOR TESTING.\n"
        "ENDCLASS.\n\n"
        "CLASS ltcl_{class}_test IMPLEMENTATION.\n"
        "  METHOD setup.\n"
        "    mo_cut = NEW #( ).\n"
        "  ENDMETHOD.\n"
        "  METHOD test_{method}.\n"
        "    \" Arrange / Act / Assert\n"
        "    DATA(lv_result) = mo_cut->{method}( ).\n"
        "    cl_abap_unit_assert=>assert_not_initial( lv_result ).\n"
        "  ENDMETHOD.\n"
        "ENDCLASS."
    ),
    suggested_test_template_de=(
        "CLASS ltcl_{class}_test DEFINITION FINAL FOR TESTING\n"
        "  DURATION SHORT RISK LEVEL HARMLESS.\n"
        "  PRIVATE SECTION.\n"
        "    DATA mo_cut TYPE REF TO {class}.\n"
        "    METHODS setup.\n"
        "    METHODS test_{method} FOR TESTING.\n"
        "ENDCLASS.\n\n"
        "CLASS ltcl_{class}_test IMPLEMENTATION.\n"
        "  METHOD setup.\n"
        "    mo_cut = NEW #( ).\n"
        "  ENDMETHOD.\n"
        "  METHOD test_{method}.\n"
        "    \" Vorbereiten / Ausfuehren / Pruefen\n"
        "    DATA(lv_result) = mo_cut->{method}( ).\n"
        "    cl_abap_unit_assert=>assert_not_initial( lv_result ).\n"
        "  ENDMETHOD.\n"
        "ENDCLASS."
    ),
)

TG_ABAP_002 = TestGapRule(
    rule_id="TG-ABAP-002",
    name="Complex branching without coverage hints",
    name_de="Komplexe Verzweigung ohne Abdeckungshinweise",
    description=(
        "Complex IF/CASE branching was detected without evidence of branch "
        "coverage testing. Each branch path should be exercised by at least "
        "one test case to ensure correctness under all conditions."
    ),
    description_de=(
        "Komplexe IF/CASE-Verzweigungen wurden erkannt, ohne Hinweise auf "
        "Branchabdeckungstests. Jeder Verzweigungspfad sollte durch "
        "mindestens einen Testfall abgedeckt werden."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT"),
    category="ABAP_UNIT",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:(?:^\s*(?:ELSE)?IF\s+.*\.\s*$)|(?:^\s*WHEN\s+))"
    ),
    suggested_test_template=(
        "METHOD test_{method}_branch_coverage.\n"
        "  \" Test each branch:\n"
        "  \" Branch 1 — condition TRUE\n"
        "  DATA(lv_result_true) = mo_cut->{method}( iv_param = 'CASE_A' ).\n"
        "  cl_abap_unit_assert=>assert_equals( act = lv_result_true exp = ... ).\n\n"
        "  \" Branch 2 — condition FALSE / ELSE\n"
        "  DATA(lv_result_false) = mo_cut->{method}( iv_param = 'CASE_B' ).\n"
        "  cl_abap_unit_assert=>assert_equals( act = lv_result_false exp = ... ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_{method}_branchabdeckung.\n"
        "  \" Jeden Zweig testen:\n"
        "  \" Zweig 1 — Bedingung WAHR\n"
        "  DATA(lv_result_true) = mo_cut->{method}( iv_param = 'FALL_A' ).\n"
        "  cl_abap_unit_assert=>assert_equals( act = lv_result_true exp = ... ).\n\n"
        "  \" Zweig 2 — Bedingung FALSCH / ELSE\n"
        "  DATA(lv_result_false) = mo_cut->{method}( iv_param = 'FALL_B' ).\n"
        "  cl_abap_unit_assert=>assert_equals( act = lv_result_false exp = ... ).\n"
        "ENDMETHOD."
    ),
)

TG_ABAP_003 = TestGapRule(
    rule_id="TG-ABAP-003",
    name="Exception handling without negative path test",
    name_de="Ausnahmebehandlung ohne Negativpfad-Test",
    description=(
        "Exception handling logic (TRY/CATCH, RAISE EXCEPTION) was found. "
        "Negative path tests must verify that exceptions are raised under "
        "the correct conditions and that catch blocks handle them properly."
    ),
    description_de=(
        "Ausnahmebehandlungslogik (TRY/CATCH, RAISE EXCEPTION) wurde gefunden. "
        "Negativpfad-Tests muessen sicherstellen, dass Ausnahmen unter den "
        "richtigen Bedingungen ausgeloest und korrekt behandelt werden."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT"),
    category="ABAP_UNIT",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:RAISE\s+EXCEPTION\s+TYPE\s+\w+|CATCH\s+\w+)"
    ),
    suggested_test_template=(
        "METHOD test_{method}_exception_path.\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_invalid_param = 'INVALID' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'Exception expected but not raised' ).\n"
        "    CATCH {exception_class} INTO DATA(lx_err).\n"
        "      cl_abap_unit_assert=>assert_not_initial( lx_err->get_text( ) ).\n"
        "  ENDTRY.\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_{method}_ausnahmepfad.\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_invalid_param = 'UNGUELTIG' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'Ausnahme erwartet aber nicht ausgeloest' ).\n"
        "    CATCH {exception_class} INTO DATA(lx_err).\n"
        "      cl_abap_unit_assert=>assert_not_initial( lx_err->get_text( ) ).\n"
        "  ENDTRY.\n"
        "ENDMETHOD."
    ),
)

TG_ABAP_004 = TestGapRule(
    rule_id="TG-ABAP-004",
    name="AUTHORITY-CHECK without authorization test",
    name_de="AUTHORITY-CHECK ohne Berechtigungstest",
    description=(
        "AUTHORITY-CHECK statements were found. Both the positive path "
        "(authorized user proceeds) and negative path (unauthorized user "
        "is blocked) must be tested to prevent authorization bypasses."
    ),
    description_de=(
        "AUTHORITY-CHECK-Anweisungen wurden gefunden. Sowohl der positive "
        "Pfad (berechtigter Benutzer) als auch der negative Pfad "
        "(unberechtigter Benutzer wird blockiert) muessen getestet werden."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT"),
    category="ABAP_UNIT",
    default_priority="CRITICAL",
    detection_pattern=(
        r"AUTHORITY-CHECK\s+OBJECT\s+"
    ),
    suggested_test_template=(
        "METHOD test_{method}_authorization.\n"
        "  \" Test 1 — authorized user\n"
        "  \" (requires test double or CL_OSQL_TEST_ENVIRONMENT setup)\n"
        "  DATA(lv_result) = mo_cut->{method}( iv_vkorg = '1000' ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lv_result ).\n\n"
        "  \" Test 2 — unauthorized user should raise exception\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_vkorg = '9999' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'No auth check triggered' ).\n"
        "    CATCH zcx_no_authority.\n"
        "      \" Expected\n"
        "  ENDTRY.\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_{method}_berechtigung.\n"
        "  \" Test 1 — berechtigter Benutzer\n"
        "  DATA(lv_result) = mo_cut->{method}( iv_vkorg = '1000' ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lv_result ).\n\n"
        "  \" Test 2 — unberechtigter Benutzer soll Ausnahme ausloesen\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_vkorg = '9999' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'Keine Berechtigungspruefung' ).\n"
        "    CATCH zcx_no_authority.\n"
        "      \" Erwartet\n"
        "  ENDTRY.\n"
        "ENDMETHOD."
    ),
)

TG_ABAP_005 = TestGapRule(
    rule_id="TG-ABAP-005",
    name="Data validation logic without boundary test",
    name_de="Datenvalidierungslogik ohne Grenzwerttest",
    description=(
        "Data validation logic was found (IS INITIAL, IS NOT INITIAL, "
        "string length checks, range checks). Boundary value tests should "
        "verify behavior at valid/invalid boundaries and edge cases."
    ),
    description_de=(
        "Datenvalidierungslogik wurde gefunden (IS INITIAL, IS NOT INITIAL, "
        "Stringlaengenpruefungen, Bereichspruefungen). Grenzwerttests sollten "
        "das Verhalten an gueltigen/ungueltigen Grenzen pruefen."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT"),
    category="ABAP_UNIT",
    default_priority="OPTIONAL",
    detection_pattern=(
        r"(?:IS\s+(?:NOT\s+)?INITIAL|"
        r"(?:strlen|xstrlen)\s*\(|"
        r"(?:BETWEEN|[<>]=?\s*\d+))"
    ),
    suggested_test_template=(
        "METHOD test_{method}_boundary_values.\n"
        "  \" Empty / initial input\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_input = '' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'Should reject empty input' ).\n"
        "    CATCH zcx_validation_error.\n"
        "  ENDTRY.\n\n"
        "  \" Minimum valid input\n"
        "  DATA(lv_min) = mo_cut->{method}( iv_input = 'A' ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lv_min ).\n\n"
        "  \" Maximum boundary input\n"
        "  DATA(lv_max) = mo_cut->{method}( iv_input = lv_max_value ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lv_max ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_{method}_grenzwerte.\n"
        "  \" Leere / initiale Eingabe\n"
        "  TRY.\n"
        "      mo_cut->{method}( iv_input = '' ).\n"
        "      cl_abap_unit_assert=>fail( msg = 'Leere Eingabe sollte abgelehnt werden' ).\n"
        "    CATCH zcx_validation_error.\n"
        "  ENDTRY.\n\n"
        "  \" Minimale gueltige Eingabe\n"
        "  DATA(lv_min) = mo_cut->{method}( iv_input = 'A' ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lv_min ).\n"
        "ENDMETHOD."
    ),
)

# ---------------------------------------------------------------------------
# RAP / Action / Validation test gaps
# ---------------------------------------------------------------------------

TG_RAP_001 = TestGapRule(
    rule_id="TG-RAP-001",
    name="RAP action without action test",
    name_de="RAP-Aktion ohne Aktionstest",
    description=(
        "An action definition was found in the Behavior Definition. "
        "Each action must have a dedicated test that verifies its "
        "preconditions, execution, and postconditions."
    ),
    description_de=(
        "Eine Aktionsdefinition wurde in der Behavior Definition gefunden. "
        "Jede Aktion muss einen eigenen Test haben, der Vorbedingungen, "
        "Ausfuehrung und Nachbedingungen prueft."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION"),
    category="ACTION_VALIDATION",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:^\s*(?:static\s+)?(?:internal\s+)?action\s+(\w+))"
    ),
    suggested_test_template=(
        "METHOD test_action_{action}.\n"
        "  \" Arrange — create test data via EML\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Act — execute the action\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    EXECUTE {action} FROM VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    FAILED ls_failed\n"
        "    REPORTED ls_reported.\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Assert\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_aktion_{action}.\n"
        "  \" Vorbereiten — Testdaten per EML anlegen\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Ausfuehren — Aktion ausfuehren\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    EXECUTE {action} FROM VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    FAILED ls_failed\n"
        "    REPORTED ls_reported.\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Pruefen\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
)

TG_RAP_002 = TestGapRule(
    rule_id="TG-RAP-002",
    name="RAP validation without negative test",
    name_de="RAP-Validierung ohne Negativtest",
    description=(
        "A validation definition was found in the Behavior Definition. "
        "Validations must be tested with both valid data (passes) and "
        "invalid data (produces expected failed/reported entries)."
    ),
    description_de=(
        "Eine Validierungsdefinition wurde in der Behavior Definition gefunden. "
        "Validierungen muessen sowohl mit gueltigen Daten (bestanden) als auch "
        "mit ungueltigen Daten (erwartete Fehlermeldungen) getestet werden."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION"),
    category="ACTION_VALIDATION",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"^\s*validation\s+(\w+)\s+on\s+save"
    ),
    suggested_test_template=(
        "METHOD test_validation_{validation}_invalid.\n"
        "  \" Arrange — create entity with invalid data\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' {field} = 'INVALID' ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Assert — validation should reject\n"
        "  cl_abap_unit_assert=>assert_not_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_validierung_{validation}_ungueltig.\n"
        "  \" Vorbereiten — Entitaet mit ungueltigen Daten anlegen\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' {field} = 'UNGUELTIG' ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Pruefen — Validierung sollte ablehnen\n"
        "  cl_abap_unit_assert=>assert_not_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
)

TG_RAP_003 = TestGapRule(
    rule_id="TG-RAP-003",
    name="RAP determination without trigger test",
    name_de="RAP-Determination ohne Triggertest",
    description=(
        "A determination definition was found. Determinations must be "
        "tested to verify that they fire on the correct trigger event "
        "and produce the expected derived field values."
    ),
    description_de=(
        "Eine Determination-Definition wurde gefunden. Determinationen "
        "muessen getestet werden, um sicherzustellen, dass sie beim richtigen "
        "Trigger-Ereignis feuern und die erwarteten abgeleiteten Feldwerte "
        "erzeugen."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION"),
    category="ACTION_VALIDATION",
    default_priority="OPTIONAL",
    detection_pattern=(
        r"^\s*determination\s+(\w+)\s+on\s+(?:save|modify)"
    ),
    suggested_test_template=(
        "METHOD test_determination_{determination}.\n"
        "  \" Arrange — create entity that triggers determination\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Assert — derived field must be filled\n"
        "  READ ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    ALL FIELDS WITH VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    RESULT DATA(lt_result).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lt_result[ 1 ]-{derived_field} ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_determination_{determination}.\n"
        "  \" Vorbereiten — Entitaet anlegen die Determination ausloest\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n\n"
        "  \" Pruefen — abgeleitetes Feld muss gefuellt sein\n"
        "  READ ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    ALL FIELDS WITH VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    RESULT DATA(lt_result).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lt_result[ 1 ]-{derived_field} ).\n"
        "ENDMETHOD."
    ),
)

TG_RAP_004 = TestGapRule(
    rule_id="TG-RAP-004",
    name="Draft handling without lifecycle test",
    name_de="Draft-Handling ohne Lebenszyklus-Test",
    description=(
        "Draft handling logic was found (with draft, %is_draft, "
        "RESUME, EDIT, ACTIVATE). Draft-enabled BOs must have tests "
        "covering the full draft lifecycle: create draft, edit, validate, "
        "activate, and discard."
    ),
    description_de=(
        "Draft-Handling-Logik wurde gefunden (with draft, %is_draft, "
        "RESUME, EDIT, ACTIVATE). Draft-faehige Business-Objekte muessen "
        "Tests fuer den gesamten Draft-Lebenszyklus haben: Erstellen, "
        "Bearbeiten, Validieren, Aktivieren und Verwerfen."
    ),
    artifact_types=("BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION"),
    category="ACTION_VALIDATION",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:with\s+draft|%is_draft|draft\s+action\s+(?:Edit|Resume|Activate|Discard))"
    ),
    suggested_test_template=(
        "METHOD test_draft_lifecycle.\n"
        "  \" 1. Create draft\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' %is_draft = if_abap_behv=>mk-on ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n\n"
        "  \" 2. Activate draft\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    EXECUTE Activate FROM VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    FAILED ls_failed\n"
        "    REPORTED ls_reported.\n"
        "  COMMIT ENTITIES.\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_draft_lebenszyklus.\n"
        "  \" 1. Draft erstellen\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    CREATE SET FIELDS WITH VALUE #( ( %cid = 'CID1' %is_draft = if_abap_behv=>mk-on ... ) )\n"
        "    MAPPED DATA(ls_mapped)\n"
        "    FAILED DATA(ls_failed)\n"
        "    REPORTED DATA(ls_reported).\n"
        "  COMMIT ENTITIES.\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n\n"
        "  \" 2. Draft aktivieren\n"
        "  MODIFY ENTITIES OF {bo_name}\n"
        "    ENTITY {entity}\n"
        "    EXECUTE Activate FROM VALUE #( ( key = ls_mapped-{entity}[ 1 ]-%key ) )\n"
        "    FAILED ls_failed\n"
        "    REPORTED ls_reported.\n"
        "  COMMIT ENTITIES.\n"
        "  cl_abap_unit_assert=>assert_initial( ls_failed-{entity} ).\n"
        "ENDMETHOD."
    ),
)

# ---------------------------------------------------------------------------
# UI5 behavior test gaps
# ---------------------------------------------------------------------------

TG_UI5_001 = TestGapRule(
    rule_id="TG-UI5-001",
    name="Controller event handler without OPA5/QUnit test",
    name_de="Controller-Eventhandler ohne OPA5/QUnit-Test",
    description=(
        "A controller event handler function was found (onPress, onChange, "
        "onSelect, etc.). Each user-facing event handler should have a "
        "corresponding OPA5 integration test or QUnit unit test."
    ),
    description_de=(
        "Eine Controller-Eventhandler-Funktion wurde gefunden (onPress, "
        "onChange, onSelect, usw.). Jeder benutzerseitige Eventhandler "
        "sollte einen entsprechenden OPA5-Integrationstest oder "
        "QUnit-Unit-Test haben."
    ),
    artifact_types=("UI5_CONTROLLER",),
    category="UI_BEHAVIOR",
    default_priority="OPTIONAL",
    detection_pattern=(
        r"(?:on[A-Z]\w+)\s*[:=]\s*function\s*\("
    ),
    detection_flags=re.MULTILINE,
    suggested_test_template=(
        "// OPA5 Journey test\n"
        "opaTest(\"Should handle {handler} event\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onThe{Page}.iPressThe{Control}();\n"
        "  Then.onThe{Page}.iShouldSee{ExpectedResult}();\n"
        "});\n\n"
        "// QUnit test\n"
        "QUnit.test(\"{handler} should update model\", function(assert) {\n"
        "  var oController = new Controller();\n"
        "  oController.{handler}();\n"
        "  assert.ok(true, \"{handler} executed without errors\");\n"
        "});"
    ),
    suggested_test_template_de=(
        "// OPA5-Journey-Test\n"
        "opaTest(\"Sollte {handler}-Event behandeln\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onThe{Page}.iPressThe{Control}();\n"
        "  Then.onThe{Page}.iShouldSee{ExpectedResult}();\n"
        "});\n\n"
        "// QUnit-Test\n"
        "QUnit.test(\"{handler} sollte Model aktualisieren\", function(assert) {\n"
        "  var oController = new Controller();\n"
        "  oController.{handler}();\n"
        "  assert.ok(true, \"{handler} ohne Fehler ausgefuehrt\");\n"
        "});"
    ),
)

TG_UI5_002 = TestGapRule(
    rule_id="TG-UI5-002",
    name="Dynamic visibility logic without visibility test",
    name_de="Dynamische Sichtbarkeitslogik ohne Sichtbarkeitstest",
    description=(
        "Dynamic visibility expressions were found (visible=\"{= ...}\"). "
        "These conditions must be tested to verify that UI elements appear "
        "and disappear under the correct data conditions."
    ),
    description_de=(
        "Dynamische Sichtbarkeitsausdruecke wurden gefunden (visible=\"{= ...}\"). "
        "Diese Bedingungen muessen getestet werden, um sicherzustellen, "
        "dass UI-Elemente unter den richtigen Datenbedingungen erscheinen "
        "und verschwinden."
    ),
    artifact_types=("UI5_VIEW", "UI5_FRAGMENT"),
    category="UI_BEHAVIOR",
    default_priority="OPTIONAL",
    detection_pattern=(
        r'visible\s*=\s*"\{=\s*[^}]+'
    ),
    detection_flags=re.MULTILINE,
    suggested_test_template=(
        "// OPA5 test for visibility\n"
        "opaTest(\"Should toggle visibility based on condition\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onThe{Page}.iSetConditionTo(true);\n"
        "  Then.onThe{Page}.theControlShouldBeVisible(\"{controlId}\");\n\n"
        "  When.onThe{Page}.iSetConditionTo(false);\n"
        "  Then.onThe{Page}.theControlShouldBeHidden(\"{controlId}\");\n"
        "});"
    ),
    suggested_test_template_de=(
        "// OPA5-Test fuer Sichtbarkeit\n"
        "opaTest(\"Sichtbarkeit soll basierend auf Bedingung wechseln\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onThe{Page}.iSetConditionTo(true);\n"
        "  Then.onThe{Page}.theControlShouldBeVisible(\"{controlId}\");\n\n"
        "  When.onThe{Page}.iSetConditionTo(false);\n"
        "  Then.onThe{Page}.theControlShouldBeHidden(\"{controlId}\");\n"
        "});"
    ),
)

TG_UI5_003 = TestGapRule(
    rule_id="TG-UI5-003",
    name="Model binding manipulation without integration test",
    name_de="Model-Binding-Manipulation ohne Integrationstest",
    description=(
        "Direct model manipulation was found (setProperty, setData, "
        "getProperty). Changes to model bindings must be tested to "
        "verify that the UI reflects the correct data state."
    ),
    description_de=(
        "Direkte Modelmanipulation wurde gefunden (setProperty, setData, "
        "getProperty). Aenderungen an Model-Bindings muessen getestet "
        "werden, um sicherzustellen, dass die UI den korrekten "
        "Datenzustand widerspiegelt."
    ),
    artifact_types=("UI5_CONTROLLER", "UI5_FORMATTER"),
    category="UI_BEHAVIOR",
    default_priority="OPTIONAL",
    detection_pattern=(
        r"(?:setProperty|setData|getProperty)\s*\("
    ),
    detection_flags=re.MULTILINE,
    suggested_test_template=(
        "QUnit.test(\"Model property should be updated correctly\", function(assert) {\n"
        "  var oModel = new JSONModel({ value: \"initial\" });\n"
        "  var oController = new Controller();\n"
        "  oController.getView = function() {\n"
        "    return { getModel: function() { return oModel; } };\n"
        "  };\n"
        "  oController.{method}();\n"
        "  assert.strictEqual(oModel.getProperty(\"/{path}\"), \"{expected}\");\n"
        "});"
    ),
    suggested_test_template_de=(
        "QUnit.test(\"Model-Eigenschaft sollte korrekt aktualisiert werden\", function(assert) {\n"
        "  var oModel = new JSONModel({ value: \"initial\" });\n"
        "  var oController = new Controller();\n"
        "  oController.getView = function() {\n"
        "    return { getModel: function() { return oModel; } };\n"
        "  };\n"
        "  oController.{method}();\n"
        "  assert.strictEqual(oModel.getProperty(\"/{path}\"), \"{erwartet}\");\n"
        "});"
    ),
)

TG_UI5_004 = TestGapRule(
    rule_id="TG-UI5-004",
    name="Navigation logic without navigation flow test",
    name_de="Navigationslogik ohne Navigationsflusstest",
    description=(
        "Navigation logic was found (navTo, getRouter, display). "
        "Navigation flows must be tested to verify that the correct "
        "route is triggered with the correct parameters."
    ),
    description_de=(
        "Navigationslogik wurde gefunden (navTo, getRouter, display). "
        "Navigationsfluesse muessen getestet werden, um sicherzustellen, "
        "dass die richtige Route mit den richtigen Parametern "
        "ausgeloest wird."
    ),
    artifact_types=("UI5_CONTROLLER",),
    category="UI_BEHAVIOR",
    default_priority="OPTIONAL",
    detection_pattern=(
        r"(?:navTo|getRouter\s*\(\s*\)\s*\.(?:navTo|display))\s*\("
    ),
    detection_flags=re.MULTILINE,
    suggested_test_template=(
        "// OPA5 navigation test\n"
        "opaTest(\"Should navigate to detail page\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onTheListPage.iSelectItem(\"{itemId}\");\n"
        "  Then.onTheDetailPage.iShouldSeeTheDetailFor(\"{itemId}\");\n"
        "});\n\n"
        "// QUnit navigation unit test\n"
        "QUnit.test(\"navTo should be called with correct route\", function(assert) {\n"
        "  var oRouter = { navTo: sinon.spy() };\n"
        "  var oController = new Controller();\n"
        "  sinon.stub(oController, \"getRouter\").returns(oRouter);\n"
        "  oController.{handler}();\n"
        "  assert.ok(oRouter.navTo.calledWith(\"{route}\", { key: \"{key}\" }));\n"
        "});"
    ),
    suggested_test_template_de=(
        "// OPA5-Navigationstest\n"
        "opaTest(\"Sollte zur Detailseite navigieren\", function(Given, When, Then) {\n"
        "  Given.iStartMyApp();\n"
        "  When.onTheListPage.iSelectItem(\"{itemId}\");\n"
        "  Then.onTheDetailPage.iShouldSeeTheDetailFor(\"{itemId}\");\n"
        "});\n\n"
        "// QUnit-Navigationstest\n"
        "QUnit.test(\"navTo sollte mit korrekter Route aufgerufen werden\", function(assert) {\n"
        "  var oRouter = { navTo: sinon.spy() };\n"
        "  var oController = new Controller();\n"
        "  sinon.stub(oController, \"getRouter\").returns(oRouter);\n"
        "  oController.{handler}();\n"
        "  assert.ok(oRouter.navTo.calledWith(\"{route}\", { key: \"{key}\" }));\n"
        "});"
    ),
)

# ---------------------------------------------------------------------------
# Regression / side-effect test gaps
# ---------------------------------------------------------------------------

TG_REG_001 = TestGapRule(
    rule_id="TG-REG-001",
    name="Code modifying global/shared data without regression test",
    name_de="Code aendert globale/gemeinsame Daten ohne Regressionstest",
    description=(
        "Code modifying global or shared data was found (class-data, "
        "static attributes, shared memory, EXPORT/IMPORT). Changes to "
        "shared state must have regression tests to prevent unintended "
        "side effects across consumers."
    ),
    description_de=(
        "Code der globale oder gemeinsame Daten aendert wurde gefunden "
        "(class-data, statische Attribute, Shared Memory, EXPORT/IMPORT). "
        "Aenderungen an geteiltem Zustand muessen Regressionstests haben, "
        "um unbeabsichtigte Seiteneffekte zu verhindern."
    ),
    artifact_types=("ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT"),
    category="REGRESSION_SIDE_EFFECT",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:CLASS-DATA\s+\w+|"
        r"EXPORT\s+.*\s+TO\s+(?:MEMORY|DATABASE|SHARED\s+BUFFER)|"
        r"gv_|gs_|gt_|go_)"
    ),
    suggested_test_template=(
        "METHOD test_no_side_effects_on_shared_data.\n"
        "  \" Capture initial state\n"
        "  DATA(lv_before) = zcl_shared=>get_state( ).\n\n"
        "  \" Execute operation\n"
        "  mo_cut->{method}( ).\n\n"
        "  \" Assert state is consistent\n"
        "  DATA(lv_after) = zcl_shared=>get_state( ).\n"
        "  cl_abap_unit_assert=>assert_equals(\n"
        "    act = lv_after\n"
        "    exp = lv_expected\n"
        "    msg = 'Shared data state changed unexpectedly' ).\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_keine_seiteneffekte_auf_globale_daten.\n"
        "  \" Ausgangszustand erfassen\n"
        "  DATA(lv_before) = zcl_shared=>get_state( ).\n\n"
        "  \" Operation ausfuehren\n"
        "  mo_cut->{method}( ).\n\n"
        "  \" Zustand pruefen\n"
        "  DATA(lv_after) = zcl_shared=>get_state( ).\n"
        "  cl_abap_unit_assert=>assert_equals(\n"
        "    act = lv_after\n"
        "    exp = lv_expected\n"
        "    msg = 'Geteilter Datenzustand unerwartet geaendert' ).\n"
        "ENDMETHOD."
    ),
)

TG_REG_002 = TestGapRule(
    rule_id="TG-REG-002",
    name="Cross-entity dependency modification without cross-entity test",
    name_de="Entitaetsuebergreifende Abhaengigkeitsaenderung ohne Cross-Entity-Test",
    description=(
        "Code modifying multiple entities or cross-entity dependencies "
        "was found (modifying header and items, updating related tables, "
        "calling BAPI with multiple structures). Cross-entity tests must "
        "verify consistency after modifications."
    ),
    description_de=(
        "Code der mehrere Entitaeten oder entitaetsuebergreifende "
        "Abhaengigkeiten aendert wurde gefunden. Cross-Entity-Tests "
        "muessen die Konsistenz nach Aenderungen sicherstellen."
    ),
    artifact_types=(
        "ABAP_CLASS", "ABAP_METHOD", "ABAP_REPORT",
        "BEHAVIOR_DEFINITION", "BEHAVIOR_IMPLEMENTATION",
    ),
    category="REGRESSION_SIDE_EFFECT",
    default_priority="IMPORTANT",
    detection_pattern=(
        r"(?:MODIFY\s+(?:ztab_header|ztab_item|vbak|vbap|ekko|ekpo)|"
        r"UPDATE\s+\w+.*\.\s*\n.*UPDATE\s+\w+|"
        r"association\s+\w+\s*\{|"
        r"_(?:Item|Header|Partner|Address)\b)"
    ),
    suggested_test_template=(
        "METHOD test_cross_entity_consistency.\n"
        "  \" Arrange — create header + items\n"
        "  mo_cut->create_header( ls_header ).\n"
        "  mo_cut->create_items( lt_items ).\n\n"
        "  \" Act — modify header (should cascade to items)\n"
        "  mo_cut->update_header( ls_changed_header ).\n\n"
        "  \" Assert — items reflect header changes\n"
        "  DATA(lt_result_items) = mo_cut->get_items( ls_changed_header-key ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lt_result_items ).\n"
        "  \" Verify consistency between header and items\n"
        "  LOOP AT lt_result_items INTO DATA(ls_item).\n"
        "    cl_abap_unit_assert=>assert_equals(\n"
        "      act = ls_item-header_key\n"
        "      exp = ls_changed_header-key ).\n"
        "  ENDLOOP.\n"
        "ENDMETHOD."
    ),
    suggested_test_template_de=(
        "METHOD test_cross_entity_konsistenz.\n"
        "  \" Vorbereiten — Kopf + Positionen anlegen\n"
        "  mo_cut->create_header( ls_header ).\n"
        "  mo_cut->create_items( lt_items ).\n\n"
        "  \" Ausfuehren — Kopf aendern (sollte zu Positionen kaskadieren)\n"
        "  mo_cut->update_header( ls_changed_header ).\n\n"
        "  \" Pruefen — Positionen spiegeln Kopfaenderungen wider\n"
        "  DATA(lt_result_items) = mo_cut->get_items( ls_changed_header-key ).\n"
        "  cl_abap_unit_assert=>assert_not_initial( lt_result_items ).\n"
        "  LOOP AT lt_result_items INTO DATA(ls_item).\n"
        "    cl_abap_unit_assert=>assert_equals(\n"
        "      act = ls_item-header_key\n"
        "      exp = ls_changed_header-key ).\n"
        "  ENDLOOP.\n"
        "ENDMETHOD."
    ),
)


# ---------------------------------------------------------------------------
# Combined registry — all test gap rules in one tuple
# ---------------------------------------------------------------------------

ALL_TEST_GAP_RULES: tuple[TestGapRule, ...] = (
    TG_ABAP_001,
    TG_ABAP_002,
    TG_ABAP_003,
    TG_ABAP_004,
    TG_ABAP_005,
    TG_RAP_001,
    TG_RAP_002,
    TG_RAP_003,
    TG_RAP_004,
    TG_UI5_001,
    TG_UI5_002,
    TG_UI5_003,
    TG_UI5_004,
    TG_REG_001,
    TG_REG_002,
)
