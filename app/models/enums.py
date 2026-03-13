from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Review Type — what kind of review the user is requesting
# ---------------------------------------------------------------------------


class ReviewType(str, Enum):
    SNIPPET_REVIEW = "SNIPPET_REVIEW"
    DIFF_REVIEW = "DIFF_REVIEW"
    PRE_MERGE_REVIEW = "PRE_MERGE_REVIEW"
    SOLUTION_DESIGN_REVIEW = "SOLUTION_DESIGN_REVIEW"
    TICKET_BASED_PRE_REVIEW = "TICKET_BASED_PRE_REVIEW"
    REGRESSION_RISK_REVIEW = "REGRESSION_RISK_REVIEW"
    CLEAN_CORE_ARCHITECTURE_CHECK = "CLEAN_CORE_ARCHITECTURE_CHECK"


# ---------------------------------------------------------------------------
# Artifact Type — what kind of SAP artifact is being reviewed
# ---------------------------------------------------------------------------


class ArtifactType(str, Enum):
    ABAP_CLASS = "ABAP_CLASS"
    ABAP_METHOD = "ABAP_METHOD"
    ABAP_REPORT = "ABAP_REPORT"
    CDS_VIEW = "CDS_VIEW"
    CDS_PROJECTION = "CDS_PROJECTION"
    CDS_ANNOTATION = "CDS_ANNOTATION"
    BEHAVIOR_DEFINITION = "BEHAVIOR_DEFINITION"
    BEHAVIOR_IMPLEMENTATION = "BEHAVIOR_IMPLEMENTATION"
    SERVICE_DEFINITION = "SERVICE_DEFINITION"
    SERVICE_BINDING = "SERVICE_BINDING"
    ODATA_SERVICE = "ODATA_SERVICE"
    UI5_VIEW = "UI5_VIEW"
    UI5_CONTROLLER = "UI5_CONTROLLER"
    UI5_FRAGMENT = "UI5_FRAGMENT"
    UI5_FORMATTER = "UI5_FORMATTER"
    FIORI_ELEMENTS_APP = "FIORI_ELEMENTS_APP"
    MIXED_FULLSTACK = "MIXED_FULLSTACK"


# ---------------------------------------------------------------------------
# Review Context — project phase / intent behind the code
# ---------------------------------------------------------------------------


class ReviewContext(str, Enum):
    GREENFIELD = "GREENFIELD"
    EXTENSION = "EXTENSION"
    BUGFIX = "BUGFIX"
    REFACTORING = "REFACTORING"


# ---------------------------------------------------------------------------
# Question Focus — what the reviewer wants the AI to focus on
# ---------------------------------------------------------------------------


class QuestionFocus(str, Enum):
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"
    CLEAN_CORE = "CLEAN_CORE"
    TESTS = "TESTS"
    SECURITY = "SECURITY"
    READABILITY = "READABILITY"


# ---------------------------------------------------------------------------
# Severity — finding severity
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    OPTIONAL = "OPTIONAL"
    UNCLEAR = "UNCLEAR"


# ---------------------------------------------------------------------------
# Go / No-Go — overall merge / release recommendation
# ---------------------------------------------------------------------------


class GoNoGo(str, Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    NO_GO = "NO_GO"


# ---------------------------------------------------------------------------
# Confidence — how confident the AI is in its assessment
# ---------------------------------------------------------------------------


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------------------
# Language — output language
# ---------------------------------------------------------------------------


class Language(str, Enum):
    DE = "DE"
    EN = "EN"


# ---------------------------------------------------------------------------
# OData Version
# ---------------------------------------------------------------------------


class ODataVersion(str, Enum):
    V2 = "V2"
    V4 = "V4"


# ---------------------------------------------------------------------------
# Test Gap Category — what kind of test is missing
# ---------------------------------------------------------------------------


class TestGapCategory(str, Enum):
    ABAP_UNIT = "ABAP_UNIT"
    ACTION_VALIDATION = "ACTION_VALIDATION"
    UI_BEHAVIOR = "UI_BEHAVIOR"
    UI_ROLE = "UI_ROLE"
    UI_FILTER_SEARCH = "UI_FILTER_SEARCH"
    REGRESSION_SIDE_EFFECT = "REGRESSION_SIDE_EFFECT"


# ---------------------------------------------------------------------------
# Risk Category
# ---------------------------------------------------------------------------


class RiskCategory(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    MAINTAINABILITY = "MAINTAINABILITY"
    TESTABILITY = "TESTABILITY"
    UPGRADE_CLEAN_CORE = "UPGRADE_CLEAN_CORE"


# ---------------------------------------------------------------------------
# Risk Level
# ---------------------------------------------------------------------------


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Refactoring Category — how urgently a refactoring should be addressed
# ---------------------------------------------------------------------------


class RefactoringCategory(str, Enum):
    SMALL_FIX = "SMALL_FIX"
    TARGETED_STRUCTURE_IMPROVEMENT = "TARGETED_STRUCTURE_IMPROVEMENT"
    MEDIUM_TERM_REFACTORING_HINT = "MEDIUM_TERM_REFACTORING_HINT"
    NOT_IMMEDIATE_REBUILD = "NOT_IMMEDIATE_REBUILD"
