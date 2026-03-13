"""Curated example cases for the SAP ABAP/UI5 Review Assistant.

Each ``ExampleCase`` is a frozen dataclass containing realistic SAP code
and expected pipeline behavior metadata for validation tests and the
"Load Example" UI feature.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExampleCase:
    """A single, immutable example case with realistic SAP code.

    Parameters
    ----------
    case_id:
        Unique identifier, e.g. ``abap_clean_class``.
    title:
        English display title.
    title_de:
        German display title.
    description:
        English description of what this example demonstrates.
    description_de:
        German description.
    review_type:
        ReviewType enum value as string.
    artifact_type:
        ArtifactType enum value as string.
    review_context:
        ReviewContext enum value as string.
    code:
        Realistic SAP source code.
    expected_finding_count_min:
        Minimum expected findings from the pipeline.
    expected_finding_count_max:
        Maximum expected findings from the pipeline.
    expected_severities:
        Tuple of Severity values expected to appear in findings.
    expected_test_gap_categories:
        Tuple of TestGapCategory values expected.
    expected_risk_dimensions_above_low:
        RiskCategory values expected above LOW risk level.
    domain_tag:
        Optional domain tag for filtering.
    """

    case_id: str
    title: str
    title_de: str
    description: str
    description_de: str
    review_type: str
    artifact_type: str
    review_context: str
    code: str
    expected_finding_count_min: int
    expected_finding_count_max: int
    expected_severities: tuple[str, ...]
    expected_test_gap_categories: tuple[str, ...]
    expected_risk_dimensions_above_low: tuple[str, ...]
    domain_tag: str = ""


# ===========================================================================
# ABAP cases (5)
# ===========================================================================

ABAP_CLEAN_CLASS = ExampleCase(
    case_id="abap_clean_class",
    title="Clean OO ABAP Class",
    title_de="Saubere OO-ABAP-Klasse",
    description="Well-structured OO ABAP class with proper error handling, typed parameters, and inline declarations. Expect few or no findings.",
    description_de="Gut strukturierte OO-ABAP-Klasse mit korrekter Fehlerbehandlung, typisierten Parametern und Inline-Deklarationen. Wenige oder keine Befunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="ABAP_CLASS",
    review_context="GREENFIELD",
    code="""\
CLASS zcl_material_reader DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    METHODS get_material
      IMPORTING
        iv_matnr        TYPE matnr
      RETURNING
        VALUE(rs_mara)  TYPE mara
      RAISING
        zcx_not_found.

  PRIVATE SECTION.
    METHODS validate_input
      IMPORTING
        iv_matnr TYPE matnr
      RAISING
        zcx_not_found.
ENDCLASS.

CLASS zcl_material_reader IMPLEMENTATION.

  METHOD validate_input.
    IF iv_matnr IS INITIAL.
      RAISE EXCEPTION TYPE zcx_not_found.
    ENDIF.
  ENDMETHOD.

  METHOD get_material.
    validate_input( iv_matnr ).

    AUTHORITY-CHECK OBJECT 'M_MATE_MAR'
      ID 'ACTVT' FIELD '03'
      ID 'MATNR' FIELD iv_matnr.
    IF sy-subrc <> 0.
      RAISE EXCEPTION TYPE zcx_not_found.
    ENDIF.

    SELECT SINGLE *
      FROM mara
      WHERE matnr = @iv_matnr
      INTO @rs_mara.
    IF sy-subrc <> 0.
      RAISE EXCEPTION TYPE zcx_not_found.
    ENDIF.
  ENDMETHOD.

ENDCLASS.
""",
    expected_finding_count_min=0,
    expected_finding_count_max=2,
    expected_severities=(),
    expected_test_gap_categories=("ABAP_UNIT",),
    expected_risk_dimensions_above_low=(),
    domain_tag="MM",
)


ABAP_PROBLEMATIC_REPORT = ExampleCase(
    case_id="abap_problematic_report",
    title="Problematic ABAP Report",
    title_de="Problematischer ABAP-Report",
    description="Classic report with SELECT *, nested SELECTs in LOOP, no error handling, and WRITE statements. Expect 5-8 findings including CRITICAL and IMPORTANT.",
    description_de="Klassischer Report mit SELECT *, verschachtelten SELECTs in LOOP, fehlender Fehlerbehandlung und WRITE-Anweisungen. 5-8 Befunde erwartet, darunter CRITICAL und IMPORTANT.",
    review_type="SNIPPET_REVIEW",
    artifact_type="ABAP_REPORT",
    review_context="EXTENSION",
    code="""\
REPORT zrep_sales_list.

TABLES: vbak.

SELECT-OPTIONS: s_vkorg FOR vbak-vkorg.

START-OF-SELECTION.
  DATA: lt_orders TYPE TABLE OF vbak,
        ls_order  TYPE vbak,
        lt_items  TYPE TABLE OF vbap,
        ls_item   TYPE vbap.

  SELECT * FROM vbak INTO TABLE lt_orders.

  LOOP AT lt_orders INTO ls_order.
    SELECT * FROM vbap INTO TABLE lt_items
      WHERE vbeln = ls_order-vbeln.

    LOOP AT lt_items INTO ls_item.
      WRITE: / ls_order-vbeln, ls_item-posnr, ls_item-matnr, ls_item-netwr.
    ENDLOOP.
  ENDLOOP.

  WRITE: / 'Total orders:', lines( lt_orders ).
""",
    expected_finding_count_min=5,
    expected_finding_count_max=10,
    expected_severities=("CRITICAL", "IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=("REGRESSION_SIDE_EFFECT",),
    expected_risk_dimensions_above_low=("FUNCTIONAL", "UPGRADE_CLEAN_CORE"),
    domain_tag="SD",
)


ABAP_MISSING_AUTH = ExampleCase(
    case_id="abap_missing_auth",
    title="Missing AUTHORITY-CHECK",
    title_de="Fehlende AUTHORITY-CHECK",
    description="Method handling sensitive customer data without any AUTHORITY-CHECK. Expect CRITICAL security finding.",
    description_de="Methode die sensible Kundendaten verarbeitet ohne AUTHORITY-CHECK. CRITICAL-Sicherheitsbefund erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="ABAP_CLASS",
    review_context="GREENFIELD",
    code="""\
CLASS zcl_customer_export DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    METHODS export_customer_data
      IMPORTING
        iv_kunnr         TYPE kunnr
      RETURNING
        VALUE(rt_result) TYPE ztt_customer_export
      RAISING
        zcx_export_error.
ENDCLASS.

CLASS zcl_customer_export IMPLEMENTATION.

  METHOD export_customer_data.
    IF iv_kunnr IS INITIAL.
      RAISE EXCEPTION TYPE zcx_export_error.
    ENDIF.

    SELECT kunnr, name1, name2, stras, pstlz, ort01, land1, telf1
      FROM kna1
      WHERE kunnr = @iv_kunnr
      INTO TABLE @DATA(lt_customers).
    IF sy-subrc <> 0.
      RAISE EXCEPTION TYPE zcx_export_error.
    ENDIF.

    SELECT kunnr, bukrs, akont, zterm
      FROM knb1
      WHERE kunnr = @iv_kunnr
      INTO TABLE @DATA(lt_company).

    SELECT kunnr, vkorg, vtweg, spart, kdgrp
      FROM knvv
      WHERE kunnr = @iv_kunnr
      INTO TABLE @DATA(lt_sales).

    rt_result = CORRESPONDING #( lt_customers ).
  ENDMETHOD.

ENDCLASS.
""",
    expected_finding_count_min=1,
    expected_finding_count_max=5,
    expected_severities=("IMPORTANT",),
    expected_test_gap_categories=("ABAP_UNIT",),
    expected_risk_dimensions_above_low=("FUNCTIONAL",),
    domain_tag="SD",
)


ABAP_LEGACY_CODE = ExampleCase(
    case_id="abap_legacy_code",
    title="Legacy ABAP with Clean Core Issues",
    title_de="Legacy-ABAP mit Clean-Core-Problemen",
    description="Code with ENHANCEMENT-POINT, TABLES statement, obsolete MOVE/COMPUTE, and classic ALV. Expect clean-core and style findings.",
    description_de="Code mit ENHANCEMENT-POINT, TABLES-Anweisung, veraltetem MOVE/COMPUTE und klassischem ALV. Clean-Core- und Stilbefunde erwartet.",
    review_type="CLEAN_CORE_ARCHITECTURE_CHECK",
    artifact_type="ABAP_REPORT",
    review_context="REFACTORING",
    code="""\
REPORT zrep_legacy_stock.

TABLES: mard.

ENHANCEMENT-POINT zep_stock_01 SPOTS zspot_stock.

SELECT-OPTIONS: s_werks FOR mard-werks,
                s_lgort FOR mard-lgort.

DATA: gv_total TYPE mard-labst,
      gt_stock TYPE TABLE OF mard,
      gs_stock TYPE mard.

START-OF-SELECTION.
  SELECT * FROM mard
    INTO TABLE gt_stock
    WHERE werks IN s_werks
      AND lgort IN s_lgort.

  LOOP AT gt_stock INTO gs_stock.
    MOVE gs_stock-labst TO gv_total.
    COMPUTE gv_total = gv_total + gs_stock-insme.
  ENDLOOP.

  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
    EXPORTING
      i_structure_name = 'MARD'
    TABLES
      t_outtab         = gt_stock.
  IF sy-subrc <> 0.
    WRITE: / 'ALV display error'.
  ENDIF.
""",
    expected_finding_count_min=4,
    expected_finding_count_max=12,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=("ABAP_UNIT",),
    expected_risk_dimensions_above_low=("UPGRADE_CLEAN_CORE",),
    domain_tag="MM",
)


ABAP_COMPLEX_METHOD = ExampleCase(
    case_id="abap_complex_method",
    title="Complex Method with Deep Nesting",
    title_de="Komplexe Methode mit tiefer Verschachtelung",
    description="A 150+ line method with IF/LOOP nesting deeper than 4 levels. Expect structure and readability findings.",
    description_de="Eine 150+ Zeilen Methode mit IF/LOOP-Verschachtelung tiefer als 4 Ebenen. Struktur- und Lesbarkeitsbefunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="ABAP_CLASS",
    review_context="REFACTORING",
    code="""\
CLASS zcl_order_processor DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.
  PUBLIC SECTION.
    METHODS process_orders
      IMPORTING
        it_orders TYPE ztt_order_data
      RETURNING
        VALUE(rt_results) TYPE ztt_process_result.
ENDCLASS.

CLASS zcl_order_processor IMPLEMENTATION.
  METHOD process_orders.
    DATA: lv_status TYPE c LENGTH 1,
          lv_total  TYPE p DECIMALS 2,
          lv_tax    TYPE p DECIMALS 2,
          lv_disc   TYPE p DECIMALS 2.

    LOOP AT it_orders INTO DATA(ls_order).
      IF ls_order-order_type = 'OR'.
        IF ls_order-sales_org IS NOT INITIAL.
          SELECT SINGLE vkorg
            FROM tvko
            WHERE vkorg = @ls_order-sales_org
            INTO @DATA(lv_vkorg).
          IF sy-subrc = 0.
            LOOP AT ls_order-items INTO DATA(ls_item).
              IF ls_item-matnr IS NOT INITIAL.
                IF ls_item-quantity > 0.
                  IF ls_item-price > 0.
                    lv_total = ls_item-quantity * ls_item-price.
                    IF ls_order-tax_code IS NOT INITIAL.
                      CASE ls_order-tax_code.
                        WHEN 'V1'.
                          lv_tax = lv_total * '0.19'.
                        WHEN 'V2'.
                          lv_tax = lv_total * '0.07'.
                        WHEN OTHERS.
                          lv_tax = 0.
                      ENDCASE.
                      IF ls_order-discount_pct > 0.
                        lv_disc = lv_total * ls_order-discount_pct / 100.
                        lv_total = lv_total - lv_disc + lv_tax.
                      ELSE.
                        lv_total = lv_total + lv_tax.
                      ENDIF.
                    ENDIF.
                    lv_status = 'S'.
                  ELSE.
                    lv_status = 'E'.
                  ENDIF.
                ELSE.
                  lv_status = 'E'.
                ENDIF.
              ELSE.
                lv_status = 'E'.
              ENDIF.
              APPEND VALUE #(
                order_id = ls_order-order_id
                item_id  = ls_item-item_id
                status   = lv_status
                amount   = lv_total
              ) TO rt_results.
              CLEAR: lv_total, lv_tax, lv_disc, lv_status.
            ENDLOOP.
          ENDIF.
        ENDIF.
      ELSEIF ls_order-order_type = 'RE'.
        LOOP AT ls_order-items INTO ls_item.
          IF ls_item-quantity > 0.
            lv_total = ls_item-quantity * ls_item-price * -1.
            APPEND VALUE #(
              order_id = ls_order-order_id
              item_id  = ls_item-item_id
              status   = 'R'
              amount   = lv_total
            ) TO rt_results.
          ENDIF.
        ENDLOOP.
      ENDIF.
    ENDLOOP.

    DATA lv_dummy_01 TYPE i.
    DATA lv_dummy_02 TYPE i.
    DATA lv_dummy_03 TYPE i.
    DATA lv_dummy_04 TYPE i.
    DATA lv_dummy_05 TYPE i.
    DATA lv_dummy_06 TYPE i.
    DATA lv_dummy_07 TYPE i.
    DATA lv_dummy_08 TYPE i.
    DATA lv_dummy_09 TYPE i.
    DATA lv_dummy_10 TYPE i.
    DATA lv_dummy_11 TYPE i.
    DATA lv_dummy_12 TYPE i.
    DATA lv_dummy_13 TYPE i.
    DATA lv_dummy_14 TYPE i.
    DATA lv_dummy_15 TYPE i.
    DATA lv_dummy_16 TYPE i.
    DATA lv_dummy_17 TYPE i.
    DATA lv_dummy_18 TYPE i.
    DATA lv_dummy_19 TYPE i.
    DATA lv_dummy_20 TYPE i.
    DATA lv_dummy_21 TYPE i.
    DATA lv_dummy_22 TYPE i.
    DATA lv_dummy_23 TYPE i.
    DATA lv_dummy_24 TYPE i.
    DATA lv_dummy_25 TYPE i.
    DATA lv_dummy_26 TYPE i.
    DATA lv_dummy_27 TYPE i.
    DATA lv_dummy_28 TYPE i.
    DATA lv_dummy_29 TYPE i.
    DATA lv_dummy_30 TYPE i.
    DATA lv_dummy_31 TYPE i.
    DATA lv_dummy_32 TYPE i.
    DATA lv_dummy_33 TYPE i.
    DATA lv_dummy_34 TYPE i.
    DATA lv_dummy_35 TYPE i.
    DATA lv_dummy_36 TYPE i.
    DATA lv_dummy_37 TYPE i.
    DATA lv_dummy_38 TYPE i.
    DATA lv_dummy_39 TYPE i.
    DATA lv_dummy_40 TYPE i.
  ENDMETHOD.
ENDCLASS.
""",
    expected_finding_count_min=2,
    expected_finding_count_max=8,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=("ABAP_UNIT",),
    expected_risk_dimensions_above_low=("FUNCTIONAL",),
    domain_tag="SD",
)


# ===========================================================================
# CDS cases (3)
# ===========================================================================

CDS_CLEAN_VIEW = ExampleCase(
    case_id="cds_clean_view",
    title="Clean CDS View Entity",
    title_de="Saubere CDS View Entity",
    description="Well-annotated CDS view entity with key fields, access control, and search annotations. Expect few or no findings.",
    description_de="Gut annotierte CDS View Entity mit Schluesselfeldern, Zugriffssteuerung und Such-Annotationen. Wenige oder keine Befunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="CDS_VIEW",
    review_context="GREENFIELD",
    code="""\
@AbapCatalog.viewEnhancementCategory: [#NONE]
@AccessControl.authorizationCheck: #CHECK
@EndUserText.label: 'Sales Order Header'
@Search.searchable: true

define view entity ZI_SalesOrderHeader
  as select from vbak
  association [0..*] to ZI_SalesOrderItem as _Item
    on $projection.SalesOrder = _Item.SalesOrder
{
      @Search.defaultSearchElement: true
  key vbeln as SalesOrder,

      @Search.defaultSearchElement: true
      erdat as CreatedOn,

      auart as SalesOrderType,
      vkorg as SalesOrganization,
      vtweg as DistributionChannel,
      spart as Division,
      kunnr as SoldToParty,

      @Semantics.amount.currencyCode: 'Currency'
      netwr as NetAmount,
      waerk as Currency,

      ernam as CreatedBy,

      _Item
}
""",
    expected_finding_count_min=0,
    expected_finding_count_max=2,
    expected_severities=(),
    expected_test_gap_categories=(),
    expected_risk_dimensions_above_low=(),
    domain_tag="SD",
)


CDS_MISSING_ANNOTATIONS = ExampleCase(
    case_id="cds_missing_annotations",
    title="CDS View Missing Annotations",
    title_de="CDS View mit fehlenden Annotationen",
    description="CDS view entity without @AbapCatalog, @AccessControl, @Search annotations. Expect 3-5 annotation findings.",
    description_de="CDS View Entity ohne @AbapCatalog, @AccessControl, @Search-Annotationen. 3-5 Annotationsbefunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="CDS_VIEW",
    review_context="GREENFIELD",
    code="""\
@EndUserText.label: 'Purchase Order Header'

define view entity ZI_PurchaseOrderHeader
  as select from ekko
{
  key ebeln as PurchaseOrder,
      bukrs as CompanyCode,
      bstyp as DocumentCategory,
      bsart as DocumentType,
      lifnr as Supplier,
      ekorg as PurchasingOrganization,
      ekgrp as PurchasingGroup,
      bedat as DocumentDate,
      waers as Currency,
      rlwrt as TotalNetValue
}
""",
    expected_finding_count_min=3,
    expected_finding_count_max=6,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=(),
    expected_risk_dimensions_above_low=("FUNCTIONAL",),
    domain_tag="MM",
)


CDS_PROJECTION_ISSUES = ExampleCase(
    case_id="cds_projection_issues",
    title="CDS Projection with Issues",
    title_de="CDS Projection mit Problemen",
    description="CDS projection view without associations, without @UI annotations, and without search annotations. Expect multiple annotation and structure findings.",
    description_de="CDS Projection View ohne Associations, ohne @UI-Annotationen und ohne Such-Annotationen. Mehrere Annotations- und Strukturbefunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="CDS_PROJECTION",
    review_context="GREENFIELD",
    code="""\
@EndUserText.label: 'Material Projection'

define root view entity C_MaterialProjection
  as projection on ZI_Material
{
  key MaterialNumber,
      MaterialDescription,
      MaterialType,
      MaterialGroup,
      BaseUnit,
      Division,
      GrossWeight,
      NetWeight,
      WeightUnit
}
""",
    expected_finding_count_min=2,
    expected_finding_count_max=7,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=(),
    expected_risk_dimensions_above_low=("FUNCTIONAL",),
    domain_tag="MM",
)


# ===========================================================================
# Behavior Definition cases (2)
# ===========================================================================

BDEF_STANDARD = ExampleCase(
    case_id="bdef_standard",
    title="Standard Managed Behavior Definition",
    title_de="Standard Managed Behavior Definition",
    description="Standard managed BDEF with actions and validations. Expect test gap findings for action and validation tests.",
    description_de="Standard Managed BDEF mit Aktionen und Validierungen. Test-Gap-Befunde fuer Aktions- und Validierungstests erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="BEHAVIOR_DEFINITION",
    review_context="GREENFIELD",
    code="""\
managed implementation in class zbp_i_salesorder unique;
strict ( 2 );

define behavior for ZI_SalesOrder alias SalesOrder
persistent table zsalesorder
lock master
authorization master ( instance )
etag master LocalLastChangedAt
{
  field ( readonly ) SalesOrderUUID, LocalCreatedAt, LocalLastChangedAt;
  field ( mandatory ) SoldToParty, SalesOrganization;

  create;
  update;
  delete;

  action ( features : instance ) approveSalesOrder result [1] $self;
  action ( features : instance ) rejectSalesOrder result [1] $self;

  validation validateSoldToParty on save
    { create; update; field SoldToParty; }

  validation validateDates on save
    { create; update; field RequestedDeliveryDate; }

  mapping for zsalesorder corresponding;
}
""",
    expected_finding_count_min=0,
    expected_finding_count_max=3,
    expected_severities=(),
    expected_test_gap_categories=("ACTION_VALIDATION",),
    expected_risk_dimensions_above_low=("TESTABILITY",),
    domain_tag="SD",
)


BDEF_COMPLEX = ExampleCase(
    case_id="bdef_complex",
    title="Complex BDEF with Draft and Determinations",
    title_de="Komplexe BDEF mit Draft und Determinierungen",
    description="Complex BDEF with draft handling, determinations, multiple validations. Expect multiple test gap categories.",
    description_de="Komplexe BDEF mit Draft-Handling, Determinierungen, mehreren Validierungen. Mehrere Test-Gap-Kategorien erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="BEHAVIOR_DEFINITION",
    review_context="GREENFIELD",
    code="""\
managed implementation in class zbp_i_traveltp unique;
strict ( 2 );
with draft;

define behavior for ZI_TravelTP alias Travel
persistent table ztravel
draft table zdtravel
lock master total etag LastChangedAt
authorization master ( instance )
etag master LocalLastChangedAt
{
  field ( readonly ) TravelUUID, LocalCreatedAt, LocalLastChangedAt, LastChangedAt;
  field ( mandatory ) AgencyID, CustomerID;

  create;
  update;
  delete;

  draft action Edit;
  draft action Activate optimized;
  draft action Discard;
  draft action Resume;
  draft determine action Prepare
  {
    validation validateCustomer;
    validation validateDates;
    validation validateAgency;
  }

  action ( features : instance ) acceptTravel result [1] $self;
  action ( features : instance ) rejectTravel result [1] $self;
  action ( features : instance ) deductDiscount parameter /dmo/a_travel_discount result [1] $self;

  validation validateCustomer on save { create; update; field CustomerID; }
  validation validateDates on save { create; update; field BeginDate, EndDate; }
  validation validateAgency on save { create; update; field AgencyID; }

  determination setStatusOpen on modify { create; }
  determination calculateTotalPrice on modify { field BookingFee, CurrencyCode; }

  association _Booking { create; with draft; }

  mapping for ztravel corresponding;
}
""",
    expected_finding_count_min=0,
    expected_finding_count_max=3,
    expected_severities=(),
    expected_test_gap_categories=("ACTION_VALIDATION",),
    expected_risk_dimensions_above_low=("TESTABILITY",),
    domain_tag="TRAVEL",
)


# ===========================================================================
# UI5 cases (3)
# ===========================================================================

UI5_CLEAN_CONTROLLER = ExampleCase(
    case_id="ui5_clean_controller",
    title="Clean UI5 Controller",
    title_de="Sauberer UI5 Controller",
    description="Well-structured UI5 controller with onInit, proper error handling, and framework-compliant patterns. Expect minimal findings.",
    description_de="Gut strukturierter UI5 Controller mit onInit, korrekter Fehlerbehandlung und framework-konformen Mustern. Minimale Befunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="UI5_CONTROLLER",
    review_context="GREENFIELD",
    code="""\
sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/m/MessageBox",
  "sap/m/MessageToast",
  "sap/ui/model/json/JSONModel"
], function (Controller, MessageBox, MessageToast, JSONModel) {
  "use strict";

  return Controller.extend("com.myapp.controller.SalesOrder", {

    onInit: function () {
      var oViewModel = new JSONModel({
        busy: false,
        editable: false
      });
      this.getView().setModel(oViewModel, "viewModel");

      this.getRouter().getRoute("salesOrder").attachPatternMatched(
        this._onObjectMatched, this
      );
    },

    _onObjectMatched: function (oEvent) {
      var sSalesOrder = oEvent.getParameter("arguments").salesOrder;
      this.getView().bindElement({
        path: "/SalesOrderSet('" + sSalesOrder + "')",
        events: {
          dataRequested: function () {
            this.getView().getModel("viewModel").setProperty("/busy", true);
          }.bind(this),
          dataReceived: function () {
            this.getView().getModel("viewModel").setProperty("/busy", false);
          }.bind(this)
        }
      });
    },

    onSave: function () {
      var oModel = this.getView().getModel();
      this.getView().getModel("viewModel").setProperty("/busy", true);
      oModel.submitChanges({
        success: function () {
          this.getView().getModel("viewModel").setProperty("/busy", false);
          MessageToast.show("Saved successfully");
        }.bind(this),
        error: function (oError) {
          this.getView().getModel("viewModel").setProperty("/busy", false);
          MessageBox.error("Save failed: " + oError.message);
        }.bind(this)
      });
    },

    getRouter: function () {
      return this.getOwnerComponent().getRouter();
    }
  });
});
""",
    expected_finding_count_min=0,
    expected_finding_count_max=3,
    expected_severities=(),
    expected_test_gap_categories=("UI_BEHAVIOR",),
    expected_risk_dimensions_above_low=(),
    domain_tag="SD",
)


UI5_PROBLEMATIC_CONTROLLER = ExampleCase(
    case_id="ui5_problematic_controller",
    title="Problematic UI5 Controller",
    title_de="Problematischer UI5 Controller",
    description="Controller with hardcoded strings, no error handling on OData calls, jQuery DOM manipulation, and deprecated sap.ui.getCore(). Expect 5+ findings.",
    description_de="Controller mit hartcodierten Strings, fehlender Fehlerbehandlung bei OData-Aufrufen, jQuery-DOM-Manipulation und veraltetem sap.ui.getCore(). 5+ Befunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="UI5_CONTROLLER",
    review_context="BUGFIX",
    code="""\
sap.ui.define([
  "sap/ui/core/mvc/Controller"
], function (Controller) {
  "use strict";

  return Controller.extend("com.myapp.controller.BadExample", {

    onPress: function () {
      var sPath = "/SalesOrderSet('12345')";
      var oModel = this.getView().getModel();
      oModel.read(sPath);

      jQuery("#myCustomDiv").css("background-color", "red");
      $(".sapMList").hide();

      var oCore = sap.ui.getCore();
      var oMsgMgr = oCore.getMessageManager();

      document.getElementById("someElement").style.display = "none";
    },

    onDelete: function () {
      var oModel = this.getView().getModel();
      oModel.remove("/SalesOrderSet('99999')");
      alert("Deleted!");
    },

    formatStatus: function (sStatus) {
      if (sStatus === "A") return "Approved";
      if (sStatus === "R") return "Rejected";
      return "Pending";
    }
  });
});
""",
    expected_finding_count_min=4,
    expected_finding_count_max=10,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=("UI_BEHAVIOR",),
    expected_risk_dimensions_above_low=("FUNCTIONAL", "MAINTAINABILITY"),
    domain_tag="SD",
)


UI5_VIEW_ISSUES = ExampleCase(
    case_id="ui5_view_issues",
    title="UI5 XML View with Issues",
    title_de="UI5 XML View mit Problemen",
    description="XML view with complex expression bindings, hardcoded text strings, and inline styles. Expect i18n and readability findings.",
    description_de="XML View mit komplexen Expression-Bindings, hartcodierten Textstrings und Inline-Styles. i18n- und Lesbarkeitsbefunde erwartet.",
    review_type="SNIPPET_REVIEW",
    artifact_type="UI5_VIEW",
    review_context="EXTENSION",
    code="""\
<mvc:View
  xmlns:mvc="sap.ui.core.mvc"
  xmlns="sap.m"
  xmlns:core="sap.ui.core"
  controllerName="com.myapp.controller.Detail"
>
  <Page title="Sales Order Details">
    <content>
      <VBox class="sapUiSmallMargin">
        <Label text="Order Number" />
        <Text text="{SalesOrder}" />

        <Label text="Status" />
        <ObjectStatus
          text="{= ${Status} === 'A' ? 'Approved' : ${Status} === 'R' ? 'Rejected' : 'Pending' }"
          state="{= ${Status} === 'A' ? 'Success' : ${Status} === 'R' ? 'Error' : 'Warning' }"
        />

        <Label text="Total Amount" />
        <Text text="{NetAmount} {Currency}" />

        <Button text="Save Changes" press="onSave" type="Emphasized" />
        <Button text="Delete Order" press="onDelete" type="Reject" />
        <Button text="Cancel" press="onCancel" />
      </VBox>
    </content>
  </Page>
</mvc:View>
""",
    expected_finding_count_min=2,
    expected_finding_count_max=7,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=(),
    expected_risk_dimensions_above_low=(),
    domain_tag="SD",
)


# ===========================================================================
# Mixed / Edge cases (2)
# ===========================================================================

MIXED_FULLSTACK_CHANGE = ExampleCase(
    case_id="mixed_fullstack_change",
    title="Mixed Fullstack Change (CDS + ABAP)",
    title_de="Gemischte Fullstack-Aenderung (CDS + ABAP)",
    description="Code containing both a CDS view entity and an ABAP class. Tests mixed artifact detection and combined findings.",
    description_de="Code mit CDS View Entity und ABAP-Klasse. Testet gemischte Artefakterkennung und kombinierte Befunde.",
    review_type="SNIPPET_REVIEW",
    artifact_type="MIXED_FULLSTACK",
    review_context="GREENFIELD",
    code="""\
* --- CDS View Entity ---
@EndUserText.label: 'Delivery Item View'
define view entity ZI_DeliveryItem
  as select from lips
{
  key vbeln as DeliveryNumber,
  key posnr as DeliveryItem,
      matnr as Material,
      lfimg as DeliveredQuantity,
      meins as BaseUnit
}

* --- ABAP Service Class ---
CLASS zcl_delivery_service DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.
  PUBLIC SECTION.
    METHODS get_items
      IMPORTING
        iv_vbeln TYPE vbeln
      RETURNING
        VALUE(rt_items) TYPE ztt_delivery_item.
ENDCLASS.

CLASS zcl_delivery_service IMPLEMENTATION.
  METHOD get_items.
    SELECT * FROM lips
      WHERE vbeln = @iv_vbeln
      INTO TABLE @DATA(lt_items).
    rt_items = CORRESPONDING #( lt_items ).
  ENDMETHOD.
ENDCLASS.
""",
    expected_finding_count_min=2,
    expected_finding_count_max=10,
    expected_severities=("IMPORTANT", "OPTIONAL"),
    expected_test_gap_categories=(),
    expected_risk_dimensions_above_low=("FUNCTIONAL",),
    domain_tag="LE",
)


EMPTY_EDGE_CASE = ExampleCase(
    case_id="empty_edge_case",
    title="Minimal / Ambiguous Code Snippet",
    title_de="Minimaler / Mehrdeutiger Code-Schnipsel",
    description="Very short code snippet that is hard to classify. Tests pipeline resilience and edge case handling.",
    description_de="Sehr kurzer Code-Schnipsel der schwer zu klassifizieren ist. Testet Pipeline-Resilienz und Grenzfallbehandlung.",
    review_type="SNIPPET_REVIEW",
    artifact_type="ABAP_METHOD",
    review_context="GREENFIELD",
    code="""\
METHOD calculate_tax.
  DATA(lv_rate) = COND #(
    WHEN iv_country = 'DE' THEN '0.19'
    WHEN iv_country = 'AT' THEN '0.20'
    WHEN iv_country = 'CH' THEN '0.077'
    ELSE '0.00'
  ).
  rv_tax = iv_amount * lv_rate.
ENDMETHOD.
""",
    expected_finding_count_min=0,
    expected_finding_count_max=3,
    expected_severities=(),
    expected_test_gap_categories=("ABAP_UNIT",),
    expected_risk_dimensions_above_low=(),
    domain_tag="FI",
)


# ===========================================================================
# Registry -- all example cases
# ===========================================================================

ALL_EXAMPLE_CASES: tuple[ExampleCase, ...] = (
    ABAP_CLEAN_CLASS,
    ABAP_PROBLEMATIC_REPORT,
    ABAP_MISSING_AUTH,
    ABAP_LEGACY_CODE,
    ABAP_COMPLEX_METHOD,
    CDS_CLEAN_VIEW,
    CDS_MISSING_ANNOTATIONS,
    CDS_PROJECTION_ISSUES,
    BDEF_STANDARD,
    BDEF_COMPLEX,
    UI5_CLEAN_CONTROLLER,
    UI5_PROBLEMATIC_CONTROLLER,
    UI5_VIEW_ISSUES,
    MIXED_FULLSTACK_CHANGE,
    EMPTY_EDGE_CASE,
)

EXAMPLE_CASES_BY_ID: dict[str, ExampleCase] = {
    case.case_id: case for case in ALL_EXAMPLE_CASES
}
