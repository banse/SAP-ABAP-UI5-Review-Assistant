"""Tests for the clean-core compliance checker."""

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


def _has_rule(hints: list[CleanCoreHint], rule_fragment: str) -> bool:
    """Check if any hint finding text contains the rule fragment."""
    return any(rule_fragment.lower() in h.finding.lower() for h in hints)


# ===========================================================================
# CC-API-001: Direct database table access
# ===========================================================================


class TestCcApi001DirectTableAccess:
    def test_select_from_ztable_detected(self) -> None:
        code = "SELECT * FROM ztab_orders INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        hints = _check(code)
        assert any("ztab_orders" in h.finding for h in hints)

    def test_select_from_released_view_clean(self) -> None:
        code = "SELECT * FROM I_SalesOrder INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        hints = _check(code)
        assert not any("CC-API-001" in (h.finding or "") for h in hints)
        # Should not flag I_ views as direct table access
        assert not any("ztab" in h.finding.lower() for h in hints)


# ===========================================================================
# CC-API-002: Unreleased function module calls
# ===========================================================================


class TestCcApi002UnreleasedFm:
    def test_unreleased_fm_detected(self) -> None:
        code = "CALL FUNCTION 'SD_SALES_ORDER_READ'\n  EXPORTING iv_vbeln = lv_vbeln.\n"
        hints = _check(code)
        assert any("SD_SALES_ORDER_READ" in h.finding for h in hints)

    def test_bapi_fm_not_flagged(self) -> None:
        code = "CALL FUNCTION 'BAPI_SALESORDER_GETLIST'\n  EXPORTING customer = lv_kunnr.\n"
        hints = _check(code)
        assert not any("BAPI_SALESORDER_GETLIST" in h.finding for h in hints)


# ===========================================================================
# CC-API-003: Modification markers
# ===========================================================================


class TestCcApi003ModificationMarkers:
    def test_enhancement_point_detected(self) -> None:
        code = "ENHANCEMENT-POINT ep_custom_logic SPOTS z_custom.\n"
        hints = _check(code)
        assert any("ENHANCEMENT-POINT" in h.finding for h in hints)

    def test_enhancement_section_detected(self) -> None:
        code = "ENHANCEMENT-SECTION sec_01 SPOTS z_spot.\nDATA lv_x TYPE i.\nENHANCEMENT-SECTION.\n"
        hints = _check(code)
        assert any("ENHANCEMENT" in h.finding for h in hints)

    def test_clean_code_no_enhancement(self) -> None:
        code = "METHOD process.\n  DATA lv_result TYPE i.\n  lv_result = 42.\nENDMETHOD.\n"
        hints = _check(code)
        assert not any("ENHANCEMENT" in h.finding for h in hints)


# ===========================================================================
# CC-API-004: User-exit / BAdI modification
# ===========================================================================


class TestCcApi004UserExit:
    def test_customer_function_detected(self) -> None:
        code = "CALL CUSTOMER-FUNCTION '001'\n  EXPORTING iv_data = lv_data.\n"
        hints = _check(code)
        assert any("CUSTOMER-FUNCTION" in h.finding for h in hints)

    def test_userexit_pattern_detected(self) -> None:
        code = "FORM USEREXIT_PRICING_COND.\n  \" Custom pricing logic\nENDFORM.\n"
        hints = _check(code)
        assert any("USEREXIT_" in h.finding for h in hints)

    def test_exit_function_detected(self) -> None:
        code = "DATA: lv_val TYPE c.\nIF EXIT_SAPLV60A_001 IS NOT INITIAL.\nENDIF.\n"
        hints = _check(code)
        assert any("EXIT_" in h.finding for h in hints)


# ===========================================================================
# CC-API-005: Classic dynpro usage
# ===========================================================================


class TestCcApi005ClassicDynpro:
    def test_call_screen_detected(self) -> None:
        code = "CALL SCREEN 0100.\n"
        hints = _check(code)
        assert any("CALL SCREEN" in h.finding for h in hints)

    def test_module_input_detected(self) -> None:
        code = "MODULE user_command_0100 INPUT.\n  CASE ok_code.\n  ENDCASE.\nENDMODULE.\n"
        hints = _check(code)
        assert any("MODULE" in h.finding for h in hints)

    def test_set_screen_detected(self) -> None:
        code = "SET SCREEN 0200.\nLEAVE SCREEN.\n"
        hints = _check(code)
        assert any("SET SCREEN" in h.finding for h in hints)


# ===========================================================================
# CC-API-006: TABLES statement
# ===========================================================================


class TestCcApi006TablesStatement:
    def test_tables_statement_detected(self) -> None:
        code = "TABLES: vbak, vbap.\nSTART-OF-SELECTION.\n  SELECT * FROM vbak INTO vbak.\n"
        hints = _check(code)
        assert any("TABLES" in h.finding for h in hints)

    def test_tables_single_detected(self) -> None:
        code = "TABLES mara.\n"
        hints = _check(code)
        assert any("TABLES" in h.finding for h in hints)


# ===========================================================================
# CC-API-007: Obsolete ALV technology
# ===========================================================================


class TestCcApi007ObsoleteAlv:
    def test_reuse_alv_grid_detected(self) -> None:
        code = (
            "CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'\n"
            "  EXPORTING\n"
            "    i_structure_name = 'VBAK'\n"
            "  TABLES\n"
            "    t_outtab = lt_data.\n"
        )
        hints = _check(code)
        assert any("REUSE_ALV_GRID_DISPLAY" in h.finding for h in hints)

    def test_cl_gui_alv_grid_detected(self) -> None:
        code = "DATA: go_grid TYPE REF TO CL_GUI_ALV_GRID.\nCREATE OBJECT go_grid.\n"
        hints = _check(code)
        assert any("CL_GUI_ALV_GRID" in h.finding for h in hints)

    def test_reuse_alv_list_detected(self) -> None:
        code = "CALL FUNCTION 'REUSE_ALV_LIST_DISPLAY'\n  TABLES t_outtab = lt_data.\n"
        hints = _check(code)
        assert any("REUSE_ALV_LIST_DISPLAY" in h.finding for h in hints)

    def test_reuse_alv_fieldcatalog_detected(self) -> None:
        code = "CALL FUNCTION 'REUSE_ALV_FIELDCATALOG_MERGE'\n  EXPORTING i_structure_name = 'VBAK'.\n"
        hints = _check(code)
        assert any("REUSE_ALV_FIELDCATALOG_MERGE" in h.finding for h in hints)


# ===========================================================================
# CC-API-008: Non-released CDS view access
# ===========================================================================


class TestCcApi008NonReleasedCds:
    def test_non_released_table_flagged(self) -> None:
        code = "SELECT vbeln FROM VBAK INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        hints = _check(code)
        assert any("VBAK" in h.finding for h in hints)

    def test_released_i_view_not_flagged(self) -> None:
        code = "SELECT SalesOrder FROM I_SalesOrder INTO TABLE @lt_orders.\n"
        hints = _check(code)
        # I_ views should not be flagged by CC-API-008
        assert not any("I_SalesOrder" in h.finding for h in hints)


# ===========================================================================
# CC-API-009: Direct system field manipulation
# ===========================================================================


class TestCcApi009SystemFieldManipulation:
    def test_sy_msgid_direct_set_detected(self) -> None:
        code = "sy-msgid = 'ZMSG'.\nsy-msgno = '001'.\n"
        hints = _check(code)
        assert any("sy-msgid" in h.finding.lower() for h in hints)

    def test_sy_subrc_check_not_flagged(self) -> None:
        """Reading sy-subrc is fine, only setting sy-msg* fields is flagged."""
        code = "IF sy-subrc <> 0.\n  RAISE EXCEPTION TYPE zcx_error.\nENDIF.\n"
        hints = _check(code)
        assert not any("sy-subrc" in h.finding.lower() for h in hints)


# ===========================================================================
# CC-API-010: Old-style ABAP SQL
# ===========================================================================


class TestCcApi010OldStyleSql:
    def test_old_style_into_detected(self) -> None:
        code = "SELECT vbeln FROM vbak INTO TABLE lt_orders WHERE kunnr = iv_kunnr.\n"
        hints = _check(code)
        assert any("INTO" in h.finding.upper() for h in hints)

    def test_modern_inline_not_flagged(self) -> None:
        code = "SELECT vbeln FROM vbak INTO TABLE @DATA(lt_orders) WHERE kunnr = @iv_kunnr.\n"
        hints = _check(code)
        # The modern @ style should not trigger CC-API-010
        assert not any("inline" in h.finding.lower() and "old" in h.finding.lower() for h in hints)


# ===========================================================================
# Clean modern code — no hints expected
# ===========================================================================


class TestCleanModernCode:
    def test_clean_rap_code_no_hints(self) -> None:
        code = (
            "CLASS lhc_salesorder DEFINITION INHERITING FROM cl_abap_behavior_handler.\n"
            "  PRIVATE SECTION.\n"
            "    METHODS validate_status FOR VALIDATE ON SAVE\n"
            "      IMPORTING keys FOR SalesOrder~validateStatus.\n"
            "ENDCLASS.\n"
            "\n"
            "CLASS lhc_salesorder IMPLEMENTATION.\n"
            "  METHOD validate_status.\n"
            "    READ ENTITIES OF ZI_SalesOrder IN LOCAL MODE\n"
            "      ENTITY SalesOrder\n"
            "      FIELDS ( Status )\n"
            "      WITH CORRESPONDING #( keys )\n"
            "      RESULT DATA(lt_orders).\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        hints = _check(code)
        # RAP code using READ ENTITIES should not trigger clean-core violations
        # (may trigger CC-API-008 for non-I_ prefix but that is OPTIONAL)
        critical_hints = [h for h in hints if h.severity == Severity.CRITICAL]
        assert len(critical_hints) == 0

    def test_clean_modern_abap_no_critical_hints(self) -> None:
        code = (
            "METHOD get_orders.\n"
            "  SELECT SalesOrder, SoldToParty\n"
            "    FROM I_SalesOrder\n"
            "    INTO TABLE @DATA(lt_orders)\n"
            "    WHERE SoldToParty = @iv_customer.\n"
            "ENDMETHOD.\n"
        )
        hints = _check(code)
        critical_hints = [h for h in hints if h.severity == Severity.CRITICAL]
        assert len(critical_hints) == 0


# ===========================================================================
# Non-ABAP artifact types
# ===========================================================================


class TestNonAbapArtifacts:
    def test_cds_view_returns_empty(self) -> None:
        code = "define view entity ZI_Test as select from ztab { key id }\n"
        hints = _check(code, ArtifactType.CDS_VIEW)
        assert hints == []

    def test_ui5_controller_returns_empty(self) -> None:
        code = 'sap.ui.define(["sap/ui/core/mvc/Controller"], function(C) {});\n'
        hints = _check(code, ArtifactType.UI5_CONTROLLER)
        assert hints == []


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    def test_german_finding_text(self) -> None:
        code = "ENHANCEMENT-POINT ep_01 SPOTS z_spot.\n"
        hints = _check(code, language=Language.DE)
        assert len(hints) > 0
        assert any("Modifikationsmarker" in h.finding for h in hints)

    def test_english_finding_text(self) -> None:
        code = "ENHANCEMENT-POINT ep_01 SPOTS z_spot.\n"
        hints = _check(code, language=Language.EN)
        assert len(hints) > 0
        assert any("Modification marker" in h.finding for h in hints)


# ===========================================================================
# Severity ordering
# ===========================================================================


class TestSeverityOrdering:
    def test_critical_before_important(self) -> None:
        code = (
            "ENHANCEMENT-POINT ep_01 SPOTS z_spot.\n"
            "TABLES: vbak.\n"
            "SELECT * FROM ztab_custom INTO TABLE @lt_data.\n"
        )
        hints = _check(code)
        if len(hints) >= 2:
            severities = [h.severity for h in hints]
            severity_order = {
                Severity.CRITICAL: 0,
                Severity.IMPORTANT: 1,
                Severity.OPTIONAL: 2,
                Severity.UNCLEAR: 3,
            }
            indices = [severity_order[s] for s in severities]
            assert indices == sorted(indices)


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_empty_code_returns_empty(self) -> None:
        hints = _check("")
        assert hints == []

    def test_whitespace_only_returns_empty(self) -> None:
        hints = _check("   \n\t  \n")
        assert hints == []

    def test_released_api_alternative_present(self) -> None:
        code = "ENHANCEMENT-POINT ep_01 SPOTS z_spot.\n"
        hints = _check(code)
        for h in hints:
            if "ENHANCEMENT" in h.finding:
                assert h.released_api_alternative is not None
                assert len(h.released_api_alternative) > 0

    def test_mixed_violations_all_detected(self) -> None:
        code = (
            "TABLES: vbak.\n"
            "ENHANCEMENT-POINT ep_01 SPOTS z_spot.\n"
            "CALL SCREEN 0100.\n"
            "CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'\n"
            "  TABLES t_outtab = lt_data.\n"
            "SELECT * FROM ztab_orders INTO TABLE lt_orders.\n"
        )
        hints = _check(code)
        # Should detect multiple violations
        assert len(hints) >= 3
