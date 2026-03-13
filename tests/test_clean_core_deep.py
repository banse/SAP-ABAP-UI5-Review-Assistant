"""Tests for deep clean-core rules (CC-DEEP-001 through CC-DEEP-015)."""

from __future__ import annotations

import pytest

from app.engines.clean_core_checker import check_clean_core
from app.models.enums import ArtifactType, Language, Severity
from app.models.schemas import CleanCoreHint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check(
    code: str,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
) -> list[CleanCoreHint]:
    return check_clean_core(code, artifact_type, language)


def _has_finding(hints: list[CleanCoreHint], fragment: str) -> bool:
    """Check if any hint finding text contains the fragment (case-insensitive)."""
    return any(fragment.lower() in h.finding.lower() for h in hints)


# ===================================================================
# CC-DEEP-001: Classic Dynpro flow logic (PBO/PAI)
# ===================================================================


class TestCcDeep001ClassicDynpro:
    def test_pbo_detected(self) -> None:
        code = (
            "PROCESS BEFORE OUTPUT.\n"
            "  MODULE status_0100.\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "PROCESS BEFORE OUTPUT")

    def test_pai_detected(self) -> None:
        code = (
            "PROCESS AFTER INPUT.\n"
            "  MODULE user_command_0100.\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "PROCESS AFTER INPUT")

    def test_module_output_detected(self) -> None:
        code = "MODULE status_0100 OUTPUT.\n  SET PF-STATUS 'MAIN'.\nENDMODULE.\n"
        hints = _check(code)
        assert _has_finding(hints, "MODULE")

    def test_clean_method_not_flagged(self) -> None:
        code = "METHOD process_data.\n  DATA lv_x TYPE i.\n  lv_x = 42.\nENDMETHOD.\n"
        hints = _check(code)
        assert not _has_finding(hints, "PROCESS BEFORE OUTPUT")
        assert not _has_finding(hints, "PROCESS AFTER INPUT")


# ===================================================================
# CC-DEEP-002: Classic ALV without CL_SALV
# ===================================================================


class TestCcDeep002ClassicAlv:
    def test_reuse_alv_grid_detected(self) -> None:
        code = (
            "CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'\n"
            "  EXPORTING i_structure_name = 'VBAK'\n"
            "  TABLES t_outtab = lt_data.\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "REUSE_ALV_GRID_DISPLAY")

    def test_cl_gui_alv_grid_detected(self) -> None:
        code = "DATA: go_grid TYPE REF TO CL_GUI_ALV_GRID.\nCREATE OBJECT go_grid.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_GUI_ALV_GRID")

    def test_cl_salv_table_not_flagged_as_deep002(self) -> None:
        code = (
            "DATA: lo_salv TYPE REF TO CL_SALV_TABLE.\n"
            "CL_SALV_TABLE=>factory( IMPORTING r_salv_table = lo_salv CHANGING t_table = lt_data ).\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "Classic ALV without CL_SALV")


# ===================================================================
# CC-DEEP-003: SAPscript form usage
# ===================================================================


class TestCcDeep003SapScript:
    def test_open_form_detected(self) -> None:
        code = "CALL FUNCTION 'OPEN_FORM'\n  EXPORTING form = 'ZFORM'.\n"
        hints = _check(code)
        assert _has_finding(hints, "OPEN_FORM")

    def test_write_form_detected(self) -> None:
        code = "CALL FUNCTION 'WRITE_FORM'\n  EXPORTING element = 'HEADER'.\n"
        hints = _check(code)
        assert _has_finding(hints, "WRITE_FORM")

    def test_close_form_detected(self) -> None:
        code = "CALL FUNCTION 'CLOSE_FORM'.\n"
        hints = _check(code)
        assert _has_finding(hints, "CLOSE_FORM")

    def test_adobe_form_not_flagged(self) -> None:
        code = (
            "CALL FUNCTION '/1BCDWB/FM00000001'\n"
            "  EXPORTING iv_data = ls_data.\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "SAPscript")


# ===================================================================
# CC-DEEP-004: SAPConnect BCS email
# ===================================================================


class TestCcDeep004BcsEmail:
    def test_cl_bcs_detected(self) -> None:
        code = (
            "DATA: lo_bcs TYPE REF TO CL_BCS.\n"
            "lo_bcs = CL_BCS=>create_persistent( ).\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "CL_BCS")

    def test_cl_document_bcs_detected(self) -> None:
        code = "DATA: lo_doc TYPE REF TO CL_DOCUMENT_BCS.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_DOCUMENT_BCS")

    def test_released_mail_api_not_flagged(self) -> None:
        code = "DATA: lo_mail TYPE REF TO CL_BCS_MAIL_MESSAGE.\n"
        hints = _check(code)
        assert not _has_finding(hints, "SAPConnect BCS")


# ===================================================================
# CC-DEEP-005: Direct SAP standard table access
# ===================================================================


class TestCcDeep005SapTableAccess:
    def test_select_from_mara_detected(self) -> None:
        code = "SELECT matnr maktx FROM mara INTO TABLE @lt_material WHERE matnr = @iv_matnr.\n"
        hints = _check(code)
        assert _has_finding(hints, "MARA")

    def test_select_from_vbak_detected(self) -> None:
        code = "SELECT vbeln erdat FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        hints = _check(code)
        assert _has_finding(hints, "VBAK")

    def test_select_from_ekko_detected(self) -> None:
        code = "SELECT ebeln FROM ekko INTO TABLE @lt_po WHERE lifnr = @iv_vendor.\n"
        hints = _check(code)
        assert _has_finding(hints, "EKKO")

    def test_select_from_cds_view_not_flagged(self) -> None:
        code = (
            "SELECT MaterialNumber, MaterialDescription\n"
            "  FROM zi_material\n"
            "  INTO TABLE @lt_material\n"
            "  WHERE MaterialNumber = @iv_matnr.\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "Direct access to SAP table")

    def test_select_from_released_view_not_flagged(self) -> None:
        code = (
            "SELECT SalesOrder FROM I_SalesOrder\n"
            "  INTO TABLE @DATA(lt_orders)\n"
            "  WHERE SoldToParty = @iv_customer.\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "Direct access to SAP table")


# ===================================================================
# CC-DEEP-006: Common unreleased function module calls
# ===================================================================


class TestCcDeep006UnreleasedFm:
    def test_conversion_exit_detected(self) -> None:
        code = "CALL FUNCTION 'CONVERSION_EXIT_ALPHA_INPUT'\n  EXPORTING input = lv_in.\n"
        hints = _check(code)
        assert _has_finding(hints, "CONVERSION_EXIT_ALPHA_INPUT")

    def test_popup_to_confirm_detected(self) -> None:
        code = "CALL FUNCTION 'POPUP_TO_CONFIRM'\n  EXPORTING text_question = 'Sure?'.\n"
        hints = _check(code)
        assert _has_finding(hints, "POPUP_TO_CONFIRM")

    def test_gui_download_detected(self) -> None:
        code = "CALL FUNCTION 'GUI_DOWNLOAD'\n  EXPORTING filename = lv_file.\n"
        hints = _check(code)
        assert _has_finding(hints, "GUI_DOWNLOAD")

    def test_bapi_call_not_flagged_by_deep006(self) -> None:
        code = "CALL FUNCTION 'BAPI_SALESORDER_GETLIST'\n  EXPORTING customer = lv_kunnr.\n"
        hints = _check(code)
        assert not _has_finding(hints, "commonly unreleased")


# ===================================================================
# CC-DEEP-007: Kernel method call
# ===================================================================


class TestCcDeep007KernelCall:
    def test_kernel_call_detected(self) -> None:
        code = "CALL 'SYSTEM_TIMEZONE' ID 'TIMEZONE' FIELD lv_tz.\n"
        hints = _check(code)
        assert _has_finding(hints, "kernel call")

    def test_severity_is_critical(self) -> None:
        code = "CALL 'RFCControl' ID 'F' FIELD 'G'.\n"
        hints = _check(code)
        kernel_hints = [h for h in hints if "kernel" in h.finding.lower()]
        assert len(kernel_hints) > 0
        assert kernel_hints[0].severity == Severity.CRITICAL

    def test_normal_function_call_not_flagged(self) -> None:
        code = "CALL FUNCTION 'BAPI_MATERIAL_GET_DETAIL'\n  EXPORTING material = lv_matnr.\n"
        hints = _check(code)
        assert not _has_finding(hints, "kernel call")


# ===================================================================
# CC-DEEP-008: Table maintenance generator
# ===================================================================


class TestCcDeep008TableMaintenance:
    def test_view_maintenance_call_detected(self) -> None:
        code = (
            "CALL FUNCTION 'VIEW_MAINTENANCE_CALL'\n"
            "  EXPORTING action = 'U'\n"
            "            view_name = 'ZTAB_CONFIG'.\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "VIEW_MAINTENANCE_CALL")

    def test_rap_crud_not_flagged(self) -> None:
        code = (
            "MODIFY ENTITIES OF ZI_Config IN LOCAL MODE\n"
            "  ENTITY Config\n"
            "  UPDATE SET FIELDS WITH VALUE #( ( %key = ls_key value = lv_val ) ).\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "maintenance generator")


# ===================================================================
# CC-DEEP-009: BAdI implementation
# ===================================================================


class TestCcDeep009BadiImpl:
    def test_get_badi_detected(self) -> None:
        code = "GET BADI lo_badi TYPE badi_name.\n"
        hints = _check(code)
        assert _has_finding(hints, "GET BADI")

    def test_call_badi_detected(self) -> None:
        code = "CALL BADI lo_badi->method_name.\n"
        hints = _check(code)
        assert _has_finding(hints, "CALL BADI")

    def test_severity_is_optional(self) -> None:
        code = "GET BADI lo_badi TYPE badi_name.\n"
        hints = _check(code)
        badi_hints = [h for h in hints if "badi" in h.finding.lower()]
        assert len(badi_hints) > 0
        assert badi_hints[0].severity == Severity.OPTIONAL

    def test_cl_exithandler_detected(self) -> None:
        code = "CALL METHOD CL_EXITHANDLER=>get_instance.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_EXITHANDLER")


# ===================================================================
# CC-DEEP-010: Implicit enhancement
# ===================================================================


class TestCcDeep010ImplicitEnhancement:
    def test_enhancement_section_detected(self) -> None:
        code = 'ENHANCEMENT-SECTION sec_01 SPOTS z_spot.\nDATA lv_x TYPE i.\nEND-ENHANCEMENT-SECTION.\n'
        hints = _check(code)
        assert _has_finding(hints, "ENHANCEMENT-SECTION")

    def test_numbered_enhancement_detected(self) -> None:
        code = 'ENHANCEMENT 1 Z_MY_ENHANCEMENT.\n  lv_x = 42.\nENDENHANCEMENT.\n'
        hints = _check(code)
        assert _has_finding(hints, "ENHANCEMENT 1")

    def test_clean_code_not_flagged(self) -> None:
        code = "METHOD do_something.\n  DATA lv_x TYPE i.\n  lv_x = 1.\nENDMETHOD.\n"
        hints = _check(code)
        assert not _has_finding(hints, "Implicit enhancement")


# ===================================================================
# CC-DEEP-011: Modification assistant / SMOD/CMOD
# ===================================================================


class TestCcDeep011ModificationAssistant:
    def test_smod_reference_detected(self) -> None:
        code = "* This enhancement belongs to SMOD project Z_CUSTOM.\nDATA lv_x TYPE i.\n"
        hints = _check(code)
        assert _has_finding(hints, "SMOD")

    def test_cmod_reference_detected(self) -> None:
        code = "* Registered in CMOD project Z_PROJ.\nDATA lv_x TYPE i.\n"
        hints = _check(code)
        assert _has_finding(hints, "CMOD")

    def test_clean_code_not_flagged(self) -> None:
        code = "CLASS zcl_clean DEFINITION PUBLIC.\nENDCLASS.\n"
        hints = _check(code)
        assert not _has_finding(hints, "Modification assistant")


# ===================================================================
# CC-DEEP-012: Side-by-side extension opportunity
# ===================================================================


class TestCcDeep012SideBySide:
    def test_bapi_with_destination_detected(self) -> None:
        code = (
            "CALL FUNCTION 'BAPI_SALESORDER_CREATEFROMDAT2'\n"
            "  DESTINATION lv_rfc_dest\n"
            "  EXPORTING order_header_in = ls_header.\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "side-by-side")

    def test_bapi_without_destination_not_flagged(self) -> None:
        code = (
            "CALL FUNCTION 'BAPI_SALESORDER_GETLIST'\n"
            "  EXPORTING customer = lv_kunnr.\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "side-by-side")

    def test_severity_is_optional(self) -> None:
        code = (
            "CALL FUNCTION 'RFC_READ_TABLE'\n"
            "  DESTINATION lv_dest\n"
            "  EXPORTING query_table = 'MARA'.\n"
        )
        hints = _check(code)
        side_hints = [h for h in hints if "side-by-side" in h.finding.lower()]
        assert len(side_hints) > 0
        assert side_hints[0].severity == Severity.OPTIONAL


# ===================================================================
# CC-DEEP-013: Key user extensibility pattern
# ===================================================================


class TestCcDeep013KeyUserExt:
    def test_ci_include_detected(self) -> None:
        code = "INCLUDE STRUCTURE CI_VBAK.\n"
        hints = _check(code)
        assert _has_finding(hints, "CI_")

    def test_append_structure_detected(self) -> None:
        code = "APPEND STRUCTURE zappend TO vbak.\n"
        hints = _check(code)
        assert _has_finding(hints, "APPEND STRUCTURE")

    def test_custom_fields_api_not_flagged(self) -> None:
        code = (
            "DATA: lo_cf TYPE REF TO CL_CUST_FIELD_EXTENSIBILITY.\n"
            "lo_cf->add_field( iv_name = 'ZZ_CUSTOM' ).\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "CI_INCLUDE or append")


# ===================================================================
# CC-DEEP-014: Event-driven extension missing
# ===================================================================


class TestCcDeep014EventMissing:
    def test_modify_entities_without_event_detected(self) -> None:
        code = (
            "MODIFY ENTITIES OF ZI_SalesOrder IN LOCAL MODE\n"
            "  ENTITY SalesOrder\n"
            "  UPDATE SET FIELDS WITH VALUE #( ( %key = ls_key status = 'C' ) )\n"
            "  MAPPED DATA(ls_mapped)\n"
            "  FAILED DATA(ls_failed)\n"
            "  REPORTED DATA(ls_reported).\n"
        )
        hints = _check(code)
        assert _has_finding(hints, "without event raising")

    def test_modify_with_raise_event_clean(self) -> None:
        code = (
            "MODIFY ENTITIES OF ZI_SalesOrder IN LOCAL MODE\n"
            "  ENTITY SalesOrder\n"
            "  UPDATE SET FIELDS WITH VALUE #( ( %key = ls_key status = 'C' ) )\n"
            "  MAPPED DATA(ls_mapped)\n"
            "  FAILED DATA(ls_failed)\n"
            "  REPORTED DATA(ls_reported).\n"
            "RAISE ENTITY EVENT ZI_SalesOrder~StatusChanged\n"
            "  FROM VALUE #( ( %key = ls_key ) ).\n"
        )
        hints = _check(code)
        assert not _has_finding(hints, "without event raising")

    def test_no_modify_not_flagged(self) -> None:
        code = "METHOD get_data.\n  SELECT * FROM zi_data INTO TABLE @lt_data.\nENDMETHOD.\n"
        hints = _check(code)
        assert not _has_finding(hints, "without event raising")


# ===================================================================
# CC-DEEP-015: SAP_BASIS dependent code
# ===================================================================


class TestCcDeep015BasisDependent:
    def test_cl_gui_frontend_services_detected(self) -> None:
        code = "CL_GUI_FRONTEND_SERVICES=>file_open_dialog( CHANGING file_table = lt_files ).\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_GUI_FRONTEND_SERVICES")

    def test_cl_gui_custom_container_detected(self) -> None:
        code = "DATA: go_cont TYPE REF TO CL_GUI_CUSTOM_CONTAINER.\nCREATE OBJECT go_cont.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_GUI_CUSTOM_CONTAINER")

    def test_web_dynpro_class_detected(self) -> None:
        code = "DATA: lo_wdr TYPE REF TO CL_WDR_CONTEXT_ELEMENT.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_WDR_CONTEXT_ELEMENT")

    def test_fpm_class_detected(self) -> None:
        code = "DATA: lo_fpm TYPE REF TO CL_FPM_EVENT.\n"
        hints = _check(code)
        assert _has_finding(hints, "CL_FPM_EVENT")

    def test_modern_class_not_flagged(self) -> None:
        code = "DATA: lo_json TYPE REF TO CL_ABAP_JSON.\n"
        hints = _check(code)
        assert not _has_finding(hints, "SAP_BASIS dependent")


# ===================================================================
# Bilingual output for deep rules
# ===================================================================


class TestDeepRulesBilingual:
    def test_german_dynpro_finding(self) -> None:
        code = "PROCESS BEFORE OUTPUT.\n  MODULE status_0100.\n"
        hints = _check(code, language=Language.DE)
        assert _has_finding(hints, "Klassische Dynpro-Ablauflogik")

    def test_english_dynpro_finding(self) -> None:
        code = "PROCESS BEFORE OUTPUT.\n  MODULE status_0100.\n"
        hints = _check(code, language=Language.EN)
        assert _has_finding(hints, "Classic Dynpro flow logic")

    def test_german_kernel_finding(self) -> None:
        code = "CALL 'SYSTEM_TIMEZONE' ID 'TIMEZONE' FIELD lv_tz.\n"
        hints = _check(code, language=Language.DE)
        assert _has_finding(hints, "Kernel-Aufruf")

    def test_english_kernel_finding(self) -> None:
        code = "CALL 'SYSTEM_TIMEZONE' ID 'TIMEZONE' FIELD lv_tz.\n"
        hints = _check(code, language=Language.EN)
        assert _has_finding(hints, "kernel call")


# ===================================================================
# Severity calibration
# ===================================================================


class TestDeepSeverityCalibration:
    def test_kernel_call_is_critical(self) -> None:
        code = "CALL 'RFCControl' ID 'F' FIELD 'G'.\n"
        hints = _check(code)
        kernel_hints = [h for h in hints if "kernel" in h.finding.lower()]
        assert all(h.severity == Severity.CRITICAL for h in kernel_hints)

    def test_dynpro_is_important(self) -> None:
        code = "PROCESS BEFORE OUTPUT.\n  MODULE status_0100.\n"
        hints = _check(code)
        dynpro_hints = [h for h in hints if "dynpro" in h.finding.lower()]
        assert any(h.severity == Severity.IMPORTANT for h in dynpro_hints)

    def test_badi_is_optional(self) -> None:
        code = "GET BADI lo_badi TYPE badi_name.\n"
        hints = _check(code)
        badi_hints = [h for h in hints if "badi" in h.finding.lower()]
        assert all(h.severity == Severity.OPTIONAL for h in badi_hints)

    def test_sap_table_access_is_important(self) -> None:
        code = "SELECT matnr FROM mara INTO TABLE @lt_mat WHERE matnr = @iv_matnr.\n"
        hints = _check(code)
        table_hints = [h for h in hints if "direct access to sap table" in h.finding.lower()]
        assert all(h.severity == Severity.IMPORTANT for h in table_hints)


# ===================================================================
# Non-ABAP artifacts should not trigger deep rules
# ===================================================================


class TestDeepNonAbapArtifacts:
    def test_cds_view_returns_no_deep_hints(self) -> None:
        code = "define view entity ZI_Test as select from mara { key matnr }\n"
        hints = _check(code, ArtifactType.CDS_VIEW)
        assert hints == []

    def test_ui5_controller_returns_no_deep_hints(self) -> None:
        code = 'sap.ui.define(["sap/ui/core/mvc/Controller"], function(C) {});\n'
        hints = _check(code, ArtifactType.UI5_CONTROLLER)
        assert hints == []


# ===================================================================
# Edge cases
# ===================================================================


class TestDeepEdgeCases:
    def test_empty_code_returns_empty(self) -> None:
        hints = _check("")
        assert hints == []

    def test_released_api_alternative_present_for_deep_rules(self) -> None:
        code = "CALL 'RFCControl' ID 'F' FIELD 'G'.\n"
        hints = _check(code)
        kernel_hints = [h for h in hints if "kernel" in h.finding.lower()]
        assert len(kernel_hints) > 0
        assert kernel_hints[0].released_api_alternative is not None

    def test_mixed_deep_violations_sorted_by_severity(self) -> None:
        code = (
            "CALL 'SYSTEM_TIMEZONE' ID 'TZ' FIELD lv_tz.\n"
            "PROCESS BEFORE OUTPUT.\n"
            "  MODULE status_0100.\n"
            "GET BADI lo_badi TYPE badi_name.\n"
        )
        hints = _check(code)
        if len(hints) >= 2:
            severity_order = {
                Severity.CRITICAL: 0,
                Severity.IMPORTANT: 1,
                Severity.OPTIONAL: 2,
                Severity.UNCLEAR: 3,
            }
            indices = [severity_order[h.severity] for h in hints]
            assert indices == sorted(indices)
