/* ============================================================
   SAP ABAP/UI5 Review Assistant — Application Logic
   ============================================================ */

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Translations (DE / EN) — complete bilingual coverage
  // -----------------------------------------------------------------------
  var TRANSLATIONS = {
    de: {
      // Header
      appTitle: "SAP ABAP/UI5 Review Assistant",
      appSubtitle: "Code Review Tool",

      // Form labels
      reviewType: "Review-Typ",
      artifactType: "Artefakttyp",
      codeInput: "Code / Diff",
      contextSummary: "Kontext-Zusammenfassung",
      goalOfReview: "Ziel des Reviews",
      reviewContext: "Review-Kontext",
      advancedOptions: "Erweiterte Optionen",
      techContext: "Technologie-Kontext",
      sapRelease: "SAP Release",
      ui5Version: "UI5 Version",
      odataVersion: "OData Version",
      odataNone: "Keine / Nicht relevant",
      rapManaged: "RAP Managed",
      fioriElements: "Fiori Elements",
      knownConstraints: "Bekannte Einschraenkungen",
      domainPack: "Domain Pack",
      domainNone: "Keines",
      domainEwm: "EWM / WM",
      domainYard: "Yard Logistics",
      domainService: "Service",
      domainMii: "MII / MES",
      questionFocus: "Fokus der Pruefung",
      focusPerformance: "Performance",
      focusMaintainability: "Wartbarkeit",
      focusCleanCore: "Clean Core",
      focusTests: "Tests",
      focusSecurity: "Security",
      focusReadability: "Lesbarkeit",
      loadExample: "Beispiel laden",
      examplePlaceholder: "-- Beispiel waehlen --",
      runReview: "Review starten",

      // Placeholders
      selectPlaceholder: "-- Bitte waehlen --",
      codeInputPlaceholder: "CLASS zcl_example DEFINITION PUBLIC FINAL CREATE PUBLIC.\n  PUBLIC SECTION.\n    METHODS get_data RETURNING VALUE(rt_data) TYPE tt_data.\nENDCLASS.\n\nCLASS zcl_example IMPLEMENTATION.\n  METHOD get_data.\n    SELECT * FROM ztable INTO TABLE @rt_data.\n  ENDMETHOD.\nENDCLASS.",
      contextSummaryPlaceholder: "Beschreiben Sie, was der Code tut und in welchem Kontext er eingesetzt wird...",
      goalOfReviewPlaceholder: "Was moechten Sie durch das Review erfahren?",
      sapReleasePlaceholder: "z.B. S/4HANA 2023",
      ui5VersionPlaceholder: "z.B. 1.120",
      constraintsPlaceholder: "Einschraenkung eingeben, Enter druecken",

      // Review Type options
      rt_snippet: "Snippet Review",
      rt_diff: "Diff Review",
      rt_preMerge: "Pre-Merge Review",
      rt_solutionDesign: "Solution Design Review",
      rt_ticketBased: "Ticket-basiertes Pre-Review",
      rt_regressionRisk: "Regressionsrisiko-Review",
      rt_cleanCoreArch: "Clean-Core Architektur-Check",

      // Artifact Type options
      grpAbap: "ABAP",
      grpCdsRap: "CDS / RAP",
      grpUi5Fiori: "UI5 / Fiori",
      grpService: "Service",
      grpMixed: "Mixed",
      at_abapClass: "ABAP-Klasse",
      at_abapMethod: "ABAP-Methode",
      at_abapReport: "ABAP-Report",
      at_cdsView: "CDS View",
      at_cdsProjection: "CDS Projection",
      at_cdsAnnotation: "CDS Annotation",
      at_behaviorDef: "Behavior Definition",
      at_behaviorImpl: "Behavior Implementation",
      at_ui5View: "UI5 XML View",
      at_ui5Controller: "UI5 Controller",
      at_ui5Fragment: "UI5 Fragment",
      at_ui5Formatter: "UI5 Formatter",
      at_fioriElements: "Fiori Elements App",
      at_serviceDef: "Service Definition",
      at_serviceBinding: "Service Binding",
      at_odataService: "OData Service",
      at_mixedFullstack: "Mixed / Fullstack",

      // Review Context options
      ctx_greenfield: "Greenfield (Neuentwicklung)",
      ctx_extension: "Extension (Erweiterung)",
      ctx_bugfix: "Bugfix",
      ctx_refactoring: "Refactoring",

      // Empty / Error states
      startReview: "Review starten",
      startReviewDesc: "Fuegen Sie ABAP-Code, eine CDS-View oder ein UI5-Artefakt ein und klicken Sie auf \u00abReview starten\u00bb, um strukturierte Pruefergebnisse zu erhalten.",
      reviewError: "Fehler beim Review",
      close: "Schliessen",
      unknownError: "Unbekannter Fehler beim Review.",

      // Validation
      valReviewType: "Bitte waehlen Sie einen Review-Typ.",
      valArtifactType: "Bitte waehlen Sie einen Artefakttyp.",
      valCode: "Bitte fuegen Sie Code oder einen Diff ein.",

      // Result card titles
      resOverallAssessment: "Gesamtbewertung",
      resReviewSummary: "Review-Zusammenfassung",
      resFindings: "Befunde",
      resOpenQuestions: "Offene Fragen",
      resTestGaps: "Test-Luecken",
      resRecommendedActions: "Empfohlene Massnahmen",
      resRefactoringHints: "Refactoring-Hinweise",
      resRiskDashboard: "Risiko-Dashboard",
      resCleanCoreHints: "Clean-Core-Hinweise",

      // Result content labels
      observation: "Beobachtung",
      reasoning: "Begruendung",
      impact: "Auswirkung",
      recommendation: "Empfehlung",
      whyItMatters: "Warum relevant",
      defaultAssumption: "Standard-Annahme",
      suggestedTest: "Vorgeschlagener Test",
      effort: "Aufwand",
      benefit: "Nutzen",
      mitigation: "Massnahme",
      releasedApi: "Released API Alternative",
      confidence: "Konfidenz",
      noFindings: "Keine Befunde.",
      noOpenQuestions: "Keine offenen Fragen.",
      noTestGaps: "Keine Test-Luecken identifiziert.",
      noActions: "Keine Massnahmen empfohlen.",
      noRefactoring: "Keine Refactoring-Hinweise.",
      noRisks: "Keine Risiken identifiziert.",
      noCleanCore: "Keine Clean-Core-Hinweise.",

      // Risk categories
      riskFunctional: "Funktional",
      riskMaintainability: "Wartbarkeit",
      riskTestability: "Testbarkeit",
      riskCleanCore: "Upgrade / Clean Core",

      // GoNoGo
      goLabel: "GO",
      conditionalGoLabel: "CONDITIONAL GO",
      noGoLabel: "NO GO",

      // Open Questions inline answers
      "oq.answerPlaceholder": "Ihre Antwort...",
      "oq.answerAriaPrefix": "Antwort fuer: ",
      "oq.regenerateBtn": "Review mit Antworten erneut ausfuehren",
      "oq.answeredCount": "{n} beantwortet"
    },
    en: {
      // Header
      appTitle: "SAP ABAP/UI5 Review Assistant",
      appSubtitle: "Code Review Tool",

      // Form labels
      reviewType: "Review Type",
      artifactType: "Artifact Type",
      codeInput: "Code / Diff",
      contextSummary: "Context Summary",
      goalOfReview: "Goal of Review",
      reviewContext: "Review Context",
      advancedOptions: "Advanced Options",
      techContext: "Technology Context",
      sapRelease: "SAP Release",
      ui5Version: "UI5 Version",
      odataVersion: "OData Version",
      odataNone: "None / Not relevant",
      rapManaged: "RAP Managed",
      fioriElements: "Fiori Elements",
      knownConstraints: "Known Constraints",
      domainPack: "Domain Pack",
      domainNone: "None",
      domainEwm: "EWM / WM",
      domainYard: "Yard Logistics",
      domainService: "Service",
      domainMii: "MII / MES",
      questionFocus: "Question Focus",
      focusPerformance: "Performance",
      focusMaintainability: "Maintainability",
      focusCleanCore: "Clean Core",
      focusTests: "Tests",
      focusSecurity: "Security",
      focusReadability: "Readability",
      loadExample: "Load Example",
      examplePlaceholder: "-- Select example --",
      runReview: "Run Review",

      // Placeholders
      selectPlaceholder: "-- Please select --",
      codeInputPlaceholder: "CLASS zcl_example DEFINITION PUBLIC FINAL CREATE PUBLIC.\n  PUBLIC SECTION.\n    METHODS get_data RETURNING VALUE(rt_data) TYPE tt_data.\nENDCLASS.\n\nCLASS zcl_example IMPLEMENTATION.\n  METHOD get_data.\n    SELECT * FROM ztable INTO TABLE @rt_data.\n  ENDMETHOD.\nENDCLASS.",
      contextSummaryPlaceholder: "Describe what the code does and the context it operates in...",
      goalOfReviewPlaceholder: "What do you want to learn from this review?",
      sapReleasePlaceholder: "e.g. S/4HANA 2023",
      ui5VersionPlaceholder: "e.g. 1.120",
      constraintsPlaceholder: "Type constraint, press Enter",

      // Review Type options
      rt_snippet: "Snippet Review",
      rt_diff: "Diff Review",
      rt_preMerge: "Pre-Merge Review",
      rt_solutionDesign: "Solution Design Review",
      rt_ticketBased: "Ticket-Based Pre-Review",
      rt_regressionRisk: "Regression Risk Review",
      rt_cleanCoreArch: "Clean-Core Architecture Check",

      // Artifact Type options
      grpAbap: "ABAP",
      grpCdsRap: "CDS / RAP",
      grpUi5Fiori: "UI5 / Fiori",
      grpService: "Service",
      grpMixed: "Mixed",
      at_abapClass: "ABAP Class",
      at_abapMethod: "ABAP Method",
      at_abapReport: "ABAP Report",
      at_cdsView: "CDS View",
      at_cdsProjection: "CDS Projection",
      at_cdsAnnotation: "CDS Annotation",
      at_behaviorDef: "Behavior Definition",
      at_behaviorImpl: "Behavior Implementation",
      at_ui5View: "UI5 XML View",
      at_ui5Controller: "UI5 Controller",
      at_ui5Fragment: "UI5 Fragment",
      at_ui5Formatter: "UI5 Formatter",
      at_fioriElements: "Fiori Elements App",
      at_serviceDef: "Service Definition",
      at_serviceBinding: "Service Binding",
      at_odataService: "OData Service",
      at_mixedFullstack: "Mixed / Fullstack",

      // Review Context options
      ctx_greenfield: "Greenfield (New Development)",
      ctx_extension: "Extension",
      ctx_bugfix: "Bugfix",
      ctx_refactoring: "Refactoring",

      // Empty / Error states
      startReview: "Start Review",
      startReviewDesc: "Paste ABAP code, a CDS view, or a UI5 artifact and click \u00abRun Review\u00bb to receive structured review findings.",
      reviewError: "Review Error",
      close: "Close",
      unknownError: "Unknown error during review.",

      // Validation
      valReviewType: "Please select a review type.",
      valArtifactType: "Please select an artifact type.",
      valCode: "Please paste code or a diff.",

      // Result card titles
      resOverallAssessment: "Overall Assessment",
      resReviewSummary: "Review Summary",
      resFindings: "Findings",
      resOpenQuestions: "Open Questions",
      resTestGaps: "Test Gaps",
      resRecommendedActions: "Recommended Actions",
      resRefactoringHints: "Refactoring Hints",
      resRiskDashboard: "Risk Dashboard",
      resCleanCoreHints: "Clean-Core Hints",

      // Result content labels
      observation: "Observation",
      reasoning: "Reasoning",
      impact: "Impact",
      recommendation: "Recommendation",
      whyItMatters: "Why it matters",
      defaultAssumption: "Default assumption",
      suggestedTest: "Suggested test",
      effort: "Effort",
      benefit: "Benefit",
      mitigation: "Mitigation",
      releasedApi: "Released API Alternative",
      confidence: "Confidence",
      noFindings: "No findings.",
      noOpenQuestions: "No open questions.",
      noTestGaps: "No test gaps identified.",
      noActions: "No actions recommended.",
      noRefactoring: "No refactoring hints.",
      noRisks: "No risks identified.",
      noCleanCore: "No clean-core hints.",

      // Risk categories
      riskFunctional: "Functional",
      riskMaintainability: "Maintainability",
      riskTestability: "Testability",
      riskCleanCore: "Upgrade / Clean Core",

      // GoNoGo
      goLabel: "GO",
      conditionalGoLabel: "CONDITIONAL GO",
      noGoLabel: "NO GO",

      // Open Questions inline answers
      "oq.answerPlaceholder": "Your answer...",
      "oq.answerAriaPrefix": "Answer for: ",
      "oq.regenerateBtn": "Re-run Review with Answers",
      "oq.answeredCount": "{n} answered"
    }
  };

  var currentLang = "de";
  var clarifications = {};
  var lastPayload = null;

  function t(key) {
    var dict = TRANSLATIONS[currentLang] || TRANSLATIONS.de;
    return dict[key] || key;
  }

  // -----------------------------------------------------------------------
  // DOM References
  // -----------------------------------------------------------------------
  var form = document.getElementById("reviewForm");
  var submitBtn = document.getElementById("submitBtn");
  var placeholder = document.getElementById("placeholder");
  var loadingState = document.getElementById("loadingState");
  var errorState = document.getElementById("errorState");
  var errorMessage = document.getElementById("errorMessage");
  var resultsContainer = document.getElementById("resultsContainer");
  var themeToggle = document.getElementById("themeToggle");
  var langToggle = document.getElementById("langToggle");
  var advancedToggle = document.getElementById("advancedToggle");
  var advancedBody = document.getElementById("advancedBody");
  var btnDismissError = document.getElementById("btnDismissError");

  // -----------------------------------------------------------------------
  // Tag Input Data
  // -----------------------------------------------------------------------
  var tagData = {
    constraints: []
  };

  // -----------------------------------------------------------------------
  // Theme Toggle
  // -----------------------------------------------------------------------
  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("ra-theme", theme);
  }

  function initTheme() {
    var saved = localStorage.getItem("ra-theme");
    if (saved) applyTheme(saved);
  }

  themeToggle.addEventListener("click", function () {
    var current = document.documentElement.getAttribute("data-theme");
    var isDark = current === "dark" ||
      (!current && window.matchMedia("(prefers-color-scheme: dark)").matches);
    applyTheme(isDark ? "light" : "dark");
  });

  initTheme();

  // -----------------------------------------------------------------------
  // Language Toggle
  // -----------------------------------------------------------------------
  function applyLanguage(lang) {
    currentLang = lang;
    langToggle.textContent = lang.toUpperCase();
    document.documentElement.setAttribute("lang", lang);

    var dict = TRANSLATIONS[lang] || TRANSLATIONS.de;

    // Text content
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });

    // Placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (dict[key]) el.placeholder = dict[key];
    });

    // Titles
    document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-title");
      if (dict[key]) el.title = dict[key];
    });

    // Optgroup labels
    document.querySelectorAll("[data-i18n-label]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-label");
      if (dict[key]) el.label = dict[key];
    });

    localStorage.setItem("ra-lang", lang);
  }

  function initLanguage() {
    var saved = localStorage.getItem("ra-lang");
    if (saved) applyLanguage(saved);
  }

  langToggle.addEventListener("click", function () {
    applyLanguage(currentLang === "de" ? "en" : "de");
  });

  initLanguage();

  // -----------------------------------------------------------------------
  // Collapsible: Advanced Options
  // -----------------------------------------------------------------------
  advancedToggle.addEventListener("click", function () {
    var expanded = advancedToggle.getAttribute("aria-expanded") === "true";
    advancedToggle.setAttribute("aria-expanded", String(!expanded));
    advancedBody.hidden = expanded;
  });

  // -----------------------------------------------------------------------
  // Collapsible: Result Cards
  // -----------------------------------------------------------------------
  document.addEventListener("click", function (e) {
    var header = e.target.closest(".result-card-header");
    if (!header) return;
    var expanded = header.getAttribute("aria-expanded") === "true";
    var targetId = header.getAttribute("data-target");
    var body = document.getElementById(targetId);
    if (!body) return;
    header.setAttribute("aria-expanded", String(!expanded));
    body.hidden = expanded;
  });

  // -----------------------------------------------------------------------
  // Tag Input
  // -----------------------------------------------------------------------
  function initTagInput(inputId, tagsContainerId, dataKey) {
    var input = document.getElementById(inputId);
    var tagsContainer = document.getElementById(tagsContainerId);
    var container = input ? input.closest(".tag-input-container") : null;

    if (!input || !tagsContainer) return;

    if (container) {
      container.addEventListener("click", function (e) {
        if (e.target === container || e.target === tagsContainer) {
          input.focus();
        }
      });
    }

    function addTag(text) {
      text = text.trim();
      if (!text) return;
      if (tagData[dataKey].indexOf(text) !== -1) return;
      tagData[dataKey].push(text);
      renderTags(tagsContainer, dataKey);
      input.value = "";
    }

    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        addTag(input.value.replace(/,/g, ""));
      }
      if (e.key === "Backspace" && !input.value && tagData[dataKey].length > 0) {
        tagData[dataKey].pop();
        renderTags(tagsContainer, dataKey);
      }
    });

    input.addEventListener("paste", function (e) {
      e.preventDefault();
      var paste = (e.clipboardData || window.clipboardData).getData("text");
      paste.split(/[,;\n]+/).forEach(function (part) {
        addTag(part);
      });
    });
  }

  function renderTags(container, dataKey) {
    container.innerHTML = "";
    tagData[dataKey].forEach(function (text, idx) {
      var pill = document.createElement("span");
      pill.className = "tag-pill";
      pill.textContent = text;

      var removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "tag-pill-remove";
      removeBtn.innerHTML = "&times;";
      removeBtn.setAttribute("aria-label", "Remove " + text);
      removeBtn.addEventListener("click", function () {
        tagData[dataKey].splice(idx, 1);
        renderTags(container, dataKey);
      });

      pill.appendChild(removeBtn);
      container.appendChild(pill);
    });
  }

  initTagInput("constraintsInput", "constraintsTags", "constraints");

  // -----------------------------------------------------------------------
  // Error dismiss
  // -----------------------------------------------------------------------
  btnDismissError.addEventListener("click", function () {
    errorState.hidden = true;
    placeholder.hidden = false;
  });

  // -----------------------------------------------------------------------
  // Form Validation
  // -----------------------------------------------------------------------
  function validateForm() {
    var reviewType = document.getElementById("reviewType").value;
    var artifactType = document.getElementById("artifactType").value;
    var code = document.getElementById("codeInput").value.trim();

    if (!reviewType) {
      showValidationError(t("valReviewType"));
      return false;
    }
    if (!artifactType) {
      showValidationError(t("valArtifactType"));
      return false;
    }
    if (!code) {
      showValidationError(t("valCode"));
      return false;
    }
    return true;
  }

  function showValidationError(msg) {
    errorMessage.textContent = msg;
    errorState.hidden = false;
    placeholder.hidden = true;
    loadingState.hidden = true;
    resultsContainer.hidden = true;
  }

  // -----------------------------------------------------------------------
  // Build request payload matching ReviewRequest schema
  // -----------------------------------------------------------------------
  function buildPayload() {
    var payload = {
      review_type: document.getElementById("reviewType").value,
      artifact_type: document.getElementById("artifactType").value,
      code_or_diff: document.getElementById("codeInput").value,
      context_summary: document.getElementById("contextSummary").value || "",
      goal_of_review: document.getElementById("goalOfReview").value || "",
      review_context: document.getElementById("reviewContext").value || "GREENFIELD",
      language: currentLang.toUpperCase(),
      known_constraints: tagData.constraints.slice(),
      question_focus: [],
      clarifications: {}
    };

    // Question focus checkboxes
    document.querySelectorAll('input[name="question_focus"]:checked').forEach(function (cb) {
      payload.question_focus.push(cb.value);
    });

    // Technology context
    var sapRelease = document.getElementById("sapRelease").value.trim();
    var ui5Version = document.getElementById("ui5Version").value.trim();
    var odataVersion = document.getElementById("odataVersion").value;
    var rapManaged = document.getElementById("rapManaged").checked;
    var fioriElements = document.getElementById("fioriElements").checked;

    if (sapRelease || ui5Version || odataVersion || rapManaged || fioriElements) {
      payload.technology_context = {};
      if (sapRelease) payload.technology_context.sap_release = sapRelease;
      if (ui5Version) payload.technology_context.ui5_version = ui5Version;
      if (odataVersion) payload.technology_context.odata_version = odataVersion;
      if (rapManaged) payload.technology_context.rap_managed = true;
      if (fioriElements) payload.technology_context.fiori_elements = true;
    }

    // Domain pack
    var domainPack = document.getElementById("domainPack").value;
    if (domainPack) payload.domain_pack = domainPack;

    return payload;
  }

  // -----------------------------------------------------------------------
  // Form Submit
  // -----------------------------------------------------------------------
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    if (!validateForm()) return;

    // Reset clarifications on new review
    clarifications = {};
    var payload = buildPayload();
    lastPayload = payload;

    // UI: loading state
    submitBtn.classList.add("is-loading");
    submitBtn.disabled = true;
    placeholder.hidden = true;
    errorState.hidden = true;
    resultsContainer.hidden = true;
    loadingState.hidden = false;

    fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp.json().catch(function () { return {}; }).then(function (body) {
            throw new Error(body.detail || body.message || "HTTP " + resp.status);
          });
        }
        return resp.json();
      })
      .then(function (data) {
        renderResults(data);
      })
      .catch(function (err) {
        errorMessage.textContent = err.message || t("unknownError");
        errorState.hidden = false;
        loadingState.hidden = true;
      })
      .finally(function () {
        submitBtn.classList.remove("is-loading");
        submitBtn.disabled = false;
        loadingState.hidden = true;
      });
  });

  // -----------------------------------------------------------------------
  // Render Results
  // -----------------------------------------------------------------------
  function renderResults(data) {
    loadingState.hidden = true;

    // 1. Overall Assessment
    renderOverallAssessment(data.overall_assessment);

    // 2. Review Summary
    renderReviewSummary(data.review_summary);

    // 3. Findings
    renderFindings(data.findings || []);

    // 4. Open Questions
    renderOpenQuestions(data.missing_information || []);

    // 5. Test Gaps
    renderTestGaps(data.test_gaps || []);

    // 6. Recommended Actions
    renderRecommendedActions(data.recommended_actions || []);

    // 7. Refactoring Hints
    renderRefactoringHints(data.refactoring_hints || []);

    // 8. Risk Dashboard
    renderRiskDashboard(data.risk_notes || []);

    // 9. Clean-Core Hints
    renderCleanCoreHints(data.clean_core_hints || []);

    resultsContainer.hidden = false;
  }

  // --- Overall Assessment ---
  function renderOverallAssessment(assessment) {
    var body = document.getElementById("cardOverallAssessmentBody");
    body.innerHTML = "";

    if (!assessment) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noFindings")) + '</p>';
      return;
    }

    var goNoGo = assessment.go_no_go || "GO";
    var badgeClass = "assessment-badge--go";
    var label = t("goLabel");
    if (goNoGo === "CONDITIONAL_GO") { badgeClass = "assessment-badge--conditional"; label = t("conditionalGoLabel"); }
    if (goNoGo === "NO_GO") { badgeClass = "assessment-badge--nogo"; label = t("noGoLabel"); }

    var html = '<div class="assessment-badge ' + badgeClass + '">' + escapeHtml(label) + '</div>';

    if (assessment.confidence) {
      html += '<span style="margin-left:12px;font-size:var(--text-sm);color:var(--color-text-secondary);">' +
        escapeHtml(t("confidence")) + ': ' + escapeHtml(assessment.confidence) + '</span>';
    }

    if (assessment.summary) {
      html += '<p class="assessment-summary">' + escapeHtml(assessment.summary) + '</p>';
    }

    html += '<div class="assessment-counts">';
    html += '<span class="assessment-count"><span class="assessment-count-dot" style="background:var(--color-red)"></span> ' +
      (assessment.critical_count || 0) + ' Critical</span>';
    html += '<span class="assessment-count"><span class="assessment-count-dot" style="background:var(--color-amber)"></span> ' +
      (assessment.important_count || 0) + ' Important</span>';
    html += '<span class="assessment-count"><span class="assessment-count-dot" style="background:var(--color-primary)"></span> ' +
      (assessment.optional_count || 0) + ' Optional</span>';
    html += '</div>';

    body.innerHTML = html;
  }

  // --- Review Summary ---
  function renderReviewSummary(summary) {
    var body = document.getElementById("cardReviewSummaryBody");
    body.innerHTML = "";

    if (!summary) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noFindings")) + '</p>';
      return;
    }

    body.innerHTML = '<p class="review-summary-text">' + escapeHtml(summary) + '</p>';
  }

  // --- Findings ---
  function renderFindings(findings) {
    var body = document.getElementById("cardFindingsBody");
    body.innerHTML = "";

    if (findings.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noFindings")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "findings-list";

    findings.forEach(function (f) {
      var item = document.createElement("div");
      item.className = "finding-item finding-item--" + (f.severity || "UNCLEAR");

      var header = document.createElement("div");
      header.className = "finding-header";
      header.addEventListener("click", function () {
        item.classList.toggle("is-expanded");
      });

      var badge = document.createElement("span");
      badge.className = "severity-badge severity-badge--" + (f.severity || "UNCLEAR");
      badge.textContent = f.severity || "UNCLEAR";

      var title = document.createElement("span");
      title.className = "finding-title";
      title.textContent = f.title || "Finding";

      var expandIcon = document.createElement("svg");
      expandIcon.className = "finding-expand-icon";
      expandIcon.setAttribute("width", "12");
      expandIcon.setAttribute("height", "12");
      expandIcon.setAttribute("viewBox", "0 0 24 24");
      expandIcon.setAttribute("fill", "none");
      expandIcon.setAttribute("stroke", "currentColor");
      expandIcon.setAttribute("stroke-width", "2");
      expandIcon.innerHTML = '<polyline points="6 9 12 15 18 9"/>';

      header.appendChild(badge);
      header.appendChild(title);
      header.appendChild(expandIcon);

      var details = document.createElement("div");
      details.className = "finding-details";

      var detailFields = [
        { key: "observation", label: t("observation") },
        { key: "reasoning", label: t("reasoning") },
        { key: "impact", label: t("impact") },
        { key: "recommendation", label: t("recommendation") }
      ];

      detailFields.forEach(function (df) {
        if (f[df.key]) {
          var row = document.createElement("div");
          row.className = "finding-detail-row";
          row.innerHTML = '<div class="finding-detail-label">' + escapeHtml(df.label) + '</div>' +
            '<div class="finding-detail-text">' + escapeHtml(f[df.key]) + '</div>';
          details.appendChild(row);
        }
      });

      if (f.artifact_reference || f.line_reference || f.rule_id) {
        var ref = document.createElement("div");
        ref.className = "finding-reference";
        var parts = [];
        if (f.rule_id) parts.push("Rule: " + f.rule_id);
        if (f.artifact_reference) parts.push("Artifact: " + f.artifact_reference);
        if (f.line_reference) parts.push("Line: " + f.line_reference);
        ref.textContent = parts.join(" | ");
        details.appendChild(ref);
      }

      item.appendChild(header);
      item.appendChild(details);
      container.appendChild(item);
    });

    body.appendChild(container);
  }

  // --- Open Questions (with inline answer inputs) ---
  function updateRegenerateButton() {
    var btn = document.getElementById("btnRegenerate");
    if (!btn) return;
    var hasAny = Object.keys(clarifications).some(function (key) {
      return clarifications[key] && clarifications[key].trim() !== "";
    });
    btn.hidden = !hasAny;
  }

  function handleRegenerate(btn) {
    if (!lastPayload) return;

    // Collect non-empty clarifications
    var filledClarifications = {};
    Object.keys(clarifications).forEach(function (key) {
      if (clarifications[key] && clarifications[key].trim() !== "") {
        filledClarifications[key] = clarifications[key].trim();
      }
    });

    if (Object.keys(filledClarifications).length === 0) return;

    // Build payload with clarifications
    var payload = {};
    Object.keys(lastPayload).forEach(function (k) {
      payload[k] = lastPayload[k];
    });
    payload.clarifications = filledClarifications;
    payload.language = currentLang.toUpperCase();

    // Show loading state on re-generate button
    btn.classList.add("is-loading");
    btn.disabled = true;

    fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp.json().catch(function () { return {}; }).then(function (body) {
            throw new Error(body.detail || body.message || "HTTP " + resp.status);
          });
        }
        return resp.json();
      })
      .then(function (data) {
        renderResults(data);
        resultsContainer.hidden = false;

        // Ensure open questions card is expanded after re-generate
        var oqHeader = document.querySelector('#cardOpenQuestions .result-card-header');
        var oqBody = document.getElementById("cardOpenQuestionsBody");
        if (oqHeader && oqBody && oqBody.hidden) {
          oqBody.hidden = false;
          oqHeader.setAttribute("aria-expanded", "true");
        }
      })
      .catch(function (err) {
        errorMessage.textContent = err.message || t("unknownError");
        errorState.hidden = false;
      })
      .finally(function () {
        btn.classList.remove("is-loading");
        btn.disabled = false;
      });
  }

  function renderOpenQuestions(questions) {
    var body = document.getElementById("cardOpenQuestionsBody");
    body.innerHTML = "";

    // Remove old re-generate button if present
    var oldRegenBtn = document.getElementById("btnRegenerate");
    if (oldRegenBtn) oldRegenBtn.parentNode.removeChild(oldRegenBtn);

    if (questions.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noOpenQuestions")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "questions-list";

    questions.forEach(function (q) {
      var questionKey = q.question || "";
      var item = document.createElement("div");
      item.className = "question-item";

      // Apply has-answer class if a clarification already exists
      if (clarifications[questionKey] && clarifications[questionKey].trim() !== "") {
        item.classList.add("has-answer");
      }

      var questionText = document.createElement("div");
      questionText.className = "question-text";
      questionText.textContent = questionKey;
      item.appendChild(questionText);

      var questionWhy = document.createElement("div");
      questionWhy.className = "question-why";
      questionWhy.textContent = t("whyItMatters") + ': ' + (q.why_it_matters || "");
      item.appendChild(questionWhy);

      if (q.default_assumption) {
        var questionDefault = document.createElement("div");
        questionDefault.className = "question-default";
        questionDefault.textContent = t("defaultAssumption") + ': ' + q.default_assumption;
        item.appendChild(questionDefault);
      }

      // Inline answer input
      var answerInput = document.createElement("input");
      answerInput.type = "text";
      answerInput.className = "question-answer-input";
      answerInput.placeholder = t("oq.answerPlaceholder");
      answerInput.setAttribute("aria-label", t("oq.answerAriaPrefix") + questionKey);
      answerInput.value = clarifications[questionKey] || "";
      answerInput.addEventListener("input", function () {
        clarifications[questionKey] = answerInput.value;
        if (answerInput.value.trim() !== "") {
          item.classList.add("has-answer");
        } else {
          item.classList.remove("has-answer");
        }
        updateRegenerateButton();
      });

      item.appendChild(answerInput);
      container.appendChild(item);
    });

    body.appendChild(container);

    // Add re-generate button after the list
    var regenBtn = document.createElement("button");
    regenBtn.type = "button";
    regenBtn.id = "btnRegenerate";
    regenBtn.className = "btn-regenerate";
    regenBtn.innerHTML = '<span class="btn-regenerate-text">' + escapeHtml(t("oq.regenerateBtn")) + '</span><span class="btn-regenerate-loader" aria-hidden="true"></span>';
    regenBtn.hidden = true;
    regenBtn.addEventListener("click", function () {
      handleRegenerate(regenBtn);
    });
    // Insert after question list, inside the card
    var oqCard = document.getElementById("cardOpenQuestions");
    if (oqCard) {
      oqCard.appendChild(regenBtn);
    }

    updateRegenerateButton();
  }

  // --- Test Gaps ---
  function renderTestGaps(gaps) {
    var body = document.getElementById("cardTestGapsBody");
    body.innerHTML = "";

    if (gaps.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noTestGaps")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "test-gaps-list";

    gaps.forEach(function (g) {
      var item = document.createElement("div");
      item.className = "test-gap-item";

      var html = '<div><span class="test-gap-category">' + escapeHtml(g.category || "") + '</span>' +
        ' <span class="severity-badge severity-badge--' + (g.priority || "OPTIONAL") + '" style="margin-left:4px;">' +
        escapeHtml(g.priority || "") + '</span></div>' +
        '<div class="test-gap-content">' +
        '<div class="test-gap-description">' + escapeHtml(g.description || "") + '</div>';

      if (g.suggested_test) {
        html += '<div class="test-gap-suggestion">' + escapeHtml(t("suggestedTest")) + ': ' + escapeHtml(g.suggested_test) + '</div>';
      }

      html += '</div>';
      item.innerHTML = html;
      container.appendChild(item);
    });

    body.appendChild(container);
  }

  // --- Recommended Actions ---
  function renderRecommendedActions(actions) {
    var body = document.getElementById("cardRecommendedActionsBody");
    body.innerHTML = "";

    if (actions.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noActions")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "actions-list";

    actions.forEach(function (a) {
      var item = document.createElement("div");
      item.className = "action-item";

      var html = '<div class="action-order">' + escapeHtml(String(a.order || "")) + '</div>' +
        '<div class="action-content">' +
        '<div class="action-title">' + escapeHtml(a.title || "") + '</div>' +
        '<div class="action-description">' + escapeHtml(a.description || "") + '</div>';

      if (a.effort_hint) {
        html += '<div class="action-effort">' + escapeHtml(t("effort")) + ': ' + escapeHtml(a.effort_hint) + '</div>';
      }

      html += '</div>';
      item.innerHTML = html;
      container.appendChild(item);
    });

    body.appendChild(container);
  }

  // --- Refactoring Hints ---
  function renderRefactoringHints(hints) {
    var body = document.getElementById("cardRefactoringHintsBody");
    body.innerHTML = "";

    if (hints.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noRefactoring")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "refactoring-list";

    hints.forEach(function (h) {
      var item = document.createElement("div");
      item.className = "refactoring-item";

      var categoryLabel = (h.category || "").replace(/_/g, " ");
      var html = '<div class="refactoring-header">' +
        '<span class="refactoring-category-badge">' + escapeHtml(categoryLabel) + '</span>' +
        '<span class="refactoring-title">' + escapeHtml(h.title || "") + '</span>' +
        '</div>' +
        '<div class="refactoring-description">' + escapeHtml(h.description || "") + '</div>';

      if (h.benefit) {
        html += '<div class="refactoring-benefit">' + escapeHtml(t("benefit")) + ': ' + escapeHtml(h.benefit) + '</div>';
      }
      if (h.effort_hint) {
        html += '<div class="refactoring-effort">' + escapeHtml(t("effort")) + ': ' + escapeHtml(h.effort_hint) + '</div>';
      }

      item.innerHTML = html;
      container.appendChild(item);
    });

    body.appendChild(container);
  }

  // --- Risk Dashboard ---
  function renderRiskDashboard(risks) {
    var body = document.getElementById("cardRiskDashboardBody");
    body.innerHTML = "";

    if (risks.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noRisks")) + '</p>';
      return;
    }

    var riskCategoryLabels = {
      FUNCTIONAL: t("riskFunctional"),
      MAINTAINABILITY: t("riskMaintainability"),
      TESTABILITY: t("riskTestability"),
      UPGRADE_CLEAN_CORE: t("riskCleanCore")
    };

    var container = document.createElement("div");
    container.className = "risk-dashboard";

    risks.forEach(function (r) {
      var card = document.createElement("div");
      card.className = "risk-card risk-card--" + (r.severity || "LOW");

      var html = '<div class="risk-card-title">' + escapeHtml(riskCategoryLabels[r.category] || r.category || "") + '</div>' +
        '<div class="risk-card-severity">' + escapeHtml(r.severity || "") + '</div>' +
        '<div class="risk-card-description">' + escapeHtml(r.description || "") + '</div>';

      if (r.mitigation) {
        html += '<div class="risk-card-mitigation">' + escapeHtml(t("mitigation")) + ': ' + escapeHtml(r.mitigation) + '</div>';
      }

      card.innerHTML = html;
      container.appendChild(card);
    });

    body.appendChild(container);
  }

  // --- Clean-Core Hints ---
  function renderCleanCoreHints(hints) {
    var body = document.getElementById("cardCleanCoreHintsBody");
    body.innerHTML = "";

    if (hints.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noCleanCore")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "clean-core-list";

    hints.forEach(function (h) {
      var item = document.createElement("div");
      item.className = "clean-core-item";

      var html = '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' +
        '<span class="severity-badge severity-badge--' + (h.severity || "OPTIONAL") + '">' + escapeHtml(h.severity || "") + '</span>' +
        '<span class="clean-core-finding">' + escapeHtml(h.finding || "") + '</span>' +
        '</div>';

      if (h.released_api_alternative) {
        html += '<div class="clean-core-alternative">' + escapeHtml(t("releasedApi")) + ': ' + escapeHtml(h.released_api_alternative) + '</div>';
      }

      item.innerHTML = html;
      container.appendChild(item);
    });

    body.appendChild(container);
  }

  // -----------------------------------------------------------------------
  // Utility: escape HTML
  // -----------------------------------------------------------------------
  function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // -----------------------------------------------------------------------
  // Load Example dropdown
  // -----------------------------------------------------------------------
  var exampleSelect = document.getElementById("exampleSelect");

  function loadExampleList() {
    fetch("/api/examples")
      .then(function (resp) {
        if (!resp.ok) return [];
        return resp.json();
      })
      .then(function (examples) {
        if (!examples || !examples.length) return;
        examples.forEach(function (ex) {
          var opt = document.createElement("option");
          opt.value = ex.case_id;
          var label = currentLang === "de" ? ex.title_de : ex.title;
          opt.textContent = label;
          opt.setAttribute("data-title-de", ex.title_de || "");
          opt.setAttribute("data-title-en", ex.title || "");
          exampleSelect.appendChild(opt);
        });
      })
      .catch(function () {
        // Silently ignore — examples are optional
      });
  }

  if (exampleSelect) {
    loadExampleList();

    exampleSelect.addEventListener("change", function () {
      var caseId = exampleSelect.value;
      if (!caseId) return;

      fetch("/api/examples/" + encodeURIComponent(caseId))
        .then(function (resp) {
          if (!resp.ok) throw new Error("Example not found");
          return resp.json();
        })
        .then(function (data) {
          // Populate form fields
          var reviewTypeEl = document.getElementById("reviewType");
          var artifactTypeEl = document.getElementById("artifactType");
          var codeInputEl = document.getElementById("codeInput");
          var reviewContextEl = document.getElementById("reviewContext");

          if (reviewTypeEl && data.review_type) {
            reviewTypeEl.value = data.review_type;
          }
          if (artifactTypeEl && data.artifact_type) {
            artifactTypeEl.value = data.artifact_type;
          }
          if (codeInputEl && data.code) {
            codeInputEl.value = data.code;
          }
          if (reviewContextEl && data.review_context) {
            reviewContextEl.value = data.review_context;
          }
        })
        .catch(function () {
          // Silently ignore
        });
    });
  }

})();
