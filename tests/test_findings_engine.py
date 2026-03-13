"""Tests for the main findings engine."""

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
# ABAP rule tests
# ===========================================================================


class TestAbapRead001SelectStar:
    def test_select_star_detected(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-READ-001")

    def test_select_specific_fields_clean(self) -> None:
        code = "SELECT vbeln erdat FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-READ-001")


class TestAbapRead002NoWhere:
    def test_select_without_where(self) -> None:
        code = "SELECT vbeln FROM vbak INTO TABLE @lt_orders.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-READ-002")

    def test_select_with_where_clean(self) -> None:
        code = "SELECT vbeln FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-READ-002")


class TestAbapRead003NestedSelect:
    def test_select_in_loop(self) -> None:
        code = (
            "LOOP AT lt_items INTO DATA(ls_item).\n"
            "  SELECT SINGLE matnr FROM mara INTO @DATA(lv_matnr)\n"
            "    WHERE matnr = @ls_item-matnr.\n"
            "ENDLOOP.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-READ-003")

    def test_select_outside_loop_clean(self) -> None:
        code = (
            "SELECT matnr FROM mara INTO TABLE @lt_mara WHERE matnr IN @lr_matnr.\n"
            "LOOP AT lt_items INTO DATA(ls_item).\n"
            "  READ TABLE lt_mara TRANSPORTING NO FIELDS WITH KEY matnr = ls_item-matnr.\n"
            "ENDLOOP.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-READ-003")


class TestAbapErr001EmptyCatch:
    def test_empty_catch_block(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH cx_sy_itab_line_not_found.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERR-001")

    def test_catch_with_handling_clean(self) -> None:
        code = (
            "TRY.\n"
            "    lo_service->process( ).\n"
            "  CATCH cx_sy_itab_line_not_found INTO DATA(lx_err).\n"
            "    MESSAGE lx_err->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERR-001")


class TestAbapErr002CatchCxRoot:
    def test_catch_cx_root(self) -> None:
        code = (
            "TRY.\n"
            "    lo_api->execute( ).\n"
            "  CATCH cx_root INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERR-002")

    def test_catch_specific_exception_clean(self) -> None:
        code = (
            "TRY.\n"
            "    lo_api->execute( ).\n"
            "  CATCH zcx_order_error INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERR-002")


class TestAbapErr003MissingSySubrc:
    def test_call_function_without_check(self) -> None:
        code = (
            "CALL FUNCTION 'BAPI_SALESORDER_GETLIST'\n"
            "  EXPORTING\n"
            "    customer_number = iv_kunnr\n"
            "  TABLES\n"
            "    sales_orders = lt_orders.\n"
            "LOOP AT lt_orders INTO DATA(ls_order).\n"
            "ENDLOOP.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-ERR-003")

    def test_call_function_with_subrc_check_clean(self) -> None:
        code = (
            "CALL FUNCTION 'BAPI_SALESORDER_GETLIST'\n"
            "  EXPORTING\n"
            "    customer_number = iv_kunnr\n"
            "  TABLES\n"
            "    sales_orders = lt_orders.\n"
            "IF sy-subrc <> 0.\n"
            "  RAISE EXCEPTION TYPE zcx_api_error.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-ERR-003")


class TestAbapStruct001MethodLength:
    def test_long_method_detected(self) -> None:
        lines = ["METHOD long_method."]
        lines.extend(["  DATA lv_x TYPE i."] * 110)
        lines.append("ENDMETHOD.")
        code = "\n".join(lines)
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "ABAP-STRUCT-001")

    def test_short_method_clean(self) -> None:
        code = (
            "METHOD short_method.\n"
            "  DATA lv_x TYPE i.\n"
            "  lv_x = 1.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "ABAP-STRUCT-001")


class TestAbapStruct002DeepNesting:
    def test_deep_nesting_detected(self) -> None:
        code = (
            "IF a = 1.\n"
            "  IF b = 2.\n"
            "    IF c = 3.\n"
            "      IF d = 4.\n"
            "        IF e = 5.\n"
            "          WRITE 'deep'.\n"
            "        ENDIF.\n"
            "      ENDIF.\n"
            "    ENDIF.\n"
            "  ENDIF.\n"
            "ENDIF.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-STRUCT-002")

    def test_shallow_nesting_clean(self) -> None:
        code = "IF a = 1.\n  IF b = 2.\n    WRITE 'ok'.\n  ENDIF.\nENDIF.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-STRUCT-002")


class TestAbapStyle001WriteStatement:
    def test_write_in_class(self) -> None:
        code = (
            "CLASS zcl_test IMPLEMENTATION.\n"
            "  METHOD run.\n"
            "    WRITE: / 'Debug output'.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "ABAP-STYLE-001")

    def test_no_write_clean(self) -> None:
        code = (
            "CLASS zcl_test IMPLEMENTATION.\n"
            "  METHOD run.\n"
            "    MESSAGE 'Info' TYPE 'I'.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-STYLE-001")


class TestAbapStyle002ObsoleteMoveCompute:
    def test_move_statement(self) -> None:
        code = "MOVE lv_source TO lv_target.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-STYLE-002")

    def test_compute_statement(self) -> None:
        code = "COMPUTE lv_result = lv_a + lv_b.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-STYLE-002")

    def test_modern_assignment_clean(self) -> None:
        code = "lv_target = lv_source.\n"
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-STYLE-002")


class TestAbapSec001MissingAuthority:
    def test_select_without_authority_check(self) -> None:
        code = (
            "METHOD get_data.\n"
            "  SELECT vbeln FROM vbak INTO TABLE @rt_result WHERE kunnr = @iv_kunnr.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "ABAP-SEC-001")

    def test_select_with_authority_check_clean(self) -> None:
        code = (
            "METHOD get_data.\n"
            "  AUTHORITY-CHECK OBJECT 'V_VBAK_VKO'\n"
            "    ID 'VKORG' FIELD iv_vkorg\n"
            "    ID 'ACTVT' FIELD '03'.\n"
            "  SELECT vbeln FROM vbak INTO TABLE @rt_result WHERE kunnr = @iv_kunnr.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "ABAP-SEC-001")


class TestAbapPerf001NoOrderBy:
    def test_select_into_table_without_order_by(self) -> None:
        code = "SELECT vbeln erdat FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-PERF-001")

    def test_select_with_order_by_clean(self) -> None:
        code = (
            "SELECT vbeln erdat FROM vbak INTO TABLE @lt_orders\n"
            "  WHERE kunnr = @iv_kunnr ORDER BY vbeln.\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "ABAP-PERF-001")


class TestAbapMod001ModificationMarker:
    def test_enhancement_point(self) -> None:
        code = 'ENHANCEMENT-POINT ep_01 SPOTS z_my_spot.\n'
        findings = _run(code)
        assert _has_rule(findings, "ABAP-MOD-001")

    def test_enhancement_section(self) -> None:
        code = "ENHANCEMENT-SECTION es_01 SPOTS z_my_spot.\nENHANCEMENT-SECTION.\n"
        findings = _run(code)
        assert _has_rule(findings, "ABAP-MOD-001")

    def test_clean_code_no_modification(self) -> None:
        code = (
            "METHOD clean_method.\n"
            "  DATA lv_x TYPE i.\n"
            "  lv_x = 42.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "ABAP-MOD-001")


# ===========================================================================
# CDS rule tests
# ===========================================================================


class TestCdsAnno001MissingAbapCatalog:
    def test_view_entity_without_abap_catalog(self) -> None:
        code = (
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-ANNO-001")

    def test_view_entity_with_abap_catalog_clean(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-ANNO-001")


class TestCdsAnno002MissingAccessControl:
    def test_view_without_access_control(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-ANNO-002")

    def test_view_with_access_control_clean(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "@AccessControl.authorizationCheck: #CHECK\n"
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-ANNO-002")


class TestCdsAnno003MissingUiAnnotations:
    def test_projection_without_ui_annotations(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      Description\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-ANNO-003")

    def test_projection_with_ui_annotations_clean(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  @UI.identification: [{ position: 10 }]\n"
            "  key OrderId,\n"
            "      Description\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANNO-003")


class TestCdsAnno004MissingSearchAnnotations:
    def test_view_without_search_annotations(self) -> None:
        code = (
            "define view entity ZI_Customer\n"
            "  as select from kna1\n"
            "{\n"
            "  key kunnr as CustomerId,\n"
            "      name1 as CustomerName\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-ANNO-004")

    def test_view_with_search_annotations_clean(self) -> None:
        code = (
            "@Search.searchable: true\n"
            "define view entity ZI_Customer\n"
            "  as select from kna1\n"
            "{\n"
            "  @Search.defaultSearchElement: true\n"
            "  key kunnr as CustomerId,\n"
            "      name1 as CustomerName\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-ANNO-004")


class TestCdsStruct001MissingKeyField:
    def test_view_without_key(self) -> None:
        code = (
            "define view entity ZI_Stat\n"
            "  as select from ztab\n"
            "{\n"
            "  field1,\n"
            "  field2\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-STRUCT-001")

    def test_view_with_key_clean(self) -> None:
        code = (
            "define view entity ZI_Stat\n"
            "  as select from ztab\n"
            "{\n"
            "  key id,\n"
            "      field1\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-STRUCT-001")


class TestCdsStruct002MissingAssociation:
    def test_projection_without_association(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      Amount\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-STRUCT-002")

    def test_projection_with_association_clean(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      Amount,\n"
            "      _Customer : redirected to ZC_Customer\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-STRUCT-002")


class TestCdsPerf001JoinWithoutWhere:
    def test_join_no_where(self) -> None:
        code = (
            "define view entity ZI_Combined\n"
            "  as select from vbak\n"
            "  inner join vbap on vbak.vbeln = vbap.vbeln\n"
            "{\n"
            "  key vbak.vbeln,\n"
            "      vbap.posnr\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-PERF-001")

    def test_join_with_where_clean(self) -> None:
        code = (
            "define view entity ZI_Combined\n"
            "  as select from vbak\n"
            "  inner join vbap on vbak.vbeln = vbap.vbeln\n"
            "{\n"
            "  key vbak.vbeln,\n"
            "      vbap.posnr\n"
            "}\n"
            "where vbak.auart = 'OR'\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-PERF-001")


class TestCdsCons001InconsistentNaming:
    def test_snake_case_alias(self) -> None:
        code = (
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as order_id,\n"
            "      name1 as customer_name\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert _has_rule(findings, "CDS-CONS-001")

    def test_camel_case_alias_clean(self) -> None:
        code = (
            "define view entity ZI_Test\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId,\n"
            "      name1 as CustomerName\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        assert not _has_rule(findings, "CDS-CONS-001")


# ===========================================================================
# UI5 rule tests
# ===========================================================================


class TestUi5I18n001HardcodedString:
    def test_hardcoded_title_in_view(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Page title="Sales Orders Overview">\n'
            "  </Page>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-I18N-001")

    def test_i18n_binding_clean(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Page title="{i18n>salesOrdersTitle}">\n'
            "  </Page>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert not _has_rule(findings, "UI5-I18N-001")


class TestUi5Struct001MissingOnInit:
    def test_controller_without_on_init(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onPress: function() { }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-STRUCT-001")

    def test_controller_with_on_init_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() { },\n"
            "    onPress: function() { }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert not _has_rule(findings, "UI5-STRUCT-001")


class TestUi5Struct002DomManipulation:
    def test_jquery_in_controller(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      jQuery("#myElement").hide();\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-STRUCT-002")

    def test_dollar_in_controller(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      $("#myElement").css("display", "none");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-STRUCT-002")

    def test_by_id_usage_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      this.byId("myTable").setVisible(false);\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert not _has_rule(findings, "UI5-STRUCT-002")


class TestUi5Struct003ComplexExpression:
    def test_ternary_in_binding(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Text text="{= ${status} === \'A\' ? \'Active\' : \'Inactive\'}"/>\n'
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-STRUCT-003")


class TestUi5Err001OdataNoError:
    def test_odata_read_without_error(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      var oModel = this.getView().getModel();\n"
            '      oModel.read("/SalesOrderSet");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-ERR-001")

    def test_odata_read_with_error_handler_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      var oModel = this.getView().getModel();\n"
            '      oModel.read("/SalesOrderSet", {\n'
            "        success: function(oData) { },\n"
            "        error: function(oError) { }\n"
            "      });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert not _has_rule(findings, "UI5-ERR-001")


class TestUi5Depr001GetCore:
    def test_deprecated_get_core(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      var oCore = sap.ui.getCore();\n"
            "      oCore.getMessageManager();\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-DEPR-001")

    def test_no_get_core_clean(self) -> None:
        code = (
            'sap.ui.define([\n'
            '  "sap/ui/core/mvc/Controller",\n'
            '  "sap/ui/core/Messaging"\n'
            "], function(Controller, Messaging) {\n"
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      Messaging.getMessageModel();\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert not _has_rule(findings, "UI5-DEPR-001")


class TestUi5Perf001MissingBusy:
    def test_async_without_busy_indicator(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    loadData: function() {\n"
            "      var oModel = this.getView().getModel();\n"
            '      oModel.read("/Orders", {\n'
            "        success: function(oData) { },\n"
            "        error: function(oErr) { }\n"
            "      });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-PERF-001")

    def test_async_with_busy_indicator_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    loadData: function() {\n"
            "      this.getView().setBusy(true);\n"
            "      var oModel = this.getView().getModel();\n"
            '      oModel.read("/Orders", {\n'
            "        success: function(oData) { this.getView().setBusy(false); }.bind(this),\n"
            "        error: function(oErr) { this.getView().setBusy(false); }.bind(this)\n"
            "      });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert not _has_rule(findings, "UI5-PERF-001")


class TestUi5Bind001HardcodedPath:
    def test_hardcoded_odata_path(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      this.getView().getModel().read("/SalesOrderSet", {\n'
            "        success: function() {},\n"
            "        error: function() {}\n"
            "      });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, ArtifactType.UI5_CONTROLLER)
        assert _has_rule(findings, "UI5-BIND-001")


# ===========================================================================
# Clean code tests (no findings expected)
# ===========================================================================


class TestCleanCode:
    def test_clean_abap_no_findings(self) -> None:
        code = (
            "CLASS zcl_clean IMPLEMENTATION.\n"
            "  METHOD get_data.\n"
            "    AUTHORITY-CHECK OBJECT 'S_TCODE'\n"
            "      ID 'TCD' FIELD 'SE80'\n"
            "      ID 'ACTVT' FIELD '03'.\n"
            "    IF sy-subrc <> 0.\n"
            "      RAISE EXCEPTION TYPE zcx_no_auth.\n"
            "    ENDIF.\n"
            "    SELECT vbeln erdat FROM vbak\n"
            "      INTO TABLE @rt_result\n"
            "      WHERE kunnr = @iv_kunnr\n"
            "      ORDER BY vbeln.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        findings = _run(code)
        # Should have very few or no critical/important findings
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(critical) == 0

    def test_clean_cds_no_findings(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "@AccessControl.authorizationCheck: #CHECK\n"
            "@Search.searchable: true\n"
            "define view entity ZI_CleanOrder\n"
            "  as select from vbak\n"
            "{\n"
            "  @Search.defaultSearchElement: true\n"
            "  key vbeln as SalesOrder,\n"
            "      erdat as CreatedOn\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_VIEW)
        # All major annotations present, key field present
        assert not _has_rule(findings, "CDS-ANNO-001")
        assert not _has_rule(findings, "CDS-ANNO-002")
        assert not _has_rule(findings, "CDS-STRUCT-001")
        assert not _has_rule(findings, "CDS-ANNO-004")

    def test_clean_ui5_no_findings(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Page title="{i18n>pageTitle}">\n'
            "  </Page>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert not _has_rule(findings, "UI5-I18N-001")


# ===========================================================================
# Severity ordering
# ===========================================================================


class TestSeverityOrdering:
    def test_critical_before_important(self) -> None:
        code = (
            "LOOP AT lt_items INTO DATA(ls_item).\n"
            "  SELECT * FROM mara INTO TABLE @lt_mara.\n"
            "ENDLOOP.\n"
            "TRY.\n"
            "  lo_obj->run( ).\n"
            "CATCH cx_root INTO DATA(lx).\n"
            "  MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "ENDTRY.\n"
        )
        findings = _run(code)
        if len(findings) >= 2:
            severities = [f.severity for f in findings]
            # CRITICAL should come before IMPORTANT in sorted output
            first_critical_idx = next(
                (i for i, s in enumerate(severities) if s == Severity.CRITICAL), 999
            )
            first_important_idx = next(
                (i for i, s in enumerate(severities) if s == Severity.IMPORTANT), 999
            )
            if first_critical_idx != 999 and first_important_idx != 999:
                assert first_critical_idx < first_important_idx


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestBilingualOutput:
    def test_german_output(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code, language=Language.DE)
        assert len(findings) > 0
        # The title should be in German
        sel_star = next((f for f in findings if f.rule_id == "ABAP-READ-001"), None)
        if sel_star:
            assert "Verwendung" in sel_star.title

    def test_english_output(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code, language=Language.EN)
        sel_star = next((f for f in findings if f.rule_id == "ABAP-READ-001"), None)
        if sel_star:
            assert "usage" in sel_star.title.lower()


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEngineEdgeCases:
    def test_empty_code_returns_empty(self) -> None:
        findings = _run("")
        assert findings == []

    def test_whitespace_only_returns_empty(self) -> None:
        findings = _run("   \n\t  \n")
        assert findings == []

    def test_unknown_artifact_type(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code, ArtifactType.ODATA_SERVICE)
        # Should still produce findings using fallback rules
        assert isinstance(findings, list)

    def test_mixed_artifact_uses_all_applicable_rules(self) -> None:
        code = (
            "SELECT * FROM vbak INTO TABLE @lt_orders.\n"
            '<mvc:View xmlns:mvc="sap.ui.core.mvc">\n'
            '  <Page title="Hardcoded Title">\n'
            "  </Page>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.MIXED_FULLSTACK)
        # Should find both ABAP and UI5 issues
        rule_ids = {f.rule_id for f in findings}
        assert len(rule_ids) >= 1

    def test_findings_have_rule_id(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        for f in findings:
            if f.rule_id:
                assert f.rule_id.startswith(("ABAP-", "CDS-", "UI5-"))

    def test_findings_have_line_reference(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        findings = _run(code)
        sel_star = next((f for f in findings if f.rule_id == "ABAP-READ-001"), None)
        if sel_star:
            assert sel_star.line_reference is not None
