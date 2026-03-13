"""Tests for UI5 Freestyle review rules."""

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
    artifact_type: ArtifactType = ArtifactType.UI5_CONTROLLER,
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
# UI5-FS-001: Missing model destroy in onExit
# ===========================================================================


class TestUI5FS001MissingModelDestroy:
    def test_model_created_no_on_exit(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller", "sap/ui/model/json/JSONModel"],\n'
            "function(Controller, JSONModel) {\n"
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      var oModel = new JSONModel({items: []});\n'
            '      this.getView().setModel(oModel, "local");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-001")

    def test_model_created_with_on_exit_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller", "sap/ui/model/json/JSONModel"],\n'
            "function(Controller, JSONModel) {\n"
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      this._oModel = new JSONModel({items: []});\n'
            '      this.getView().setModel(this._oModel, "local");\n'
            "    },\n"
            "    onExit: function() {\n"
            "      this._oModel.destroy();\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-001")


# ===========================================================================
# UI5-FS-002: Synchronous XMLHttpRequest usage
# ===========================================================================


class TestUI5FS002SyncXHR:
    def test_sync_ajax_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      jQuery.ajax({ url: '/api/data', async: false });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-002")

    def test_sync_xhr_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      var xhr = new XMLHttpRequest();\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-002")

    def test_async_ajax_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      jQuery.ajax({ url: '/api/data', async: true });\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-002")


# ===========================================================================
# UI5-FS-003: Missing formatter for date/currency display
# ===========================================================================


class TestUI5FS003MissingFormatter:
    def test_date_binding_without_type(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Text text="{creationDate}"/>\n'
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-FS-003")

    def test_date_binding_with_type_clean(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <Text text="{path: \'creationDate\', type: \'sap.ui.model.type.Date\'}"/>\n'
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert not _has_rule(findings, "UI5-FS-003")


# ===========================================================================
# UI5-FS-004: Deprecated control usage
# ===========================================================================


class TestUI5FS004DeprecatedControl:
    def test_sap_ui_commons_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/commons/Button"], function(Button) {\n'
            '  return Controller.extend("my.app.Main", {});\n'
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-004")

    def test_sap_viz_detected(self) -> None:
        code = '<core:View xmlns:viz="sap.viz.ui5">\n</core:View>\n'
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-FS-004")

    def test_sap_m_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/m/Button"], function(Button) {\n'
            '  return Controller.extend("my.app.Main", {});\n'
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-004")


# ===========================================================================
# UI5-FS-005: Event handler not unregistered
# ===========================================================================


class TestUI5FS005EventHandlerNotUnregistered:
    def test_attach_without_detach(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      this.getOwnerComponent().getRouter().attachRouteMatched(this._onRouteMatched, this);\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-005")

    def test_attach_with_detach_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      this.getOwnerComponent().getRouter().attachRouteMatched(this._onRouteMatched, this);\n"
            "    },\n"
            "    onExit: function() {\n"
            "      this.getOwnerComponent().getRouter().detachRouteMatched(this._onRouteMatched, this);\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-005")


# ===========================================================================
# UI5-FS-006: Missing accessibility attributes
# ===========================================================================


class TestUI5FS006MissingAccessibility:
    def test_icon_without_tooltip(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m" xmlns:core="sap.ui.core">\n'
            '  <core:Icon src="sap-icon://delete"/>\n'
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-FS-006")

    def test_icon_with_tooltip_clean(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m" xmlns:core="sap.ui.core">\n'
            '  <core:Icon src="sap-icon://delete" tooltip="{i18n>deleteTooltip}"/>\n'
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert not _has_rule(findings, "UI5-FS-006")


# ===========================================================================
# UI5-FS-007: Routing without parameter validation
# ===========================================================================


class TestUI5FS007RoutingNoValidation:
    def test_nav_to_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {},\n"
            "    onPress: function() {\n"
            '      this.getRouter().navTo("detail", {id: sId});\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-007")


# ===========================================================================
# UI5-FS-008: Global variable in controller
# ===========================================================================


class TestUI5FS008GlobalVariable:
    def test_global_var_before_define(self) -> None:
        code = (
            'var gData = {};\n'
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {}\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-008")

    def test_no_global_var_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            "      var oData = {};\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-008")


# ===========================================================================
# UI5-FS-009: Console.log left in production code
# ===========================================================================


class TestUI5FS009ConsoleLog:
    def test_console_log_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      console.log("debug data");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-009")

    def test_console_warn_detected(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      console.warn("something");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-009")

    def test_sap_log_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller", "sap/base/Log"],\n'
            "function(Controller, Log) {\n"
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      Log.info("initialized");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-009")


# ===========================================================================
# UI5-FS-010: Missing fragment reuse
# ===========================================================================


class TestUI5FS010MissingFragmentReuse:
    def test_repeated_vbox_detected(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <VBox class="sapUiSmallMargin">\n'
            '    <Text text="A"/>\n'
            "  </VBox>\n"
            '  <VBox class="sapUiSmallMargin">\n'
            '    <Text text="B"/>\n'
            "  </VBox>\n"
            '  <VBox class="sapUiSmallMargin">\n'
            '    <Text text="C"/>\n'
            "  </VBox>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert _has_rule(findings, "UI5-FS-010")

    def test_single_vbox_clean(self) -> None:
        code = (
            '<mvc:View xmlns:mvc="sap.ui.core.mvc" xmlns="sap.m">\n'
            '  <VBox class="sapUiSmallMargin">\n'
            '    <Text text="A"/>\n'
            "  </VBox>\n"
            "</mvc:View>\n"
        )
        findings = _run(code, ArtifactType.UI5_VIEW)
        assert not _has_rule(findings, "UI5-FS-010")


# ===========================================================================
# UI5-FS-011: Synchronous module loading
# ===========================================================================


class TestUI5FS011SyncModuleLoading:
    def test_jquery_sap_require_detected(self) -> None:
        code = (
            'jQuery.sap.require("sap.m.MessageBox");\n'
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {}\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-011")

    def test_sap_ui_require_sync_detected(self) -> None:
        code = (
            'var MessageBox = sap.ui.requireSync("sap/m/MessageBox");\n'
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {});\n'
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-011")

    def test_async_define_clean(self) -> None:
        code = (
            'sap.ui.define([\n'
            '  "sap/ui/core/mvc/Controller",\n'
            '  "sap/m/MessageBox"\n'
            "], function(Controller, MessageBox) {\n"
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {}\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-011")


# ===========================================================================
# UI5-FS-012: Missing metadata section in Component.js
# ===========================================================================


class TestUI5FS012MissingComponentMetadata:
    def test_component_without_metadata(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/UIComponent"], function(UIComponent) {\n'
            '  return UIComponent.extend("my.app.Component", {\n'
            "    init: function() {\n"
            "      UIComponent.prototype.init.apply(this, arguments);\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert _has_rule(findings, "UI5-FS-012")

    def test_component_with_metadata_clean(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/UIComponent"], function(UIComponent) {\n'
            '  return UIComponent.extend("my.app.Component", {\n'
            "    metadata: {\n"
            '      manifest: "json"\n'
            "    },\n"
            "    init: function() {\n"
            "      UIComponent.prototype.init.apply(this, arguments);\n"
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code)
        assert not _has_rule(findings, "UI5-FS-012")


# ===========================================================================
# Bilingual output
# ===========================================================================


class TestUI5FreestyleBilingual:
    def test_german_output(self) -> None:
        code = (
            'sap.ui.define(["sap/ui/core/mvc/Controller"], function(Controller) {\n'
            '  return Controller.extend("my.app.Main", {\n'
            "    onInit: function() {\n"
            '      console.log("test");\n'
            "    }\n"
            "  });\n"
            "});\n"
        )
        findings = _run(code, language=Language.DE)
        fs009 = next((f for f in findings if f.rule_id == "UI5-FS-009"), None)
        if fs009:
            assert "Produktionscode" in fs009.title
