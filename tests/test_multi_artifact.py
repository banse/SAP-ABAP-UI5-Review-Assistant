"""Tests for the multi-artifact input handler."""

from __future__ import annotations

import pytest

from app.engines.multi_artifact_handler import (
    ArtifactSection,
    split_change_package,
)
from app.models.enums import ArtifactType


# ---------------------------------------------------------------------------
# Sample inputs
# ---------------------------------------------------------------------------

SEPARATOR_DELIMITED = """\
// CDS View: ZI_ORDER
define view entity ZI_ORDER as select from ztable {
  key order_id,
      customer_name,
      status
}
---
* Class: ZCL_ORDER
CLASS zcl_order DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS get_data.
ENDCLASS.

CLASS zcl_order IMPLEMENTATION.
  METHOD get_data.
    SELECT * FROM ztable INTO TABLE @rt_data.
  ENDMETHOD.
ENDCLASS.
"""

EQUALS_SEPARATOR = """\
define view entity ZI_ITEM as select from zitem {
  key item_id,
      description
}
===
CLASS zcl_item DEFINITION PUBLIC.
  PUBLIC SECTION.
ENDCLASS.
CLASS zcl_item IMPLEMENTATION.
ENDCLASS.
"""

SINGLE_ARTIFACT = """\
CLASS zcl_single DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS do_something.
ENDCLASS.

CLASS zcl_single IMPLEMENTATION.
  METHOD do_something.
    WRITE 'hello'.
  ENDMETHOD.
ENDCLASS.
"""

MIXED_THREE_TYPES = """\
// CDS View: ZI_SALES
define view entity ZI_SALES as select from zsales {
  key sales_id,
      amount
}
---
* Class: ZCL_SALES
CLASS zcl_sales DEFINITION PUBLIC.
  PUBLIC SECTION.
ENDCLASS.
CLASS zcl_sales IMPLEMENTATION.
ENDCLASS.
---
// UI5 Controller: SalesController
sap.ui.define([
  "sap/ui/core/mvc/Controller"
], function (Controller) {
  "use strict";
  return Controller.extend("com.example.controller.Sales", {
    onInit: function () {}
  });
});
"""

AUTO_DETECT_INPUT = """\
define view entity ZI_AUTO as select from ztable {
  key auto_id,
      name
}

CLASS zcl_auto DEFINITION PUBLIC.
  PUBLIC SECTION.
ENDCLASS.
CLASS zcl_auto IMPLEMENTATION.
ENDCLASS.
"""

EMPTY_SECTIONS = """\
---
---
define view entity ZI_ONLY as select from ztable {
  key only_id
}
---
---
"""


# ---------------------------------------------------------------------------
# Tests: separator-delimited splitting
# ---------------------------------------------------------------------------


class TestSeparatorDelimitedSplit:
    """Test explicit separator-delimited splitting."""

    def test_two_sections_found(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert len(sections) == 2

    def test_first_section_is_cds(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert sections[0].artifact_type == ArtifactType.CDS_VIEW

    def test_second_section_is_abap(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert sections[1].artifact_type == ArtifactType.ABAP_CLASS

    def test_first_section_name(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert sections[0].artifact_name == "ZI_ORDER"

    def test_second_section_name(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert sections[1].artifact_name == "ZCL_ORDER"

    def test_section_indices(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        assert sections[0].section_index == 0
        assert sections[1].section_index == 1

    def test_section_code_not_empty(self):
        sections = split_change_package(SEPARATOR_DELIMITED)
        for s in sections:
            assert s.code.strip() != ""

    def test_equals_separator(self):
        sections = split_change_package(EQUALS_SEPARATOR)
        assert len(sections) == 2

    def test_equals_separator_types(self):
        sections = split_change_package(EQUALS_SEPARATOR)
        assert sections[0].artifact_type == ArtifactType.CDS_VIEW
        assert sections[1].artifact_type == ArtifactType.ABAP_CLASS


class TestAutoDetectSplit:
    """Test auto-detection of artifact boundaries."""

    def test_auto_detect_finds_two_artifacts(self):
        sections = split_change_package(AUTO_DETECT_INPUT)
        assert len(sections) >= 2

    def test_auto_detect_has_cds(self):
        sections = split_change_package(AUTO_DETECT_INPUT)
        types = {s.artifact_type for s in sections}
        assert ArtifactType.CDS_VIEW in types

    def test_auto_detect_has_abap(self):
        sections = split_change_package(AUTO_DETECT_INPUT)
        types = {s.artifact_type for s in sections}
        assert ArtifactType.ABAP_CLASS in types


class TestSingleArtifact:
    """Test that single artifact is treated as single section."""

    def test_single_artifact_one_section(self):
        sections = split_change_package(SINGLE_ARTIFACT)
        assert len(sections) == 1

    def test_single_artifact_is_abap_class(self):
        sections = split_change_package(SINGLE_ARTIFACT)
        assert sections[0].artifact_type == ArtifactType.ABAP_CLASS

    def test_single_artifact_name(self):
        sections = split_change_package(SINGLE_ARTIFACT)
        assert "zcl_single" in sections[0].artifact_name.lower()


class TestEmptySections:
    """Test that empty sections are skipped."""

    def test_empty_input(self):
        sections = split_change_package("")
        assert sections == []

    def test_whitespace_input(self):
        sections = split_change_package("   \n\n  ")
        assert sections == []

    def test_empty_between_separators(self):
        sections = split_change_package(EMPTY_SECTIONS)
        assert len(sections) == 1
        assert sections[0].artifact_type == ArtifactType.CDS_VIEW


class TestMixedThreeTypes:
    """Test mixed ABAP + CDS + UI5 change package."""

    def test_three_sections_found(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        assert len(sections) == 3

    def test_first_is_cds(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        assert sections[0].artifact_type == ArtifactType.CDS_VIEW

    def test_second_is_abap(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        assert sections[1].artifact_type == ArtifactType.ABAP_CLASS

    def test_third_is_ui5(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        assert sections[2].artifact_type == ArtifactType.UI5_CONTROLLER

    def test_names_derived(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        assert sections[0].artifact_name == "ZI_SALES"
        assert sections[1].artifact_name == "ZCL_SALES"

    def test_all_sections_have_code(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        for s in sections:
            assert len(s.code.strip()) > 10

    def test_all_sections_correctly_typed(self):
        sections = split_change_package(MIXED_THREE_TYPES)
        types = [s.artifact_type for s in sections]
        assert ArtifactType.CDS_VIEW in types
        assert ArtifactType.ABAP_CLASS in types
        assert ArtifactType.UI5_CONTROLLER in types


class TestHeaderParsing:
    """Test header line parsing for section names."""

    def test_cds_header_parsed(self):
        text = "// CDS View: ZI_TEST\ndefine view entity ZI_TEST as select from zt { key id }"
        sections = split_change_package(text)
        assert len(sections) == 1
        # Name should be derived from the code or header
        assert "ZI_TEST" in sections[0].artifact_name

    def test_abap_header_parsed(self):
        text = "* Class: ZCL_TEST\nCLASS zcl_test DEFINITION PUBLIC.\nENDCLASS.\nCLASS zcl_test IMPLEMENTATION.\nENDCLASS."
        sections = split_change_package(text)
        assert len(sections) == 1

    def test_no_header_derives_name_from_code(self):
        text = "CLASS zcl_derived DEFINITION PUBLIC.\nENDCLASS.\nCLASS zcl_derived IMPLEMENTATION.\nENDCLASS."
        sections = split_change_package(text)
        assert "zcl_derived" in sections[0].artifact_name.lower()
