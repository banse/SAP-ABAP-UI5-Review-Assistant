from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ArtifactType,
    Confidence,
    GoNoGo,
    Language,
    ODataVersion,
    QuestionFocus,
    RefactoringCategory,
    ReviewContext,
    ReviewType,
    RiskCategory,
    Severity,
    TestGapCategory,
)


# ---------------------------------------------------------------------------
# Input Models
# ---------------------------------------------------------------------------


class TechnologyContext(BaseModel):
    """Technology stack details that influence review rules and suggestions."""

    sap_release: str | None = None
    ui5_version: str | None = None
    odata_version: ODataVersion | None = None
    rap_managed: bool | None = None
    fiori_elements: bool | None = None


class ReviewRequest(BaseModel):
    """Primary input payload for triggering a code / design review."""

    model_config = ConfigDict(str_strip_whitespace=True)

    review_type: ReviewType
    artifact_type: ArtifactType
    code_or_diff: str = Field(min_length=1)
    input_mode: str = "snippet"  # "snippet", "diff", or "change_package"
    context_summary: str = ""
    review_context: ReviewContext = ReviewContext.GREENFIELD
    goal_of_review: str = ""
    technology_context: TechnologyContext | None = None
    known_constraints: list[str] = Field(default_factory=list)
    domain_pack: str | None = None
    question_focus: list[QuestionFocus] = Field(default_factory=list)
    language: Language = Language.EN
    clarifications: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Output Models — individual building blocks
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    """A single review finding with structured reasoning."""

    severity: Severity
    title: str
    observation: str
    reasoning: str
    impact: str
    recommendation: str
    artifact_reference: str | None = None
    line_reference: str | None = None
    rule_id: str | None = None


class DiffFinding(BaseModel):
    """A finding with diff context — indicates whether it is new or pre-existing."""

    finding: Finding
    is_new: bool = True  # True if finding is in added code, False if pre-existing
    diff_context: str = ""  # The diff hunk containing this finding


class TestGap(BaseModel):
    """An identified gap in test coverage."""

    category: TestGapCategory
    description: str
    priority: Severity
    suggested_test: str | None = None


class RiskNote(BaseModel):
    """A risk associated with the reviewed code or design."""

    category: RiskCategory
    description: str
    severity: Severity
    mitigation: str | None = None


class CleanCoreHint(BaseModel):
    """A hint about Clean Core / ABAP Cloud compliance."""

    finding: str
    released_api_alternative: str | None = None
    severity: Severity


class RecommendedAction(BaseModel):
    """A concrete action the developer should take, ordered by priority."""

    order: int
    title: str
    description: str
    effort_hint: str | None = None
    finding_references: list[str] = Field(default_factory=list)


class RefactoringHint(BaseModel):
    """A refactoring suggestion with urgency classification."""

    category: RefactoringCategory
    title: str
    description: str
    benefit: str
    effort_hint: str | None = None


class MissingInformation(BaseModel):
    """Information the reviewer could not determine from the input."""

    question: str
    why_it_matters: str
    default_assumption: str | None = None
    category: str = "context"


class OverallAssessment(BaseModel):
    """High-level go/no-go verdict for the reviewed artifact."""

    go_no_go: GoNoGo
    confidence: Confidence
    summary: str
    critical_count: int = 0
    important_count: int = 0
    optional_count: int = 0


# ---------------------------------------------------------------------------
# Output Models — top-level response
# ---------------------------------------------------------------------------


class FindingResolutionRequest(BaseModel):
    """Request body for setting a finding resolution status."""

    status: str  # OPEN, ACCEPTED, REJECTED, DEFERRED, FIXED
    reviewer_name: str = ""
    comment: str = ""


class ReviewCompletion(BaseModel):
    """Completion metrics for a review."""

    total_findings: int = 0
    resolved: int = 0
    completion_pct: float = 0.0
    by_status: dict = Field(default_factory=dict)


class ReviewResponse(BaseModel):
    """Complete review output returned to the caller."""

    review_summary: str
    review_type: ReviewType
    artifact_type: ArtifactType
    findings: list[Finding] = Field(default_factory=list)
    missing_information: list[MissingInformation] = Field(default_factory=list)
    test_gaps: list[TestGap] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    refactoring_hints: list[RefactoringHint] = Field(default_factory=list)
    risk_notes: list[RiskNote] = Field(default_factory=list)
    clean_core_hints: list[CleanCoreHint] = Field(default_factory=list)
    overall_assessment: OverallAssessment
    language: Language = Language.EN
    similar_reviews: list[dict] = Field(default_factory=list)
    recurring_patterns: list[dict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Quality Gate Config (for API requests)
# ---------------------------------------------------------------------------


class QualityGateConfig(BaseModel):
    """Configuration for CI quality gate thresholds."""

    max_critical: int = 0
    max_important: int = -1
    max_total: int = -1
    require_go: bool = False
    require_clean_core: bool = False
    custom_blocked_rules: list[str] = Field(default_factory=list)
