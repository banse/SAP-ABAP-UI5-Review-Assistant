"""Tests for Service Definition and OData Binding review rules (SRV-EXP-*)."""

from __future__ import annotations

import pytest

from app.engines.findings_engine import run_findings_engine
from app.models.enums import ArtifactType, Language, ReviewContext, ReviewType
from app.models.schemas import Finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(
    code: str,
    artifact_type: ArtifactType = ArtifactType.SERVICE_DEFINITION,
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
# SRV-EXP-001: Exposing interface views directly
# ===========================================================================


class TestSrvExp001:
    def test_expose_i_view_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZI_Order as Order;\n"
            "  expose ZI_OrderItem as OrderItem;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-001")

    def test_expose_i_prefix_without_z(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose I_SalesOrder as SalesOrder;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-001")

    def test_expose_c_view_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-001")


# ===========================================================================
# SRV-EXP-002: Excessive entity exposure
# ===========================================================================


class TestSrvExp002:
    def test_excessive_expose_detected(self) -> None:
        lines = ["define service ZUI_LARGE_V4 {"]
        for i in range(12):
            lines.append(f"  expose ZC_Entity{i} as Entity{i};")
        lines.append("}")
        code = "\n".join(lines) + "\n"
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-002")

    def test_few_expose_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "  expose ZC_Customer as Customer;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-002")

    def test_exactly_ten_expose_clean(self) -> None:
        lines = ["define service ZUI_MEDIUM_V4 {"]
        for i in range(10):
            lines.append(f"  expose ZC_Ent{i} as Ent{i};")
        lines.append("}")
        code = "\n".join(lines) + "\n"
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-002")


# ===========================================================================
# SRV-EXP-003: Missing service binding authorization
# ===========================================================================


class TestSrvExp003:
    def test_binding_without_auth_detected(self) -> None:
        code = (
            "service binding ZUI_ORDER_V4_BIND\n"
            "  for ZUI_ORDER_V4\n"
            "  type odata_v4\n"
        )
        findings = _run(code, ArtifactType.SERVICE_BINDING)
        assert _has_rule(findings, "SRV-EXP-003")

    def test_binding_with_auth_clean(self) -> None:
        code = (
            "service binding ZUI_ORDER_V4_BIND\n"
            "  for ZUI_ORDER_V4\n"
            "  type odata_v4\n"
            "  @AccessControl.authorizationCheck: #CHECK\n"
        )
        findings = _run(code, ArtifactType.SERVICE_BINDING)
        assert not _has_rule(findings, "SRV-EXP-003")

    def test_binding_with_authorization_keyword_clean(self) -> None:
        code = (
            "service binding ZUI_ORDER_V4_BIND\n"
            "  for ZUI_ORDER_V4\n"
            "  authorization check enabled\n"
        )
        findings = _run(code, ArtifactType.SERVICE_BINDING)
        assert not _has_rule(findings, "SRV-EXP-003")


# ===========================================================================
# SRV-EXP-004: Missing etag handling
# ===========================================================================


class TestSrvExp004:
    def test_expose_without_etag_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-004")

    def test_expose_with_etag_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
            "etag master LastChangedAt\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-004")

    def test_expose_with_semantic_key_clean(self) -> None:
        code = (
            "@ObjectModel.semanticKey: ['OrderId']\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-004")


# ===========================================================================
# SRV-EXP-005: OData V2 patterns with V4 intent
# ===========================================================================


class TestSrvExp005:
    def test_v2_annotation_in_v4_service_detected(self) -> None:
        code = (
            "@OData.publish: true\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-005")

    def test_sap_label_in_v4_service_detected(self) -> None:
        code = (
            "@sap.label: 'Order Service'\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-005")

    def test_v4_clean_service_clean(self) -> None:
        code = (
            "@EndUserText.label: 'Order Service'\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-005")


# ===========================================================================
# SRV-EXP-006: Missing filter restrictions
# ===========================================================================


class TestSrvExp006:
    def test_expose_without_filter_restrictions_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-006")

    def test_expose_with_filter_restrictions_clean(self) -> None:
        code = (
            "@Capabilities.FilterRestrictions.RequiredProperties: ['OrderId']\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-006")


# ===========================================================================
# SRV-EXP-007: Composition without deep operations
# ===========================================================================


class TestSrvExp007:
    def test_composition_without_draft_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
            "composition of ZC_OrderItem\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-007")

    def test_composition_with_draft_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
            "composition of ZC_OrderItem\n"
            "with draft\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-007")

    def test_no_composition_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-007")


# ===========================================================================
# SRV-EXP-008: Missing service description
# ===========================================================================


class TestSrvExp008:
    def test_service_without_description_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-008")

    def test_service_with_enduser_text_clean(self) -> None:
        code = (
            "@EndUserText.label: 'Order Management Service'\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-008")

    def test_service_with_comment_clean(self) -> None:
        code = (
            "// Order management service for Fiori apps\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-008")


# ===========================================================================
# SRV-EXP-009: Cross-service entity reference
# ===========================================================================


class TestSrvExp009:
    def test_cross_service_reference_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose OtherService.ZC_Product as Product;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-009")

    def test_same_namespace_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose ZC_OrderItem as OrderItem;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-009")


# ===========================================================================
# SRV-EXP-010: Missing pagination support
# ===========================================================================


class TestSrvExp010:
    def test_expose_without_pagination_detected(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-010")

    def test_expose_with_top_supported_clean(self) -> None:
        code = (
            "@Capabilities.TopSupported: true\n"
            "@Capabilities.SkipSupported: true\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-010")

    def test_expose_with_count_restrictions_clean(self) -> None:
        code = (
            "@Capabilities.CountRestrictions.Countable: true\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-010")


# ===========================================================================
# SRV-EXP-011: Draft-enabled entity without draft actions
# ===========================================================================


class TestSrvExp011:
    def test_draft_enabled_without_actions_detected(self) -> None:
        code = (
            "draft enabled\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "SRV-EXP-011")

    def test_draft_enabled_with_draft_actions_clean(self) -> None:
        code = (
            "draft enabled\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
            "with draft\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-011")

    def test_draft_with_draft_admin_data_clean(self) -> None:
        code = (
            "@ObjectModel.draft.enabled: true\n"
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "  expose DraftAdministrativeData;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-011")

    def test_no_draft_reference_clean(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZC_Order as Order;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "SRV-EXP-011")


# ===========================================================================
# SRV-EXP-012: Service binding without /sap/ prefix
# ===========================================================================


class TestSrvExp012:
    def test_binding_non_standard_path_detected(self) -> None:
        code = (
            "service binding ZUI_ORDER_V4_BIND\n"
            "  path: '/custom/odata/v4/order'\n"
        )
        findings = _run(code, ArtifactType.SERVICE_BINDING)
        assert _has_rule(findings, "SRV-EXP-012")

    def test_binding_standard_path_clean(self) -> None:
        code = (
            "service binding ZUI_ORDER_V4_BIND\n"
            "  path: '/sap/opu/odata4/sap/zui_order_v4'\n"
        )
        findings = _run(code, ArtifactType.SERVICE_BINDING)
        assert not _has_rule(findings, "SRV-EXP-012")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestServiceOdataBilingual:
    def test_german_output(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZI_Order as Order;\n"
            "}\n"
        )
        findings = _run(code, language=Language.DE)
        srv001 = next((f for f in findings if f.rule_id == "SRV-EXP-001"), None)
        assert srv001 is not None
        assert "Interface-View" in srv001.title

    def test_english_output(self) -> None:
        code = (
            "define service ZUI_ORDER_V4 {\n"
            "  expose ZI_Order as Order;\n"
            "}\n"
        )
        findings = _run(code, language=Language.EN)
        srv001 = next((f for f in findings if f.rule_id == "SRV-EXP-001"), None)
        assert srv001 is not None
        assert "interface view" in srv001.title.lower()
