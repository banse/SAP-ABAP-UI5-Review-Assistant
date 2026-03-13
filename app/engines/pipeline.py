"""Orchestrator pipeline for the SAP ABAP/UI5 Review Assistant.

Accepts a ``ReviewRequest`` and drives every engine in sequence,
then assembles the outputs into a single ``ReviewResponse``.
"""

from __future__ import annotations

from app.engines.action_engine import generate_actions
from app.engines.artifact_classifier import classify_artifact
from app.engines.assessment_engine import generate_assessment
from app.engines.clean_core_checker import check_clean_core
from app.engines.findings_engine import run_findings_engine
from app.engines.question_engine import generate_questions
from app.engines.refactoring_engine import generate_refactoring_hints
from app.engines.review_type_detector import detect_review_type
from app.engines.risk_engine import assess_risks
from app.engines.test_gap_analyzer import analyze_test_gaps
from app.models.enums import Language, ReviewType, Severity
from app.models.schemas import ReviewRequest, ReviewResponse


# ---------------------------------------------------------------------------
# Review summary builder
# ---------------------------------------------------------------------------


def _build_review_summary(
    review_type: ReviewType,
    artifact_type_value: str,
    findings_count: int,
    critical_count: int,
    important_count: int,
    optional_count: int,
    top_risk_dimension: str | None,
    go_no_go: str,
    language: Language,
) -> str:
    """Build a bilingual review summary."""
    is_de = language == Language.DE
    art_label = artifact_type_value.replace("_", " ").title()
    rt_label = review_type.value.replace("_", " ").title()

    if is_de:
        parts = [
            f"Review-Typ: {rt_label} | Artefakt: {art_label}",
            f"Findings gesamt: {findings_count} "
            f"(Kritisch: {critical_count}, Wichtig: {important_count}, "
            f"Optional: {optional_count})",
        ]
        if top_risk_dimension:
            parts.append(f"Hoechste Risikodimension: {top_risk_dimension}")
        parts.append(f"Gesamtbewertung: {go_no_go}")
    else:
        parts = [
            f"Review Type: {rt_label} | Artifact: {art_label}",
            f"Total findings: {findings_count} "
            f"(Critical: {critical_count}, Important: {important_count}, "
            f"Optional: {optional_count})",
        ]
        if top_risk_dimension:
            parts.append(f"Top risk dimension: {top_risk_dimension}")
        parts.append(f"Overall assessment: {go_no_go}")

    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_review_pipeline(request: ReviewRequest) -> ReviewResponse:
    """Run the full review pipeline.

    Pipeline steps:
        1. Detect review type (if AUTO or validate provided)
        2. Classify artifact type (if AUTO or validate provided)
        3. Enrich context with clarification answers
        4. Run findings engine
        5. Run test-gap analyzer
        6. Run clean-core checker
        7. Run risk engine
        8. Generate questions (filter already-answered)
        9. Generate recommended actions
        10. Generate refactoring hints
        11. Generate overall assessment
        12. Generate review summary text
        13. Return ReviewResponse

    Parameters
    ----------
    request:
        The validated review request.

    Returns
    -------
    ReviewResponse
        A fully-populated review response.
    """
    language = request.language
    code = request.code_or_diff

    # Step 1 -- Detect review type
    review_type = detect_review_type(
        code=code,
        provided_type=request.review_type,
    )

    # Step 2 -- Classify artifact type
    artifact_type = classify_artifact(
        code=code,
        provided_type=request.artifact_type,
    )

    # Step 3 -- Enrich context with clarification answers
    enriched_code = code
    if request.clarifications:
        enrichment_lines: list[str] = []
        for question, answer in request.clarifications.items():
            if answer and answer.strip():
                enrichment_lines.append(f"Q: {question} A: {answer.strip()}")
        if enrichment_lines:
            enriched_code = (
                code
                + "\n\n" + "* Additional clarifications:\n"
                + "\n".join(enrichment_lines)
            )

    # Step 4 -- Run findings engine
    findings = run_findings_engine(
        code=enriched_code,
        artifact_type=artifact_type,
        review_type=review_type,
        review_context=request.review_context,
        language=language,
    )

    # Step 5 -- Run test-gap analyzer
    test_gaps = analyze_test_gaps(
        code=enriched_code,
        artifact_type=artifact_type,
        review_context=request.review_context,
        language=language,
    )

    # Step 6 -- Run clean-core checker
    clean_core_hints = check_clean_core(
        code=enriched_code,
        artifact_type=artifact_type,
        language=language,
    )

    # Step 7 -- Run risk engine
    risk_notes = assess_risks(
        findings=findings,
        test_gaps=test_gaps,
        clean_core_hints=clean_core_hints,
        language=language,
    )

    # Step 8 -- Generate questions (filter already-answered)
    missing_information = generate_questions(
        code=code,
        review_type=review_type,
        artifact_type=artifact_type,
        review_context=request.review_context,
        findings=findings,
        clarifications=request.clarifications,
        language=language,
    )

    # Step 9 -- Generate recommended actions
    recommended_actions = generate_actions(
        findings=findings,
        test_gaps=test_gaps,
        language=language,
    )

    # Step 10 -- Generate refactoring hints
    refactoring_hints = generate_refactoring_hints(
        findings=findings,
        artifact_type=artifact_type,
        language=language,
    )

    # Step 11 -- Generate overall assessment
    overall_assessment = generate_assessment(
        findings=findings,
        test_gaps=test_gaps,
        risk_notes=risk_notes,
        language=language,
    )

    # Step 12 -- Build review summary
    top_risk = None
    if risk_notes:
        top_risk = risk_notes[0].category.value

    review_summary = _build_review_summary(
        review_type=review_type,
        artifact_type_value=artifact_type.value,
        findings_count=len(findings),
        critical_count=overall_assessment.critical_count,
        important_count=overall_assessment.important_count,
        optional_count=overall_assessment.optional_count,
        top_risk_dimension=top_risk,
        go_no_go=overall_assessment.go_no_go.value,
        language=language,
    )

    # Step 13 -- Assemble response
    return ReviewResponse(
        review_summary=review_summary,
        review_type=review_type,
        artifact_type=artifact_type,
        findings=findings,
        missing_information=missing_information,
        test_gaps=test_gaps,
        recommended_actions=recommended_actions,
        refactoring_hints=refactoring_hints,
        risk_notes=risk_notes,
        clean_core_hints=clean_core_hints,
        overall_assessment=overall_assessment,
        language=language,
    )
