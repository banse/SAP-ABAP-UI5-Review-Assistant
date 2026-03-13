"""Tests for the review type detection engine."""

from __future__ import annotations

import pytest

from app.engines.review_type_detector import detect_review_type
from app.models.enums import ReviewType


# ---------------------------------------------------------------------------
# Diff detection
# ---------------------------------------------------------------------------


class TestDiffDetection:
    def test_unified_diff_markers(self) -> None:
        code = (
            "--- a/src/zcl_order.clas.abap\n"
            "+++ b/src/zcl_order.clas.abap\n"
            "@@ -10,6 +10,8 @@\n"
            " METHOD get_orders.\n"
            "+   SELECT vbeln FROM vbak INTO TABLE @rt_result.\n"
            " ENDMETHOD.\n"
        )
        assert detect_review_type(code) == ReviewType.DIFF_REVIEW

    def test_diff_with_plus_markers_only(self) -> None:
        code = "+++ b/src/zcl_order.clas.abap\n+  new line added\n"
        assert detect_review_type(code) == ReviewType.DIFF_REVIEW

    def test_diff_with_minus_markers_only(self) -> None:
        code = "--- a/src/zcl_order.clas.abap\nsome context\n"
        assert detect_review_type(code) == ReviewType.DIFF_REVIEW

    def test_diff_with_hunk_markers(self) -> None:
        code = "@@ -1,5 +1,7 @@\n METHOD test.\n ENDMETHOD.\n"
        assert detect_review_type(code) == ReviewType.DIFF_REVIEW


# ---------------------------------------------------------------------------
# ABAP snippet detection
# ---------------------------------------------------------------------------


class TestAbapSnippetDetection:
    def test_abap_class_definition(self) -> None:
        code = (
            "CLASS zcl_order DEFINITION PUBLIC.\n"
            "  PUBLIC SECTION.\n"
            "    METHODS get_orders.\n"
            "ENDCLASS.\n"
        )
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW

    def test_abap_select_statement(self) -> None:
        code = "SELECT vbeln erdat FROM vbak INTO TABLE @lt_orders WHERE kunnr = @iv_kunnr.\n"
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW

    def test_abap_report(self) -> None:
        code = "REPORT z_test_report.\nWRITE: 'Hello World'.\n"
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW


# ---------------------------------------------------------------------------
# CDS snippet detection
# ---------------------------------------------------------------------------


class TestCdsSnippetDetection:
    def test_cds_view_entity(self) -> None:
        code = (
            "@AbapCatalog.viewEnhancementCategory: [#NONE]\n"
            "define view entity ZI_SalesOrder as select from vbak {\n"
            "  key vbeln as SalesOrder\n"
            "}\n"
        )
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW

    def test_cds_projection(self) -> None:
        code = "define root view entity ZC_Order as projection on ZI_Order {\n  key OrderId\n}\n"
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW


# ---------------------------------------------------------------------------
# UI5 snippet detection
# ---------------------------------------------------------------------------


class TestUi5SnippetDetection:
    def test_ui5_controller(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {}\n"
            "  });\n"
            "});\n"
        )
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW

    def test_ui5_xml_view(self) -> None:
        code = '<mvc:View xmlns:mvc="sap.ui.core.mvc">\n  <Page title="Test"/>\n</mvc:View>\n'
        assert detect_review_type(code) == ReviewType.SNIPPET_REVIEW


# ---------------------------------------------------------------------------
# Solution design text detection
# ---------------------------------------------------------------------------


class TestDesignTextDetection:
    def test_design_prose(self) -> None:
        text = (
            "Our proposed solution architecture involves a side-by-side extension approach. "
            "The design includes a BTP-based microservice that communicates via OData. "
            "We need to evaluate the strategy for data replication."
        )
        assert detect_review_type(text) == ReviewType.SOLUTION_DESIGN_REVIEW

    def test_design_with_code_is_snippet(self) -> None:
        text = (
            "The design approach for this solution is to use a CDS view.\n"
            "define view entity ZI_Test as select from ztab { key id }\n"
        )
        # Has code patterns, so should NOT be solution design
        assert detect_review_type(text) == ReviewType.SNIPPET_REVIEW


# ---------------------------------------------------------------------------
# Ticket reference detection
# ---------------------------------------------------------------------------


class TestTicketDetection:
    def test_jira_ticket(self) -> None:
        text = "Please review the changes for JIRA-12345."
        assert detect_review_type(text) == ReviewType.TICKET_BASED_PRE_REVIEW

    def test_snow_incident(self) -> None:
        text = "Pre-review for INC0012345 — customer order creation fails."
        assert detect_review_type(text) == ReviewType.TICKET_BASED_PRE_REVIEW

    def test_ticket_with_code_is_snippet(self) -> None:
        text = (
            "JIRA-999 fix:\n"
            "CLASS zcl_fix DEFINITION PUBLIC.\n"
            "ENDCLASS.\n"
        )
        # Contains code, so it is a snippet even though there is a ticket ref
        assert detect_review_type(text) == ReviewType.SNIPPET_REVIEW


# ---------------------------------------------------------------------------
# Provided type override
# ---------------------------------------------------------------------------


class TestProvidedTypeOverride:
    def test_override_with_provided_type(self) -> None:
        code = "+++ b/file.abap\n@@ -1 +1 @@\n"
        # Would normally detect DIFF, but we override
        assert detect_review_type(code, ReviewType.SNIPPET_REVIEW) == ReviewType.SNIPPET_REVIEW

    def test_override_regression(self) -> None:
        assert (
            detect_review_type("anything", ReviewType.REGRESSION_RISK_REVIEW)
            == ReviewType.REGRESSION_RISK_REVIEW
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string(self) -> None:
        assert detect_review_type("") == ReviewType.SNIPPET_REVIEW

    def test_whitespace_only(self) -> None:
        assert detect_review_type("   \n\t  ") == ReviewType.SNIPPET_REVIEW

    def test_none_provided_type(self) -> None:
        code = "METHOD test. ENDMETHOD."
        assert detect_review_type(code, None) == ReviewType.SNIPPET_REVIEW

    def test_random_text_defaults_to_snippet(self) -> None:
        assert detect_review_type("lorem ipsum dolor sit amet") == ReviewType.SNIPPET_REVIEW
