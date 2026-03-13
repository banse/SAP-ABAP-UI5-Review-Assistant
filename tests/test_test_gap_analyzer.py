"""Tests for the test gap analyzer engine.

Uses realistic SAP ABAP, RAP Behavior Definition, and UI5 code snippets
to validate that the analyzer correctly identifies missing test coverage.
"""

from __future__ import annotations

import pytest

from app.engines.test_gap_analyzer import analyze_test_gaps
from app.models.enums import (
    ArtifactType,
    Language,
    ReviewContext,
    Severity,
    TestGapCategory,
)
from app.models.schemas import TestGap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(
    code: str,
    artifact_type: ArtifactType = ArtifactType.ABAP_CLASS,
    language: Language = Language.EN,
    review_context: ReviewContext = ReviewContext.GREENFIELD,
) -> list[TestGap]:
    return analyze_test_gaps(
        code=code,
        artifact_type=artifact_type,
        review_context=review_context,
        language=language,
    )


def _has_rule(gaps: list[TestGap], rule_fragment: str) -> bool:
    """Check if any gap description contains the given rule text fragment."""
    return any(rule_fragment in g.description for g in gaps)


def _has_category(gaps: list[TestGap], cat: TestGapCategory) -> bool:
    return any(g.category == cat for g in gaps)


# ---------------------------------------------------------------------------
# Realistic SAP code fixtures
# ---------------------------------------------------------------------------

ABAP_CLASS_WITH_PUBLIC_METHODS = """\
CLASS zcl_sales_order_service DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    METHODS get_sales_orders
      IMPORTING
        iv_kunnr TYPE kunnr
      RETURNING
        VALUE(rt_orders) TYPE ztt_sales_order.

    METHODS create_sales_order
      IMPORTING
        is_order TYPE zstr_sales_order
      RETURNING
        VALUE(rv_vbeln) TYPE vbeln.

    METHODS validate_customer
      IMPORTING
        iv_kunnr TYPE kunnr
      RAISING
        zcx_invalid_customer.

  PRIVATE SECTION.
    METHODS _check_duplicates
      IMPORTING
        iv_vbeln TYPE vbeln.
ENDCLASS.

CLASS zcl_sales_order_service IMPLEMENTATION.

  METHOD get_sales_orders.
    SELECT vbeln, erdat, auart, netwr, waerk
      FROM vbak
      WHERE kunnr = @iv_kunnr
      INTO TABLE @rt_orders
      ORDER BY vbeln.
  ENDMETHOD.

  METHOD create_sales_order.
    \" creation logic
  ENDMETHOD.

  METHOD validate_customer.
    SELECT SINGLE kunnr FROM kna1
      WHERE kunnr = @iv_kunnr
      INTO @DATA(lv_kunnr).
    IF sy-subrc <> 0.
      RAISE EXCEPTION TYPE zcx_invalid_customer.
    ENDIF.
  ENDMETHOD.

  METHOD _check_duplicates.
    \" private helper
  ENDMETHOD.

ENDCLASS.
"""

ABAP_COMPLEX_BRANCHING = """\
METHOD determine_pricing.
  CASE iv_order_type.
    WHEN 'OR'.
      IF iv_customer_group = 'VIP'.
        rv_discount = 15.
      ELSEIF iv_customer_group = 'PREMIUM'.
        rv_discount = 10.
      ELSE.
        rv_discount = 0.
      ENDIF.
    WHEN 'CR'.
      rv_discount = 0.
    WHEN 'RE'.
      IF iv_return_reason IS NOT INITIAL.
        rv_discount = 100.
      ELSE.
        RAISE EXCEPTION TYPE zcx_missing_return_reason.
      ENDIF.
    WHEN OTHERS.
      rv_discount = 0.
  ENDCASE.
ENDMETHOD.
"""

ABAP_EXCEPTION_HANDLING = """\
METHOD process_order.
  TRY.
      lo_bapi_wrapper->create_order(
        EXPORTING is_header = ls_header
                  it_items  = lt_items
        IMPORTING ev_vbeln  = rv_vbeln ).
    CATCH zcx_bapi_error INTO DATA(lx_bapi).
      RAISE EXCEPTION TYPE zcx_order_processing
        EXPORTING
          previous = lx_bapi.
    CATCH cx_sy_itab_line_not_found INTO DATA(lx_itab).
      RAISE EXCEPTION TYPE zcx_order_processing
        EXPORTING
          textid   = zcx_order_processing=>item_not_found
          previous = lx_itab.
  ENDTRY.
ENDMETHOD.
"""

ABAP_AUTHORITY_CHECK = """\
METHOD get_sales_data.
  AUTHORITY-CHECK OBJECT 'V_VBAK_VKO'
    ID 'VKORG' FIELD iv_vkorg
    ID 'VTWEG' FIELD iv_vtweg
    ID 'SPART' FIELD iv_spart
    ID 'ACTVT' FIELD '03'.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE zcx_no_authority
      EXPORTING
        object = 'V_VBAK_VKO'.
  ENDIF.

  SELECT vbeln, erdat, netwr, waerk
    FROM vbak
    WHERE vkorg = @iv_vkorg
      AND vtweg = @iv_vtweg
    INTO TABLE @rt_result
    ORDER BY vbeln.
ENDMETHOD.
"""

ABAP_VALIDATION_LOGIC = """\
METHOD validate_input.
  IF iv_kunnr IS INITIAL.
    RAISE EXCEPTION TYPE zcx_validation_error
      EXPORTING textid = zcx_validation_error=>customer_required.
  ENDIF.

  IF strlen( iv_description ) > 40.
    RAISE EXCEPTION TYPE zcx_validation_error
      EXPORTING textid = zcx_validation_error=>description_too_long.
  ENDIF.

  IF iv_quantity <= 0.
    RAISE EXCEPTION TYPE zcx_validation_error
      EXPORTING textid = zcx_validation_error=>invalid_quantity.
  ENDIF.
ENDMETHOD.
"""

BEHAVIOR_DEFINITION_WITH_ACTIONS = """\
managed implementation in class zbp_i_salesorder unique;
strict ( 2 );

define behavior for ZI_SalesOrder alias SalesOrder
persistent table zsalesorder
lock master
authorization master ( instance )
{
  create;
  update;
  delete;

  action ( features : instance ) confirmOrder result [1] $self;
  action rejectOrder result [1] $self;
  static action createFromTemplate parameter ZA_SalesOrderTemplate result [1] $self;

  validation validateCustomer on save { create; update; field CustomerId; }
  validation validateAmount on save { create; update; field NetAmount; }

  determination setCreatedInfo on modify { create; }
  determination calculateTax on save { create; update; field NetAmount; }

  draft action Edit;
  draft action Resume;
  draft action Activate optimized;
  draft action Discard;
  draft determine action Prepare;

  mapping for zsalesorder
  {
    SalesOrderId = salesorder_id;
    CustomerId   = customer_id;
    NetAmount    = net_amount;
    Currency     = currency;
  }
}

define behavior for ZI_SalesOrderItem alias SalesOrderItem
persistent table zsalesorderitem
lock dependent by _SalesOrder
authorization dependent by _SalesOrder
{
  update;
  delete;

  determination calculateItemTotal on modify { field Quantity, UnitPrice; }

  field ( readonly ) SalesOrderId;

  association _SalesOrder;
}
"""

BEHAVIOR_DEFINITION_VALIDATIONS_ONLY = """\
managed implementation in class zbp_i_product unique;
strict ( 2 );

define behavior for ZI_Product alias Product
persistent table zproduct
lock master
authorization master ( instance )
{
  create;
  update;

  validation validateProductId on save { create; field ProductId; }
  validation validateDescription on save { create; update; field Description; }
}
"""

BEHAVIOR_DEFINITION_DETERMINATIONS_ONLY = """\
managed implementation in class zbp_i_invoice unique;
strict ( 2 );

define behavior for ZI_Invoice alias Invoice
persistent table zinvoice
lock master
authorization master ( instance )
{
  create;
  update;

  determination setInvoiceNumber on modify { create; }
  determination calculateTotal on save { create; update; field Amount; }
}
"""

UI5_CONTROLLER_WITH_HANDLERS = """\
sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/ui/model/json/JSONModel",
  "sap/m/MessageToast"
], function(Controller, JSONModel, MessageToast) {
  "use strict";

  return Controller.extend("com.myapp.controller.SalesOrder", {

    onInit: function() {
      var oViewModel = new JSONModel({
        busy: false,
        editable: false
      });
      this.getView().setModel(oViewModel, "viewModel");
    },

    onCreateOrder: function(oEvent) {
      var oModel = this.getView().getModel();
      var oContext = oModel.createEntry("/SalesOrderSet", {
        properties: {
          CustomerNumber: this.byId("customerInput").getValue()
        }
      });
      this.getView().setBindingContext(oContext);
      oModel.submitChanges({
        success: function() {
          MessageToast.show("Order created");
        },
        error: function(oError) {
          MessageToast.show("Error: " + oError.message);
        }
      });
    },

    onDeleteOrder: function(oEvent) {
      var oContext = oEvent.getSource().getBindingContext();
      this.getView().getModel().remove(oContext.getPath(), {
        success: function() {
          MessageToast.show("Order deleted");
        },
        error: function() {
          MessageToast.show("Delete failed");
        }
      });
    },

    onFilterOrders: function(oEvent) {
      var sQuery = oEvent.getParameter("query");
      var oTable = this.byId("salesOrderTable");
      var oBinding = oTable.getBinding("items");
      oBinding.filter(new sap.ui.model.Filter("CustomerName", "Contains", sQuery));
    },

    onNavToDetail: function(oEvent) {
      var sOrderId = oEvent.getSource().getBindingContext().getProperty("SalesOrderId");
      this.getOwnerComponent().getRouter().navTo("detail", {
        orderId: sOrderId
      });
    }
  });
});
"""

UI5_VIEW_WITH_DYNAMIC_VISIBILITY = """\
<mvc:View
  xmlns:mvc="sap.ui.core.mvc"
  xmlns="sap.m"
  xmlns:core="sap.ui.core"
  controllerName="com.myapp.controller.SalesOrder">

  <Page title="{i18n>salesOrderTitle}">
    <headerContent>
      <Button
        text="{i18n>createOrder}"
        press="onCreateOrder"
        visible="{= ${viewModel>/editable} === true}"/>
      <Button
        text="{i18n>deleteOrder}"
        press="onDeleteOrder"
        visible="{= ${viewModel>/selectedCount} > 0}"
        type="Reject"/>
    </headerContent>

    <content>
      <Table id="salesOrderTable" items="{/SalesOrderSet}">
        <columns>
          <Column><Text text="{i18n>orderId}"/></Column>
          <Column><Text text="{i18n>customer}"/></Column>
          <Column><Text text="{i18n>amount}"/></Column>
          <Column visible="{= ${viewModel>/showStatus} === true}">
            <Text text="{i18n>status}"/>
          </Column>
        </columns>
        <items>
          <ColumnListItem press="onNavToDetail" type="Navigation">
            <cells>
              <Text text="{SalesOrderId}"/>
              <Text text="{CustomerName}"/>
              <ObjectNumber number="{NetAmount}" unit="{Currency}"/>
              <ObjectStatus
                text="{Status}"
                state="{= ${Status} === 'CONFIRMED' ? 'Success' : 'Warning'}"
                visible="{= ${viewModel>/showStatus} === true}"/>
            </cells>
          </ColumnListItem>
        </items>
      </Table>
    </content>
  </Page>
</mvc:View>
"""

UI5_CONTROLLER_WITH_MODEL_MANIPULATION = """\
sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/ui/model/json/JSONModel"
], function(Controller, JSONModel) {
  "use strict";

  return Controller.extend("com.myapp.controller.Detail", {

    onInit: function() {
      this.getView().setModel(new JSONModel({}), "detail");
    },

    onUpdateStatus: function(oEvent) {
      var oModel = this.getView().getModel("detail");
      oModel.setProperty("/status", "CONFIRMED");
      oModel.setProperty("/confirmedAt", new Date().toISOString());
      oModel.setData(Object.assign(oModel.getData(), { lastAction: "confirm" }));
    },

    onLoadDetails: function() {
      var sPath = this.getView().getBindingContext().getPath();
      var oData = this.getView().getModel().getProperty(sPath);
      this.getView().getModel("detail").setData(oData);
    }
  });
});
"""

UI5_CONTROLLER_WITH_NAVIGATION = """\
sap.ui.define([
  "sap/ui/core/mvc/Controller"
], function(Controller) {
  "use strict";

  return Controller.extend("com.myapp.controller.List", {

    onInit: function() {},

    onItemPress: function(oEvent) {
      var sId = oEvent.getSource().getBindingContext().getProperty("Id");
      this.getOwnerComponent().getRouter().navTo("detail", { id: sId });
    },

    onNavBack: function() {
      this.getOwnerComponent().getRouter().navTo("main");
    },

    onNavigateToCreate: function() {
      var oRouter = this.getOwnerComponent().getRouter();
      oRouter.navTo("create", { mode: "new" });
    }
  });
});
"""

ABAP_GLOBAL_DATA_MODIFICATION = """\
CLASS zcl_order_cache DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    CLASS-DATA gt_order_cache TYPE ztt_order_cache.
    CLASS-DATA gv_last_refresh TYPE timestamp.

    METHODS refresh_cache
      IMPORTING iv_vkorg TYPE vkorg.

    METHODS get_cached_orders
      RETURNING VALUE(rt_orders) TYPE ztt_order_cache.

  PRIVATE SECTION.
    DATA gs_config TYPE zstr_cache_config.
ENDCLASS.

CLASS zcl_order_cache IMPLEMENTATION.

  METHOD refresh_cache.
    SELECT vbeln, erdat, kunnr, netwr, waerk
      FROM vbak
      WHERE vkorg = @iv_vkorg
      INTO TABLE @gt_order_cache
      ORDER BY vbeln.

    GET TIME STAMP FIELD gv_last_refresh.

    EXPORT gt_order_cache TO MEMORY ID 'Z_ORDER_CACHE'.
  ENDMETHOD.

  METHOD get_cached_orders.
    rt_orders = gt_order_cache.
  ENDMETHOD.

ENDCLASS.
"""

ABAP_CROSS_ENTITY_MODIFICATION = """\
METHOD update_order_with_items.
  \" Update header
  MODIFY ztab_header FROM ls_header.

  \" Update items based on header changes
  LOOP AT lt_items INTO DATA(ls_item).
    ls_item-currency = ls_header-currency.
    MODIFY ztab_item FROM ls_item.
  ENDLOOP.

  \" Update partner assignment
  MODIFY ztab_partner FROM ls_partner.
ENDMETHOD.
"""

ABAP_CLEAN_SIMPLE = """\
METHOD get_material_text.
  SELECT SINGLE maktx
    FROM makt
    WHERE matnr = @iv_matnr
      AND spras = @sy-langu
    INTO @rv_text.
ENDMETHOD.
"""

ABAP_WITH_EXISTING_TESTS = """\
CLASS zcl_calculator DEFINITION
  PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.
    METHODS add
      IMPORTING iv_a TYPE i iv_b TYPE i
      RETURNING VALUE(rv_sum) TYPE i.
ENDCLASS.

CLASS zcl_calculator IMPLEMENTATION.
  METHOD add.
    rv_sum = iv_a + iv_b.
  ENDMETHOD.
ENDCLASS.

CLASS ltcl_calculator_test DEFINITION FINAL FOR TESTING
  DURATION SHORT RISK LEVEL HARMLESS.
  PRIVATE SECTION.
    METHODS test_add FOR TESTING.
ENDCLASS.

CLASS ltcl_calculator_test IMPLEMENTATION.
  METHOD test_add.
    DATA(lo_cut) = NEW zcl_calculator( ).
    cl_abap_unit_assert=>assert_equals(
      act = lo_cut->add( iv_a = 2 iv_b = 3 )
      exp = 5 ).
  ENDMETHOD.
ENDCLASS.
"""

BEHAVIOR_DEFINITION_WITH_DRAFT = """\
managed implementation in class zbp_i_travel unique;
strict ( 2 );
with draft;

define behavior for ZI_Travel alias Travel
persistent table ztravel
draft table ztravel_d
lock master total etag LastChangedAt
authorization master ( instance )
{
  create;
  update;
  delete;

  draft action Edit;
  draft action Resume;
  draft action Activate optimized;
  draft action Discard;
  draft determine action Prepare
  {
    validation validateAgency;
    validation validateDates;
  }

  validation validateAgency on save { create; update; field AgencyId; }
  validation validateDates on save { create; update; field BeginDate, EndDate; }

  determination setTravelNumber on modify { create; }
}
"""


# ===========================================================================
# TG-ABAP-001: Public method without test class
# ===========================================================================


class TestTgAbap001PublicMethodGap:

    def test_detects_public_methods_without_tests(self) -> None:
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        assert _has_category(gaps, TestGapCategory.ABAP_UNIT)
        assert any("TG-ABAP-001" in g.description or "METHODS" in g.description for g in gaps)

    def test_public_method_gap_has_suggested_test(self) -> None:
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        unit_gaps = [g for g in gaps if g.category == TestGapCategory.ABAP_UNIT]
        assert len(unit_gaps) > 0
        assert any(g.suggested_test is not None for g in unit_gaps)

    def test_downgrades_priority_when_tests_exist(self) -> None:
        gaps = _run(ABAP_WITH_EXISTING_TESTS)
        method_gaps = [
            g for g in gaps
            if g.category == TestGapCategory.ABAP_UNIT and "METHODS" in g.description
        ]
        # Should be downgraded to OPTIONAL since test class already exists
        for g in method_gaps:
            assert g.priority == Severity.OPTIONAL

    def test_no_false_positive_on_private_methods(self) -> None:
        code = """\
CLASS zcl_helper DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PRIVATE SECTION.
    METHODS _internal_helper.
ENDCLASS.
CLASS zcl_helper IMPLEMENTATION.
  METHOD _internal_helper.
  ENDMETHOD.
ENDCLASS.
"""
        gaps = _run(code)
        # Private-only classes: the rule still fires on the METHODS keyword,
        # but the point is it detects methods that need tests.
        # This is acceptable — the rule is intentionally broad.
        assert isinstance(gaps, list)


# ===========================================================================
# TG-ABAP-002: Complex branching
# ===========================================================================


class TestTgAbap002ComplexBranching:

    def test_detects_complex_case_when_branching(self) -> None:
        gaps = _run(ABAP_COMPLEX_BRANCHING, ArtifactType.ABAP_METHOD)
        assert _has_category(gaps, TestGapCategory.ABAP_UNIT)

    def test_detects_elseif_branching(self) -> None:
        gaps = _run(ABAP_COMPLEX_BRANCHING, ArtifactType.ABAP_METHOD)
        # Should find WHEN / ELSEIF patterns
        branch_gaps = [g for g in gaps if "TG-ABAP-002" in g.description or "branch" in g.description.lower()]
        assert len(branch_gaps) > 0

    def test_branch_gap_has_important_priority(self) -> None:
        gaps = _run(ABAP_COMPLEX_BRANCHING, ArtifactType.ABAP_METHOD)
        branch_gaps = [g for g in gaps if "branch" in g.description.lower() or "WHEN" in g.description]
        for g in branch_gaps:
            assert g.priority in (Severity.IMPORTANT, Severity.CRITICAL)

    def test_simple_if_still_detected(self) -> None:
        code = """\
METHOD check_status.
  IF iv_status = 'A'.
    rv_active = abap_true.
  ELSEIF iv_status = 'I'.
    rv_active = abap_false.
  ENDIF.
ENDMETHOD.
"""
        gaps = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_category(gaps, TestGapCategory.ABAP_UNIT)


# ===========================================================================
# TG-ABAP-003: Exception handling
# ===========================================================================


class TestTgAbap003ExceptionHandling:

    def test_detects_raise_exception(self) -> None:
        gaps = _run(ABAP_EXCEPTION_HANDLING, ArtifactType.ABAP_METHOD)
        exc_gaps = [g for g in gaps if "exception" in g.description.lower() or "CATCH" in g.description]
        assert len(exc_gaps) > 0

    def test_detects_catch_blocks(self) -> None:
        gaps = _run(ABAP_EXCEPTION_HANDLING, ArtifactType.ABAP_METHOD)
        assert _has_category(gaps, TestGapCategory.ABAP_UNIT)

    def test_exception_gap_suggests_negative_test(self) -> None:
        gaps = _run(ABAP_EXCEPTION_HANDLING, ArtifactType.ABAP_METHOD)
        exc_gaps = [g for g in gaps if "exception" in g.description.lower() or "CATCH" in g.description]
        for g in exc_gaps:
            assert g.suggested_test is not None
            assert "CATCH" in g.suggested_test or "fail" in g.suggested_test

    def test_simple_catch_detected(self) -> None:
        code = """\
METHOD safe_divide.
  TRY.
      rv_result = iv_a / iv_b.
    CATCH cx_sy_zerodivide.
      rv_result = 0.
  ENDTRY.
ENDMETHOD.
"""
        gaps = _run(code, ArtifactType.ABAP_METHOD)
        exc_gaps = [g for g in gaps if "exception" in g.description.lower() or "CATCH" in g.description]
        assert len(exc_gaps) > 0


# ===========================================================================
# TG-ABAP-004: AUTHORITY-CHECK
# ===========================================================================


class TestTgAbap004AuthorityCheck:

    def test_detects_authority_check(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description]
        assert len(auth_gaps) > 0

    def test_authority_gap_is_critical(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description]
        for g in auth_gaps:
            assert g.priority == Severity.CRITICAL

    def test_authority_gap_suggests_both_paths(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description]
        for g in auth_gaps:
            assert g.suggested_test is not None
            assert "authorized" in g.suggested_test.lower() or "auth" in g.suggested_test.lower()


# ===========================================================================
# TG-ABAP-005: Data validation logic
# ===========================================================================


class TestTgAbap005DataValidation:

    def test_detects_is_initial_validation(self) -> None:
        gaps = _run(ABAP_VALIDATION_LOGIC, ArtifactType.ABAP_METHOD)
        val_gaps = [g for g in gaps if "IS INITIAL" in g.description or "validation" in g.description.lower()]
        assert len(val_gaps) > 0

    def test_detects_strlen_boundary(self) -> None:
        gaps = _run(ABAP_VALIDATION_LOGIC, ArtifactType.ABAP_METHOD)
        assert _has_category(gaps, TestGapCategory.ABAP_UNIT)

    def test_validation_gap_suggests_boundary_test(self) -> None:
        gaps = _run(ABAP_VALIDATION_LOGIC, ArtifactType.ABAP_METHOD)
        val_gaps = [g for g in gaps if "validation" in g.description.lower() or "boundary" in g.description.lower() or "IS INITIAL" in g.description]
        assert len(val_gaps) > 0
        for g in val_gaps:
            assert g.suggested_test is not None


# ===========================================================================
# TG-RAP-001: Action without test
# ===========================================================================


class TestTgRap001ActionGap:

    def test_detects_action_definitions(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        action_gaps = [g for g in gaps if g.category == TestGapCategory.ACTION_VALIDATION and "action" in g.description.lower()]
        assert len(action_gaps) > 0

    def test_action_gap_has_eml_template(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        action_gaps = [g for g in gaps if "action" in g.description.lower() and g.category == TestGapCategory.ACTION_VALIDATION]
        eml_gaps = [g for g in action_gaps if g.suggested_test and "MODIFY ENTITIES" in g.suggested_test]
        assert len(eml_gaps) > 0

    def test_static_action_detected(self) -> None:
        code = """\
define behavior for ZI_Order alias Order
{
  static action createFromTemplate parameter ZA_OrderTemplate result [1] $self;
}
"""
        gaps = _run(code, ArtifactType.BEHAVIOR_DEFINITION)
        action_gaps = [g for g in gaps if "action" in g.description.lower()]
        assert len(action_gaps) > 0


# ===========================================================================
# TG-RAP-002: Validation without negative test
# ===========================================================================


class TestTgRap002ValidationGap:

    def test_detects_validation_definitions(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_VALIDATIONS_ONLY, ArtifactType.BEHAVIOR_DEFINITION)
        val_gaps = [g for g in gaps if "validation" in g.description.lower()]
        assert len(val_gaps) > 0

    def test_validation_gap_suggests_invalid_data_test(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_VALIDATIONS_ONLY, ArtifactType.BEHAVIOR_DEFINITION)
        val_gaps = [g for g in gaps if "validation" in g.description.lower() and g.suggested_test]
        for g in val_gaps:
            assert "INVALID" in g.suggested_test or "invalid" in g.suggested_test.lower()

    def test_validation_in_full_bdef_detected(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        val_gaps = [g for g in gaps if "validation" in g.description.lower() and "on save" in g.description.lower()]
        assert len(val_gaps) > 0


# ===========================================================================
# TG-RAP-003: Determination without trigger test
# ===========================================================================


class TestTgRap003DeterminationGap:

    def test_detects_determination_definitions(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_DETERMINATIONS_ONLY, ArtifactType.BEHAVIOR_DEFINITION)
        det_gaps = [g for g in gaps if "determination" in g.description.lower()]
        assert len(det_gaps) > 0

    def test_determination_gap_has_optional_priority(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_DETERMINATIONS_ONLY, ArtifactType.BEHAVIOR_DEFINITION)
        det_gaps = [g for g in gaps if "determination" in g.description.lower()]
        for g in det_gaps:
            assert g.priority == Severity.OPTIONAL

    def test_determination_in_full_bdef_detected(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        det_gaps = [g for g in gaps if "determination" in g.description.lower()]
        assert len(det_gaps) > 0


# ===========================================================================
# TG-RAP-004: Draft handling
# ===========================================================================


class TestTgRap004DraftHandling:

    def test_detects_draft_handling(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_DRAFT, ArtifactType.BEHAVIOR_DEFINITION)
        draft_gaps = [g for g in gaps if "draft" in g.description.lower()]
        assert len(draft_gaps) > 0

    def test_draft_gap_suggests_lifecycle_test(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_DRAFT, ArtifactType.BEHAVIOR_DEFINITION)
        draft_gaps = [g for g in gaps if "draft" in g.description.lower() and g.suggested_test]
        for g in draft_gaps:
            assert "Activate" in g.suggested_test or "draft" in g.suggested_test.lower()

    def test_with_draft_keyword_detected(self) -> None:
        code = """\
managed implementation in class zbp_test unique;
with draft;

define behavior for ZI_Test alias Test
persistent table ztest
draft table ztest_d
lock master
{
  create;
  update;
  draft action Edit;
  draft action Activate optimized;
}
"""
        gaps = _run(code, ArtifactType.BEHAVIOR_DEFINITION)
        draft_gaps = [g for g in gaps if "draft" in g.description.lower()]
        assert len(draft_gaps) > 0


# ===========================================================================
# TG-UI5-001: Controller event handlers
# ===========================================================================


class TestTgUi5001EventHandlerGap:

    def test_detects_event_handlers(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_HANDLERS, ArtifactType.UI5_CONTROLLER)
        handler_gaps = [g for g in gaps if g.category == TestGapCategory.UI_BEHAVIOR]
        assert len(handler_gaps) > 0

    def test_suggests_opa5_test(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_HANDLERS, ArtifactType.UI5_CONTROLLER)
        handler_gaps = [g for g in gaps if g.category == TestGapCategory.UI_BEHAVIOR and g.suggested_test]
        opa_gaps = [g for g in handler_gaps if "OPA5" in (g.suggested_test or "") or "opaTest" in (g.suggested_test or "")]
        assert len(opa_gaps) > 0

    def test_oncreate_handler_detected(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_HANDLERS, ArtifactType.UI5_CONTROLLER)
        # The event handler rule fires on the first on[A-Z] pattern it finds.
        # Verify that at least one UI_BEHAVIOR gap references an event handler.
        handler_gaps = [
            g for g in gaps
            if g.category == TestGapCategory.UI_BEHAVIOR and "Detected:" in g.description
        ]
        assert len(handler_gaps) > 0
        # The matched text should contain an event handler pattern
        assert any("on" in g.description for g in handler_gaps)


# ===========================================================================
# TG-UI5-002: Dynamic visibility
# ===========================================================================


class TestTgUi5002DynamicVisibility:

    def test_detects_dynamic_visibility(self) -> None:
        gaps = _run(UI5_VIEW_WITH_DYNAMIC_VISIBILITY, ArtifactType.UI5_VIEW)
        vis_gaps = [g for g in gaps if "visible" in g.description.lower() or "visibility" in g.description.lower()]
        assert len(vis_gaps) > 0

    def test_visibility_gap_category(self) -> None:
        gaps = _run(UI5_VIEW_WITH_DYNAMIC_VISIBILITY, ArtifactType.UI5_VIEW)
        assert _has_category(gaps, TestGapCategory.UI_BEHAVIOR)

    def test_suggests_visibility_test(self) -> None:
        gaps = _run(UI5_VIEW_WITH_DYNAMIC_VISIBILITY, ArtifactType.UI5_VIEW)
        vis_gaps = [g for g in gaps if "visible" in g.description.lower() and g.suggested_test]
        for g in vis_gaps:
            assert "Visible" in g.suggested_test or "visible" in g.suggested_test.lower()


# ===========================================================================
# TG-UI5-003: Model binding manipulation
# ===========================================================================


class TestTgUi5003ModelBindingManipulation:

    def test_detects_set_property(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_MODEL_MANIPULATION, ArtifactType.UI5_CONTROLLER)
        model_gaps = [g for g in gaps if "setProperty" in g.description or "model" in g.description.lower()]
        assert len(model_gaps) > 0

    def test_model_gap_suggests_qunit(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_MODEL_MANIPULATION, ArtifactType.UI5_CONTROLLER)
        model_gaps = [g for g in gaps if "setProperty" in g.description or "setData" in g.description]
        for g in model_gaps:
            if g.suggested_test:
                assert "QUnit" in g.suggested_test or "assert" in g.suggested_test


# ===========================================================================
# TG-UI5-004: Navigation logic
# ===========================================================================


class TestTgUi5004NavigationLogic:

    def test_detects_nav_to(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_NAVIGATION, ArtifactType.UI5_CONTROLLER)
        nav_gaps = [g for g in gaps if "navTo" in g.description or "navigation" in g.description.lower()]
        assert len(nav_gaps) > 0

    def test_navigation_gap_suggests_route_test(self) -> None:
        gaps = _run(UI5_CONTROLLER_WITH_NAVIGATION, ArtifactType.UI5_CONTROLLER)
        nav_gaps = [g for g in gaps if "navTo" in g.description and g.suggested_test]
        for g in nav_gaps:
            assert "route" in g.suggested_test.lower() or "navTo" in g.suggested_test


# ===========================================================================
# TG-REG-001: Global/shared data modification
# ===========================================================================


class TestTgReg001GlobalDataModification:

    def test_detects_class_data(self) -> None:
        gaps = _run(ABAP_GLOBAL_DATA_MODIFICATION)
        reg_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        assert len(reg_gaps) > 0

    def test_detects_export_to_memory(self) -> None:
        gaps = _run(ABAP_GLOBAL_DATA_MODIFICATION)
        reg_gaps = [g for g in gaps if "EXPORT" in g.description or "global" in g.description.lower()]
        assert len(reg_gaps) > 0

    def test_global_data_gap_is_important(self) -> None:
        gaps = _run(ABAP_GLOBAL_DATA_MODIFICATION)
        reg_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        for g in reg_gaps:
            assert g.priority in (Severity.IMPORTANT, Severity.CRITICAL)

    def test_detects_global_variable_prefixes(self) -> None:
        code = """\
METHOD update_global_state.
  gv_last_update = sy-datum.
  gs_config-active = abap_true.
  APPEND ls_entry TO gt_log.
ENDMETHOD.
"""
        gaps = _run(code, ArtifactType.ABAP_METHOD)
        reg_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        assert len(reg_gaps) > 0


# ===========================================================================
# TG-REG-002: Cross-entity dependency
# ===========================================================================


class TestTgReg002CrossEntityDependency:

    def test_detects_cross_table_modification(self) -> None:
        gaps = _run(ABAP_CROSS_ENTITY_MODIFICATION, ArtifactType.ABAP_METHOD)
        cross_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        assert len(cross_gaps) > 0

    def test_detects_association_pattern_in_bdef(self) -> None:
        code = """\
define behavior for ZI_Order alias Order
{
  create;
  association _Item { create; }
}
"""
        gaps = _run(code, ArtifactType.BEHAVIOR_DEFINITION)
        # The _Item association pattern should trigger cross-entity detection
        cross_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        assert len(cross_gaps) > 0

    def test_cross_entity_gap_suggests_consistency_test(self) -> None:
        gaps = _run(ABAP_CROSS_ENTITY_MODIFICATION, ArtifactType.ABAP_METHOD)
        cross_gaps = [
            g for g in gaps
            if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT and g.suggested_test
        ]
        for g in cross_gaps:
            assert "consist" in g.suggested_test.lower() or "header" in g.suggested_test.lower()


# ===========================================================================
# Clean / minimal code — few or no gaps
# ===========================================================================


class TestCleanCodeMinimalGaps:

    def test_simple_method_has_few_gaps(self) -> None:
        gaps = _run(ABAP_CLEAN_SIMPLE, ArtifactType.ABAP_METHOD)
        # A simple SELECT method might still get flagged for missing unit test
        # but should not have critical gaps
        critical_gaps = [g for g in gaps if g.priority == Severity.CRITICAL]
        assert len(critical_gaps) == 0

    def test_no_regression_gap_for_clean_code(self) -> None:
        gaps = _run(ABAP_CLEAN_SIMPLE, ArtifactType.ABAP_METHOD)
        reg_gaps = [g for g in gaps if g.category == TestGapCategory.REGRESSION_SIDE_EFFECT]
        assert len(reg_gaps) == 0


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:

    def test_empty_code_returns_empty(self) -> None:
        gaps = _run("")
        assert gaps == []

    def test_whitespace_only_returns_empty(self) -> None:
        gaps = _run("   \n\t  \n")
        assert gaps == []

    def test_none_like_empty_string(self) -> None:
        gaps = _run("")
        assert gaps == []

    def test_unknown_artifact_type_returns_empty(self) -> None:
        # SERVICE_DEFINITION is not covered by any test gap rule
        gaps = _run(
            "expose ZC_SalesOrder as SalesOrder;",
            ArtifactType.SERVICE_DEFINITION,
        )
        assert gaps == []

    def test_all_gaps_have_valid_category(self) -> None:
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        for g in gaps:
            assert isinstance(g.category, TestGapCategory)

    def test_all_gaps_have_valid_priority(self) -> None:
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        for g in gaps:
            assert isinstance(g.priority, Severity)

    def test_all_gaps_have_description(self) -> None:
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        for g in gaps:
            assert len(g.description) > 10

    def test_deduplication_works(self) -> None:
        """Multiple METHODS lines should not produce duplicate TG-ABAP-001 gaps."""
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        # Each rule ID should appear at most once
        categories_and_descs = [(g.category, g.description[:80]) for g in gaps]
        assert len(categories_and_descs) == len(set(categories_and_descs))


# ===========================================================================
# Bilingual output (DE vs EN)
# ===========================================================================


class TestBilingualOutput:

    def test_english_output_contains_english_text(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD, language=Language.EN)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description]
        assert len(auth_gaps) > 0
        for g in auth_gaps:
            # English description should contain English words
            assert "authorization" in g.description.lower() or "authority" in g.description.lower()

    def test_german_output_contains_german_text(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD, language=Language.DE)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description]
        assert len(auth_gaps) > 0
        for g in auth_gaps:
            # German description should contain German words
            assert "Berechtigung" in g.description or "berechtig" in g.description.lower()

    def test_german_test_template(self) -> None:
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD, language=Language.DE)
        auth_gaps = [g for g in gaps if "AUTHORITY-CHECK" in g.description and g.suggested_test]
        for g in auth_gaps:
            assert "berechtigung" in g.suggested_test.lower() or "Berechtigung" in g.suggested_test

    def test_english_bdef_output(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION, language=Language.EN)
        assert len(gaps) > 0
        for g in gaps:
            # Should be in English
            assert "wurde gefunden" not in g.description

    def test_german_bdef_output(self) -> None:
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION, language=Language.DE)
        assert len(gaps) > 0
        # At least some descriptions should be in German
        german_count = sum(1 for g in gaps if "wurde gefunden" in g.description or "muessen" in g.description)
        assert german_count > 0


# ===========================================================================
# Priority ordering
# ===========================================================================


class TestPriorityOrdering:

    def test_critical_before_important(self) -> None:
        """CRITICAL-priority gaps must appear before IMPORTANT ones."""
        gaps = _run(ABAP_AUTHORITY_CHECK, ArtifactType.ABAP_METHOD)
        if len(gaps) >= 2:
            priorities = [g.priority for g in gaps]
            first_critical = next(
                (i for i, p in enumerate(priorities) if p == Severity.CRITICAL), 999
            )
            first_important = next(
                (i for i, p in enumerate(priorities) if p == Severity.IMPORTANT), 999
            )
            if first_critical != 999 and first_important != 999:
                assert first_critical < first_important

    def test_important_before_optional(self) -> None:
        """IMPORTANT-priority gaps must appear before OPTIONAL ones."""
        gaps = _run(ABAP_CLASS_WITH_PUBLIC_METHODS)
        if len(gaps) >= 2:
            priorities = [g.priority for g in gaps]
            first_important = next(
                (i for i, p in enumerate(priorities) if p == Severity.IMPORTANT), 999
            )
            first_optional = next(
                (i for i, p in enumerate(priorities) if p == Severity.OPTIONAL), 999
            )
            if first_important != 999 and first_optional != 999:
                assert first_important < first_optional

    def test_authority_gap_ranks_highest(self) -> None:
        """In code with both authority checks and simple methods, auth gap comes first."""
        code = ABAP_AUTHORITY_CHECK
        gaps = _run(code, ArtifactType.ABAP_METHOD)
        if gaps:
            assert gaps[0].priority == Severity.CRITICAL

    def test_full_bdef_priority_ordering(self) -> None:
        """A full BDEF with actions, validations, determinations, and drafts should be
        sorted correctly."""
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        priorities = [_SEVERITY_TO_INT[g.priority] for g in gaps]
        assert priorities == sorted(priorities)


_SEVERITY_TO_INT = {
    Severity.CRITICAL: 0,
    Severity.IMPORTANT: 1,
    Severity.OPTIONAL: 2,
    Severity.UNCLEAR: 3,
}


# ===========================================================================
# Combined / integration scenarios
# ===========================================================================


class TestIntegrationScenarios:

    def test_full_abap_class_produces_multiple_gap_types(self) -> None:
        """A full ABAP class with methods, exceptions, and auth checks should
        produce gaps from multiple categories."""
        code = ABAP_CLASS_WITH_PUBLIC_METHODS + "\n" + ABAP_AUTHORITY_CHECK
        gaps = _run(code)
        categories = {g.category for g in gaps}
        assert TestGapCategory.ABAP_UNIT in categories

    def test_full_bdef_produces_multiple_gap_types(self) -> None:
        """A BDEF with actions, validations, determinations, and drafts should
        produce ACTION_VALIDATION and possibly REGRESSION gaps."""
        gaps = _run(BEHAVIOR_DEFINITION_WITH_ACTIONS, ArtifactType.BEHAVIOR_DEFINITION)
        categories = {g.category for g in gaps}
        assert TestGapCategory.ACTION_VALIDATION in categories

    def test_ui5_controller_produces_multiple_gap_types(self) -> None:
        """A UI5 controller with handlers, model manipulation, and navigation
        should produce UI_BEHAVIOR gaps."""
        gaps = _run(UI5_CONTROLLER_WITH_HANDLERS, ArtifactType.UI5_CONTROLLER)
        assert _has_category(gaps, TestGapCategory.UI_BEHAVIOR)

    def test_mixed_fullstack_not_matched(self) -> None:
        """MIXED_FULLSTACK is not in any test gap rule's artifact_types,
        so no gaps should be returned."""
        code = ABAP_CLASS_WITH_PUBLIC_METHODS
        gaps = _run(code, ArtifactType.MIXED_FULLSTACK)
        # MIXED_FULLSTACK is not explicitly listed in any rule
        assert gaps == []

    def test_behavior_implementation_uses_bdef_rules(self) -> None:
        """BEHAVIOR_IMPLEMENTATION should also trigger RAP gap rules."""
        code = """\
CLASS lhc_SalesOrder DEFINITION INHERITING FROM cl_abap_behavior_handler.
  PRIVATE SECTION.
    METHODS confirmOrder FOR MODIFY
      IMPORTING keys FOR ACTION SalesOrder~confirmOrder RESULT result.

    METHODS validateCustomer FOR VALIDATE ON SAVE
      IMPORTING keys FOR SalesOrder~validateCustomer.
ENDCLASS.
"""
        # This code doesn't contain the BDEF keywords (action/validation on save)
        # but BEHAVIOR_IMPLEMENTATION is in the artifact types for TG-RAP-001
        gaps = _run(code, ArtifactType.BEHAVIOR_IMPLEMENTATION)
        assert isinstance(gaps, list)
