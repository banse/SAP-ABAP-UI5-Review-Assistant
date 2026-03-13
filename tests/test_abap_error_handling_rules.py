"""Tests for ABAP error handling and testability rules."""

from __future__ import annotations

import pytest

from app.engines.findings_engine import run_findings_engine
from app.models.enums import (
    ArtifactType,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import Finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(
    code: str,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
) -> list[Finding]:
    return run_findings_engine(
        code=code,
        artifact_type=artifact_type,
        review_type=ReviewType.SNIPPET_REVIEW,
        review_context=ReviewContext.GREENFIELD,
        language=language,
    )


def _has_rule(findings: list[Finding], rule_id: str) -> bool:
    return any(f.rule_id == rule_id for f in findings)


# ===========================================================================
# ABAP-ERRH-001: Missing CLEANUP block
# ===========================================================================


class TestAbapErrh001MissingCleanup:
    def test_try_with_enqueue_no_cleanup_detected(self) -> None:
        code = (
            "TRY.\n"
            "    CALL FUNCTION 'ENQUEUE_EZVBAK'\n"
            "      EXPORTING vbeln = lv_vbeln.\n"
            "  CATCH cx_foreign_lock INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-001")

    def test_try_with_cleanup_clean(self) -> None:
        code = (
            "TRY.\n"
            "    CALL FUNCTION 'ENQUEUE_EZVBAK'\n"
            "      EXPORTING vbeln = lv_vbeln.\n"
            "  CATCH cx_foreign_lock INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "  CLEANUP.\n"
            "    CALL FUNCTION 'DEQUEUE_EZVBAK'\n"
            "      EXPORTING vbeln = lv_vbeln.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-001")

    def test_try_without_resources_clean(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH zcx_process_error INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-001")


# ===========================================================================
# ABAP-ERRH-002: RAISE EXCEPTION without message
# ===========================================================================


class TestAbapErrh002RaiseWithoutMessage:
    def test_raise_without_message_detected(self) -> None:
        code = "RAISE EXCEPTION TYPE zcx_invalid_input.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-002")

    def test_raise_with_message_clean(self) -> None:
        code = (
            "RAISE EXCEPTION TYPE zcx_invalid_input\n"
            "  MESSAGE e001(zmsg).\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-002")

    def test_raise_with_exporting_clean(self) -> None:
        code = (
            "RAISE EXCEPTION TYPE zcx_invalid_input\n"
            "  EXPORTING\n"
            "    textid = zcx_invalid_input=>invalid_customer.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-002")


# ===========================================================================
# ABAP-ERRH-003: Missing RESUMABLE exception handling
# ===========================================================================


class TestAbapErrh003ResumableException:
    def test_resumable_raising_detected(self) -> None:
        code = (
            "METHODS validate\n"
            "  RAISING RESUMABLE(zcx_validation_warning).\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-003")

    def test_normal_raising_clean(self) -> None:
        code = (
            "METHODS validate\n"
            "  RAISING zcx_validation_error.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-003")


# ===========================================================================
# ABAP-ERRH-004: Method signature unfriendly to test doubles
# ===========================================================================


class TestAbapErrh004TestDoubles:
    def test_concrete_class_ref_detected(self) -> None:
        code = "DATA lo_service TYPE REF TO zcl_order_service.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-004")

    def test_interface_ref_clean(self) -> None:
        code = "DATA lo_service TYPE REF TO zif_order_service.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-004")

    def test_standard_class_ref_clean(self) -> None:
        code = "DATA lo_logger TYPE REF TO cl_log.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-004")


# ===========================================================================
# ABAP-ERRH-005: Global data dependency
# ===========================================================================


class TestAbapErrh005GlobalDataDependency:
    def test_instance_method_accessing_class_data_detected(self) -> None:
        code = (
            "CLASS-DATA gv_counter TYPE i.\n"
            "METHOD increment.\n"
            "  gv_counter = gv_counter + 1.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-005")

    def test_no_class_data_clean(self) -> None:
        code = (
            "DATA mv_counter TYPE i.\n"
            "METHOD increment.\n"
            "  mv_counter = mv_counter + 1.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-005")


# ===========================================================================
# ABAP-ERRH-006: Missing constructor injection
# ===========================================================================


class TestAbapErrh006ConstructorInjection:
    def test_create_object_in_method_detected(self) -> None:
        code = (
            "METHOD process.\n"
            "  CREATE OBJECT lo_service TYPE zcl_order_service.\n"
            "  lo_service->execute( ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-006")

    def test_new_in_method_detected(self) -> None:
        code = (
            "METHOD process.\n"
            "  DATA(lo_service) = NEW zcl_order_service( ).\n"
            "  lo_service->execute( ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-006")

    def test_create_in_constructor_clean(self) -> None:
        code = (
            "METHOD constructor.\n"
            "  CREATE OBJECT mo_service TYPE zcl_order_service.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-006")


# ===========================================================================
# ABAP-ERRH-007: Factory pattern absence
# ===========================================================================


class TestAbapErrh007FactoryPattern:
    def test_same_class_created_multiple_times_detected(self) -> None:
        code = (
            "METHOD a.\n"
            "  CREATE OBJECT lo TYPE zcl_helper.\n"
            "ENDMETHOD.\n"
            "METHOD b.\n"
            "  CREATE OBJECT lo TYPE zcl_helper.\n"
            "ENDMETHOD.\n"
            "METHOD c.\n"
            "  CREATE OBJECT lo TYPE zcl_helper.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-007")

    def test_single_creation_clean(self) -> None:
        code = (
            "METHOD factory.\n"
            "  CREATE OBJECT ro_result TYPE zcl_helper.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-007")


# ===========================================================================
# ABAP-ERRH-008: CATCH without INTO
# ===========================================================================


class TestAbapErrh008CatchWithoutInto:
    def test_catch_without_into_detected(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH zcx_process_error.\n"
            "    MESSAGE 'Error occurred' TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-008")

    def test_catch_with_into_clean(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH zcx_process_error INTO DATA(lx_err).\n"
            "    MESSAGE lx_err->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-008")


# ===========================================================================
# ABAP-ERRH-009: Missing precondition check
# ===========================================================================


class TestAbapErrh009MissingPrecondition:
    def test_method_without_validation_detected(self) -> None:
        code = (
            "METHOD process_order.\n"
            "  SELECT SINGLE * FROM vbak\n"
            "    INTO @DATA(ls_order)\n"
            "    WHERE vbeln = @iv_vbeln.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-009")

    def test_method_with_assert_clean(self) -> None:
        code = (
            "METHOD process_order.\n"
            "  ASSERT iv_vbeln IS NOT INITIAL.\n"
            "  SELECT SINGLE * FROM vbak\n"
            "    INTO @DATA(ls_order)\n"
            "    WHERE vbeln = @iv_vbeln.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-009")

    def test_method_with_raise_clean(self) -> None:
        code = (
            "METHOD process_order.\n"
            "  IF iv_vbeln IS INITIAL.\n"
            "    RAISE EXCEPTION TYPE zcx_invalid_input.\n"
            "  ENDIF.\n"
            "  SELECT SINGLE * FROM vbak\n"
            "    INTO @DATA(ls_order)\n"
            "    WHERE vbeln = @iv_vbeln.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-009")


# ===========================================================================
# ABAP-ERRH-010: Missing sy-subrc check after READ TABLE
# ===========================================================================


class TestAbapErrh010ReadTableSubrc:
    def test_read_table_without_subrc_detected(self) -> None:
        code = (
            "READ TABLE lt_orders INTO DATA(ls_order)\n"
            "  WITH KEY vbeln = lv_vbeln.\n"
            "lv_amount = ls_order-netwr.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERRH-010")

    def test_read_table_with_subrc_clean(self) -> None:
        code = (
            "READ TABLE lt_orders INTO DATA(ls_order)\n"
            "  WITH KEY vbeln = lv_vbeln.\n"
            "IF sy-subrc = 0.\n"
            "  lv_amount = ls_order-netwr.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERRH-010")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestErrorHandlingBilingual:
    def test_german_output(self) -> None:
        code = "RAISE EXCEPTION TYPE zcx_invalid_input.\n"
        findings = _run(code, language=Language.DE)
        errh002 = next((f for f in findings if f.rule_id == "ABAP-ERRH-002"), None)
        if errh002:
            assert "Nachricht" in errh002.title or "ohne" in errh002.title

    def test_english_output(self) -> None:
        code = "RAISE EXCEPTION TYPE zcx_invalid_input.\n"
        findings = _run(code, language=Language.EN)
        errh002 = next((f for f in findings if f.rule_id == "ABAP-ERRH-002"), None)
        if errh002:
            assert "message" in errh002.title.lower() or "RAISE" in errh002.title


# ===========================================================================
# Severity calibration
# ===========================================================================


class TestErrorHandlingSeverity:
    def test_raise_without_message_is_important(self) -> None:
        code = "RAISE EXCEPTION TYPE zcx_invalid_input.\n"
        findings = _run(code)
        errh002 = next((f for f in findings if f.rule_id == "ABAP-ERRH-002"), None)
        if errh002:
            assert errh002.severity == Severity.IMPORTANT

    def test_catch_without_into_is_important(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH zcx_process_error.\n"
            "    MESSAGE 'Error occurred' TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        errh008 = next((f for f in findings if f.rule_id == "ABAP-ERRH-008"), None)
        if errh008:
            assert errh008.severity == Severity.IMPORTANT

    def test_missing_cleanup_is_optional(self) -> None:
        code = (
            "TRY.\n"
            "    CALL FUNCTION 'ENQUEUE_EZVBAK'\n"
            "      EXPORTING vbeln = lv_vbeln.\n"
            "  CATCH cx_foreign_lock INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        errh001 = next((f for f in findings if f.rule_id == "ABAP-ERRH-001"), None)
        if errh001:
            assert errh001.severity == Severity.OPTIONAL
