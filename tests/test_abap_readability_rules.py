"""Tests for ABAP readability and structure rules."""

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
# ABAP-RDBL-001: Naming convention violations
# ===========================================================================


class TestAbapRdbl001NamingConvention:
    def test_bad_variable_name_detected(self) -> None:
        code = "DATA counter TYPE i.\ncounter = 1.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-001")

    def test_proper_prefix_clean(self) -> None:
        code = "DATA lv_counter TYPE i.\nlv_counter = 1.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-001")

    def test_table_prefix_clean(self) -> None:
        code = "DATA lt_orders TYPE TABLE OF vbak.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-001")

    def test_structure_prefix_clean(self) -> None:
        code = "DATA ls_order TYPE vbak.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-001")


# ===========================================================================
# ABAP-RDBL-002: Method too many parameters
# ===========================================================================


class TestAbapRdbl002TooManyParams:
    def test_method_with_many_params_detected(self) -> None:
        code = (
            "METHODS process_order\n"
            "  IMPORTING\n"
            "    iv_order_id TYPE vbeln\n"
            "    iv_customer TYPE kunnr\n"
            "    iv_material TYPE matnr\n"
            "    iv_quantity TYPE menge_d\n"
            "    iv_plant TYPE werks_d\n"
            "    iv_date TYPE datum\n"
            "  EXPORTING\n"
            "    ev_result TYPE string.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-002")

    def test_method_with_few_params_clean(self) -> None:
        code = (
            "METHODS get_order\n"
            "  IMPORTING\n"
            "    iv_order_id TYPE vbeln\n"
            "  RETURNING\n"
            "    VALUE(rs_order) TYPE zstr_order.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-002")


# ===========================================================================
# ABAP-RDBL-003: Commented-out code
# ===========================================================================


class TestAbapRdbl003CommentedOutCode:
    def test_commented_select_detected(self) -> None:
        code = "* SELECT * FROM vbak INTO TABLE lt_orders.\nDATA lv_x TYPE i.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-003")

    def test_commented_loop_detected(self) -> None:
        code = "* LOOP AT lt_orders INTO DATA(ls_order).\nDATA lv_x TYPE i.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-003")

    def test_normal_comment_clean(self) -> None:
        code = "* This is a regular documentation comment.\nDATA lv_x TYPE i.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-003")


# ===========================================================================
# ABAP-RDBL-004: Dead code after RETURN/RAISE
# ===========================================================================


class TestAbapRdbl004DeadCode:
    def test_code_after_return_detected(self) -> None:
        code = (
            "METHOD process.\n"
            "  RETURN.\n"
            "  DATA lv_x TYPE i.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-004")

    def test_code_after_raise_detected(self) -> None:
        code = (
            "METHOD validate.\n"
            "  RAISE EXCEPTION TYPE zcx_error.\n"
            "  lv_result = 1.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-004")

    def test_return_before_endmethod_clean(self) -> None:
        code = (
            "METHOD process.\n"
            "  DATA lv_x TYPE i.\n"
            "  lv_x = 1.\n"
            "  RETURN.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-004")


# ===========================================================================
# ABAP-RDBL-005: String literal duplication
# ===========================================================================


class TestAbapRdbl005StringDuplication:
    def test_duplicated_literal_detected(self) -> None:
        code = (
            "IF lv_status = 'ACTIVE'.\n"
            "ELSEIF lv_other = 'ACTIVE'.\n"
            "ELSEIF lv_third = 'ACTIVE'.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-005")

    def test_unique_literals_clean(self) -> None:
        code = (
            "IF lv_status = 'ACTIVE'.\n"
            "ELSEIF lv_other = 'PENDING'.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-005")


# ===========================================================================
# ABAP-RDBL-006: Obsolete type usage
# ===========================================================================


class TestAbapRdbl006ObsoleteType:
    def test_type_c_without_length_detected(self) -> None:
        code = "DATA lv_flag TYPE c.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-006")

    def test_type_c_with_length_clean(self) -> None:
        code = "DATA lv_flag TYPE c LENGTH 1.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-006")

    def test_type_string_clean(self) -> None:
        code = "DATA lv_text TYPE string.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-006")


# ===========================================================================
# ABAP-RDBL-007: Missing method documentation
# ===========================================================================


class TestAbapRdbl007MissingMethodDoc:
    def test_method_without_doc_detected(self) -> None:
        code = (
            "  METHODS get_orders\n"
            "    RETURNING VALUE(rt_result) TYPE ztt_orders.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-007")

    def test_method_with_abap_doc_clean(self) -> None:
        code = (
            '  "! Returns sales orders for a given customer.\n'
            "  METHODS get_orders\n"
            "    RETURNING VALUE(rt_result) TYPE ztt_orders.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-007")


# ===========================================================================
# ABAP-RDBL-008: Inline declaration opportunity
# ===========================================================================


class TestAbapRdbl008InlineDeclaration:
    def test_data_then_assignment_detected(self) -> None:
        code = (
            "DATA lv_count TYPE i.\n"
            "lv_count = lines( lt_orders ).\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-008")

    def test_inline_data_clean(self) -> None:
        code = "DATA(lv_count) = lines( lt_orders ).\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-008")


# ===========================================================================
# ABAP-RDBL-009: Magic number detection
# ===========================================================================


class TestAbapRdbl009MagicNumber:
    def test_magic_number_in_if_detected(self) -> None:
        code = "IF lv_count > 100.\n  WRITE 'too many'.\nENDIF.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-009")

    def test_named_constant_clean(self) -> None:
        code = (
            "CONSTANTS lc_max_count TYPE i VALUE 100.\n"
            "IF lv_count > lc_max_count.\n"
            "  WRITE 'too many'.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-009")

    def test_small_number_clean(self) -> None:
        code = "IF lv_count > 0.\n  WRITE 'has items'.\nENDIF.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-009")


# ===========================================================================
# ABAP-RDBL-010: CLASS-DATA overuse
# ===========================================================================


class TestAbapRdbl010ClassDataOveruse:
    def test_many_class_data_detected(self) -> None:
        code = (
            "CLASS-DATA gv_one TYPE i.\n"
            "CLASS-DATA gv_two TYPE i.\n"
            "CLASS-DATA gv_three TYPE i.\n"
            "CLASS-DATA gv_four TYPE i.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-RDBL-010")

    def test_few_class_data_clean(self) -> None:
        code = (
            "CLASS-DATA gv_instance TYPE REF TO zcl_singleton.\n"
            "DATA mv_value TYPE i.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-RDBL-010")


# ===========================================================================
# ABAP-RDBL-011: Too many local variables
# ===========================================================================


class TestAbapRdbl011TooManyLocalVars:
    def test_many_data_declarations_detected(self) -> None:
        lines = ["METHOD complex_logic."]
        for i in range(12):
            lines.append(f"  DATA lv_var{i} TYPE i.")
        lines.append("ENDMETHOD.")
        code = "\n".join(lines)
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "ABAP-RDBL-011")

    def test_few_data_declarations_clean(self) -> None:
        code = (
            "METHOD simple_logic.\n"
            "  DATA lv_x TYPE i.\n"
            "  DATA lv_y TYPE i.\n"
            "  lv_x = 1.\n"
            "  lv_y = 2.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "ABAP-RDBL-011")


# ===========================================================================
# ABAP-RDBL-012: Missing FINAL for read-only variables
# ===========================================================================


class TestAbapRdbl012MissingFinal:
    def test_single_assignment_var_detected(self) -> None:
        code = (
            "METHOD get_count.\n"
            "  DATA lv_count TYPE i.\n"
            "  lv_count = lines( lt_orders ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "ABAP-RDBL-012")

    def test_reassigned_var_clean(self) -> None:
        code = (
            "METHOD accumulate.\n"
            "  DATA lv_sum TYPE i.\n"
            "  lv_sum = 0.\n"
            "  lv_sum = lv_sum + 1.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "ABAP-RDBL-012")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestReadabilityBilingual:
    def test_german_output(self) -> None:
        code = "DATA counter TYPE i.\ncounter = 1.\n"
        findings = _run(code, language=Language.DE)
        rdbl001 = next((f for f in findings if f.rule_id == "ABAP-RDBL-001"), None)
        if rdbl001:
            assert "Namenskonvention" in rdbl001.title

    def test_english_output(self) -> None:
        code = "DATA counter TYPE i.\ncounter = 1.\n"
        findings = _run(code, language=Language.EN)
        rdbl001 = next((f for f in findings if f.rule_id == "ABAP-RDBL-001"), None)
        if rdbl001:
            assert "Naming" in rdbl001.title
