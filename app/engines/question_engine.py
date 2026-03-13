"""Missing-information engine for the SAP ABAP/UI5 Review Assistant.

Generates contextual questions based on detected gaps in the review input,
filtering out already-answered questions and deduplicating similar ones.
"""

from __future__ import annotations

from app.models.enums import (
    ArtifactType,
    Language,
    ReviewContext,
    ReviewType,
    Severity,
)
from app.models.schemas import Finding, MissingInformation
from app.rules.questions import ALL_QUESTION_RULES, QuestionRule


# ---------------------------------------------------------------------------
# CDS artifact types for trigger matching
# ---------------------------------------------------------------------------

_CDS_ARTIFACTS: set[str] = {
    ArtifactType.CDS_VIEW.value,
    ArtifactType.CDS_PROJECTION.value,
    ArtifactType.CDS_ANNOTATION.value,
}


# ---------------------------------------------------------------------------
# Trigger condition evaluators
# ---------------------------------------------------------------------------


def _should_trigger(
    rule: QuestionRule,
    review_type: ReviewType,
    artifact_type: ArtifactType,
    review_context: ReviewContext,
    findings: list[Finding],
    has_tech_context: bool,
    has_test_gaps: bool,
) -> bool:
    """Evaluate whether a question rule's trigger condition is met."""
    cond = rule.trigger_condition

    if cond == "always":
        return True

    if cond == "no_tech_context":
        return not has_tech_context

    if cond == "performance_finding":
        return any(
            f.impact and "performance" in f.impact.lower()
            for f in findings
        )

    if cond == "no_auth":
        # Trigger if there is ABAP code but no auth-related finding
        has_auth_finding = any(
            f.impact and "security" in f.impact.lower()
            for f in findings
        )
        return not has_auth_finding

    if cond == "test_gaps":
        return has_test_gaps

    if cond == "snippet_review":
        return review_type == ReviewType.SNIPPET_REVIEW

    if cond == "cds_artifact":
        return artifact_type.value in _CDS_ARTIFACTS

    if cond == "unclear_finding":
        return any(f.severity == Severity.UNCLEAR for f in findings)

    if cond == "ticket_review":
        return review_type == ReviewType.TICKET_BASED_PRE_REVIEW

    return False


def _is_already_answered(rule: QuestionRule, clarifications: dict[str, str]) -> bool:
    """Check whether this question has already been answered."""
    if not clarifications:
        return False

    q_lower = rule.question.lower()
    q_de_lower = rule.question_de.lower()
    qid_lower = rule.question_id.lower()

    for key, value in clarifications.items():
        if not value or not value.strip():
            continue
        key_lower = key.lower()
        # Match by question ID, exact question text, or significant overlap
        if key_lower == qid_lower:
            return True
        if key_lower == q_lower or key_lower == q_de_lower:
            return True
        # Fuzzy: if the clarification key contains the question ID
        if qid_lower in key_lower:
            return True

    return False


def _rule_to_missing_info(rule: QuestionRule, language: Language) -> MissingInformation:
    """Convert a question rule to a MissingInformation schema object."""
    is_de = language == Language.DE

    return MissingInformation(
        question=rule.question_de if is_de else rule.question,
        why_it_matters=rule.why_it_matters_de if is_de else rule.why_it_matters,
        default_assumption=(
            rule.default_assumption_de if is_de else rule.default_assumption
        ),
        category=rule.category,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_questions(
    code: str,
    review_type: ReviewType,
    artifact_type: ArtifactType,
    review_context: ReviewContext,
    findings: list[Finding],
    clarifications: dict[str, str],
    language: Language,
) -> list[MissingInformation]:
    """Generate contextual questions based on missing information.

    Parameters
    ----------
    code:
        The source code being reviewed.
    review_type:
        The detected or provided review type.
    artifact_type:
        The detected or provided artifact type.
    review_context:
        The project phase / intent.
    findings:
        Findings produced by the findings engine.
    clarifications:
        Already-answered questions (key=question text or ID, value=answer).
    language:
        Output language (EN or DE).

    Returns
    -------
    list[MissingInformation]
        Deduplicated list of contextual questions.
    """
    if not code or not code.strip():
        return []

    has_tech_context = False  # caller should set via technology_context
    has_test_gaps = False  # will be inferred from findings

    # Infer test gap presence from findings that mention testing
    has_test_gaps = any(
        f.impact and "test" in f.impact.lower()
        for f in findings
    )

    questions: list[MissingInformation] = []
    seen_categories: set[str] = set()
    seen_questions: set[str] = set()

    for rule in ALL_QUESTION_RULES:
        # Skip already-answered
        if _is_already_answered(rule, clarifications):
            continue

        # Check trigger condition
        if not _should_trigger(
            rule=rule,
            review_type=review_type,
            artifact_type=artifact_type,
            review_context=review_context,
            findings=findings,
            has_tech_context=has_tech_context,
            has_test_gaps=has_test_gaps,
        ):
            continue

        info = _rule_to_missing_info(rule, language)

        # Deduplicate by question text
        q_key = info.question.lower().strip()
        if q_key in seen_questions:
            continue
        seen_questions.add(q_key)

        questions.append(info)

    return questions
