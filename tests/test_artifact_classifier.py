"""Tests for the artifact type classification engine."""

from __future__ import annotations

import pytest

from app.engines.artifact_classifier import classify_artifact
from app.models.enums import ArtifactType


# ---------------------------------------------------------------------------
# ABAP artifact detection
# ---------------------------------------------------------------------------


class TestAbapClassification:
    def test_abap_class_definition(self) -> None:
        code = (
            "CLASS zcl_order DEFINITION PUBLIC FINAL CREATE PUBLIC.\n"
            "  PUBLIC SECTION.\n"
            "    METHODS get_orders RETURNING VALUE(rt_result) TYPE ztt_orders.\n"
            "ENDCLASS.\n"
        )
        assert classify_artifact(code) == ArtifactType.ABAP_CLASS

    def test_abap_class_implementation(self) -> None:
        code = (
            "CLASS zcl_order IMPLEMENTATION.\n"
            "  METHOD get_orders.\n"
            "    SELECT vbeln FROM vbak INTO TABLE @rt_result.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        assert classify_artifact(code) == ArtifactType.ABAP_CLASS

    def test_abap_method_only(self) -> None:
        code = (
            "METHOD get_orders.\n"
            "  SELECT vbeln FROM vbak INTO TABLE @rt_result.\n"
            "ENDMETHOD.\n"
        )
        assert classify_artifact(code) == ArtifactType.ABAP_METHOD

    def test_abap_report(self) -> None:
        code = (
            "REPORT z_sales_report.\n"
            "DATA: lt_vbak TYPE TABLE OF vbak.\n"
            "SELECT * FROM vbak INTO TABLE lt_vbak.\n"
            "LOOP AT lt_vbak INTO DATA(ls_vbak).\n"
            "  WRITE: / ls_vbak-vbeln.\n"
            "ENDLOOP.\n"
        )
        assert classify_artifact(code) == ArtifactType.ABAP_REPORT


# ---------------------------------------------------------------------------
# CDS artifact detection
# ---------------------------------------------------------------------------


class TestCdsClassification:
    def test_cds_view_entity(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "@AccessControl.authorizationCheck: #CHECK\n"
            "define view entity ZI_SalesOrder\n"
            "  as select from vbak\n"
            "{\n"
            "  key vbeln as SalesOrder,\n"
            "      erdat as CreatedOn\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.CDS_VIEW

    def test_cds_legacy_view(self) -> None:
        code = (
            "@AbapCatalog.sqlViewName: 'ZVSOHDR'\n"
            "define view ZC_SalesOrderHeader\n"
            "  as select from vbak\n"
            "{\n"
            "  key vbeln as SalesOrder\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.CDS_VIEW

    def test_cds_projection(self) -> None:
        code = (
            "define root view entity ZC_SalesOrder\n"
            "  as projection on ZI_SalesOrder\n"
            "{\n"
            "  key SalesOrder,\n"
            "      CreatedOn\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.CDS_PROJECTION

    def test_cds_annotation_extension(self) -> None:
        code = (
            "annotate view ZI_SalesOrder with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  SalesOrder;\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.CDS_ANNOTATION


# ---------------------------------------------------------------------------
# RAP artifact detection
# ---------------------------------------------------------------------------


class TestRapClassification:
    def test_behavior_definition_managed(self) -> None:
        code = (
            "managed implementation in class zcl_bp_salesorder unique;\n"
            "strict;\n"
            "define behavior for ZI_SalesOrder alias SalesOrder\n"
            "persistent table ztab_so\n"
            "{\n"
            "  create;\n"
            "  update;\n"
            "  delete;\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.BEHAVIOR_DEFINITION

    def test_behavior_definition_unmanaged(self) -> None:
        code = (
            "unmanaged implementation in class zcl_bp_legacy unique;\n"
            "define behavior for ZI_Legacy alias Legacy\n"
            "{\n"
            "  create;\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.BEHAVIOR_DEFINITION

    def test_behavior_implementation(self) -> None:
        code = (
            "METHOD create_order FOR MODIFY\n"
            "  IMPORTING entities FOR CREATE SalesOrder.\n"
            "  \" business logic here\n"
            "ENDMETHOD.\n"
        )
        assert classify_artifact(code) == ArtifactType.BEHAVIOR_IMPLEMENTATION

    def test_service_definition(self) -> None:
        code = (
            "define service ZSB_SalesOrder {\n"
            "  expose ZC_SalesOrder as SalesOrder;\n"
            "  expose ZC_SalesOrderItem as SalesOrderItem;\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.SERVICE_DEFINITION

    def test_service_binding(self) -> None:
        code = "bind service ZSB_SalesOrder\n  provider OData V4;\n"
        assert classify_artifact(code) == ArtifactType.SERVICE_BINDING


# ---------------------------------------------------------------------------
# UI5 artifact detection
# ---------------------------------------------------------------------------


class TestUi5Classification:
    def test_ui5_controller(self) -> None:
        code = (
            'sap.ui.define([\n'
            '  "sap/ui/core/mvc/Controller"\n'
            '], function(Controller) {\n'
            '  "use strict";\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      this.getView().setModel(new JSONModel(), "view");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        assert classify_artifact(code) == ArtifactType.UI5_CONTROLLER

    def test_ui5_controller_legacy(self) -> None:
        code = (
            'sap.ui.controller("my.app.Main", {\n'
            "  onInit: function() {}\n"
            "});\n"
        )
        assert classify_artifact(code) == ArtifactType.UI5_CONTROLLER

    def test_ui5_xml_view(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc"\n'
            '  xmlns="sap.m"\n'
            '  controllerName="my.app.Main">\n'
            '  <Page title="{i18n>title}">\n'
            "    <content>\n"
            '      <List items="{/Orders}"/>\n'
            "    </content>\n"
            "  </Page>\n"
            "</mvc:View>\n"
        )
        assert classify_artifact(code) == ArtifactType.UI5_VIEW

    def test_ui5_fragment(self) -> None:
        code = (
            '<core:FragmentDefinition\n'
            '  xmlns="sap.m"\n'
            '  xmlns:core="sap.ui.core">\n'
            '  <Dialog title="Confirm">\n'
            '    <Button text="OK" press=".onConfirm"/>\n'
            "  </Dialog>\n"
            "</core:FragmentDefinition>\n"
        )
        assert classify_artifact(code) == ArtifactType.UI5_FRAGMENT


# ---------------------------------------------------------------------------
# Mixed fullstack detection
# ---------------------------------------------------------------------------


class TestMixedDetection:
    def test_abap_and_cds_mixed(self) -> None:
        code = (
            "CLASS zcl_test DEFINITION PUBLIC.\n"
            "ENDCLASS.\n"
            "---\n"
            "define view entity ZI_Test as select from ztab {\n"
            "  key id\n"
            "}\n"
        )
        assert classify_artifact(code) == ArtifactType.MIXED_FULLSTACK

    def test_abap_and_ui5_mixed(self) -> None:
        code = (
            "CLASS zcl_test DEFINITION PUBLIC.\n"
            "ENDCLASS.\n"
            '<mvc:View xmlns:mvc="sap.ui.core.mvc">\n'
            '  <Page title="Test"/>\n'
            "</mvc:View>\n"
        )
        assert classify_artifact(code) == ArtifactType.MIXED_FULLSTACK

    def test_cds_and_ui5_mixed(self) -> None:
        code = (
            "define view entity ZI_Test as select from ztab { key id }\n"
            '<mvc:View xmlns:mvc="sap.ui.core.mvc">\n'
            '  <Page title="Test"/>\n'
            "</mvc:View>\n"
        )
        assert classify_artifact(code) == ArtifactType.MIXED_FULLSTACK


# ---------------------------------------------------------------------------
# Provided type override
# ---------------------------------------------------------------------------


class TestProvidedTypeOverride:
    def test_override_classification(self) -> None:
        code = "define view entity ZI_Test as select from ztab { key id }\n"
        assert classify_artifact(code, ArtifactType.ABAP_REPORT) == ArtifactType.ABAP_REPORT

    def test_override_with_none(self) -> None:
        code = "CLASS zcl_test DEFINITION PUBLIC. ENDCLASS.\n"
        assert classify_artifact(code, None) == ArtifactType.ABAP_CLASS


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string(self) -> None:
        result = classify_artifact("")
        assert result == ArtifactType.ABAP_CLASS  # safe default

    def test_whitespace_only(self) -> None:
        result = classify_artifact("   \n\t  ")
        assert result == ArtifactType.ABAP_CLASS

    def test_unrecognized_code(self) -> None:
        result = classify_artifact("print('hello world')\n")
        assert result == ArtifactType.ABAP_CLASS  # safe default
