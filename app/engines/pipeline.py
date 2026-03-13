"""Orchestrator pipeline for the SAP ABAP/UI5 Review Assistant.

Accepts a ``ReviewRequest`` and drives every engine in sequence,
then assembles the outputs into a single ``ReviewResponse``.
"""

from __future__ import annotations

from app.engines.action_engine import generate_actions
from app.engines.artifact_classifier import classify_artifact
from app.engines.assessment_engine import generate_assessment
from app.engines.clean_core_checker import check_clean_core
from app.engines.cross_artifact_checker import check_cross_artifact_consistency
from app.engines.design_reviewer import run_design_review
from app.engines.diff_parser import extract_new_code, parse_unified_diff
from app.engines.findings_engine import run_findings_engine
from app.engines.multi_artifact_handler import split_change_package
from app.engines.question_engine import generate_questions
from app.engines.refactoring_engine import generate_refactoring_hints
from app.engines.review_type_detector import detect_review_type
from app.engines.risk_engine import assess_risks
from app.engines.test_gap_analyzer import analyze_test_gaps
from app.models.enums import Language, ReviewType, Severity
from app.models.schemas import Finding, ReviewRequest, ReviewResponse


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


def _run_diff_pipeline(request: ReviewRequest) -> ReviewResponse:
    """Run review pipeline in diff mode.

    Parses the unified diff, extracts new code, runs findings on
    the new code, and marks each finding with ``is_new`` metadata.
    """
    diff_files = parse_unified_diff(request.code_or_diff)
    new_code = extract_new_code(diff_files)

    if not new_code.strip():
        # If no added code, still run against the raw text as a fallback
        new_code = request.code_or_diff

    # Run the standard pipeline with extracted new code
    modified = request.model_copy(update={"code_or_diff": new_code, "input_mode": "snippet"})
    return run_review_pipeline(modified)


def _run_change_package_pipeline(request: ReviewRequest) -> ReviewResponse:
    """Run review pipeline in change-package mode.

    Splits the input into artifact sections, reviews each, and
    consolidates findings.
    """
    sections = split_change_package(request.code_or_diff)

    if len(sections) <= 1:
        # Single artifact — run standard pipeline
        modified = request.model_copy(update={"input_mode": "snippet"})
        return run_review_pipeline(modified)

    # Run pipeline per section and consolidate
    all_findings: list[Finding] = []
    all_responses: list[ReviewResponse] = []

    for section in sections:
        section_request = request.model_copy(
            update={
                "code_or_diff": section.code,
                "artifact_type": section.artifact_type,
                "input_mode": "snippet",
            }
        )
        section_response = run_review_pipeline(section_request)

        # Tag findings with artifact reference
        for finding in section_response.findings:
            if not finding.artifact_reference:
                finding.artifact_reference = section.artifact_name
            all_findings.append(finding)

        all_responses.append(section_response)

    # Run cross-artifact consistency checks across all sections
    cross_artifact_findings = check_cross_artifact_consistency(
        sections, request.language
    )
    all_findings.extend(cross_artifact_findings)

    if not all_responses:
        modified = request.model_copy(update={"input_mode": "snippet"})
        return run_review_pipeline(modified)

    # Consolidate: use findings from all sections, other outputs from first
    base = all_responses[0]

    # Merge findings, test_gaps, clean_core_hints from all sections
    merged_test_gaps = []
    merged_clean_core = []
    merged_risk_notes = []
    for resp in all_responses:
        merged_test_gaps.extend(resp.test_gaps)
        merged_clean_core.extend(resp.clean_core_hints)
        merged_risk_notes.extend(resp.risk_notes)

    # Sort consolidated findings by severity
    severity_order = {"CRITICAL": 0, "IMPORTANT": 1, "OPTIONAL": 2, "UNCLEAR": 3}
    all_findings.sort(key=lambda f: severity_order.get(f.severity.value, 99))

    return ReviewResponse(
        review_summary=base.review_summary,
        review_type=base.review_type,
        artifact_type=base.artifact_type,
        findings=all_findings,
        missing_information=base.missing_information,
        test_gaps=merged_test_gaps,
        recommended_actions=base.recommended_actions,
        refactoring_hints=base.refactoring_hints,
        risk_notes=merged_risk_notes,
        clean_core_hints=merged_clean_core,
        overall_assessment=base.overall_assessment,
        language=base.language,
    )


def run_review_pipeline(request: ReviewRequest) -> ReviewResponse:
    """Run the full review pipeline.

    Pipeline steps:
        0. Check input_mode and dispatch to diff/change_package handler
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
    # Step 0 -- Dispatch based on input mode
    input_mode = request.input_mode or "snippet"

    if input_mode == "diff":
        return _run_diff_pipeline(request)

    if input_mode == "change_package":
        return _run_change_package_pipeline(request)

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

    # Step 4 -- Run findings engine (or design reviewer for design reviews)
    is_design_review = review_type == ReviewType.SOLUTION_DESIGN_REVIEW

    if is_design_review:
        findings = run_design_review(
            code=enriched_code,
            language=language,
        )
    else:
        findings = run_findings_engine(
            code=enriched_code,
            artifact_type=artifact_type,
            review_type=review_type,
            review_context=request.review_context,
            language=language,
        )

    # Step 5 -- Run test-gap analyzer (skip for design reviews)
    if is_design_review:
        test_gaps = []
    else:
        test_gaps = analyze_test_gaps(
            code=enriched_code,
            artifact_type=artifact_type,
            review_context=request.review_context,
            language=language,
        )

    # Step 6 -- Run clean-core checker (skip for design reviews)
    if is_design_review:
        clean_core_hints = []
    else:
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
