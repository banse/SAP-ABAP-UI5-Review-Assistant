"""Tests for CDS annotation review rules."""

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
    artifact_type: ArtifactType = ArtifactType.CDS_VIEW,
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
# CDS-ANN-001: Annotation overkill on interface view
# ===========================================================================


class TestCdsAnn001AnnotationOverkill:
    def test_ui_annotation_on_interface_view_detected(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-001")

    def test_interface_view_without_ui_clean(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-001")

    def test_consumption_view_with_ui_clean(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANN-001")


# ===========================================================================
# CDS-ANN-002: Missing @Semantics for currency/quantity fields
# ===========================================================================


class TestCdsAnn002MissingSemantics:
    def test_amount_field_without_semantics(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId,\n"
            "      betrag as Amount,\n"
            "      waerk as Currency\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-002")

    def test_amount_field_with_semantics_clean(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId,\n"
            "      @Semantics.amount.currencyCode: 'Currency'\n"
            "      betrag as Amount,\n"
            "      @Semantics.currencyCode: true\n"
            "      waerk as Currency\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-002")


# ===========================================================================
# CDS-ANN-003: Missing @ObjectModel annotations
# ===========================================================================


class TestCdsAnn003MissingObjectModel:
    def test_view_without_object_model(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-003")

    def test_view_with_object_model_clean(self) -> None:
        code = (
            "@ObjectModel.modelCategory: #BUSINESS_OBJECT\n"
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-003")


# ===========================================================================
# CDS-ANN-004: Value help annotation incomplete
# ===========================================================================


class TestCdsAnn004MissingValueHelp:
    def test_id_field_without_value_help(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      CustomerId,\n"
            "      StatusCode\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-ANN-004")

    def test_id_field_with_value_help_clean(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      @Consumption.valueHelpDefinition: [{ entity: { name: 'ZI_Customer' } }]\n"
            "      CustomerId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANN-004")


# ===========================================================================
# CDS-ANN-005: CDS view layering violation
# ===========================================================================


class TestCdsAnn005LayeringViolation:
    def test_interface_view_referencing_consumption_view(self) -> None:
        code = (
            "define view entity ZI_OrderAnalytics\n"
            "  as select from ZC_Order\n"
            "{\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-005")

    def test_interface_view_referencing_base_table_clean(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-005")


# ===========================================================================
# CDS-ANN-006: Missing @EndUserText for fields without alias
# ===========================================================================


class TestCdsAnn006MissingEndUserText:
    def test_technical_fields_without_end_user_text(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from vbak\n"
            "{\n"
            "  key vbeln,\n"
            "      erdat,\n"
            "      kunnr\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-006")

    def test_fields_with_end_user_text_clean(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from vbak\n"
            "{\n"
            "  @EndUserText.label: 'Sales Order'\n"
            "  key vbeln,\n"
            "      erdat as CreatedOn\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-006")


# ===========================================================================
# CDS-ANN-007: Missing @Metadata.allowExtensions
# ===========================================================================


class TestCdsAnn007MissingMetadataAllowExtensions:
    def test_projection_without_metadata_allow_extensions(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-ANN-007")

    def test_projection_with_metadata_allow_extensions_clean(self) -> None:
        code = (
            "@Metadata.allowExtensions: true\n"
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANN-007")


# ===========================================================================
# CDS-ANN-008: Composition without to-parent association
# ===========================================================================


class TestCdsAnn008CompositionWithoutParent:
    def test_composition_without_parent_association(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "  composition [0..*] of ZI_OrderItem as _Items\n"
            "{\n"
            "  key id as OrderId,\n"
            "      _Items\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "CDS-ANN-008")

    def test_composition_with_parent_association_clean(self) -> None:
        code = (
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "  composition [0..*] of ZI_OrderItem as _Items\n"
            "  association to parent ZI_Root as _Root on $projection.RootId = _Root.Id\n"
            "{\n"
            "  key id as OrderId,\n"
            "      _Items\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "CDS-ANN-008")


# ===========================================================================
# CDS-ANN-009: Missing @Consumption.filter annotation
# ===========================================================================


class TestCdsAnn009MissingConsumptionFilter:
    def test_projection_without_consumption_filter(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  key OrderId,\n"
            "      CustomerName\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-ANN-009")

    def test_projection_with_consumption_filter_clean(self) -> None:
        code = (
            "define root view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  @Consumption.filter: { selectionType: #SINGLE }\n"
            "  key OrderId,\n"
            "      CustomerName\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANN-009")


# ===========================================================================
# CDS-ANN-010: Redundant annotation override
# ===========================================================================


class TestCdsAnn010RedundantAnnotation:
    def test_duplicate_annotation_detected(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  @UI.lineItem: [{ position: 20 }]\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert _has_rule(findings, "CDS-ANN-010")

    def test_unique_annotations_clean(self) -> None:
        code = (
            "@UI.headerInfo: { typeName: 'Order' }\n"
            "define view entity ZC_Order\n"
            "  as projection on ZI_Order\n"
            "{\n"
            "  @UI.lineItem: [{ position: 10 }]\n"
            "  key OrderId\n"
            "}\n"
        )
        findings = _run(code, ArtifactType.CDS_PROJECTION)
        assert not _has_rule(findings, "CDS-ANN-010")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestCdsAnnotationBilingual:
    def test_german_output(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code, language=Language.DE)
        ann001 = next((f for f in findings if f.rule_id == "CDS-ANN-001"), None)
        if ann001:
            assert "Ueberladung" in ann001.title or "Interface" in ann001.title

    def test_english_output(self) -> None:
        code = (
            "@UI.lineItem: [{ position: 10 }]\n"
            "define view entity ZI_Order\n"
            "  as select from ztab\n"
            "{\n"
            "  key id as OrderId\n"
            "}\n"
        )
        findings = _run(code, language=Language.EN)
        ann001 = next((f for f in findings if f.rule_id == "CDS-ANN-001"), None)
        if ann001:
            assert "overkill" in ann001.title.lower() or "interface" in ann001.title.lower()


# ===========================================================================
# Edge cases
# ===========================================================================


class TestCdsAnnotationEdgeCases:
    def test_empty_code(self) -> None:
        findings = _run("")
        assert findings == []

    def test_non_cds_code_no_false_positives(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders.\n"
        findings = _run(code, ArtifactType.CDS_VIEW)
        # Should not fire CDS-ANN rules on ABAP code
        ann_rules = [f for f in findings if f.rule_id.startswith("CDS-ANN-")]
        assert len(ann_rules) == 0
