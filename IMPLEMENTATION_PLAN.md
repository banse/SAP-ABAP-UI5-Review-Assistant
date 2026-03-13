# SAP ABAP/UI5 Review Assistant -- Implementation Plan

**Created**: 2026-03-13
**Status**: Active
**Covers**: MVP, v1, v2, v3 (deferred)

---

## Phase Overview

| Phase | Goal | Work Packages | Estimated Duration | Test Target |
|-------|------|---------------|-------------------|-------------|
| **Phase 0: MVP** | Review-type detection, artifact classification, prioritized findings, test gaps, questions, next steps, structured output | 8 WPs | 3-4 weeks | 400+ |
| **Phase 1: v1 -- Solid Practice** | Stronger ABAP/RAP/CDS/Fiori/UI5 rule packs, solution design review, domain packs, history, feedback | 8 WPs | 4-6 weeks | 800+ |
| **Phase 2: v2 -- Premium** | Diff/multi-artifact review, repo-aware context, cross-artifact consistency, similarity search, team workflows | 7 WPs | 6-8 weeks | 1200+ |
| **Phase 3: v3 -- LLM-Augmented** | LLM-powered semantic analysis, natural-language findings, auto-fix suggestions | Deferred | TBD | TBD |

---

## Dependency Graph (simplified)

```
Phase 0 (MVP)
  WP-0.1  Project Scaffolding --------+
  WP-0.2  Pydantic Schemas -----------+---> WP-0.4 Findings Engine
  WP-0.3  Input Form + Basic UI       |---> WP-0.5 Test-Gap Analyzer
  WP-0.4  Findings Engine ------------+---> WP-0.6 Risk & Impact Engine
  WP-0.5  Test-Gap Analyzer ----------+---> WP-0.7 Pipeline + Output
  WP-0.6  Risk & Impact Engine -------+
  WP-0.7  Pipeline + Output + Summary
  WP-0.8  Example Case Library + Validation Tests

Phase 1 (v1)
  WP-1.1  ABAP Rule Packs (Readability, Error Handling, Testability)
  WP-1.2  CDS / Annotation / RAP Rule Packs
  WP-1.3  UI5 Freestyle + Fiori Elements Rule Packs
  WP-1.4  Service / OData Exposure Rule Pack
  WP-1.5  Domain Packs (EWM, Yard, Service, MII/MES)
  WP-1.6  Solution Design Review Mode
  WP-1.7  History + Feedback
  WP-1.8  UI Polish + Template Outputs

Phase 2 (v2)
  WP-2.1  Diff & Multi-Artifact Input --------> WP-2.2 Cross-Artifact Consistency
  WP-2.2  Cross-Artifact Consistency Checker
  WP-2.3  Clean-Core / Released-API Deep Rules
  WP-2.4  Similarity Search + Past Reviews
  WP-2.5  Team Review Workflows
  WP-2.6  CI/Merge-Ready Export
  WP-2.7  UI Premium + Cohesion Pass
```

---

## Phase 0: MVP

### WP-0.1 -- Project Scaffolding

**Priority**: 1 (must be first)
**Effort**: M
**Agent**: Senior Developer
**Test Contribution**: ~20 tests

**Problem**: The project directory is empty. Before any domain logic can be built, the foundational project structure, dependency management, configuration, FastAPI server, database layer, and static frontend shell must exist. Must mirror the Field-Change Accelerator and Skeleton Generator architecture pattern exactly.

**Deliverables**:
- Project directory structure matching the reference architecture
- `requirements.txt` with Python 3.12 + FastAPI + Pydantic v2 + uvicorn + SQLAlchemy 2.0 + asyncpg + httpx + pytest + pytest-asyncio
- `app/__init__.py`, `app/main.py` with FastAPI app setup, CORS, static file mounting, lifespan handler
- `app/api/routes.py` with placeholder endpoints: `POST /review`, `GET /health`
- `app/db/` with async PostgreSQL connection (SQLAlchemy 2.0 + asyncpg), graceful degradation when DB unavailable
- `app/db/models.py` with base SQLAlchemy model for review history
- `app/db/repository.py` with async CRUD operations
- `static/index.html`, `static/style.css`, `static/app.js` -- minimal shell matching Field-Change Accelerator look and feel
- `tests/conftest.py` with async test fixtures
- `.env.example` with documented configuration variables
- `CLAUDE.md` with project-specific agent instructions

**Acceptance Criteria**:
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /review` accepts a JSON body and returns a placeholder response
- [ ] Static files served at root (`/`)
- [ ] Browser shows the UI shell with header, input panel, output panel
- [ ] PostgreSQL connection works when available, gracefully degrades when not
- [ ] `pytest` runs and passes with at least one test
- [ ] Directory structure matches the reference architecture

**Files affected**:
- `requirements.txt` (NEW)
- `app/__init__.py` (NEW)
- `app/main.py` (NEW)
- `app/api/__init__.py` (NEW)
- `app/api/routes.py` (NEW)
- `app/db/__init__.py` (NEW)
- `app/db/connection.py` (NEW)
- `app/db/models.py` (NEW)
- `app/db/repository.py` (NEW)
- `app/engines/__init__.py` (NEW)
- `app/rules/__init__.py` (NEW)
- `app/models/__init__.py` (NEW)
- `app/formatter/__init__.py` (NEW)
- `static/index.html` (NEW)
- `static/style.css` (NEW)
- `static/app.js` (NEW)
- `tests/__init__.py` (NEW)
- `tests/conftest.py` (NEW)
- `tests/test_health.py` (NEW)
- `.env.example` (NEW)
- `CLAUDE.md` (NEW)

---

### WP-0.2 -- Pydantic Schemas (Input/Output Models)

**Priority**: 1 (parallel with WP-0.1)
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~40 tests

**Problem**: All engines, API routes, and the frontend depend on well-defined data contracts. The review input schema (review_type, artifact_type, code_or_diff, context, goal, technology_context, constraints, domain_pack, question_focus) and output schema (review_summary, findings, test_gaps, risk_notes, clean_core_hints, recommended_actions, overall_assessment) must be defined before any engine work begins.

**Deliverables**:
- `ReviewType` enum: SNIPPET_REVIEW, DIFF_REVIEW, PRE_MERGE_REVIEW, SOLUTION_DESIGN_REVIEW, TICKET_BASED_PRE_REVIEW, REGRESSION_RISK_REVIEW, CLEAN_CORE_ARCHITECTURE_CHECK
- `ArtifactType` enum: ABAP_CLASS, ABAP_METHOD, ABAP_REPORT, CDS_VIEW, CDS_PROJECTION, CDS_ANNOTATION, BEHAVIOR_DEFINITION, BEHAVIOR_IMPLEMENTATION, SERVICE_DEFINITION, SERVICE_BINDING, ODATA_SERVICE, UI5_VIEW, UI5_CONTROLLER, UI5_FRAGMENT, UI5_FORMATTER, FIORI_ELEMENTS_APP, MIXED_FULLSTACK
- `ReviewContext` enum: GREENFIELD, EXTENSION, BUGFIX, REFACTORING
- `QuestionFocus` enum: PERFORMANCE, MAINTAINABILITY, CLEAN_CORE, TESTS, SECURITY, READABILITY
- `TechnologyContext` model: sap_release (str | None), ui5_version (str | None), odata_version (enum V2|V4|None), rap_managed (bool | None), fiori_elements (bool | None)
- `ReviewRequest` model: review_type (ReviewType), artifact_type (ArtifactType), context_summary (str), code_or_diff (str), goal_of_review (str | None), technology_context (TechnologyContext | None), known_constraints (list[str] | None), domain_pack (str | None), question_focus (list[QuestionFocus] | None), language (enum DE|EN)
- `Severity` enum: CRITICAL, IMPORTANT, OPTIONAL, UNCLEAR
- `Finding` model: severity (Severity), title (str), observation (str), reasoning (str), impact (str), recommendation (str), artifact_reference (str | None), line_reference (str | None)
- `TestGap` model: category (enum: ABAP_UNIT, ACTION_VALIDATION, UI_BEHAVIOR, UI_ROLE, UI_FILTER_SEARCH, REGRESSION_SIDE_EFFECT), description (str), priority (str), suggested_test (str | None)
- `RiskNote` model: category (enum: FUNCTIONAL, MAINTAINABILITY, TESTABILITY, UPGRADE_CLEAN_CORE), description (str), severity (Severity), mitigation (str | None)
- `CleanCoreHint` model: finding (str), released_api_alternative (str | None), severity (Severity)
- `RecommendedAction` model: order (int), title (str), description (str), effort_hint (str | None), finding_references (list[str] | None)
- `MissingInformation` model: question (str), why_it_matters (str), default_assumption (str | None)
- `OverallAssessment` model: go_no_go (enum: GO, CONDITIONAL_GO, NO_GO), confidence (enum: HIGH, MEDIUM, LOW), summary (str)
- `ReviewResponse` model: review_summary (str), findings (list[Finding]), missing_information (list[MissingInformation]), test_gaps (list[TestGap]), recommended_actions (list[RecommendedAction]), risk_notes (list[RiskNote]), clean_core_hints (list[CleanCoreHint]), overall_assessment (OverallAssessment)
- Bilingual support fields (language enum: DE | EN)

**Acceptance Criteria**:
- [ ] All models validate with Pydantic v2 (model_validate round-trip)
- [ ] Minimal input (review_type + artifact_type + code_or_diff) validates successfully
- [ ] Full input with all optional fields validates successfully
- [ ] Enums cover all review types from the PDF spec
- [ ] Enums cover all artifact types from the PDF spec
- [ ] Severity model matches the spec (CRITICAL, IMPORTANT, OPTIONAL, UNCLEAR)
- [ ] JSON serialization/deserialization works for all models
- [ ] Finding model includes all fields: severity, title, observation, reasoning, impact, recommendation

**Files affected**:
- `app/models/__init__.py` (NEW)
- `app/models/schemas.py` (NEW)
- `app/models/enums.py` (NEW)
- `tests/test_schemas.py` (NEW)

---

### WP-0.3 -- Input Form + Basic UI Shell

**Priority**: 2 (after WP-0.1 scaffolding exists)
**Effort**: M
**Agent**: sap-frontend-developer
**Test Contribution**: ~15 tests (manual UI + API integration)

**Problem**: Users need a web workbench to paste code or diffs, select a review type and artifact type, and receive structured review findings. The UI must match the Field-Change Accelerator's look and feel (split-panel layout, dark/light mode, DE/EN toggle, same CSS design system) while exposing the Review Assistant's specific input schema.

**Deliverables**:
- Split-panel layout: left = input form, right = output/results
- Input form fields matching `ReviewRequest`: review type (dropdown), artifact type (dropdown), code or diff (large textarea with monospace font and line numbers), context summary (textarea), goal of review (text)
- Collapsible "Advanced Options" section: technology context fields (SAP release, UI5 version, OData version, RAP managed toggle, Fiori Elements toggle), known constraints (tag-style multi-input), domain pack (dropdown: EWM, Yard, Service, MII/MES, None), question focus (multi-select checkboxes: performance, maintainability, clean-core, tests, security, readability)
- Dark/light mode toggle (matching Field-Change Accelerator CSS custom properties)
- DE/EN language toggle with full bilingual support
- "Review" button that POSTs to `/review`
- Empty results panel with placeholder state
- Responsive layout for 1440px, 1680px, 1920px widths
- CSS design system: same custom properties, typography, color palette as Field-Change Accelerator

**Acceptance Criteria**:
- [ ] Form renders all required and optional input fields
- [ ] Code textarea supports monospace display and preserves whitespace
- [ ] "Review" button sends well-formed JSON to `POST /review`
- [ ] Dark/light mode toggle works with smooth transition
- [ ] DE/EN toggle switches all labels, placeholders, and tooltips
- [ ] Advanced options collapse/expand correctly
- [ ] Layout matches Field-Change Accelerator visual style
- [ ] Form validates required fields before submission (review_type, artifact_type, code_or_diff)

**Files affected**:
- `static/index.html` -- full HTML structure
- `static/style.css` -- complete CSS design system
- `static/app.js` -- form logic, API calls, language/theme toggles
- `app/engines/i18n.py` (NEW) -- translation keys for DE/EN

---

### WP-0.4 -- Findings Engine (Core Review Logic)

**Priority**: 2 (depends on WP-0.2 schemas)
**Effort**: L
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~80 tests

**Problem**: The central engine of the tool. Takes code or diff input along with review type and artifact type, applies rule-based analysis, and produces prioritized findings with severity, observation, reasoning, impact, and recommendation. Must be rule-based using frozen dataclass rules. This is the foundation engine -- all other output engines (test gaps, risks, actions) consume its findings.

**Deliverables**:
- `app/engines/review_type_detector.py` -- classifies the review type if set to AUTO or validates provided type; detects snippet vs diff vs design text patterns
- `app/engines/artifact_classifier.py` -- identifies artifact family from code patterns: ABAP keywords (CLASS, METHOD, REPORT, FUNCTION-POOL), CDS keywords (define view entity, define projection, annotate view), Behavior Definition keywords (managed implementation, define behavior), UI5 patterns (sap.ui.define, XMLView, Controller.extend), mixed detection
- `app/engines/findings_engine.py` -- main findings engine: iterates applicable rules against input, produces Finding objects with severity, applies severity model (CRITICAL: security/data-loss/crash, IMPORTANT: maintainability/correctness, OPTIONAL: style/improvement, UNCLEAR: needs more context)
- `app/rules/base_rules.py` -- frozen dataclass rule structure: Rule(id, name, description, artifact_types, severity, pattern, check_fn, recommendation_template)
- `app/rules/abap_basic.py` -- MVP ABAP rules: hardcoded SELECT without WHERE (performance), missing error handling after function call, SELECT * usage, missing authority check pattern, empty CATCH blocks, overly long methods (>100 lines heuristic), missing comments on complex logic, WRITE statement in non-report context, obsolete ABAP statements (MOVE, COMPUTE)
- `app/rules/cds_basic.py` -- MVP CDS rules: missing key fields, missing associations, performance-relevant annotations missing, missing @AbapCatalog annotations, CDS view without WHERE clause on large tables
- `app/rules/ui5_basic.py` -- MVP UI5 rules: missing i18n usage (hardcoded strings), missing error handling in OData calls, deprecated API usage, missing busy indicator patterns, controller without onInit
- Severity calibration: rules are tagged with default severity, engine can upgrade/downgrade based on context (e.g., missing auth check is CRITICAL in production, OPTIONAL in prototype)

**Acceptance Criteria**:
- [ ] Review type detector correctly identifies snippet vs diff vs design text
- [ ] Artifact classifier correctly identifies ABAP class, CDS view, Behavior Definition, UI5 controller from code
- [ ] Findings engine produces Finding objects with all required fields (severity, title, observation, reasoning, impact, recommendation)
- [ ] At least 8 ABAP basic rules produce findings on known-bad code
- [ ] At least 5 CDS basic rules produce findings on known-bad CDS
- [ ] At least 5 UI5 basic rules produce findings on known-bad UI5 code
- [ ] Severity model correctly assigns CRITICAL/IMPORTANT/OPTIONAL/UNCLEAR
- [ ] Engine handles mixed artifacts (code containing both ABAP and CDS) gracefully
- [ ] Works with both DE and EN output language

**Files affected**:
- `app/engines/review_type_detector.py` (NEW)
- `app/engines/artifact_classifier.py` (NEW)
- `app/engines/findings_engine.py` (NEW)
- `app/rules/base_rules.py` (NEW) -- frozen dataclass rule structure
- `app/rules/abap_basic.py` (NEW) -- MVP ABAP rules
- `app/rules/cds_basic.py` (NEW) -- MVP CDS rules
- `app/rules/ui5_basic.py` (NEW) -- MVP UI5 rules
- `tests/test_review_type_detector.py` (NEW)
- `tests/test_artifact_classifier.py` (NEW)
- `tests/test_findings_engine.py` (NEW)

---

### WP-0.5 -- Test-Gap Analyzer

**Priority**: 3 (depends on WP-0.4 findings)
**Effort**: M
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~50 tests

**Problem**: The fourth core function: given the artifact type and code, identify what tests are missing. Must detect: untested ABAP Unit paths, missing action/validation test coverage, UI behavior gaps (role tests, filter tests, search tests), and regression side-effect risks. Rule-based pattern matching against the code to identify testable concerns that lack corresponding test evidence.

**Deliverables**:
- `app/engines/test_gap_analyzer.py` -- test gap detection engine
- `app/rules/test_gap_rules.py` -- test gap detection rules per artifact type
- ABAP Unit gap detection: public methods without test class references, complex branches without path coverage hints, exception handling paths, authority check branches
- Action/Validation gap detection: actions defined in Behavior Definition without corresponding test suggestions, validations without negative-path test suggestions
- UI behavior gap detection: controllers with event handlers without OPA5/QUnit test hints, dynamic visibility logic without test coverage, model binding without integration test hints
- Regression side-effect detection: code touching shared/global data, modifications to standard SAP objects, cross-entity dependencies
- Each TestGap includes: category, description, priority, and suggested_test skeleton

**Acceptance Criteria**:
- [ ] ABAP code with public methods produces test gap findings
- [ ] Behavior Definition with actions produces action test gap findings
- [ ] UI5 controller with event handlers produces UI test gap findings
- [ ] Regression risks identified for code modifying shared data
- [ ] Each test gap has a concrete suggested_test description
- [ ] Priority ordering reflects risk (untested CRITICAL paths first)
- [ ] Works for all artifact types (ABAP, CDS, Behavior, UI5)

**Files affected**:
- `app/engines/test_gap_analyzer.py` (NEW)
- `app/rules/test_gap_rules.py` (NEW)
- `tests/test_test_gap_analyzer.py` (NEW)

---

### WP-0.6 -- Risk & Impact Engine

**Priority**: 3 (depends on WP-0.4 findings)
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~40 tests

**Problem**: The sixth core function: assess the reviewed code across four risk dimensions -- functional risk, maintainability risk, testability risk, and upgrade/clean-core risk. Aggregates signals from findings and test gaps into a structured risk view. Must also generate basic clean-core hints (unreleased API usage, direct table access, non-released CDS views).

**Deliverables**:
- `app/engines/risk_engine.py` -- risk assessment engine: aggregates findings by risk dimension, computes per-dimension risk level (LOW, MEDIUM, HIGH, CRITICAL)
- `app/engines/clean_core_checker.py` -- clean-core hint generator: detects unreleased API calls, direct DB access patterns, non-released CDS views, modification-dependent code, classic dynpro usage, obsolete technology patterns
- `app/rules/risk_rules.py` -- risk aggregation rules: finding severity weighting, threshold definitions per risk dimension
- `app/rules/clean_core_rules.py` -- clean-core pattern rules: unreleased API catalog (basic MVP set), direct DB access patterns (SELECT FROM <db_table>), modification markers (ENHANCEMENT-POINT, MODIFICATION)
- Functional risk: based on missing error handling, missing validation, incorrect data access patterns
- Maintainability risk: based on code complexity, naming violations, missing documentation, coupling
- Testability risk: based on test gap count and severity
- Upgrade/clean-core risk: based on clean-core hint count and severity

**Acceptance Criteria**:
- [ ] Risk engine produces risk levels for all four dimensions
- [ ] Risk level correlates with finding severity and count
- [ ] Clean-core checker detects unreleased API patterns
- [ ] Clean-core checker detects direct table access
- [ ] Clean-core checker detects modification-dependent code
- [ ] Each risk note includes category, description, severity, and mitigation
- [ ] Clean-core hints include released API alternatives where known

**Files affected**:
- `app/engines/risk_engine.py` (NEW)
- `app/engines/clean_core_checker.py` (NEW)
- `app/rules/risk_rules.py` (NEW)
- `app/rules/clean_core_rules.py` (NEW)
- `tests/test_risk_engine.py` (NEW)
- `tests/test_clean_core_checker.py` (NEW)

---

### WP-0.7 -- Pipeline Orchestration, Summary, Output Formatting

**Priority**: 4 (depends on WP-0.4, WP-0.5, WP-0.6)
**Effort**: L
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~80 tests

**Problem**: The engines (Findings, Test-Gap Analyzer, Risk & Impact, Clean-Core Checker) must be orchestrated into a pipeline that also generates the remaining core outputs: missing information questions, recommended correction order, refactoring hints, overall go/no-go assessment, and formatted output. The API endpoint must call this pipeline and the frontend must render the full review results.

**Deliverables**:
- `app/engines/pipeline.py` -- main orchestration: validate input -> detect review type -> classify artifact -> run findings engine -> run test-gap analyzer -> run risk engine -> run clean-core checker -> generate questions -> generate recommended actions -> generate refactoring hints -> assess go/no-go -> format output
- `app/engines/question_engine.py` -- Missing Information Engine: detects ambiguities in input and findings that require clarification ("Is this production code or prototype?", "What SAP release is targeted?", "Is authorization relevant here?", "What is the expected data volume?")
- `app/engines/action_engine.py` -- Recommended Actions Generator: orders corrections by priority (CRITICAL findings first), groups related findings, suggests correction sequence, estimates effort per action
- `app/engines/refactoring_engine.py` -- Refactoring Hint Generator: categorizes suggestions as small_fix, targeted_structure_improvement, medium_term_refactoring_hint; explicitly marks what is NOT an immediate rebuild
- `app/engines/assessment_engine.py` -- Overall Assessment: GO (no critical findings, acceptable risk), CONDITIONAL_GO (critical findings addressable, medium risk), NO_GO (blocking issues, high risk); includes confidence level
- `app/rules/questions.py` -- dedicated question rules by review type and artifact type
- `app/rules/refactoring_rules.py` -- refactoring pattern detection rules
- `app/formatter/output.py` -- format response as structured JSON and Markdown
- API endpoint `POST /review` wired to pipeline
- Frontend results rendering: review summary, findings list with severity badges, missing information, test gaps, recommended actions, risk dashboard, clean-core hints, overall assessment with go/no-go badge
- Results panel with collapsible sections per output category
- Export functionality: Markdown download

**Acceptance Criteria**:
- [ ] `POST /review` with minimal input returns a complete `ReviewResponse`
- [ ] All output sections are populated: findings, missing_information, test_gaps, recommended_actions, risk_notes, clean_core_hints, overall_assessment
- [ ] Findings are ordered by severity (CRITICAL first)
- [ ] Recommended actions reference specific findings
- [ ] Refactoring hints are categorized correctly (small_fix vs medium_term)
- [ ] Go/no-go assessment reflects finding severity distribution
- [ ] Missing information questions are contextually relevant
- [ ] Frontend renders all sections with expand/collapse
- [ ] Severity badges use color coding (red=CRITICAL, orange=IMPORTANT, blue=OPTIONAL, gray=UNCLEAR)
- [ ] Markdown export produces a complete review document
- [ ] Pipeline handles edge cases gracefully (empty code, unknown artifact type, minimal input)
- [ ] Bilingual output works (DE/EN)

**Files affected**:
- `app/engines/pipeline.py` (NEW)
- `app/engines/question_engine.py` (NEW)
- `app/engines/action_engine.py` (NEW)
- `app/engines/refactoring_engine.py` (NEW)
- `app/engines/assessment_engine.py` (NEW)
- `app/rules/questions.py` (NEW)
- `app/rules/refactoring_rules.py` (NEW)
- `app/formatter/output.py` (NEW)
- `app/api/routes.py` -- wire pipeline to POST /review
- `static/app.js` -- results rendering
- `static/style.css` -- results styling, severity badges, risk dashboard
- `tests/test_pipeline.py` (NEW)
- `tests/test_question_engine.py` (NEW)
- `tests/test_action_engine.py` (NEW)
- `tests/test_refactoring_engine.py` (NEW)
- `tests/test_assessment_engine.py` (NEW)

---

### WP-0.8 -- Example Case Library + Validation Tests

**Priority**: 5 (after pipeline is functional)
**Effort**: M
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~75 tests

**Problem**: No curated example cases exist to validate engine output quality or demonstrate the tool. The PDF specifies an Example Case Library for MVP. These cases serve triple duty: quality benchmarks, regression tests, and tool demonstration.

**Deliverables**:
- 12-15 curated example cases as a Python module
- Each case includes: review_type, artifact_type, code_or_diff (realistic SAP code snippet), expected_finding_count_range, expected_severity_distribution, expected_test_gap_categories, expected_risk_dimensions, domain_tag
- Coverage across artifact types: ABAP Class (2-3), CDS View (2-3), Behavior Definition (2), UI5 Controller (2), UI5 View (1), Mixed Fullstack (1-2), Service/OData (1)
- Coverage across review types: snippet review (majority), diff review (2), solution design review (1)
- Quality spectrum: clean code with few findings (1-2), moderately problematic code (majority), severely problematic code with CRITICAL findings (2-3)
- Edge cases: empty code input (1), very short snippet (1), ambiguous artifact type (1)
- A pytest module that runs each case through the pipeline and validates key output fields
- Cases also loadable as example scenarios in the UI ("Load Example" dropdown)

**Acceptance Criteria**:
- [ ] 12+ example cases defined with expected outputs
- [ ] Each case validates: artifact classification, finding count range, severity presence, test gap categories
- [ ] All major artifact types covered by at least one case
- [ ] Test file `tests/test_example_cases.py` passes
- [ ] Cases are accessible from the UI as "Load Example" options
- [ ] Edge cases produce reasonable output (not crashes)
- [ ] At least 2 cases produce CRITICAL findings
- [ ] At least 2 cases produce clean/minimal findings (to validate no false positives)

**Files affected**:
- `app/rules/example_cases.py` (NEW) -- case definitions with code snippets
- `tests/test_example_cases.py` (NEW) -- validation tests
- `static/app.js` -- "Load Example" dropdown integration
- `tests/conftest.py` -- shared fixtures for example cases

---

### Phase 0 Execution Waves

**Wave 1** (parallel, no dependencies):
- WP-0.1 (Project Scaffolding) -- Senior Developer
- WP-0.2 (Pydantic Schemas) -- sap-modern-fullstack-developer

**Wave 2** (depends on Wave 1):
- WP-0.3 (Input Form + UI Shell) -- sap-frontend-developer
- WP-0.4 (Findings Engine) -- sap-backend-abap-developer

**Wave 3** (depends on WP-0.4):
- WP-0.5 (Test-Gap Analyzer) -- sap-backend-abap-developer
- WP-0.6 (Risk & Impact Engine) -- sap-modern-fullstack-developer

**Wave 4** (depends on WP-0.5 + WP-0.6):
- WP-0.7 (Pipeline + Summary + Output) -- sap-modern-fullstack-developer

**Wave 5** (depends on WP-0.7):
- WP-0.8 (Example Cases + Tests) -- sap-backend-abap-developer

**Phase 0 Test Target**: 400+ tests across all WPs

---

## Phase 1: v1 -- Solid Practice Version

### WP-1.1 -- ABAP Readability & Structure + Error Handling & Testability Rule Packs

**Priority**: 1 (primary v1 rule expansion)
**Effort**: L
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~60 tests

**Problem**: The MVP has basic ABAP rules. v1 needs deep, SAP-expert-quality rule packs covering ABAP readability and structure (naming conventions, method length, parameter count, class cohesion, commented-out code, dead code detection, string handling, type usage) and error handling and testability (exception class usage, TRY/CATCH patterns, testable method signatures, dependency injection hints, test double friendliness).

**Deliverables**:
- `app/rules/abap_readability.py` -- ABAP Readability & Structure Pack:
  - Naming convention violations (variables, methods, classes per SAP naming guidelines)
  - Method length heuristic (>50 lines warning, >100 lines important)
  - Parameter count (>5 parameters warning)
  - Commented-out code detection
  - Dead code patterns (unreachable code after RETURN/RAISE)
  - String literal duplication
  - Obsolete type usage (C, N, P vs modern types)
  - Missing method documentation (ABAP Doc)
  - Inline declaration opportunities (DATA vs inline)
  - Magic number detection
- `app/rules/abap_error_handling.py` -- ABAP Error Handling & Testability Pack:
  - Empty CATCH blocks
  - Generic CX_ROOT catches without specific handling
  - Missing CLEANUP blocks in TRY/CATCH
  - RAISE EXCEPTION without message
  - Missing RESUMABLE exception handling
  - Method signatures unfriendly to test doubles (no interfaces, concrete class dependencies)
  - Global data dependencies (class-data usage, static method overuse)
  - Factory pattern absence for testability
  - Missing constructor injection patterns

**Acceptance Criteria**:
- [ ] At least 12 readability rules produce findings on realistic ABAP code
- [ ] At least 10 error handling/testability rules produce findings
- [ ] Rules are frozen dataclasses consistent with base_rules.py structure
- [ ] Each rule has a unique ID, clear description, and actionable recommendation
- [ ] Rules do not produce excessive false positives on clean code
- [ ] Rule severity is calibrated (naming = OPTIONAL, empty CATCH = IMPORTANT, missing auth = CRITICAL)

**Files affected**:
- `app/rules/abap_readability.py` (NEW)
- `app/rules/abap_error_handling.py` (NEW)
- `app/engines/findings_engine.py` -- register new rule packs
- `tests/test_abap_readability_rules.py` (NEW)
- `tests/test_abap_error_handling_rules.py` (NEW)

---

### WP-1.2 -- CDS / Annotation Review Pack + RAP Consistency Pack

**Priority**: 1 (parallel with WP-1.1)
**Effort**: L
**Agent**: sap-modern-fullstack-developer-cap-first
**Test Contribution**: ~55 tests

**Problem**: The MVP has basic CDS rules. v1 needs expert-quality CDS/Annotation and RAP Consistency packs covering: CDS view layering correctness, annotation completeness and correctness, association/composition patterns, Behavior Definition consistency with CDS model, action/validation/determination completeness, draft handling correctness, managed vs unmanaged pattern adherence.

**Deliverables**:
- `app/rules/cds_annotation.py` -- CDS / Annotation Review Pack:
  - CDS view layering violations (Interface -> Projection -> Consumption wrong order)
  - Missing @AbapCatalog.sqlViewName or @AbapCatalog.viewEnhancementCategory
  - Missing or incorrect @ObjectModel annotations
  - Annotation overkill on interface views (annotations belong on projection/metadata extension)
  - Missing @Semantics annotations for currency, quantity, date fields
  - Association cardinality issues
  - Composition vs association misuse
  - Missing @Search annotations for searchable fields
  - Value help annotation completeness (@Consumption.valueHelpDefinition)
  - Missing @UI annotations on projection/metadata extension
- `app/rules/rap_consistency.py` -- RAP Consistency Pack:
  - Behavior Definition entity references not matching CDS model
  - Actions defined but missing implementation class binding
  - Validations defined but likely untested (heuristic)
  - Determinations on wrong trigger (create vs save)
  - Draft handling incomplete (missing draft actions, missing draft determine actions)
  - Managed implementation with unmanaged patterns (conflicting approach)
  - Missing authorization master/instance annotations
  - Missing feature control for conditional actions
  - Numbering (early/late) inconsistency with managed approach
  - Side-effects annotation missing for actions modifying multiple fields

**Acceptance Criteria**:
- [ ] At least 10 CDS/Annotation rules produce findings
- [ ] At least 10 RAP Consistency rules produce findings
- [ ] CDS rules distinguish between interface view and projection view context
- [ ] RAP rules detect inconsistency between Behavior Definition and CDS model
- [ ] Draft handling rules detect incomplete draft setup
- [ ] Rules use frozen dataclass structure from base_rules.py
- [ ] False positive rate is acceptable on well-written CDS/RAP code

**Files affected**:
- `app/rules/cds_annotation.py` (NEW)
- `app/rules/rap_consistency.py` (NEW)
- `app/engines/findings_engine.py` -- register new rule packs
- `tests/test_cds_annotation_rules.py` (NEW)
- `tests/test_rap_consistency_rules.py` (NEW)

---

### WP-1.3 -- UI5 Freestyle + Fiori Elements Review Rule Packs

**Priority**: 1 (parallel with WP-1.1, WP-1.2)
**Effort**: L
**Agent**: sap-frontend-developer
**Test Contribution**: ~50 tests

**Problem**: The MVP has basic UI5 rules. v1 needs expert-quality rule packs for both UI5 Freestyle development and Fiori Elements configuration, covering: controller patterns, model handling, binding patterns, fragment usage, formatter best practices, and Fiori Elements annotation-driven configuration correctness.

**Deliverables**:
- `app/rules/ui5_freestyle.py` -- UI5 Freestyle Review Pack:
  - Missing model destroy in onExit
  - Synchronous XMLHttpRequest usage
  - Direct DOM manipulation instead of control API
  - Missing formatter for date/currency/number display
  - Hardcoded paths in model binding
  - Missing metadata.json manifest entries
  - Deprecated control usage (sap.ui.commons, sap.viz)
  - Missing fragment reuse opportunities (duplicate XML structures)
  - Event handler not unregistered on detach
  - Missing accessibility attributes (ariaLabel, tooltip)
  - Routing without parameter validation
  - Missing busy state management during async operations
- `app/rules/fiori_elements.py` -- Fiori Elements Review Pack:
  - Incomplete List Report configuration (missing selection fields, line items)
  - Object Page without header info
  - Missing criticality/importance on key fields
  - Filter bar configuration gaps
  - Action annotation issues (missing @UI.lineItem type DataFieldForAction)
  - Navigation configuration gaps (target annotation missing)
  - Missing i18n for annotation labels
  - Value help configuration issues
  - Extension point misuse (breaking Fiori Elements patterns)
  - Missing variant management configuration

**Acceptance Criteria**:
- [ ] At least 12 UI5 Freestyle rules produce findings
- [ ] At least 10 Fiori Elements rules produce findings
- [ ] UI5 rules detect common anti-patterns in realistic controller code
- [ ] Fiori Elements rules detect annotation configuration gaps
- [ ] Rules distinguish between UI5 Freestyle and Fiori Elements context
- [ ] Deprecated API detection covers SAP UI5 lifecycle
- [ ] Rules follow frozen dataclass structure

**Files affected**:
- `app/rules/ui5_freestyle.py` (NEW)
- `app/rules/fiori_elements.py` (NEW)
- `app/engines/findings_engine.py` -- register new rule packs
- `tests/test_ui5_freestyle_rules.py` (NEW)
- `tests/test_fiori_elements_rules.py` (NEW)

---

### WP-1.4 -- Service / OData Exposure Rule Pack

**Priority**: 2 (after initial rule packs establish pattern)
**Effort**: M
**Agent**: sap-modern-fullstack-developer-cap-first
**Test Contribution**: ~35 tests

**Problem**: Service Definition and OData Binding patterns have their own review concerns: over-exposure of entities, missing authorization on service level, OData V2 vs V4 issues, missing $expand/$filter support, batch handling, etag handling, deep insert support. The MVP has no service-level rules.

**Deliverables**:
- `app/rules/service_odata.py` -- Service / OData Exposure Pack:
  - Service Definition exposing internal/interface views instead of projections
  - Missing authorization on Service Binding level
  - Excessive entity exposure (every entity exposed, no scoping)
  - Missing etag handling for concurrency
  - OData V2 patterns used with V4 binding (or vice versa)
  - Missing $expand support for navigation properties
  - Missing filter restrictions annotation
  - Batch request handling concerns
  - Deep insert/update support gaps
  - Missing service documentation/description
  - Cross-service reference issues
  - Missing pagination support for large entity sets

**Acceptance Criteria**:
- [ ] At least 10 service/OData rules produce findings
- [ ] Rules detect over-exposure patterns
- [ ] Rules detect authorization gaps at service level
- [ ] OData version mismatch detected
- [ ] Etag and concurrency rules produce actionable findings
- [ ] Rules apply to Service Definition and Service Binding artifacts

**Files affected**:
- `app/rules/service_odata.py` (NEW)
- `app/engines/findings_engine.py` -- register new rule pack
- `tests/test_service_odata_rules.py` (NEW)

---

### WP-1.5 -- Domain Packs (EWM, Yard, Service, MII/MES)

**Priority**: 2 (parallel with WP-1.4)
**Effort**: L
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~40 tests

**Problem**: Generic rules miss domain-specific review concerns. Yard Logistics, EWM, Service, and MII/MES each have unique patterns, common mistakes, performance pitfalls, and integration concerns. Domain packs add context-aware findings when the domain is detected.

**Deliverables**:
- `app/rules/domains/` directory with domain pack modules
- Yard Logistics pack: gate process timing issues, carrier integration patterns, slot management concurrency, RF device UI concerns, yard task sequencing, check-in/check-out flow completeness
- EWM/WM pack: warehouse task confirmation patterns, HU handling complexity, RF transaction patterns, performance on large warehouse operations, stock consistency checks, movement type validation
- Service pack: service order approval flow completeness, warranty/SLA calculation patterns, notification workflow concerns, technician assignment logic, spare part reservation handling
- MII/MES pack: production order confirmation timing, shopfloor control communication patterns, real-time data handling concerns, MES integration robustness, operator UI simplicity
- Domain auto-detection from context_summary, code patterns, and domain_pack field
- Domain-specific rules merge with generic rules at runtime, adding domain-relevant findings

**Acceptance Criteria**:
- [ ] Domain is auto-detected from input text or explicit domain_pack field
- [ ] Domain-specific findings appear alongside generic findings
- [ ] Each domain pack has at least 5 domain-specific rules
- [ ] Domain-specific findings include domain context in reasoning
- [ ] Generic analysis works unchanged when no domain detected
- [ ] Domain rules follow frozen dataclass structure

**Files affected**:
- `app/rules/domains/__init__.py` (NEW)
- `app/rules/domains/yard.py` (NEW)
- `app/rules/domains/ewm.py` (NEW)
- `app/rules/domains/service.py` (NEW)
- `app/rules/domains/mii_mes.py` (NEW)
- `app/engines/findings_engine.py` -- domain-aware rule loading
- `app/engines/pipeline.py` -- domain detection integration
- `tests/test_domain_packs.py` (NEW)

---

### WP-1.6 -- Solution Design Review Mode

**Priority**: 3 (after rule packs are solid)
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~35 tests

**Problem**: The MVP handles code snippets and diffs. v1 must also support Solution Design Review: users paste a design description, architecture sketch, or technical concept text instead of code, and the tool reviews it for completeness, feasibility, risk, and missing considerations. Different rules apply to design text vs code.

**Deliverables**:
- `app/engines/design_reviewer.py` -- solution design review engine: analyzes text for architectural completeness, technology choices, missing considerations
- `app/rules/design_review_rules.py` -- design review rules:
  - Missing error handling strategy in design
  - Missing authorization concept
  - Missing test strategy
  - Missing performance considerations for listed data volumes
  - Missing migration/cutover plan for extension scenarios
  - Technology choice concerns (e.g., using V2 when V4 is available)
  - Missing clean-core considerations
  - Missing integration point documentation
  - Incomplete entity model (entities mentioned but not fully specified)
  - Missing UI pattern justification
- Design review produces findings with the same severity model but different rule set
- Design review generates more "missing information" questions than code review
- Pipeline detects SOLUTION_DESIGN_REVIEW type and routes to design_reviewer

**Acceptance Criteria**:
- [ ] Solution design text produces design-specific findings
- [ ] Findings focus on completeness and feasibility, not syntax
- [ ] Missing information questions are extensive for design reviews
- [ ] Risk assessment reflects architectural risk rather than code risk
- [ ] Design review output is clearly distinguished from code review output
- [ ] Pipeline correctly routes based on review_type

**Files affected**:
- `app/engines/design_reviewer.py` (NEW)
- `app/rules/design_review_rules.py` (NEW)
- `app/engines/pipeline.py` -- route SOLUTION_DESIGN_REVIEW
- `static/app.js` -- design review input mode (larger text area, no line numbers)
- `tests/test_design_reviewer.py` (NEW)

---

### WP-1.7 -- History + Feedback

**Priority**: 3 (parallel with WP-1.6)
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~30 tests

**Problem**: The MVP has no persistence beyond the current session. v1 needs review history (stored in PostgreSQL) so users can revisit past reviews, and a feedback mechanism (thumbs up/down per finding) to guide rule quality improvement.

**Deliverables**:
- History panel: sidebar or tab showing past reviews (timestamp, artifact type, review type, finding count, overall assessment)
- History detail: click a past review to reload its full output
- History stored via PostgreSQL (graceful degradation when DB unavailable -- history panel hidden)
- "Load from History" replaces current output panel
- Clear history / delete individual entries
- Feedback mechanism: thumbs up/down per finding + optional comment
- Feedback stored alongside review record in PostgreSQL
- Feedback summary visible in history (how many findings were rated helpful)

**Acceptance Criteria**:
- [ ] History panel shows past reviews sorted by date
- [ ] Clicking a history entry loads its full output
- [ ] History works when PostgreSQL available, panel hidden when not
- [ ] Delete and clear functions work
- [ ] Feedback per finding is stored and displayed
- [ ] Feedback data is queryable for rule quality analysis

**Files affected**:
- `static/style.css` -- history panel styling, feedback UI styling
- `static/index.html` -- history panel markup
- `static/app.js` -- history logic, feedback logic, API calls
- `app/api/routes.py` -- history endpoints (GET /history, GET /history/{id}, DELETE /history/{id}), feedback endpoint (POST /review/{id}/feedback)
- `app/db/repository.py` -- history CRUD, feedback CRUD
- `app/db/models.py` -- review history model, feedback model
- `tests/test_history.py` (NEW)
- `tests/test_feedback.py` (NEW)

---

### WP-1.8 -- UI Polish + Template Outputs

**Priority**: 4 (after all v1 features)
**Effort**: M
**Agent**: sap-frontend-developer
**Test Contribution**: ~25 tests

**Problem**: v1 adds significant rule packs and features. The UI needs a cohesion pass and template output support: users should be able to export reviews in different formats (Markdown, structured text, clipboard-friendly format for ticket comments).

**Deliverables**:
- UI beautification: typography refinement, spacing fixes, card styling, severity badge refinement, skeleton loading animation, print stylesheet
- Template output formats: Markdown (full review document), Ticket Comment (condensed format for JIRA/ServiceNow), Clipboard (plain text summary)
- Export buttons per format
- Finding detail expansion: click a finding to see full reasoning/impact/recommendation (collapsed by default showing title + severity)
- Complexity/risk heuristic visualization: simple bar or indicator per risk dimension
- Responsive refinements for 1440px-1920px

**Acceptance Criteria**:
- [ ] UI matches Field-Change Accelerator visual quality
- [ ] Markdown export produces clean review document
- [ ] Ticket comment export is concise and actionable
- [ ] Clipboard copy works with one click
- [ ] Finding expansion/collapse works smoothly
- [ ] Risk visualization is clear and informative
- [ ] Print stylesheet produces clean output

**Files affected**:
- `static/style.css` -- beautification, print stylesheet
- `static/index.html` -- template output markup
- `static/app.js` -- export logic, finding expansion, risk visualization
- `app/formatter/output.py` -- add ticket comment and clipboard formats
- `app/formatter/templates.py` (NEW) -- output templates per format
- `tests/test_output_formats.py` (NEW)

---

### Phase 1 Execution Waves

**Wave 1** (parallel, all rule packs):
- WP-1.1 (ABAP Rule Packs) -- sap-backend-abap-developer
- WP-1.2 (CDS/Annotation + RAP Consistency Packs) -- sap-modern-fullstack-developer-cap-first
- WP-1.3 (UI5 + Fiori Elements Rule Packs) -- sap-frontend-developer

**Wave 2** (depends on Wave 1 patterns established):
- WP-1.4 (Service/OData Rule Pack) -- sap-modern-fullstack-developer-cap-first
- WP-1.5 (Domain Packs) -- sap-backend-abap-developer

**Wave 3** (depends on all rule packs):
- WP-1.6 (Solution Design Review) -- sap-modern-fullstack-developer
- WP-1.7 (History + Feedback) -- sap-modern-fullstack-developer

**Wave 4** (after all v1 features):
- WP-1.8 (UI Polish + Template Outputs) -- sap-frontend-developer

**Phase 1 Test Target**: 800+ tests cumulative (400 from MVP + 330 from v1 WPs)

---

## Phase 2: v2 -- Premium

### WP-2.1 -- Diff & Multi-Artifact Input

**Priority**: 1 (key v2 differentiator)
**Effort**: L
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~50 tests

**Problem**: The MVP and v1 review single code snippets. v2 must support diff-based review (git diff, transport comparison) and multi-artifact review (a change package containing CDS + Behavior + UI5 changes together). The diff parser must understand added/removed/modified lines and focus findings on changed code.

**Deliverables**:
- `app/engines/diff_parser.py` -- unified diff parser: extracts added/removed/modified lines, identifies changed files/artifacts, maps line numbers between old and new
- `app/engines/multi_artifact_handler.py` -- multi-artifact input handler: splits a change package into individual artifacts, identifies artifact type per section, runs review per artifact, consolidates findings
- Enhanced input UI: tab for "Single Snippet", tab for "Diff", tab for "Change Package"
- Diff-aware findings: findings reference specific diff hunks, changed lines highlighted, findings on unchanged code marked as "pre-existing" vs "introduced by this change"
- Change package input format: separator-delimited sections with artifact type headers, or multiple text areas

**Acceptance Criteria**:
- [ ] Unified diff parsed correctly (added/removed/modified lines identified)
- [ ] Multi-artifact input correctly splits into individual artifacts
- [ ] Findings reference specific changed lines in diff context
- [ ] Pre-existing issues distinguished from newly introduced issues
- [ ] Change package review consolidates findings across artifacts
- [ ] UI supports all three input modes with clean tab switching

**Files affected**:
- `app/engines/diff_parser.py` (NEW)
- `app/engines/multi_artifact_handler.py` (NEW)
- `app/engines/pipeline.py` -- diff-aware and multi-artifact pipeline routing
- `app/models/schemas.py` -- InputMode enum, enhanced ReviewRequest
- `static/app.js` -- tabbed input modes, diff rendering
- `static/style.css` -- diff highlighting, tab styling
- `tests/test_diff_parser.py` (NEW)
- `tests/test_multi_artifact.py` (NEW)

---

### WP-2.2 -- Cross-Artifact Consistency Checker

**Priority**: 2 (depends on WP-2.1 multi-artifact support)
**Effort**: M
**Agent**: sap-modern-fullstack-developer-cap-first
**Test Contribution**: ~40 tests

**Problem**: When reviewing a change package with multiple artifacts, cross-artifact consistency matters: CDS view field changes must match Behavior Definition, UI5 binding paths must match OData entity structure, annotation changes must match CDS model changes. No single-artifact rule can catch these cross-cutting issues.

**Deliverables**:
- `app/engines/cross_artifact_checker.py` -- cross-artifact consistency engine
- `app/rules/cross_artifact_rules.py` -- cross-artifact rules:
  - CDS field added but not exposed in Behavior Definition
  - Action added in Behavior Definition but missing UI annotation
  - OData entity field changed but UI binding not updated
  - CDS association added but not navigable in service
  - UI5 binding path references non-existent OData property
  - Authorization annotation changed but UI feature control not updated
  - Draft field added but draft table not extended
  - Value help CDS view changed but consumption annotation not updated
- Cross-artifact findings reference both artifacts involved
- Findings include "consistency" tag for filtering

**Acceptance Criteria**:
- [ ] Cross-artifact checker detects CDS-Behavior inconsistency
- [ ] Cross-artifact checker detects CDS-UI binding mismatch
- [ ] Findings reference both artifacts involved in the inconsistency
- [ ] At least 8 cross-artifact rules produce findings
- [ ] Works only when multi-artifact input is provided (no false triggers on single artifact)

**Files affected**:
- `app/engines/cross_artifact_checker.py` (NEW)
- `app/rules/cross_artifact_rules.py` (NEW)
- `app/engines/pipeline.py` -- integrate cross-artifact check for multi-artifact input
- `tests/test_cross_artifact_checker.py` (NEW)

---

### WP-2.3 -- Clean-Core / Released-API Deep Rules

**Priority**: 2 (parallel with WP-2.2)
**Effort**: M
**Agent**: sap-backend-abap-developer
**Test Contribution**: ~35 tests

**Problem**: The MVP has basic clean-core hints. v2 needs a comprehensive clean-core rule set: released API catalog (broader set), key user extensibility patterns, side-by-side extension patterns, deprecated technology detection (classic dynpro, ALV grid, SAP Script, SAPConnect), and upgrade impact assessment for non-clean-core code.

**Deliverables**:
- `app/rules/clean_core_deep.py` -- expanded clean-core rules:
  - Broader released API pattern catalog (beyond MVP basics)
  - Key user extensibility pattern detection (custom fields, custom logic)
  - Side-by-side extension patterns (BTP integration, event-driven)
  - Classic technology detection: dynpro (PROCESS BEFORE OUTPUT, MODULE), ALV (REUSE_ALV_GRID_DISPLAY), SAP Script (OPEN_FORM), SAPConnect
  - BAdI implementation vs modification detection
  - Enhancement implementation detection and upgrade risk
  - Implicit enhancement usage warning
  - Kernel method calls and SAP_BASIS dependency detection
  - Direct DDIC table access vs CDS view access
  - Custom table maintenance generator usage
- Upgrade impact scoring: estimates upgrade risk based on non-clean-core pattern count and severity
- Clean-core migration suggestions: for each non-clean-core pattern, suggest the clean-core alternative

**Acceptance Criteria**:
- [ ] Released API catalog covers at least 50 common unreleased APIs with alternatives
- [ ] Classic technology patterns detected (dynpro, ALV, SAP Script)
- [ ] Enhancement and modification patterns detected with upgrade risk
- [ ] Upgrade impact score reflects clean-core adherence level
- [ ] Migration suggestions are actionable and reference specific clean-core alternatives
- [ ] Rules work for both S/4HANA and BTP context

**Files affected**:
- `app/rules/clean_core_deep.py` (NEW)
- `app/engines/clean_core_checker.py` -- integrate deep rules
- `app/rules/clean_core_rules.py` -- expand released API catalog
- `tests/test_clean_core_deep.py` (NEW)

---

### WP-2.4 -- Similarity Search + Past Reviews

**Priority**: 3
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~30 tests

**Problem**: No mechanism to leverage past reviews for current analysis. If similar code was reviewed before, its findings and resolutions are valuable context. v2 adds similarity search: when a new review starts, the system finds similar past reviews and surfaces relevant findings, patterns, and resolutions.

**Deliverables**:
- `app/engines/similarity.py` -- similarity search engine: matches current input against past reviews by artifact_type + keyword overlap + code structure similarity (simple TF-IDF or Jaccard on tokenized code)
- Similar past reviews display: when reviewing, show 1-3 similar past reviews with their findings and resolutions
- Pattern detection: if the same finding appears across multiple reviews, flag it as "recurring pattern" with higher confidence
- Feedback-informed relevance: past reviews with positive feedback ranked higher
- Statistics dashboard: most common findings, most common artifact types, recurring patterns

**Acceptance Criteria**:
- [ ] Similarity matching finds relevant past reviews by artifact type and code patterns
- [ ] Similar reviews displayed alongside current review results
- [ ] Recurring patterns flagged across multiple reviews
- [ ] Statistics dashboard shows aggregate review data
- [ ] Works without PostgreSQL (similarity features gracefully hidden)

**Files affected**:
- `app/engines/similarity.py` (NEW)
- `app/db/repository.py` -- similarity query methods
- `app/api/routes.py` -- statistics endpoint, similar reviews endpoint
- `static/app.js` -- similar reviews display, statistics page
- `static/style.css` -- similar reviews styling, statistics styling
- `tests/test_similarity.py` (NEW)

---

### WP-2.5 -- Team Review Workflows

**Priority**: 3 (parallel with WP-2.4)
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~30 tests

**Problem**: The tool is single-user. v2 adds team workflow support: shared review sessions, review assignment, finding acknowledgment (accepted/rejected/deferred), and review completion tracking. Enables use in team code review processes.

**Deliverables**:
- Review session model: a review can be assigned to a reviewer, findings can be individually acknowledged (accepted, rejected with reason, deferred)
- Finding status tracking: each finding has a resolution status (OPEN, ACCEPTED, REJECTED, DEFERRED, FIXED)
- Review completion metric: percentage of findings addressed
- Shared review link: URL with review ID that loads the review for any team member
- Export with acknowledgment status: Markdown/ticket export includes finding resolution status
- Lightweight -- no authentication in v2 (reviewer name is self-reported)

**Acceptance Criteria**:
- [ ] Findings can be individually acknowledged with status
- [ ] Review completion percentage calculated correctly
- [ ] Shared review link loads the correct review
- [ ] Export includes finding resolution status
- [ ] Works without PostgreSQL (team features hidden)

**Files affected**:
- `app/db/models.py` -- finding resolution status, reviewer fields
- `app/db/repository.py` -- resolution CRUD
- `app/api/routes.py` -- finding resolution endpoints, shared review endpoint
- `app/models/schemas.py` -- FindingResolution model
- `static/app.js` -- finding acknowledgment UI, completion tracking, shared links
- `static/style.css` -- acknowledgment styling
- `tests/test_team_workflows.py` (NEW)

---

### WP-2.6 -- CI/Merge-Ready Export

**Priority**: 4
**Effort**: M
**Agent**: sap-modern-fullstack-developer
**Test Contribution**: ~25 tests

**Problem**: Users want to integrate review results into CI/merge pipelines. v2 adds machine-readable export formats: JSON (for CI tools), SARIF (for GitHub/Azure DevOps code scanning), and quality gate logic (pass/fail based on finding severity thresholds).

**Deliverables**:
- `app/formatter/sarif.py` -- SARIF v2.1.0 format export (Static Analysis Results Interchange Format)
- `app/formatter/ci_json.py` -- CI-friendly JSON export with quality gate result
- `app/engines/quality_gate.py` -- quality gate engine: configurable thresholds (e.g., "fail if any CRITICAL finding", "warn if >3 IMPORTANT findings")
- Quality gate configuration in request or server config
- API endpoint `POST /review` with `?format=sarif` or `?format=ci_json` query parameter
- Quality gate result included in standard review response

**Acceptance Criteria**:
- [ ] SARIF export is valid SARIF v2.1.0
- [ ] CI JSON export includes quality gate pass/fail
- [ ] Quality gate thresholds are configurable
- [ ] SARIF can be uploaded to GitHub Code Scanning or Azure DevOps
- [ ] Quality gate integrates with overall assessment (NO_GO when gate fails)

**Files affected**:
- `app/formatter/sarif.py` (NEW)
- `app/formatter/ci_json.py` (NEW)
- `app/engines/quality_gate.py` (NEW)
- `app/api/routes.py` -- format query parameter support
- `app/models/schemas.py` -- QualityGateConfig, QualityGateResult models
- `tests/test_sarif_export.py` (NEW)
- `tests/test_quality_gate.py` (NEW)

---

### WP-2.7 -- UI Premium + Cohesion Pass

**Priority**: 4 (after all v2 features)
**Effort**: M
**Agent**: sap-frontend-developer
**Test Contribution**: ~20 tests

**Problem**: v2 adds significant new UI surface area (diff input, multi-artifact tabs, cross-artifact findings, similarity display, team workflows, CI export). The UI needs a cohesion pass: consistent interaction patterns, transitions, responsive behavior, and performance optimization.

**Deliverables**:
- UI cohesion pass: consistent card styling, interaction patterns, transitions across all v2 features
- Performance: lazy rendering for large finding lists, virtualized scrolling if needed
- Accessibility: keyboard navigation, ARIA labels, focus management
- Responsive: all v2 features work at 1440px-1920px
- Code organization: if vanilla JS has grown too large, extract into ES6 modules
- Error handling: consistent error display, retry logic, timeout handling
- Diff syntax highlighting: basic syntax coloring in diff view for ABAP/CDS/UI5

**Acceptance Criteria**:
- [ ] All v2 features have consistent visual treatment
- [ ] No perceptible lag for reviews with 50+ findings
- [ ] Keyboard navigation works through all interactive elements
- [ ] Responsive at 1440px, 1680px, 1920px
- [ ] Error states handled gracefully with user-friendly messages
- [ ] app.js organized into logical modules (if size warrants)
- [ ] Diff view has basic syntax highlighting

**Files affected**:
- `static/style.css` -- cohesion updates, transitions, accessibility
- `static/app.js` -- refactoring, performance, error handling (possibly split into modules)
- `static/index.html` -- ARIA labels, semantic improvements
- `tests/test_e2e.py` (NEW) -- basic end-to-end tests

**Phase 2 Test Target**: 1200+ tests cumulative (800 from v1 + 230 from v2 WPs)

---

### Phase 2 Execution Waves

**Wave 1** (parallel):
- WP-2.1 (Diff & Multi-Artifact Input) -- sap-modern-fullstack-developer
- WP-2.3 (Clean-Core Deep Rules) -- sap-backend-abap-developer

**Wave 2** (depends on WP-2.1):
- WP-2.2 (Cross-Artifact Consistency) -- sap-modern-fullstack-developer-cap-first
- WP-2.4 (Similarity Search) -- sap-modern-fullstack-developer

**Wave 3** (parallel):
- WP-2.5 (Team Review Workflows) -- sap-modern-fullstack-developer
- WP-2.6 (CI/Merge Export) -- sap-modern-fullstack-developer

**Wave 4** (after all v2 features):
- WP-2.7 (UI Premium + Cohesion Pass) -- sap-frontend-developer

---

## Phase 3: v3 -- LLM-Augmented (Deferred)

Phase 3 adds LLM intelligence while keeping the rule-based engine as default and fallback. Feature-flagged via `LLM_ENABLED=false` (default). Same pattern as the Field-Change Accelerator and Skeleton Generator Phase 3.

### WP-3.1 -- LLM Infrastructure + Provider Abstraction (Deferred)

**Effort**: M | **Agent**: Senior Developer

LLM provider abstraction (Protocol class), Claude provider implementation, `LLM_ENABLED` feature flag, graceful fallback to rule-based, token usage tracking, rate limiting. Identical pattern to sibling projects WP-3.1.

### WP-3.2 -- LLM-Powered Semantic Code Analysis (Deferred)

**Effort**: L | **Agent**: sap-backend-abap-developer

Use LLM to understand code semantics beyond pattern matching: detect logical errors, understand business intent from code structure, identify subtle bugs that regex rules cannot catch. Fallback: rule-based findings only. This is the highest-value LLM feature -- turns pattern matching into semantic understanding.

### WP-3.3 -- LLM-Enhanced Finding Explanations (Deferred)

**Effort**: M | **Agent**: sap-backend-abap-developer

Use LLM to generate context-aware, natural-language explanations for findings. Instead of template text, each finding gets a tailored explanation referencing the specific code context. Fallback: template-based explanations from rule definitions.

### WP-3.4 -- LLM-Powered Fix Suggestions (Deferred)

**Effort**: L | **Agent**: sap-backend-abap-developer

Use LLM to generate semi-automatic fix suggestions: for each finding, produce a code diff showing the recommended change. Particularly valuable for refactoring hints and clean-core migration. Fallback: textual recommendation only.

### WP-3.5 -- LLM-Powered Design Review (Deferred)

**Effort**: M | **Agent**: sap-modern-fullstack-developer

Enhance solution design review (WP-1.6) with LLM-powered analysis: understand architectural intent from natural language, detect logical gaps in design descriptions, generate comprehensive question lists. Fallback: rule-based design review.

### WP-3.6 -- Confidence Calibration + Quality Dashboard (Deferred)

**Effort**: M | **Agent**: Senior Developer

Side-by-side comparison of rule-based vs LLM findings, confidence calibration based on feedback data, quality metrics dashboard, false-positive tracking. Helps tune the hybrid approach over time.

### Phase 3 Execution Order (When Activated)

**Wave 1**: WP-3.1 (LLM Infrastructure) -- must come first
**Wave 2**: WP-3.2 (Semantic Analysis) + WP-3.4 (Fix Suggestions) -- parallel
**Wave 3**: WP-3.3 (Finding Explanations) + WP-3.5 (Design Review Enhancement) -- parallel
**Wave 4**: WP-3.6 (Quality Dashboard)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Findings Engine produces false positives on well-written code | HIGH | Example case library includes clean code cases; feedback mechanism tracks false positive rate; severity calibration per rule |
| Regex-based code parsing is fragile for malformed or partial code | HIGH | Parse defensively; treat parse failures as "unable to parse" findings; degrade gracefully to fewer findings rather than crashes |
| Rule packs become outdated as SAP evolves ABAP/RAP/UI5 patterns | MEDIUM | Keep rules declarative and data-driven (frozen dataclasses); version rules; document SAP release dependencies |
| Severity model is too aggressive or too lenient | MEDIUM | Feedback per finding; severity distribution monitoring in statistics; calibration passes per phase |
| Domain packs (WP-1.5) become maintenance burden | MEDIUM | Keep domain rules declarative; test per pack independently; domain packs are optional overlays |
| UI complexity grows beyond vanilla JS manageability | MEDIUM | Maintain strict module separation in app.js; consider ES6 module extraction at v2; do not migrate framework until v3 |
| PostgreSQL dependency blocks history/feedback features | LOW | Graceful degradation pattern: features hidden when DB unavailable; core review works locally without DB |
| Cross-artifact checker produces noise when artifacts are incomplete | MEDIUM | Only trigger cross-artifact rules when multiple artifact types present; clearly label cross-artifact findings |
| Clean-core released API catalog becomes stale | MEDIUM | Catalog is a data file, not code; versioned per SAP release; community contribution model possible |
| SARIF export fails validation with specific CI tools | LOW | Test against GitHub Code Scanning and Azure DevOps; SARIF v2.1.0 is well-documented standard |
| LLM API costs grow with usage (Phase 3) | HIGH | Hybrid approach: LLM only when rule-based is insufficient; budget cap per request; feature flag default off |
| LLM hallucinations in fix suggestions (Phase 3) | HIGH | Syntax validation; "LLM-generated" disclaimer; rule-based fallback always available |
| Scope creep: tool tries to be a full static analysis tool instead of review assistant | HIGH | Clear positioning: "Review Assistant for SAP developers", not "SAP SonarQube"; focus on actionable findings over exhaustive analysis |

---

## Open Questions

1. **Finding granularity bar**: How detailed should individual findings be? Decision: each finding should be actionable in isolation -- a developer should be able to fix the issue based on the finding alone. Avoid findings that are too vague ("code could be better") or too detailed ("rename variable on line 47 from x to customer_id").

2. **Severity calibration**: How strictly should CRITICAL be reserved? Decision: CRITICAL = potential data loss, security hole, or production crash. Missing a best practice is IMPORTANT at most. Validate with SAP domain expert during WP-0.4.

3. **Code parsing depth**: How much code parsing should the rule-based engine attempt? Decision: regex-based pattern matching for MVP/v1, not full AST parsing. Full parsing deferred to v3 LLM features. Accept that regex will miss some patterns and produce some false positives.

4. **UI framework migration**: At what point does vanilla JS become unsustainable? Current expectation: v2 features (diff view, multi-artifact tabs, team workflows) may push toward ES6 modules. Full framework migration deferred to v3 at earliest.

5. **Deployment model**: Same question as sibling projects -- local dev tool, team server, or cloud service? Affects PostgreSQL dependency, authentication, and multi-tenancy decisions.

6. **Cross-tool integration**: Should the Review Assistant share infrastructure with sibling tools (Field-Change Accelerator, Skeleton Generator)? Current decision: independent projects that share patterns, not code. Re-evaluate at v2.

7. **Rule pack extensibility**: Should users be able to add custom rules without code changes? Decision: not in MVP/v1. Rule packs are Python modules. v2 could add a JSON/YAML rule definition format for user-defined rules.

8. **SARIF and CI integration scope**: How deep should CI integration go? Decision: export formats only in v2. Actual CI pipeline plugins (GitHub Action, Azure Pipeline task) deferred to Premium/v3.

---

## Summary: Recommended Execution Order

### Phase 0 (MVP) -- parallel tracks

**Track A** (infrastructure): WP-0.1 (scaffolding) + WP-0.2 (schemas) in parallel
**Track B** (UI, after WP-0.1): WP-0.3 (input form + UI shell)
**Track C** (engines, after WP-0.2): WP-0.4 (Findings Engine) -> WP-0.5 (Test-Gap Analyzer) + WP-0.6 (Risk & Impact Engine) in parallel
**Track D** (integration, after Track C): WP-0.7 (pipeline + summary + output)
**Track E** (validation, after Track D): WP-0.8 (example cases + tests)

### Phase 1 (v1) -- staggered

**Week 1-3**: WP-1.1 (ABAP packs) + WP-1.2 (CDS/RAP packs) + WP-1.3 (UI5/Fiori packs) in parallel
**Week 3-4**: WP-1.4 (Service/OData pack) + WP-1.5 (Domain packs) in parallel
**Week 4-5**: WP-1.6 (Solution design review) + WP-1.7 (History + feedback) in parallel
**Week 5-6**: WP-1.8 (UI polish + template outputs)

### Phase 2 (v2) -- sequential with parallelism

**First**: WP-2.1 (Diff & multi-artifact) + WP-2.3 (Clean-core deep rules) in parallel
**Second**: WP-2.2 (Cross-artifact consistency) + WP-2.4 (Similarity search) in parallel
**Third**: WP-2.5 (Team workflows) + WP-2.6 (CI/merge export) in parallel
**Fourth**: WP-2.7 (UI premium + cohesion pass)

### Phase 3 (v3) -- deferred, sequential LLM dependency chain

**First**: WP-3.1 (LLM infrastructure)
**Second**: WP-3.2 (Semantic analysis) + WP-3.4 (Fix suggestions) in parallel
**Third**: WP-3.3 (Finding explanations) + WP-3.5 (Design review enhancement) in parallel
**Fourth**: WP-3.6 (Quality dashboard)
