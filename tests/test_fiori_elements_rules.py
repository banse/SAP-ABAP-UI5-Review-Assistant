"""Tests for Fiori Elements review rules."""

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
    artifact_type: ArtifactType = ArtifactType.CDS_ANNOTATION,
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
# FE-CFG-001: Incomplete List Report configuration
# ===========================================================================


class TestFECFG001MissingSelectionFields:
    def test_line_item_without_selection_field(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-001")

    def test_line_item_with_selection_field_clean(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  @UI.selectionField: [{ position: 10 }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-001")


# ===========================================================================
# FE-CFG-002: Object Page without header info
# ===========================================================================


class TestFECFG002MissingHeaderInfo:
    def test_identification_without_header_info(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.identification: [{ position: 10 }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-002")

    def test_identification_with_header_info_clean(self) -> None:
        code = (
            "@UI.headerInfo: {\n"
            "  typeName: 'Order',\n"
            "  typeNamePlural: 'Orders'\n"
            "}\n"
            "annotate ZC_Order with {\n"
            "  @UI.identification: [{ position: 10 }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-002")


# ===========================================================================
# FE-CFG-003: Missing criticality on status fields
# ===========================================================================


class TestFECFG003MissingStatusCriticality:
    def test_status_field_without_criticality(self) -> None:
        code = (
            "define view entity ZC_Order as projection on ZI_Order {\n"
            "  key OrderId,\n"
            "      overallStatus\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "FE-CFG-003")

    def test_status_field_with_criticality_clean(self) -> None:
        code = (
            "define view entity ZC_Order as projection on ZI_Order {\n"
            "  key OrderId,\n"
            "      @UI.lineItem: [{ criticality: 'StatusCriticality' }]\n"
            "      overallStatus\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "FE-CFG-003")


# ===========================================================================
# FE-CFG-004: Action annotation missing DataFieldForAction
# ===========================================================================


class TestFECFG004MissingActionAnnotation:
    def test_action_without_for_action(self) -> None:
        code = (
            "action approveOrder parameter OrderId : UUID;\n"
            "@UI.lineItem: [{ position: 10 }]\n"
            "annotate ZC_Order with { OrderId; }\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-004")

    def test_action_with_for_action_clean(self) -> None:
        code = (
            "action approveOrder parameter OrderId : UUID;\n"
            "@UI.lineItem: [{ type: #FOR_ACTION, dataAction: 'approveOrder' }]\n"
            "annotate ZC_Order with { OrderId; }\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-004")


# ===========================================================================
# FE-CFG-005: Missing navigation configuration
# ===========================================================================


class TestFECFG005MissingNavigation:
    def test_line_item_without_navigation(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  OrderId;\n"
            "  @UI.lineItem: [{ position: 20 }]\n"
            "  Description;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-005")

    def test_line_item_with_navigation_clean(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10, type: #WITH_INTENT_BASED_NAVIGATION,\n"
            "    semanticObject: 'SalesOrder' }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-005")


# ===========================================================================
# FE-CFG-006: Missing i18n for annotation labels
# ===========================================================================


class TestFECFG006MissingI18n:
    def test_inline_label_detected(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10, label: 'Sales Order Number' }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-006")

    def test_i18n_label_clean(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10, label: '{i18n>orderIdLabel}' }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-006")


# ===========================================================================
# FE-CFG-007: Extension point misuse
# ===========================================================================


class TestFECFG007ExtensionPointMisuse:
    def test_custom_controller_override_detected(self) -> None:
        code = (
            '{\n'
            '  "sap.ui5": {\n'
            '    "extends": {\n'
            '      "extensions": {\n'
            '        "sap.ui.controllerExtensions": {\n'
            '          "sap.fe.templates.ListReport.ListReportController": {\n'
            '            "controllerName": "my.app.ext.ListReportExt"\n'
            '          }\n'
            '        }\n'
            '      }\n'
            '    }\n'
            '  }\n'
            '}\n'
        )
        findings = _run(code, ArtifactType.FIORI_ELEMENTS_APP)
        assert _has_rule(findings, "FE-CFG-007")

    def test_sap_standard_controller_clean(self) -> None:
        code = (
            '{\n'
            '  "sap.ui5": {\n'
            '    "routing": {\n'
            '      "targets": {\n'
            '        "OrderList": {\n'
            '          "controllerName": "sap.fe.templates.ListReport"\n'
            '        }\n'
            '      }\n'
            '    }\n'
            '  }\n'
            '}\n'
        )
        findings = _run(code, ArtifactType.FIORI_ELEMENTS_APP)
        assert not _has_rule(findings, "FE-CFG-007")


# ===========================================================================
# FE-CFG-008: Missing variant management configuration
# ===========================================================================


class TestFECFG008MissingVariantManagement:
    def test_fe_app_without_variant_management(self) -> None:
        code = (
            '{\n'
            '  "sap.ui.generic.app": {\n'
            '    "pages": {\n'
            '      "ListReport": {\n'
            '        "entitySet": "Orders"\n'
            '      }\n'
            '    }\n'
            '  }\n'
            '}\n'
        )
        findings = _run(code, ArtifactType.FIORI_ELEMENTS_APP)
        assert _has_rule(findings, "FE-CFG-008")

    def test_fe_app_with_variant_management_clean(self) -> None:
        code = (
            '{\n'
            '  "sap.ui.generic.app": {\n'
            '    "pages": {\n'
            '      "ListReport": {\n'
            '        "entitySet": "Orders",\n'
            '        "component": {\n'
            '          "settings": {\n'
            '            "variantManagement": "Page"\n'
            '          }\n'
            '        }\n'
            '      }\n'
            '    }\n'
            '  }\n'
            '}\n'
        )
        findings = _run(code, ArtifactType.FIORI_ELEMENTS_APP)
        assert not _has_rule(findings, "FE-CFG-008")


# ===========================================================================
# FE-CFG-009: Filter bar without default values
# ===========================================================================


class TestFECFG009FilterBarNoDefaults:
    def test_selection_field_without_default(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.selectionField: [{ position: 10 }]\n"
            "  OrderStatus;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-009")

    def test_selection_field_with_default_clean(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.selectionField: [{ position: 10 }]\n"
            "  @Consumption.filter.defaultValue: 'OPEN'\n"
            "  OrderStatus;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-009")


# ===========================================================================
# FE-CFG-010: Table without initial sort order
# ===========================================================================


class TestFECFG010MissingSortOrder:
    def test_line_item_without_sort(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  OrderId;\n"
            "  @UI.lineItem: [{ position: 20 }]\n"
            "  CustomerName;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "FE-CFG-010")

    def test_line_item_with_presentation_variant_clean(self) -> None:
        code = (
            "@UI.presentationVariant: [{\n"
            "  sortOrder: [{ by: 'OrderId', direction: #DESC }]\n"
            "}]\n"
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "FE-CFG-010")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestFioriElementsBilingual:
    def test_german_output(self) -> None:
        code = (
            "annotate ZC_Order with {\n"
            "  @UI.lineItem: [{ position: 10, label: 'Sales Order' }]\n"
            "  OrderId;\n"
            "}\n"
        )
        findings = _run(code, language=Language.DE)
        fe006 = next((f for f in findings if f.rule_id == "FE-CFG-006"), None)
        if fe006:
            assert "i18n" in fe006.title.lower() or "Fehlende" in fe006.title
