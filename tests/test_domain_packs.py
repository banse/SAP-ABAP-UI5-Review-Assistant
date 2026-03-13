"""Tests for domain-specific rule packs (Yard, EWM, Service, MII/MES).

Covers domain detection, positive rule firing on realistic domain code,
and negative tests ensuring clean code does not trigger domain rules.
"""

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
from app.rules.domains import detect_domain


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
# Domain detection tests
# ===========================================================================


class TestDomainDetection:
    def test_detect_yard_from_gate_process(self) -> None:
        code = "CALL METHOD lo_yard->gate_in( iv_trailer = lv_trailer )."
        assert detect_domain(code) == "YARD"

    def test_detect_yard_from_dock_assign(self) -> None:
        code = "lo_mgr->dock_assign( iv_dock_door = lv_door )."
        assert detect_domain(code) == "YARD"

    def test_detect_ewm_from_warehouse_task(self) -> None:
        code = "lo_wm->warehouse_task_confirm( iv_lgnum = lv_lgnum )."
        assert detect_domain(code) == "EWM"

    def test_detect_ewm_from_handling_unit(self) -> None:
        code = "DATA: lv_hu TYPE handling_unit. lo_ewm->hu_check( lv_hu )."
        assert detect_domain(code) == "EWM"

    def test_detect_ewm_from_scwm(self) -> None:
        code = "CALL FUNCTION '/SCWM/TO_CONFIRM'."
        assert detect_domain(code) == "EWM"

    def test_detect_service_from_service_order(self) -> None:
        code = "lo_svc->create_service_order( iv_equipment = lv_equi )."
        assert detect_domain(code) == "SERVICE"

    def test_detect_service_from_warranty(self) -> None:
        code = "IF ls_contract-warranty IS NOT INITIAL."
        assert detect_domain(code) == "SERVICE"

    def test_detect_service_from_technician(self) -> None:
        code = "lo_plan->technician_assign( iv_tech_id = lv_tech )."
        assert detect_domain(code) == "SERVICE"

    def test_detect_mii_from_production_order(self) -> None:
        code = "lo_mes->prod_confirm( iv_aufnr = lv_aufnr )."
        assert detect_domain(code) == "MII_MES"

    def test_detect_mii_from_plc_call(self) -> None:
        code = "lo_shop->plc_call( iv_signal = lv_signal )."
        assert detect_domain(code) == "MII_MES"

    def test_detect_mii_from_shopfloor(self) -> None:
        code = "DATA: lo_ui TYPE REF TO zcl_shopfloor_ui."
        assert detect_domain(code) == "MII_MES"

    def test_detect_none_for_generic_code(self) -> None:
        code = (
            "CLASS zcl_generic IMPLEMENTATION.\n"
            "  METHOD run.\n"
            "    DATA lv_x TYPE i.\n"
            "    lv_x = 42.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        assert detect_domain(code) is None

    def test_detect_none_for_empty_code(self) -> None:
        assert detect_domain("") is None

    def test_detect_with_context_summary(self) -> None:
        code = "DATA lv_x TYPE i."
        context = "This is a yard management gate process enhancement."
        assert detect_domain(code, context) == "YARD"


# ===========================================================================
# Yard rule tests (DOM-YARD-*)
# ===========================================================================


class TestYard001GateTiming:
    def test_gate_in_without_timing(self) -> None:
        code = (
            "METHOD process_arrival.\n"
            "  lo_yard->gate_in( iv_trailer = lv_trailer ).\n"
            "  lo_yard->assign_dock( iv_dock = lv_dock ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-001")

    def test_gate_in_with_timing_clean(self) -> None:
        code = (
            "METHOD process_arrival.\n"
            "  DATA lv_ts TYPE timestamp.\n"
            "  GET TIME STAMP FIELD lv_ts.\n"
            "  IF lv_ts < lv_arrival_time.\n"
            "    RAISE EXCEPTION TYPE zcx_invalid_time.\n"
            "  ENDIF.\n"
            "  lo_yard->gate_in( iv_trailer = lv_trailer ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-001")


class TestYard002CarrierErrorHandling:
    def test_carrier_api_without_try(self) -> None:
        code = (
            "METHOD notify_carrier.\n"
            "  lo_api->carrier_api( iv_scac = lv_scac ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-002")

    def test_carrier_api_with_try_clean(self) -> None:
        code = (
            "METHOD notify_carrier.\n"
            "  TRY.\n"
            "    lo_api->carrier_api( iv_scac = lv_scac ).\n"
            "  CATCH zcx_carrier_error INTO DATA(lx).\n"
            "    MESSAGE lx->get_text( ) TYPE 'E'.\n"
            "  ENDTRY.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-002")


class TestYard003SlotConcurrency:
    def test_slot_book_without_lock(self) -> None:
        code = (
            "METHOD book_slot.\n"
            "  lo_mgr->slot_book( iv_slot = lv_slot iv_time = lv_time ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-003")

    def test_slot_book_with_enqueue_clean(self) -> None:
        code = (
            "METHOD book_slot.\n"
            "  CALL FUNCTION 'ENQUEUE_EZYARD_SLOT'\n"
            "    EXPORTING iv_slot = lv_slot.\n"
            "  IF sy-subrc = 0.\n"
            "    lo_mgr->slot_book( iv_slot = lv_slot iv_time = lv_time ).\n"
            "  ENDIF.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-003")


class TestYard004RfComplexity:
    def test_rf_screen_with_many_fields(self) -> None:
        code = (
            "METHOD display_rf_screen.\n"
            "  PARAMETERS p1 TYPE c.\n"
            "  PARAMETERS p2 TYPE c.\n"
            "  PARAMETERS p3 TYPE c.\n"
            "  PARAMETERS p4 TYPE c.\n"
            "  PARAMETERS p5 TYPE c.\n"
            "  PARAMETERS p6 TYPE c.\n"
            "  WRITE: / 'RF Screen: ', rf_screen.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-004")

    def test_rf_screen_simple_clean(self) -> None:
        code = (
            "METHOD display_rf_screen.\n"
            "  DATA lv_barcode TYPE c.\n"
            "  WRITE: / 'Scan: ', rf_screen.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-004")


class TestYard005TaskSequencing:
    def test_yard_task_without_predecessor(self) -> None:
        code = (
            "METHOD create_task.\n"
            "  lo_mgr->create_yard_task( iv_type = 'MOVE' ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-005")

    def test_yard_task_with_predecessor_clean(self) -> None:
        code = (
            "METHOD create_task.\n"
            "  lo_mgr->check_predecessor( iv_task = lv_prev ).\n"
            "  lo_mgr->create_yard_task( iv_type = 'MOVE' ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-005")


class TestYard006CheckinCheckout:
    def test_checkin_without_checkout(self) -> None:
        code = (
            "METHOD process_vehicle.\n"
            "  lo_yard->check_in( iv_vehicle = lv_vehicle ).\n"
            "  lo_yard->assign_dock( iv_dock = lv_dock ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-YARD-006")

    def test_checkin_with_checkout_clean(self) -> None:
        code = (
            "METHOD process_vehicle.\n"
            "  lo_yard->check_in( iv_vehicle = lv_vehicle ).\n"
            "  lo_yard->load_trailer( ).\n"
            "  lo_yard->check_out( iv_vehicle = lv_vehicle ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-YARD-006")


# ===========================================================================
# EWM rule tests (DOM-EWM-*)
# ===========================================================================


class TestEwm001WtHuValidation:
    def test_wt_confirm_without_hu(self) -> None:
        code = (
            "METHOD confirm_task.\n"
            "  lo_wm->wt_confirm( iv_tanum = lv_tanum ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-001")

    def test_wt_confirm_with_hu_clean(self) -> None:
        code = (
            "METHOD confirm_task.\n"
            "  lo_wm->hu_check( iv_exidv = lv_hu ).\n"
            "  lo_wm->wt_confirm( iv_tanum = lv_tanum ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-001")


class TestEwm002BatchProcessing:
    def test_mass_transfer_without_batch(self) -> None:
        code = (
            "METHOD run_mass_transfer.\n"
            "  lo_wm->mass_stock_transfer( it_items = lt_items ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-002")

    def test_mass_transfer_with_commit_clean(self) -> None:
        code = (
            "METHOD run_mass_transfer.\n"
            "  LOOP AT lt_packets INTO DATA(ls_pkt).\n"
            "    lo_wm->mass_stock_transfer( it_items = ls_pkt-items ).\n"
            "    COMMIT WORK AND WAIT.\n"
            "  ENDLOOP.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-002")


class TestEwm003StockConsistency:
    def test_goods_movement_without_check(self) -> None:
        code = (
            "METHOD post_movement.\n"
            "  lo_wm->goods_movement( iv_bwart = '311' ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-003")

    def test_goods_movement_with_consistency_clean(self) -> None:
        code = (
            "METHOD post_movement.\n"
            "  lo_wm->check_availability( iv_matnr = lv_matnr ).\n"
            "  lo_wm->goods_movement( iv_bwart = '311' ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-003")


class TestEwm004MovementTypeHardcoding:
    def test_bwart_with_hardcoded_value(self) -> None:
        code = (
            "METHOD post_goods.\n"
            "  ls_header-bwart = '101'.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-004")

    def test_bwart_with_constant_clean(self) -> None:
        code = (
            "METHOD post_goods.\n"
            "  ls_header-bwart = gc_mvt_goods_receipt.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-004")


class TestEwm005BinValidation:
    def test_put_away_without_bin_check(self) -> None:
        code = (
            "METHOD put_away_stock.\n"
            "  lo_wm->put_away( iv_lgpla = lv_bin ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-005")

    def test_put_away_with_bin_check_clean(self) -> None:
        code = (
            "METHOD put_away_stock.\n"
            "  lo_wm->bin_exist( iv_lgpla = lv_bin ).\n"
            "  lo_wm->put_away( iv_lgpla = lv_bin ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-005")


class TestEwm006RfPerformance:
    def test_rf_with_many_selects(self) -> None:
        code = (
            "METHOD rf_process.\n"
            "  DATA lv_rf TYPE rf_screen.\n"
            "  SELECT matnr FROM mara INTO @DATA(lv1) WHERE matnr = @lv_m.\n"
            "  SELECT lgort FROM mard INTO @DATA(lv2) WHERE matnr = @lv_m.\n"
            "  SELECT lgpla FROM lagp INTO @DATA(lv3) WHERE lgpla = @lv_b.\n"
            "  SELECT charg FROM mch1 INTO @DATA(lv4) WHERE matnr = @lv_m.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-EWM-006")

    def test_rf_with_single_select_clean(self) -> None:
        code = (
            "METHOD rf_process.\n"
            "  DATA lv_rf TYPE rf_screen.\n"
            "  SELECT matnr FROM mara INTO @DATA(lv1) WHERE matnr = @lv_m.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-EWM-006")


# ===========================================================================
# Service Management rule tests (DOM-SVC-*)
# ===========================================================================


class TestSvc001ApprovalFlow:
    def test_approval_without_reject(self) -> None:
        code = (
            "METHOD handle_approval.\n"
            "  lo_svc->service_order_approve( iv_order = lv_order ).\n"
            "  lo_svc->update_status( iv_status = 'APPROVED' ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-SVC-001")

    def test_approval_with_reject_clean(self) -> None:
        code = (
            "METHOD handle_approval.\n"
            "  IF iv_decision = 'APPROVE'.\n"
            "    lo_svc->service_order_approve( iv_order = lv_order ).\n"
            "  ELSE.\n"
            "    lo_svc->reject( iv_order = lv_order ).\n"
            "  ENDIF.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-SVC-001")


class TestSvc002WarrantySla:
    def test_service_order_without_sla(self) -> None:
        code = (
            "METHOD create_order.\n"
            "  lo_svc->create_service_order( iv_equi = lv_equi ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-SVC-002")

    def test_service_order_with_sla_clean(self) -> None:
        code = (
            "METHOD create_order.\n"
            "  lo_svc->determine_sla( iv_contract = lv_contract ).\n"
            "  lo_svc->create_service_order( iv_equi = lv_equi ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-SVC-002")


class TestSvc003NotificationWorkflow:
    def test_notification_without_followup(self) -> None:
        code = (
            "METHOD report_issue.\n"
            "  lo_svc->notification_create( iv_equi = lv_equi iv_text = lv_text ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-SVC-003")

    def test_notification_with_followup_clean(self) -> None:
        code = (
            "METHOD report_issue.\n"
            "  lo_svc->notification_create( iv_equi = lv_equi iv_text = lv_text ).\n"
            "  lo_svc->task_create( iv_notif = lv_notif ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-SVC-003")


class TestSvc004TechnicianAvailability:
    def test_technician_assign_without_check(self) -> None:
        code = (
            "METHOD dispatch.\n"
            "  lo_plan->technician_assign( iv_tech = lv_tech iv_order = lv_order ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-SVC-004")

    def test_technician_assign_with_availability_clean(self) -> None:
        code = (
            "METHOD dispatch.\n"
            "  lo_plan->check_availability( iv_tech = lv_tech ).\n"
            "  lo_plan->technician_assign( iv_tech = lv_tech iv_order = lv_order ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-SVC-004")


class TestSvc005SparePartStock:
    def test_spare_part_reserve_without_stock(self) -> None:
        code = (
            "METHOD reserve_parts.\n"
            "  lo_svc->spare_part_reserve( iv_matnr = lv_matnr iv_qty = lv_qty ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-SVC-005")

    def test_spare_part_reserve_with_stock_clean(self) -> None:
        code = (
            "METHOD reserve_parts.\n"
            "  lo_svc->check_stock( iv_matnr = lv_matnr ).\n"
            "  lo_svc->spare_part_reserve( iv_matnr = lv_matnr iv_qty = lv_qty ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-SVC-005")


# ===========================================================================
# MII/MES rule tests (DOM-MII-*)
# ===========================================================================


class TestMii001ConfirmTiming:
    def test_prod_confirm_without_timestamp(self) -> None:
        code = (
            "METHOD confirm_operation.\n"
            "  lo_mes->prod_confirm( iv_aufnr = lv_aufnr iv_vornr = lv_vornr ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-MII-001")

    def test_prod_confirm_with_timestamp_clean(self) -> None:
        code = (
            "METHOD confirm_operation.\n"
            "  DATA lv_ts TYPE timestamp.\n"
            "  GET TIME STAMP FIELD lv_ts.\n"
            "  lo_mes->prod_confirm(\n"
            "    iv_aufnr = lv_aufnr\n"
            "    iv_confirm_date = sy-datum\n"
            "  ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-MII-001")


class TestMii002ShopfloorRetry:
    def test_plc_call_without_retry(self) -> None:
        code = (
            "METHOD read_sensor.\n"
            "  lo_plc->plc_read( iv_address = lv_addr ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-MII-002")

    def test_plc_call_with_retry_clean(self) -> None:
        code = (
            "METHOD read_sensor.\n"
            "  DATA lv_retry TYPE i VALUE 3.\n"
            "  DO lv_retry TIMES.\n"
            "    TRY.\n"
            "      lo_plc->plc_read( iv_address = lv_addr ).\n"
            "      EXIT.\n"
            "    CATCH zcx_plc_error.\n"
            "      lv_retries = lv_retries + 1.\n"
            "    ENDTRY.\n"
            "  ENDDO.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-MII-002")


class TestMii003RealtimeBuffer:
    def test_sensor_data_without_buffer(self) -> None:
        code = (
            "METHOD process_signals.\n"
            "  lo_mes->sensor_data( iv_signal = lv_signal ).\n"
            "  lo_mes->store_immediately( ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-MII-003")

    def test_sensor_data_with_buffer_clean(self) -> None:
        code = (
            "METHOD process_signals.\n"
            "  lo_buffer->collect_data( iv_signal = lv_signal ).\n"
            "  lo_mes->sensor_data( iv_signal = lv_signal ).\n"
            "  lo_buffer->flush_batch( ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-MII-003")


class TestMii004OperatorUi:
    def test_operator_screen_with_many_fields(self) -> None:
        code = (
            "METHOD display_operator_screen.\n"
            "  PARAMETERS p1 TYPE c.\n"
            "  PARAMETERS p2 TYPE c.\n"
            "  PARAMETERS p3 TYPE c.\n"
            "  PARAMETERS p4 TYPE c.\n"
            "  PARAMETERS p5 TYPE c.\n"
            "  PARAMETERS p6 TYPE c.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-MII-004")

    def test_operator_screen_simple_clean(self) -> None:
        code = (
            "METHOD display_operator_screen.\n"
            "  DATA lv_barcode TYPE c.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-MII-004")


class TestMii005OrderStatusCheck:
    def test_confirm_without_status_check(self) -> None:
        code = (
            "METHOD confirm_order.\n"
            "  lo_mes->prod_confirm( iv_aufnr = lv_aufnr ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert _has_rule(findings, "DOM-MII-005")

    def test_confirm_with_status_check_clean(self) -> None:
        code = (
            "METHOD confirm_order.\n"
            "  lo_mes->get_status( iv_aufnr = lv_aufnr ).\n"
            "  IF lv_order_status = 'REL'.\n"
            "    lo_mes->prod_confirm( iv_aufnr = lv_aufnr ).\n"
            "  ENDIF.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        assert not _has_rule(findings, "DOM-MII-005")


# ===========================================================================
# Clean code — no domain rules should fire
# ===========================================================================


class TestDomainCleanCode:
    def test_generic_abap_no_domain_findings(self) -> None:
        code = (
            "CLASS zcl_generic IMPLEMENTATION.\n"
            "  METHOD get_data.\n"
            "    AUTHORITY-CHECK OBJECT 'S_TCODE'\n"
            "      ID 'TCD' FIELD 'SE80'\n"
            "      ID 'ACTVT' FIELD '03'.\n"
            "    SELECT vbeln erdat FROM vbak\n"
            "      INTO TABLE @rt_result\n"
            "      WHERE kunnr = @iv_kunnr\n"
            "      ORDER BY vbeln.\n"
            "  ENDMETHOD.\n"
            "ENDCLASS.\n"
        )
        findings = _run(code)
        domain_findings = [f for f in findings if f.rule_id and f.rule_id.startswith("DOM-")]
        assert len(domain_findings) == 0

    def test_simple_loop_no_domain_findings(self) -> None:
        code = (
            "METHOD process.\n"
            "  LOOP AT lt_items INTO DATA(ls_item).\n"
            "    ls_item-status = 'OK'.\n"
            "    MODIFY lt_items FROM ls_item.\n"
            "  ENDLOOP.\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD)
        domain_findings = [f for f in findings if f.rule_id and f.rule_id.startswith("DOM-")]
        assert len(domain_findings) == 0


# ===========================================================================
# Bilingual output for domain rules
# ===========================================================================


class TestDomainBilingual:
    def test_german_output_yard(self) -> None:
        code = (
            "METHOD process_arrival.\n"
            "  lo_yard->gate_in( iv_trailer = lv_trailer ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD, Language.DE)
        yard_finding = next(
            (f for f in findings if f.rule_id == "DOM-YARD-001"), None,
        )
        if yard_finding:
            assert "Gate-Prozess" in yard_finding.title

    def test_english_output_ewm(self) -> None:
        code = (
            "METHOD confirm_task.\n"
            "  lo_wm->wt_confirm( iv_tanum = lv_tanum ).\n"
            "ENDMETHOD.\n"
        )
        findings = _run(code, ArtifactType.ABAP_METHOD, Language.EN)
        ewm_finding = next(
            (f for f in findings if f.rule_id == "DOM-EWM-001"), None,
        )
        if ewm_finding:
            assert "Warehouse task" in ewm_finding.title
