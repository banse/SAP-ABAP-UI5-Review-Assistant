"""Tests for RAP Behavior Definition consistency rules."""

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
    artifact_type: ArtifactType = ArtifactType.BEHAVIOR_DEFINITION,
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
# RAP-CONS-001: Behavior definition entity mismatch
# ===========================================================================


class TestRapCons001EntityMismatch:
    def test_bdef_entity_mismatch_detected(self) -> None:
        code = (
            "define view entity ZI_Order as select from ztab { key id }\n"
            "define behavior for ZI_WrongName\n"
            "implementation in class zcl_order unique\n"
        )
        findings = _run(code, ArtifactType.MIXED_FULLSTACK)
        assert _has_rule(findings, "RAP-CONS-001")

    def test_bdef_entity_match_clean(self) -> None:
        code = (
            "define view entity ZI_Order as select from ztab { key id }\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
        )
        findings = _run(code, ArtifactType.MIXED_FULLSTACK)
        assert not _has_rule(findings, "RAP-CONS-001")

    def test_bdef_only_no_false_positive(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-001")


# ===========================================================================
# RAP-CONS-002: Action without implementation class
# ===========================================================================


class TestRapCons002ActionWithoutImpl:
    def test_action_without_implementation(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-002")

    def test_action_with_implementation_clean(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-002")


# ===========================================================================
# RAP-CONS-003: Validation on save without field trigger
# ===========================================================================


class TestRapCons003ValidationWithoutTrigger:
    def test_validation_without_field_list(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  validation validateStatus on save;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-003")

    def test_validation_with_field_list_clean(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  validation validateStatus on save { field Status; }\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-003")


# ===========================================================================
# RAP-CONS-004: Determination on wrong trigger
# ===========================================================================


class TestRapCons004DeterminationTrigger:
    def test_status_determination_on_create(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  determination setStatus on save { create; }\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-004")

    def test_key_determination_on_create_clean(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  determination setKey on save { create; }\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-004")


# ===========================================================================
# RAP-CONS-005: Incomplete draft handling
# ===========================================================================


class TestRapCons005IncompleteDraft:
    def test_draft_table_without_draft_actions(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "persistent table ztab_order\n"
            "draft table ztab_order_d\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-005")

    def test_draft_table_with_draft_actions_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "persistent table ztab_order\n"
            "draft table ztab_order_d\n"
            "{\n"
            "  create; update; delete;\n"
            "  draft action Edit;\n"
            "  draft action Activate;\n"
            "  draft action Discard;\n"
            "  draft action Resume;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-005")


# ===========================================================================
# RAP-CONS-006: Managed with unmanaged patterns
# ===========================================================================


class TestRapCons006ManagedUnmanagedConflict:
    def test_managed_with_unmanaged_save(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "with unmanaged save\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-006")

    def test_managed_only_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-006")


# ===========================================================================
# RAP-CONS-007: Missing authorization
# ===========================================================================


class TestRapCons007MissingAuthorization:
    def test_bdef_without_authorization(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-007")

    def test_bdef_with_authorization_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "authorization master ( instance )\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-007")


# ===========================================================================
# RAP-CONS-008: Missing feature control
# ===========================================================================


class TestRapCons008MissingFeatureControl:
    def test_action_without_feature_control(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-008")

    def test_action_with_feature_control_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  action approve;\n"
            "  instance feature control;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-008")


# ===========================================================================
# RAP-CONS-009: Missing side-effects
# ===========================================================================


class TestRapCons009MissingSideEffects:
    def test_action_without_side_effects(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-009")

    def test_action_with_side_effects_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  action approve;\n"
            "  side effects { change Status; }\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-009")


# ===========================================================================
# RAP-CONS-010: Numbering inconsistency
# ===========================================================================


class TestRapCons010NumberingInconsistency:
    def test_managed_with_early_numbering(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "early numbering\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-010")

    def test_managed_with_late_numbering_clean(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "late numbering\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "RAP-CONS-010")

    def test_managed_without_numbering_flagged(self) -> None:
        code = (
            "managed;\n"
            "define behavior for ZI_Order\n"
            "implementation in class zcl_order unique\n"
            "{\n"
            "  create; update; delete;\n"
            "}\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "RAP-CONS-010")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestRapConsistencyBilingual:
    def test_german_output(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code, language=Language.DE)
        cons002 = next((f for f in findings if f.rule_id == "RAP-CONS-002"), None)
        if cons002:
            assert "Implementierungsklasse" in cons002.title or "Action" in cons002.title

    def test_english_output(self) -> None:
        code = (
            "define behavior for ZI_Order\n"
            "{\n"
            "  action approve;\n"
            "}\n"
        )
        findings = _run(code, language=Language.EN)
        cons002 = next((f for f in findings if f.rule_id == "RAP-CONS-002"), None)
        if cons002:
            assert "implementation" in cons002.title.lower() or "action" in cons002.title.lower()


# ===========================================================================
# Edge cases
# ===========================================================================


class TestRapConsistencyEdgeCases:
    def test_empty_code(self) -> None:
        findings = _run("")
        assert findings == []

    def test_non_bdef_code_no_false_positives(self) -> None:
        code = "SELECT * FROM vbak INTO TABLE @lt_orders.\n"
        findings = _run(code)
        rap_rules = [f for f in findings if f.rule_id.startswith("RAP-CONS-")]
        assert len(rap_rules) == 0
