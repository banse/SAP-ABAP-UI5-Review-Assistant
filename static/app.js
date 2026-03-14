/* ============================================================
   SAP ABAP/UI5 Review Assistant — Application Logic
   WP-2.7: Cohesion Pass — organized, performant, accessible
   ============================================================ */

(function () {
  "use strict";

  // ===========================================================================
  // SECTION: Configuration & State
  // ===========================================================================
  var currentLang = "de";
  var currentInputMode = "snippet";
  var clarifications = {};
  var lastPayload = null;
  var lastResponse = null;
  var dbAvailable = false;
  var currentReviewId = null;
  var feedbackState = {}; // { "reviewId-findingIndex": true/false }
  var resolutionState = {}; // { findingIndex: "STATUS" }
  var LAZY_RENDER_THRESHOLD = 20;
  var LAZY_RENDER_BATCH = 20;
  var _reviewTypeDebounceTimer = null;

  // ===========================================================================
  // SECTION: Translations (DE/EN)
  // ===========================================================================
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
      designInputPlaceholder: "Fuegen Sie hier Ihre Loesungsbeschreibung ein...\n\nBeispiel:\nWir planen eine Custom Fiori App fuer die Auftragsbearbeitung.\nDie App nutzt OData V4 mit RAP Managed Szenario.\nEntitaeten: Auftrag, Auftragsposition, Kunde.",

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
      networkError: "Netzwerkfehler. Bitte pruefen Sie Ihre Verbindung.",
      timeoutError: "Die Anfrage dauert laenger als erwartet. Bitte warten...",
      retryBtn: "Erneut versuchen",

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
      "oq.answeredCount": "{n} beantwortet",

      // History
      historyTitle: "Verlauf",
      historyEmpty: "Noch keine Reviews gespeichert.",
      historyClearAll: "Alle loeschen",
      historyToggleTitle: "Verlauf anzeigen",
      historyDeleteConfirm: "Diesen Eintrag wirklich loeschen?",
      historyClearConfirm: "Gesamten Verlauf wirklich loeschen?",
      historyFindings: "Befunde",

      // Feedback
      feedbackLabel: "Hilfreich?",
      feedbackUp: "Ja",
      feedbackDown: "Nein",

      // Export
      exportMarkdown: "Markdown exportieren",
      copyTicketComment: "Als Ticket-Kommentar kopieren",
      copyClipboard: "In Zwischenablage kopieren",
      copiedToClipboard: "In die Zwischenablage kopiert",
      markdownDownloaded: "Markdown-Datei heruntergeladen",
      exportSarif: "SARIF exportieren",
      exportCiJson: "CI JSON exportieren",
      sarifDownloaded: "SARIF-Datei heruntergeladen",
      ciJsonDownloaded: "CI-JSON-Datei heruntergeladen",
      qualityGate: "Quality Gate",
      qualityGatePass: "BESTANDEN",
      qualityGateFail: "FEHLGESCHLAGEN",

      // Input mode tabs
      inputSnippet: "Code Snippet",
      inputDiff: "Git Diff",
      inputChangePackage: "Change Package",
      diffPlaceholder: "Unified Diff hier einfuegen (git diff Ausgabe)...",
      changePackagePlaceholder: "Mehrere Artefakte einfuegen, getrennt durch --- Zeilen...\n\n// CDS View: ZI_ORDER\ndefine view entity ZI_ORDER as ...\n---\n* Class: ZCL_ORDER\nCLASS zcl_order DEFINITION PUBLIC ...",
      badgeNew: "NEU",
      badgePreExisting: "VORBESTEHEND",

      // Finding expansion
      lineRef: "Zeile",

      // Lazy rendering
      showMore: "Weitere {n} anzeigen",

      // Similar Reviews & Statistics
      resSimilarReviews: "Aehnliche vergangene Reviews",
      similarScore: "Aehnlichkeit",
      similarSharedFindings: "Gemeinsame Befunde",
      noSimilarReviews: "Keine aehnlichen Reviews gefunden.",
      recurringBadge: "Wiederkehrend: in {n} Reviews gesehen",
      statisticsTitle: "Review-Statistiken",
      statisticsToggleTitle: "Statistiken anzeigen",
      statisticsLoading: "Lade Statistiken...",
      statTotalReviews: "Reviews gesamt",
      statAvgFindings: "Durchschn. Befunde",
      statTopFindings: "Haeufigste Befunde",
      statArtifactTypes: "Artefakttypen",
      statAssessmentDist: "Bewertungsverteilung",
      statNoData: "Noch keine Statistik-Daten vorhanden.",

      // Team Workflow
      reviewerName: "Reviewer",
      reviewerNamePlaceholder: "Ihr Name",
      completionProgress: "Fortschritt",
      resolutionLabel: "Status:",
      resAccepted: "Akzeptiert",
      resRejected: "Abgelehnt",
      resDeferred: "Zurueckgestellt",
      resFixed: "Behoben",
      resOpen: "Offen",
      shareReview: "Review teilen",
      shareUrlCopied: "Link in die Zwischenablage kopiert",
      resolutionCommentPlaceholder: "Kommentar (optional)"
    },
    en: {
      appTitle: "SAP ABAP/UI5 Review Assistant",
      appSubtitle: "Code Review Tool",
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
      selectPlaceholder: "-- Please select --",
      codeInputPlaceholder: "CLASS zcl_example DEFINITION PUBLIC FINAL CREATE PUBLIC.\n  PUBLIC SECTION.\n    METHODS get_data RETURNING VALUE(rt_data) TYPE tt_data.\nENDCLASS.\n\nCLASS zcl_example IMPLEMENTATION.\n  METHOD get_data.\n    SELECT * FROM ztable INTO TABLE @rt_data.\n  ENDMETHOD.\nENDCLASS.",
      contextSummaryPlaceholder: "Describe what the code does and the context it operates in...",
      goalOfReviewPlaceholder: "What do you want to learn from this review?",
      sapReleasePlaceholder: "e.g. S/4HANA 2023",
      ui5VersionPlaceholder: "e.g. 1.120",
      constraintsPlaceholder: "Type constraint, press Enter",
      designInputPlaceholder: "Paste your solution design description here...\n\nExample:\nWe plan to build a custom Fiori app for sales order management.\nThe app will use OData V4 with RAP managed scenario.\nEntities: SalesOrder, SalesOrderItem, Customer.",
      rt_snippet: "Snippet Review",
      rt_diff: "Diff Review",
      rt_preMerge: "Pre-Merge Review",
      rt_solutionDesign: "Solution Design Review",
      rt_ticketBased: "Ticket-Based Pre-Review",
      rt_regressionRisk: "Regression Risk Review",
      rt_cleanCoreArch: "Clean-Core Architecture Check",
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
      ctx_greenfield: "Greenfield (New Development)",
      ctx_extension: "Extension",
      ctx_bugfix: "Bugfix",
      ctx_refactoring: "Refactoring",
      startReview: "Start Review",
      startReviewDesc: "Paste ABAP code, a CDS view, or a UI5 artifact and click \u00abRun Review\u00bb to receive structured review findings.",
      reviewError: "Review Error",
      close: "Close",
      unknownError: "Unknown error during review.",
      networkError: "Network error. Please check your connection.",
      timeoutError: "The request is taking longer than expected. Please wait...",
      retryBtn: "Retry",
      valReviewType: "Please select a review type.",
      valArtifactType: "Please select an artifact type.",
      valCode: "Please paste code or a diff.",
      resOverallAssessment: "Overall Assessment",
      resReviewSummary: "Review Summary",
      resFindings: "Findings",
      resOpenQuestions: "Open Questions",
      resTestGaps: "Test Gaps",
      resRecommendedActions: "Recommended Actions",
      resRefactoringHints: "Refactoring Hints",
      resRiskDashboard: "Risk Dashboard",
      resCleanCoreHints: "Clean-Core Hints",
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
      riskFunctional: "Functional",
      riskMaintainability: "Maintainability",
      riskTestability: "Testability",
      riskCleanCore: "Upgrade / Clean Core",
      goLabel: "GO",
      conditionalGoLabel: "CONDITIONAL GO",
      noGoLabel: "NO GO",
      "oq.answerPlaceholder": "Your answer...",
      "oq.answerAriaPrefix": "Answer for: ",
      "oq.regenerateBtn": "Re-run Review with Answers",
      "oq.answeredCount": "{n} answered",
      historyTitle: "History",
      historyEmpty: "No reviews saved yet.",
      historyClearAll: "Clear All",
      historyToggleTitle: "Toggle history panel",
      historyDeleteConfirm: "Really delete this entry?",
      historyClearConfirm: "Really clear all history?",
      historyFindings: "Findings",
      feedbackLabel: "Helpful?",
      feedbackUp: "Yes",
      feedbackDown: "No",
      exportMarkdown: "Export Markdown",
      copyTicketComment: "Copy as Ticket Comment",
      copyClipboard: "Copy to Clipboard",
      copiedToClipboard: "Copied to clipboard",
      markdownDownloaded: "Markdown file downloaded",
      exportSarif: "Export SARIF",
      exportCiJson: "Export CI JSON",
      sarifDownloaded: "SARIF file downloaded",
      ciJsonDownloaded: "CI JSON file downloaded",
      qualityGate: "Quality Gate",
      qualityGatePass: "PASSED",
      qualityGateFail: "FAILED",
      inputSnippet: "Code Snippet",
      inputDiff: "Git Diff",
      inputChangePackage: "Change Package",
      diffPlaceholder: "Paste unified diff (git diff output) here...",
      changePackagePlaceholder: "Paste multiple artifacts separated by --- lines...\n\n// CDS View: ZI_ORDER\ndefine view entity ZI_ORDER as ...\n---\n* Class: ZCL_ORDER\nCLASS zcl_order DEFINITION PUBLIC ...",
      badgeNew: "NEW",
      badgePreExisting: "PRE-EXISTING",
      lineRef: "Line",
      showMore: "Show {n} more",
      resSimilarReviews: "Similar Past Reviews",
      similarScore: "Similarity",
      similarSharedFindings: "Shared findings",
      noSimilarReviews: "No similar reviews found.",
      recurringBadge: "Recurring: seen in {n} reviews",
      statisticsTitle: "Review Statistics",
      statisticsToggleTitle: "Show statistics",
      statisticsLoading: "Loading statistics...",
      statTotalReviews: "Total Reviews",
      statAvgFindings: "Avg. Findings",
      statTopFindings: "Top Findings",
      statArtifactTypes: "Artifact Types",
      statAssessmentDist: "Assessment Distribution",
      statNoData: "No statistics data available yet.",
      reviewerName: "Reviewer",
      reviewerNamePlaceholder: "Your name",
      completionProgress: "Progress",
      resolutionLabel: "Status:",
      resAccepted: "Accepted",
      resRejected: "Rejected",
      resDeferred: "Deferred",
      resFixed: "Fixed",
      resOpen: "Open",
      shareReview: "Share Review",
      shareUrlCopied: "Link copied to clipboard",
      resolutionCommentPlaceholder: "Comment (optional)"
    }
  };

  function t(key) {
    var dict = TRANSLATIONS[currentLang] || TRANSLATIONS.de;
    return dict[key] || key;
  }

  // ===========================================================================
  // SECTION: DOM References
  // ===========================================================================
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
  var historyToggle = document.getElementById("historyToggle");
  var historyPanel = document.getElementById("historyPanel");
  var historyList = document.getElementById("historyList");
  var historyEmpty = document.getElementById("historyEmpty");
  var historyCloseBtn = document.getElementById("historyCloseBtn");
  var btnClearHistory = document.getElementById("btnClearHistory");
  var statisticsToggle = document.getElementById("statisticsToggle");
  var statisticsModal = document.getElementById("statisticsModal");
  var statisticsModalClose = document.getElementById("statisticsModalClose");
  var statisticsModalBody = document.getElementById("statisticsModalBody");
  var ariaLiveRegion = document.getElementById("ariaLiveRegion");

  // ===========================================================================
  // SECTION: Utilities
  // ===========================================================================
  function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function showToast(message) {
    var existing = document.querySelector(".toast-notification");
    if (existing) existing.parentNode.removeChild(existing);

    var toast = document.createElement("div");
    toast.className = "toast-notification";
    toast.textContent = message;
    toast.setAttribute("role", "status");
    document.body.appendChild(toast);
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 3000);
  }

  function announceToScreenReader(msg) {
    if (ariaLiveRegion) {
      ariaLiveRegion.textContent = msg;
    }
  }

  function debounce(fn, delay) {
    var timer;
    return function () {
      var args = arguments;
      var ctx = this;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
    };
  }

  function simpleHash(str) {
    var h = 0;
    for (var i = 0; i < str.length; i++) {
      h = ((h * 31) + str.charCodeAt(i)) >>> 0;
    }
    return ("00000000" + h.toString(16)).slice(-8);
  }

  function parseStartLine(ref) {
    if (!ref) return null;
    var cleaned = ref.replace(/^(Line |line |L|l)/, "");
    var m = cleaned.match(/^(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  }

  function downloadAsFile(content, filename, mimeType) {
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast(t("copiedToClipboard"));
      }).catch(function () {
        fallbackCopy(text);
      });
    } else {
      fallbackCopy(text);
    }
  }

  function fallbackCopy(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    try { document.execCommand("copy"); showToast(t("copiedToClipboard")); } catch (e) { /* noop */ }
    document.body.removeChild(textarea);
  }

  // Tag Input Data
  var tagData = { constraints: [] };

  // ===========================================================================
  // SECTION: Input Mode & Tabs
  // ===========================================================================
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

  // Language Toggle
  function applyLanguage(lang) {
    currentLang = lang;
    langToggle.textContent = lang.toUpperCase();
    document.documentElement.setAttribute("lang", lang);

    var dict = TRANSLATIONS[lang] || TRANSLATIONS.de;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (dict[key]) el.placeholder = dict[key];
    });

    document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-title");
      if (dict[key]) el.title = dict[key];
    });

    document.querySelectorAll("[data-i18n-label]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-label");
      if (dict[key]) el.label = dict[key];
    });

    localStorage.setItem("ra-lang", lang);
  }

  function initLanguage() {
    var urlLang = new URLSearchParams(window.location.search).get("lang");
    var saved = urlLang ? urlLang.toLowerCase() : localStorage.getItem("ra-lang");
    if (saved) applyLanguage(saved);
  }

  langToggle.addEventListener("click", function () {
    applyLanguage(currentLang === "de" ? "en" : "de");
  });

  initLanguage();

  // Dynamic placeholder for Solution Design Review (debounced)
  (function () {
    var reviewTypeEl = document.getElementById("reviewType");
    var codeInputEl = document.getElementById("codeInput");
    if (reviewTypeEl && codeInputEl) {
      reviewTypeEl.addEventListener("change", debounce(function () {
        if (reviewTypeEl.value === "SOLUTION_DESIGN_REVIEW") {
          codeInputEl.placeholder = t("designInputPlaceholder");
        } else {
          codeInputEl.placeholder = t("codeInputPlaceholder");
        }
      }, 100));
    }
  })();

  // Input Mode Tabs (with ARIA)
  (function () {
    var tabContainer = document.getElementById("inputModeTabs");
    var codeInputEl = document.getElementById("codeInput");
    if (!tabContainer || !codeInputEl) return;

    tabContainer.addEventListener("click", function (e) {
      var btn = e.target.closest(".input-tab");
      if (!btn) return;

      var mode = btn.getAttribute("data-mode");
      if (!mode || mode === currentInputMode) return;

      currentInputMode = mode;

      // Update active tab and ARIA
      tabContainer.querySelectorAll(".input-tab").forEach(function (tab) {
        var isActive = tab === btn;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", String(isActive));
      });

      // Update placeholder
      if (mode === "diff") {
        codeInputEl.placeholder = t("diffPlaceholder");
      } else if (mode === "change_package") {
        codeInputEl.placeholder = t("changePackagePlaceholder");
      } else {
        var reviewTypeEl = document.getElementById("reviewType");
        if (reviewTypeEl && reviewTypeEl.value === "SOLUTION_DESIGN_REVIEW") {
          codeInputEl.placeholder = t("designInputPlaceholder");
        } else {
          codeInputEl.placeholder = t("codeInputPlaceholder");
        }
      }
    });

    // Keyboard support for tabs
    tabContainer.addEventListener("keydown", function (e) {
      var tabs = tabContainer.querySelectorAll(".input-tab");
      var current = tabContainer.querySelector(".input-tab.active");
      var idx = Array.prototype.indexOf.call(tabs, current);

      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        var next = e.key === "ArrowRight" ? (idx + 1) % tabs.length : (idx - 1 + tabs.length) % tabs.length;
        tabs[next].click();
        tabs[next].focus();
      }
    });
  })();

  // Collapsible: Advanced Options
  advancedToggle.addEventListener("click", function () {
    var expanded = advancedToggle.getAttribute("aria-expanded") === "true";
    advancedToggle.setAttribute("aria-expanded", String(!expanded));
    advancedBody.hidden = expanded;
  });

  // Collapsible: Result Cards (with keyboard support)
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

  // Keyboard: Enter/Space on finding headers to expand/collapse
  document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      var findingHeader = e.target.closest(".finding-header");
      if (findingHeader) {
        e.preventDefault();
        findingHeader.click();
      }
    }
  });

  // Tag Input
  function initTagInput(inputId, tagsContainerId, dataKey) {
    var input = document.getElementById(inputId);
    var tagsContainer = document.getElementById(tagsContainerId);
    var container = input ? input.closest(".tag-input-container") : null;

    if (!input || !tagsContainer) return;

    if (container) {
      container.addEventListener("click", function (e) {
        if (e.target === container || e.target === tagsContainer) { input.focus(); }
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
      paste.split(/[,;\n]+/).forEach(function (part) { addTag(part); });
    });
  }

  function renderTags(container, dataKey) {
    container.innerHTML = "";
    var frag = document.createDocumentFragment();
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
      frag.appendChild(pill);
    });
    container.appendChild(frag);
  }

  initTagInput("constraintsInput", "constraintsTags", "constraints");

  // Error dismiss
  btnDismissError.addEventListener("click", function () {
    errorState.hidden = true;
    placeholder.hidden = false;
  });

  // ===========================================================================
  // SECTION: Form Submission & Pipeline
  // ===========================================================================
  function validateForm() {
    var reviewType = document.getElementById("reviewType").value;
    var artifactType = document.getElementById("artifactType").value;
    var code = document.getElementById("codeInput").value.trim();

    if (!reviewType) { showValidationError(t("valReviewType")); return false; }
    if (!artifactType) { showValidationError(t("valArtifactType")); return false; }
    if (!code) { showValidationError(t("valCode")); return false; }
    return true;
  }

  function showValidationError(msg) {
    errorMessage.textContent = msg;
    errorState.hidden = false;
    placeholder.hidden = true;
    loadingState.hidden = true;
    resultsContainer.hidden = true;
  }

  function buildPayload() {
    var payload = {
      review_type: document.getElementById("reviewType").value,
      artifact_type: document.getElementById("artifactType").value,
      code_or_diff: document.getElementById("codeInput").value,
      input_mode: currentInputMode,
      context_summary: document.getElementById("contextSummary").value || "",
      goal_of_review: document.getElementById("goalOfReview").value || "",
      review_context: document.getElementById("reviewContext").value || "GREENFIELD",
      language: currentLang.toUpperCase(),
      known_constraints: tagData.constraints.slice(),
      question_focus: [],
      clarifications: {}
    };

    document.querySelectorAll('input[name="question_focus"]:checked').forEach(function (cb) {
      payload.question_focus.push(cb.value);
    });

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

    var domainPack = document.getElementById("domainPack").value;
    if (domainPack) payload.domain_pack = domainPack;

    return payload;
  }

  function submitReview(payload) {
    submitBtn.classList.add("is-loading");
    submitBtn.disabled = true;
    placeholder.hidden = true;
    errorState.hidden = true;
    resultsContainer.hidden = true;
    loadingState.hidden = false;

    // Dismiss any inline error banners
    dismissAllErrorBanners();

    // Timeout handling: show message after 30s
    var timeoutId = setTimeout(function () {
      announceToScreenReader(t("timeoutError"));
      showToast(t("timeoutError"));
    }, 30000);

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
        currentReviewId = data._history_id || null;
        renderResults(data);
        if (dbAvailable) loadHistory();
        announceToScreenReader(t("resOverallAssessment") + ": " + ((data.overall_assessment || {}).go_no_go || "GO"));
        // Focus first result card for accessibility
        var firstCard = resultsContainer.querySelector(".result-card-header");
        if (firstCard) firstCard.focus();
      })
      .catch(function (err) {
        var isNetworkError = !err.message || err.message === "Failed to fetch";
        if (isNetworkError) {
          showErrorBanner(t("networkError"), function () { submitReview(payload); });
        } else {
          showErrorBanner(err.message || t("unknownError"), function () { submitReview(payload); });
        }
        loadingState.hidden = true;
        placeholder.hidden = false;
      })
      .finally(function () {
        clearTimeout(timeoutId);
        submitBtn.classList.remove("is-loading");
        submitBtn.disabled = false;
        loadingState.hidden = true;
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!validateForm()) return;
    clarifications = {};
    var payload = buildPayload();
    lastPayload = payload;
    submitReview(payload);
  });

  // ===========================================================================
  // SECTION: Error Handling UX
  // ===========================================================================
  function showErrorBanner(message, retryFn) {
    dismissAllErrorBanners();

    var banner = document.createElement("div");
    banner.className = "error-banner";
    banner.setAttribute("role", "alert");

    var textSpan = document.createElement("span");
    textSpan.className = "error-banner-text";
    textSpan.textContent = message;
    banner.appendChild(textSpan);

    if (retryFn) {
      var retryBtn = document.createElement("button");
      retryBtn.type = "button";
      retryBtn.className = "error-banner-retry";
      retryBtn.textContent = t("retryBtn");
      retryBtn.addEventListener("click", function () {
        banner.parentNode.removeChild(banner);
        retryFn();
      });
      banner.appendChild(retryBtn);
    }

    var dismissBtn = document.createElement("button");
    dismissBtn.type = "button";
    dismissBtn.className = "error-banner-dismiss";
    dismissBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    dismissBtn.setAttribute("aria-label", t("close"));
    dismissBtn.addEventListener("click", function () {
      banner.parentNode.removeChild(banner);
    });
    banner.appendChild(dismissBtn);

    var panel = document.querySelector(".panel-right");
    if (panel) panel.insertBefore(banner, panel.firstChild);
  }

  function dismissAllErrorBanners() {
    document.querySelectorAll(".error-banner").forEach(function (b) {
      b.parentNode.removeChild(b);
    });
  }

  // ===========================================================================
  // SECTION: Results Rendering
  // ===========================================================================
  function renderResults(data) {
    loadingState.hidden = true;
    lastResponse = data;

    renderOverallAssessment(data.overall_assessment);
    renderReviewSummary(data.review_summary);
    renderOpenQuestions(data.missing_information || []);
    renderFindings(data.findings || []);
    renderTestGaps(data.test_gaps || []);
    renderRecommendedActions(data.recommended_actions || []);
    renderRefactoringHints(data.refactoring_hints || []);
    renderRiskDashboard(data.risk_notes || []);
    renderCleanCoreHints(data.clean_core_hints || []);
    renderSimilarReviews(data.similar_reviews || []);
    renderRecurringPatterns(data.recurring_patterns || [], data.findings || []);

    resultsContainer.hidden = false;

    if (dbAvailable && currentReviewId) {
      showTeamWorkflowBar(true);
      updateCompletionBar(currentReviewId);
    } else {
      showTeamWorkflowBar(false);
    }
  }

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
      html += '<span style="margin-left:0.75rem;font-size:var(--text-sm);color:var(--color-text-secondary);">' +
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

    if (lastResponse && lastResponse.quality_gate) {
      var qg = lastResponse.quality_gate;
      var qgClass = qg.passed ? "quality-gate-badge--pass" : "quality-gate-badge--fail";
      var qgLabel = qg.passed ? (t("qualityGatePass")) : (t("qualityGateFail"));
      html += '<div class="quality-gate-badge ' + qgClass + '">' +
        escapeHtml(t("qualityGate")) + ': ' + escapeHtml(qgLabel) + '</div>';
      if (!qg.passed && qg.reason) {
        html += '<p class="quality-gate-reason">' + escapeHtml(qg.reason) + '</p>';
      }
    }

    body.innerHTML = html;
  }

  function renderReviewSummary(summary) {
    var body = document.getElementById("cardReviewSummaryBody");
    body.innerHTML = "";

    if (!summary) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noFindings")) + '</p>';
      return;
    }

    body.innerHTML = '<p class="review-summary-text">' + escapeHtml(summary) + '</p>';
  }

  // ===========================================================================
  // SECTION: Findings (Expansion, Resolution, Feedback)
  // ===========================================================================
  function renderFindings(findings) {
    var body = document.getElementById("cardFindingsBody");
    body.innerHTML = "";

    if (findings.length === 0) {
      body.innerHTML = '<p class="result-empty-hint">' + escapeHtml(t("noFindings")) + '</p>';
      return;
    }

    var container = document.createElement("div");
    container.className = "findings-list";

    var totalFindings = findings.length;
    var renderCount = totalFindings > LAZY_RENDER_THRESHOLD ? LAZY_RENDER_THRESHOLD : totalFindings;

    // Use DocumentFragment for batch rendering
    var frag = document.createDocumentFragment();
    for (var i = 0; i < renderCount; i++) {
      frag.appendChild(buildFindingItem(findings[i], i));
    }
    container.appendChild(frag);

    body.appendChild(container);

    // Lazy rendering: show more button if needed
    if (totalFindings > renderCount) {
      var remaining = totalFindings - renderCount;
      var showMoreBtn = document.createElement("button");
      showMoreBtn.type = "button";
      showMoreBtn.className = "btn-show-more";
      showMoreBtn.textContent = t("showMore").replace("{n}", String(remaining));
      showMoreBtn.setAttribute("aria-label", t("showMore").replace("{n}", String(remaining)));

      var rendered = renderCount;
      showMoreBtn.addEventListener("click", function () {
        var nextBatch = Math.min(rendered + LAZY_RENDER_BATCH, totalFindings);
        var batchFrag = document.createDocumentFragment();
        for (var j = rendered; j < nextBatch; j++) {
          batchFrag.appendChild(buildFindingItem(findings[j], j));
        }
        container.appendChild(batchFrag);
        rendered = nextBatch;

        if (rendered >= totalFindings) {
          showMoreBtn.parentNode.removeChild(showMoreBtn);
        } else {
          var newRemaining = totalFindings - rendered;
          showMoreBtn.textContent = t("showMore").replace("{n}", String(newRemaining));
        }
      });

      body.appendChild(showMoreBtn);
    }
  }

  function buildFindingItem(f, idx) {
    var item = document.createElement("div");
    item.className = "finding-item finding-item--" + (f.severity || "UNCLEAR");
    item.setAttribute("tabindex", "0");
    item.setAttribute("role", "region");
    item.setAttribute("aria-label", (f.severity || "UNCLEAR") + ": " + (f.title || "Finding"));

    if (idx < 3) item.classList.add("is-expanded");

    var header = document.createElement("div");
    header.className = "finding-header";
    header.setAttribute("role", "button");
    header.setAttribute("tabindex", "0");
    header.setAttribute("aria-expanded", idx < 3 ? "true" : "false");
    header.addEventListener("click", function () {
      var expanded = item.classList.toggle("is-expanded");
      header.setAttribute("aria-expanded", String(expanded));
    });

    var badge = document.createElement("span");
    badge.className = "severity-badge severity-badge--" + (f.severity || "UNCLEAR");
    badge.textContent = f.severity || "UNCLEAR";

    var title = document.createElement("span");
    title.className = "finding-title";
    title.textContent = f.title || "Finding";

    header.appendChild(badge);
    header.appendChild(title);

    // Diff mode badges
    if (currentInputMode === "diff") {
      var diffBadge = document.createElement("span");
      var isNew = f.is_new !== false;
      diffBadge.className = isNew ? "badge-new" : "badge-preexisting";
      diffBadge.textContent = isNew ? t("badgeNew") : t("badgePreExisting");
      header.appendChild(diffBadge);
    }

    if (f.line_reference) {
      var lineRef = document.createElement("span");
      lineRef.className = "finding-line-ref";
      lineRef.textContent = t("lineRef") + " " + f.line_reference;
      header.appendChild(lineRef);
    }

    var expandIcon = document.createElement("svg");
    expandIcon.className = "finding-expand-icon";
    expandIcon.setAttribute("width", "12");
    expandIcon.setAttribute("height", "12");
    expandIcon.setAttribute("viewBox", "0 0 24 24");
    expandIcon.setAttribute("fill", "none");
    expandIcon.setAttribute("stroke", "currentColor");
    expandIcon.setAttribute("stroke-width", "2");
    expandIcon.setAttribute("aria-hidden", "true");
    expandIcon.innerHTML = '<polyline points="6 9 12 15 18 9"/>';
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

    // Feedback buttons
    if (dbAvailable && currentReviewId) {
      var fbRow = document.createElement("div");
      fbRow.className = "finding-feedback";
      fbRow.setAttribute("data-finding-index", idx);

      var fbLabel = document.createElement("span");
      fbLabel.className = "feedback-label";
      fbLabel.textContent = t("feedbackLabel");
      fbRow.appendChild(fbLabel);

      var fbKey = currentReviewId + "-" + idx;
      var btnUp = document.createElement("button");
      btnUp.type = "button";
      btnUp.className = "feedback-btn feedback-btn--up" + (feedbackState[fbKey] === true ? " active" : "");
      btnUp.setAttribute("aria-label", t("feedbackUp"));
      btnUp.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg> ' + escapeHtml(t("feedbackUp"));

      var btnDown = document.createElement("button");
      btnDown.type = "button";
      btnDown.className = "feedback-btn feedback-btn--down" + (feedbackState[fbKey] === false ? " active" : "");
      btnDown.setAttribute("aria-label", t("feedbackDown"));
      btnDown.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/><path d="M17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"/></svg> ' + escapeHtml(t("feedbackDown"));

      (function (upBtn, downBtn, findingIdx, ruleId, key) {
        upBtn.onclick = function (e) {
          e.stopPropagation();
          submitFeedback(currentReviewId, findingIdx, ruleId, true);
          feedbackState[key] = true;
          upBtn.classList.add("active");
          downBtn.classList.remove("active");
        };
        downBtn.onclick = function (e) {
          e.stopPropagation();
          submitFeedback(currentReviewId, findingIdx, ruleId, false);
          feedbackState[key] = false;
          downBtn.classList.add("active");
          upBtn.classList.remove("active");
        };
      })(btnUp, btnDown, idx, f.rule_id || null, fbKey);

      fbRow.appendChild(btnUp);
      fbRow.appendChild(btnDown);
      details.appendChild(fbRow);

      // Resolution controls
      var resRow = document.createElement("div");
      resRow.className = "finding-resolution";
      resRow.setAttribute("data-finding-index", idx);

      var resLabel = document.createElement("span");
      resLabel.className = "resolution-label";
      resLabel.textContent = t("resolutionLabel");
      resRow.appendChild(resLabel);

      var currentStatus = resolutionState[idx] || "OPEN";

      var statuses = [
        { value: "ACCEPTED", label: t("resAccepted") },
        { value: "REJECTED", label: t("resRejected") },
        { value: "DEFERRED", label: t("resDeferred") },
        { value: "FIXED", label: t("resFixed") }
      ];

      (function (findingIdx, ruleId, resRowEl) {
        statuses.forEach(function (s) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "resolution-btn" + (currentStatus === s.value ? " active" : "");
          btn.setAttribute("data-status", s.value);
          btn.setAttribute("aria-label", s.label);
          btn.textContent = s.label;
          btn.onclick = function (e) {
            e.stopPropagation();
            var isActive = btn.classList.contains("active");
            resRowEl.querySelectorAll(".resolution-btn").forEach(function (b) { b.classList.remove("active"); });
            var newStatus = isActive ? "OPEN" : s.value;
            if (!isActive) btn.classList.add("active");
            resolutionState[findingIdx] = newStatus;
            var commentInput = resRowEl.querySelector(".resolution-comment");
            var commentVal = commentInput ? commentInput.value.trim() : "";
            setFindingResolution(currentReviewId, findingIdx, newStatus, commentVal);
            updateFindingStatusBadge(findingIdx, newStatus);
          };
          resRowEl.appendChild(btn);
        });

        var commentInput = document.createElement("input");
        commentInput.type = "text";
        commentInput.className = "resolution-comment";
        commentInput.placeholder = t("resolutionCommentPlaceholder");
        commentInput.setAttribute("aria-label", t("resolutionCommentPlaceholder"));
        commentInput.onclick = function (e) { e.stopPropagation(); };
        resRowEl.appendChild(commentInput);
      })(idx, f.rule_id || null, resRow);

      details.appendChild(resRow);

      if (currentStatus && currentStatus !== "OPEN") {
        var statusBadge = document.createElement("span");
        statusBadge.className = "resolution-status-badge resolution-status-" + currentStatus;
        statusBadge.setAttribute("data-resolution-badge", idx);
        statusBadge.textContent = currentStatus;
        var expandIcon2 = header.querySelector(".finding-expand-icon");
        if (expandIcon2) {
          header.insertBefore(statusBadge, expandIcon2);
        } else {
          header.appendChild(statusBadge);
        }
      }
    }

    item.appendChild(header);
    item.appendChild(details);
    return item;
  }

  // Open Questions (with inline answer inputs)
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

    var filledClarifications = {};
    Object.keys(clarifications).forEach(function (key) {
      if (clarifications[key] && clarifications[key].trim() !== "") {
        filledClarifications[key] = clarifications[key].trim();
      }
    });

    if (Object.keys(filledClarifications).length === 0) return;

    var payload = {};
    Object.keys(lastPayload).forEach(function (k) { payload[k] = lastPayload[k]; });
    payload.clarifications = filledClarifications;
    payload.language = currentLang.toUpperCase();

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
        currentReviewId = data._history_id || null;
        renderResults(data);
        resultsContainer.hidden = false;
        if (dbAvailable) loadHistory();

        var oqHeader = document.querySelector('#cardOpenQuestions .result-card-header');
        var oqBody = document.getElementById("cardOpenQuestionsBody");
        if (oqHeader && oqBody && oqBody.hidden) {
          oqBody.hidden = false;
          oqHeader.setAttribute("aria-expanded", "true");
        }
      })
      .catch(function (err) {
        showErrorBanner(err.message || t("unknownError"), null);
      })
      .finally(function () {
        btn.classList.remove("is-loading");
        btn.disabled = false;
      });
  }

  function renderOpenQuestions(questions) {
    var body = document.getElementById("cardOpenQuestionsBody");
    body.innerHTML = "";

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

    var regenBtn = document.createElement("button");
    regenBtn.type = "button";
    regenBtn.id = "btnRegenerate";
    regenBtn.className = "btn-regenerate";
    regenBtn.innerHTML = '<span class="btn-regenerate-text">' + escapeHtml(t("oq.regenerateBtn")) + '</span><span class="btn-regenerate-loader" aria-hidden="true"></span>';
    regenBtn.hidden = true;
    regenBtn.addEventListener("click", function () { handleRegenerate(regenBtn); });
    var oqCard = document.getElementById("cardOpenQuestions");
    if (oqCard) oqCard.appendChild(regenBtn);

    updateRegenerateButton();
  }

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
        ' <span class="severity-badge severity-badge--' + (g.priority || "OPTIONAL") + '" style="margin-left:0.25rem;">' +
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
      html += '<div class="risk-bar"><div class="risk-bar-fill"></div></div>';
      card.innerHTML = html;
      container.appendChild(card);
    });
    body.appendChild(container);
  }

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
      var html = '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">' +
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

  // ===========================================================================
  // SECTION: Export & Download
  // ===========================================================================
  function formatAsMarkdown(response) {
    var isDE = currentLang === "de";
    var lines = [];
    lines.push("# " + (isDE ? "Review-Bericht" : "Review Report"));
    lines.push("");
    var assessment = response.overall_assessment || {};
    if (assessment.go_no_go) {
      lines.push("## " + (isDE ? "Gesamtbewertung" : "Overall Assessment"));
      lines.push("");
      var verdictMap = { GO: "GO", CONDITIONAL_GO: "CONDITIONAL GO", NO_GO: "NO-GO" };
      var verdict = verdictMap[assessment.go_no_go] || assessment.go_no_go;
      var confLabel = isDE ? "Konfidenz" : "Confidence";
      lines.push("**" + verdict + "**" + (assessment.confidence ? " (" + confLabel + ": " + assessment.confidence + ")" : ""));
      lines.push("");
      if (assessment.summary) { lines.push(assessment.summary); lines.push(""); }
      var counts = [];
      if (assessment.critical_count) counts.push(assessment.critical_count + " Critical");
      if (assessment.important_count) counts.push(assessment.important_count + " Important");
      if (assessment.optional_count) counts.push(assessment.optional_count + " Optional");
      if (counts.length) { lines.push(counts.join(" | ")); lines.push(""); }
    }
    if (response.review_summary) {
      lines.push("## " + (isDE ? "Zusammenfassung" : "Summary"));
      lines.push("");
      lines.push(response.review_summary);
      lines.push("");
    }
    var findings = response.findings || [];
    if (findings.length) {
      lines.push("## " + (isDE ? "Befunde" : "Findings"));
      lines.push("");
      lines.push(isDE ? "| # | Schweregrad | Titel | Empfehlung |" : "| # | Severity | Title | Recommendation |");
      lines.push("|---|-----------|-------|--------------|");
      findings.forEach(function (f, i) {
        var rec = (f.recommendation || "").replace(/\|/g, "\\|");
        if (rec.length > 120) rec = rec.substring(0, 117) + "...";
        lines.push("| " + (i + 1) + " | " + (f.severity || "") + " | " + (f.title || "").replace(/\|/g, "\\|") + " | " + rec + " |");
      });
      lines.push("");
      findings.forEach(function (f, i) {
        lines.push("### " + (i + 1) + ". [" + (f.severity || "") + "] " + (f.title || ""));
        lines.push("");
        if (f.observation) { lines.push("**" + (isDE ? "Beobachtung" : "Observation") + ":** " + f.observation); lines.push(""); }
        if (f.reasoning) { lines.push("**" + (isDE ? "Begruendung" : "Reasoning") + ":** " + f.reasoning); lines.push(""); }
        if (f.impact) { lines.push("**" + (isDE ? "Auswirkung" : "Impact") + ":** " + f.impact); lines.push(""); }
        if (f.recommendation) { lines.push("**" + (isDE ? "Empfehlung" : "Recommendation") + ":** " + f.recommendation); lines.push(""); }
        var refs = [];
        if (f.rule_id) refs.push("Rule: " + f.rule_id);
        if (f.line_reference) refs.push("Line: " + f.line_reference);
        if (refs.length) { lines.push("_" + refs.join(" | ") + "_"); lines.push(""); }
      });
    }
    var testGaps = response.test_gaps || [];
    if (testGaps.length) {
      lines.push("## " + (isDE ? "Testluecken" : "Test Gaps"));
      lines.push("");
      testGaps.forEach(function (g) {
        lines.push("- **[" + (g.priority || "") + "]** " + (g.category || "") + ": " + (g.description || ""));
        if (g.suggested_test) lines.push("  - " + g.suggested_test);
      });
      lines.push("");
    }
    var risks = response.risk_notes || [];
    if (risks.length) {
      lines.push("## " + (isDE ? "Risiko-Dashboard" : "Risk Dashboard"));
      lines.push("");
      risks.forEach(function (r) {
        lines.push("- **" + (r.category || "") + "** [" + (r.severity || "") + "]: " + (r.description || ""));
        if (r.mitigation) lines.push("  - " + (isDE ? "Massnahme" : "Mitigation") + ": " + r.mitigation);
      });
      lines.push("");
    }
    var actions = response.recommended_actions || [];
    if (actions.length) {
      lines.push("## " + (isDE ? "Empfohlene Massnahmen" : "Recommended Actions"));
      lines.push("");
      actions.forEach(function (a) {
        var effort = a.effort_hint ? " [" + a.effort_hint + "]" : "";
        lines.push((a.order || "") + ". **" + (a.title || "") + "**" + effort);
        if (a.description) lines.push("   " + a.description);
      });
      lines.push("");
    }
    return lines.join("\n");
  }

  function formatAsTicketComment(response) {
    var isDE = currentLang === "de";
    var lines = [];
    var assessment = response.overall_assessment || {};
    var verdictMap = { GO: "GO", CONDITIONAL_GO: "CONDITIONAL GO", NO_GO: "NO-GO" };
    var verdict = verdictMap[assessment.go_no_go] || assessment.go_no_go || "GO";
    lines.push("[" + verdict + "] " + (isDE ? "Code-Review Ergebnis" : "Code Review Result"));
    lines.push("");
    if (assessment.summary) { lines.push(assessment.summary); lines.push(""); }
    var findings = response.findings || [];
    if (findings.length) {
      lines.push(isDE ? "Befunde:" : "Findings:");
      findings.slice(0, 5).forEach(function (f) {
        var rec = (f.recommendation || "");
        if (rec.length > 80) rec = rec.substring(0, 77) + "...";
        lines.push("- [" + (f.severity || "") + "] " + (f.title || ""));
        if (rec) lines.push("  -> " + rec);
      });
      if (findings.length > 5) {
        lines.push("  (+" + (findings.length - 5) + " " + (isDE ? "weitere" : "more") + ")");
      }
      lines.push("");
    }
    var actions = response.recommended_actions || [];
    if (actions.length) {
      lines.push(isDE ? "Naechste Schritte:" : "Next Steps:");
      actions.slice(0, 3).forEach(function (a) { lines.push("- " + (a.title || "")); });
      lines.push("");
    }
    return lines.join("\n");
  }

  function formatAsClipboard(response) {
    var lines = [];
    var assessment = response.overall_assessment || {};
    var verdictMap = { GO: "GO", CONDITIONAL_GO: "CONDITIONAL GO", NO_GO: "NO-GO" };
    var verdict = verdictMap[assessment.go_no_go] || assessment.go_no_go || "GO";
    var line = verdict;
    if (assessment.confidence) line += " (" + assessment.confidence + ")";
    if (assessment.summary) line += " - " + assessment.summary;
    lines.push(line);
    lines.push("");
    var isDE = currentLang === "de";
    var findings = response.findings || [];
    if (findings.length) {
      lines.push(isDE ? "Befunde:" : "Findings:");
      findings.forEach(function (f) {
        lines.push("  [" + (f.severity || "") + "] " + (f.title || ""));
      });
      lines.push("");
    }
    var actions = response.recommended_actions || [];
    if (actions.length) {
      lines.push(isDE ? "Massnahmen:" : "Actions:");
      actions.forEach(function (a) {
        lines.push("  " + (a.order || "") + ". " + (a.title || ""));
      });
      lines.push("");
    }
    return lines.join("\n");
  }

  function formatAsSarif(response) {
    var SEVERITY_MAP = { CRITICAL: "error", IMPORTANT: "error", OPTIONAL: "warning", UNCLEAR: "note" };
    var findings = response.findings || [];
    var rules = [];
    var ruleIndexMap = {};
    var results = [];
    findings.forEach(function (f) {
      var ruleId = f.rule_id || ("REVIEW-" + simpleHash(f.title || "unknown"));
      var level = SEVERITY_MAP[f.severity] || "note";
      if (!(ruleId in ruleIndexMap)) {
        ruleIndexMap[ruleId] = rules.length;
        var ruleDef = { id: ruleId, shortDescription: { text: f.title || "" }, defaultConfiguration: { level: level } };
        if (f.recommendation) ruleDef.help = { text: f.recommendation };
        if (f.reasoning) ruleDef.fullDescription = { text: f.reasoning };
        rules.push(ruleDef);
      }
      var result = { ruleId: ruleId, ruleIndex: ruleIndexMap[ruleId], level: level, message: { text: f.observation || f.title || "" } };
      var startLine = parseStartLine(f.line_reference);
      if (startLine || f.artifact_reference) {
        var physLoc = {};
        if (f.artifact_reference) physLoc.artifactLocation = { uri: f.artifact_reference };
        if (startLine) physLoc.region = { startLine: startLine };
        result.locations = [{ physicalLocation: physLoc }];
      }
      results.push(result);
    });
    return {
      "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
      version: "2.1.0",
      runs: [{ tool: { driver: { name: "SAP ABAP/UI5 Review Assistant", version: "2.0.0", rules: rules } }, results: results }]
    };
  }

  function formatAsCiJson(response) {
    var findings = response.findings || [];
    var bySeverity = {};
    findings.forEach(function (f) {
      var sev = f.severity || "UNCLEAR";
      bySeverity[sev] = (bySeverity[sev] || 0) + 1;
    });
    var assessment = response.overall_assessment || {};
    var criticalCount = bySeverity.CRITICAL || 0;
    var passed = criticalCount === 0;
    var violations = [];
    if (criticalCount > 0) violations.push("CRITICAL findings: " + criticalCount + " (max allowed: 0)");
    var qualityGate = response.quality_gate || {
      passed: passed,
      reason: passed ? "All quality gate checks passed" : "Quality gate failed: " + violations.length + " violation(s)",
      violations: violations,
      config: { max_critical: 0, max_important: -1, max_total: -1, require_go: false, require_clean_core: false, custom_blocked_rules: [] }
    };
    return {
      tool: "SAP ABAP/UI5 Review Assistant",
      version: "2.0.0",
      timestamp: new Date().toISOString(),
      quality_gate: qualityGate,
      summary: { total_findings: findings.length, by_severity: bySeverity, assessment: assessment.go_no_go || "GO", confidence: assessment.confidence || "MEDIUM" },
      findings: findings.map(function (f) {
        return { severity: f.severity || "UNCLEAR", title: f.title || "", rule_id: f.rule_id || null, line_reference: f.line_reference || null, recommendation: f.recommendation || "" };
      }),
      test_gaps: (response.test_gaps || []).map(function (g) {
        return { category: g.category || "", description: g.description || "", priority: g.priority || "OPTIONAL" };
      }),
      risk_notes: (response.risk_notes || []).map(function (n) {
        return { category: n.category || "", description: n.description || "", severity: n.severity || "LOW" };
      }),
      clean_core_hints: (response.clean_core_hints || []).map(function (h) {
        return { finding: h.finding || "", severity: h.severity || "OPTIONAL", released_api_alternative: h.released_api_alternative || null };
      })
    };
  }

  // Export Button Handlers
  var btnExportMarkdown = document.getElementById("btnExportMarkdown");
  var btnCopyTicket = document.getElementById("btnCopyTicket");
  var btnCopyClipboard = document.getElementById("btnCopyClipboard");

  if (btnExportMarkdown) {
    btnExportMarkdown.addEventListener("click", function () {
      if (!lastResponse) return;
      var md = formatAsMarkdown(lastResponse);
      var filename = "review-" + new Date().toISOString().slice(0, 10) + ".md";
      downloadAsFile(md, filename, "text/markdown");
      showToast(t("markdownDownloaded"));
    });
  }

  if (btnCopyTicket) {
    btnCopyTicket.addEventListener("click", function () {
      if (!lastResponse) return;
      copyToClipboard(formatAsTicketComment(lastResponse));
    });
  }

  if (btnCopyClipboard) {
    btnCopyClipboard.addEventListener("click", function () {
      if (!lastResponse) return;
      copyToClipboard(formatAsClipboard(lastResponse));
    });
  }

  var btnExportSarif = document.getElementById("btnExportSarif");
  if (btnExportSarif) {
    btnExportSarif.addEventListener("click", function () {
      if (!lastResponse) return;
      var sarif = formatAsSarif(lastResponse);
      var json = JSON.stringify(sarif, null, 2);
      downloadAsFile(json, "review-" + new Date().toISOString().slice(0, 10) + ".sarif.json", "application/sarif+json");
      showToast(t("sarifDownloaded"));
    });
  }

  var btnExportCiJson = document.getElementById("btnExportCiJson");
  if (btnExportCiJson) {
    btnExportCiJson.addEventListener("click", function () {
      if (!lastResponse) return;
      var ciJson = formatAsCiJson(lastResponse);
      var json = JSON.stringify(ciJson, null, 2);
      downloadAsFile(json, "review-" + new Date().toISOString().slice(0, 10) + ".ci.json", "application/json");
      showToast(t("ciJsonDownloaded"));
    });
  }

  // ===========================================================================
  // SECTION: History
  // ===========================================================================
  function checkDbAvailability() {
    fetch("/api/health")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        dbAvailable = !!data.db_available;
        if (dbAvailable) {
          historyToggle.hidden = false;
          if (statisticsToggle) statisticsToggle.hidden = false;
          loadHistory();
        } else {
          historyToggle.hidden = true;
          historyPanel.hidden = true;
          if (statisticsToggle) statisticsToggle.hidden = true;
        }
      })
      .catch(function () {
        dbAvailable = false;
        historyToggle.hidden = true;
        if (statisticsToggle) statisticsToggle.hidden = true;
      });
  }

  checkDbAvailability();

  historyToggle.addEventListener("click", function () {
    var isOpen = !historyPanel.hidden;
    historyPanel.hidden = isOpen;
    historyToggle.classList.toggle("is-active", !isOpen);
    if (!isOpen) loadHistory();
  });

  historyCloseBtn.addEventListener("click", function () {
    historyPanel.hidden = true;
    historyToggle.classList.remove("is-active");
  });

  function loadHistory() {
    fetch("/api/history?limit=50")
      .then(function (resp) { return resp.json(); })
      .then(function (entries) { renderHistoryList(entries || []); })
      .catch(function () { renderHistoryList([]); });
  }

  function renderHistoryList(entries) {
    var children = historyList.children;
    for (var i = children.length - 1; i >= 0; i--) {
      if (children[i] !== historyEmpty) historyList.removeChild(children[i]);
    }

    if (entries.length === 0) {
      historyEmpty.hidden = false;
      return;
    }

    historyEmpty.hidden = true;
    var frag = document.createDocumentFragment();

    entries.forEach(function (entry) {
      var el = document.createElement("div");
      el.className = "history-entry";
      el.setAttribute("data-review-id", entry.id);

      var date = new Date(entry.created_at);
      var dateStr = date.toLocaleDateString(currentLang === "de" ? "de-DE" : "en-US", {
        day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
      });

      var assessClass = "history-assessment-badge--" + (entry.overall_assessment || "GO");
      var assessLabel = entry.overall_assessment || "GO";
      if (assessLabel === "CONDITIONAL_GO") assessLabel = "COND.";

      var artifactLabel = (entry.artifact_type || "").replace(/_/g, " ");

      el.innerHTML =
        '<div class="history-entry-top">' +
          '<span class="history-entry-date">' + escapeHtml(dateStr) + '</span>' +
          '<span class="history-entry-badge ' + assessClass + '">' + escapeHtml(assessLabel) + '</span>' +
        '</div>' +
        '<div class="history-entry-meta">' +
          '<span class="history-artifact-badge">' + escapeHtml(artifactLabel) + '</span>' +
          '<span class="history-finding-count">' + (entry.finding_count || 0) + ' ' + escapeHtml(t("historyFindings")) + '</span>' +
        '</div>' +
        '<div class="history-entry-actions">' +
          '<button type="button" class="history-delete-btn" data-delete-id="' + escapeHtml(entry.id) + '" aria-label="Delete entry">' +
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' +
          '</button>' +
        '</div>';

      el.addEventListener("click", function (e) {
        if (e.target.closest(".history-delete-btn")) return;
        loadHistoryEntry(entry.id);
      });

      var delBtn = el.querySelector(".history-delete-btn");
      if (delBtn) {
        delBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          deleteHistoryEntry(entry.id);
        });
      }

      frag.appendChild(el);
    });

    historyList.appendChild(frag);
  }

  function loadHistoryEntry(id) {
    fetch("/api/history/" + encodeURIComponent(id))
      .then(function (resp) {
        if (!resp.ok) throw new Error("Not found");
        return resp.json();
      })
      .then(function (data) {
        if (data.full_response) {
          currentReviewId = id;
          loadFeedbackForReview(id, function () {
            loadResolutions(id, function () {
              renderResults(data.full_response);
              resultsContainer.hidden = false;
              placeholder.hidden = true;
              errorState.hidden = true;
            });
          });
        }
      })
      .catch(function () { /* noop */ });
  }

  function deleteHistoryEntry(id) {
    if (!confirm(t("historyDeleteConfirm"))) return;
    fetch("/api/history/" + encodeURIComponent(id), { method: "DELETE" })
      .then(function () { loadHistory(); })
      .catch(function () { /* noop */ });
  }

  btnClearHistory.addEventListener("click", function () {
    if (!confirm(t("historyClearConfirm"))) return;
    fetch("/api/history", { method: "DELETE" })
      .then(function () { loadHistory(); })
      .catch(function () { /* noop */ });
  });

  // ===========================================================================
  // SECTION: Similarity & Statistics
  // ===========================================================================
  function renderSimilarReviews(similarReviews) {
    var card = document.getElementById("cardSimilarReviews");
    var list = document.getElementById("similarReviewsList");
    if (!card || !list) return;

    list.innerHTML = "";

    if (!similarReviews || similarReviews.length === 0) {
      card.style.display = "none";
      return;
    }

    card.style.display = "";

    similarReviews.forEach(function (sr) {
      var item = document.createElement("div");
      item.className = "similar-review-item";

      var date = sr.created_at ? new Date(sr.created_at) : null;
      var dateStr = date ? date.toLocaleDateString(currentLang === "de" ? "de-DE" : "en-US", {
        day: "2-digit", month: "2-digit", year: "numeric"
      }) : "";

      var assessClass = "history-assessment-badge--" + (sr.assessment || "GO");
      var assessLabel = sr.assessment || "GO";
      if (assessLabel === "CONDITIONAL_GO") assessLabel = "COND.";

      var artifactLabel = (sr.artifact_type || "").replace(/_/g, " ");
      var scorePercent = Math.round((sr.score || 0) * 100);

      var html =
        '<div class="similar-review-top">' +
          '<span class="similar-review-date">' + escapeHtml(dateStr) + '</span>' +
          '<span class="history-entry-badge ' + assessClass + '">' + escapeHtml(assessLabel) + '</span>' +
        '</div>' +
        '<div class="similar-review-meta">' +
          '<span class="history-artifact-badge">' + escapeHtml(artifactLabel) + '</span>' +
          '<span class="history-finding-count">' + (sr.finding_count || 0) + ' ' + escapeHtml(t("historyFindings")) + '</span>' +
        '</div>' +
        '<div class="similarity-score-label">' + escapeHtml(t("similarScore")) + ': ' + scorePercent + '%</div>' +
        '<div class="similarity-score-bar"><div class="similarity-score-fill" style="width:' + scorePercent + '%"></div></div>';

      if (sr.shared_findings && sr.shared_findings.length > 0) {
        html += '<div class="similar-review-shared">' +
          escapeHtml(t("similarSharedFindings")) + ': ' + sr.shared_findings.length + '</div>';
      }

      item.innerHTML = html;

      (function (reviewId) {
        item.addEventListener("click", function () { loadHistoryEntry(reviewId); });
      })(sr.review_id);

      list.appendChild(item);
    });
  }

  function renderRecurringPatterns(patterns, findings) {
    if (!patterns || patterns.length === 0 || !findings || findings.length === 0) return;

    var patternMap = {};
    patterns.forEach(function (p) { patternMap[p.rule_id] = p; });

    var findingItems = document.querySelectorAll("#cardFindingsBody .finding-item");
    findingItems.forEach(function (item, idx) {
      if (idx >= findings.length) return;
      var f = findings[idx];
      if (!f.rule_id) return;
      var pattern = patternMap[f.rule_id];
      if (!pattern) return;

      var header = item.querySelector(".finding-header");
      if (!header || header.querySelector(".recurring-badge")) return;

      var badge = document.createElement("span");
      badge.className = "recurring-badge";
      badge.textContent = t("recurringBadge").replace("{n}", String(pattern.occurrence_count));
      var expandIcon = header.querySelector(".finding-expand-icon");
      if (expandIcon) {
        header.insertBefore(badge, expandIcon);
      } else {
        header.appendChild(badge);
      }
    });
  }

  // Statistics Modal
  if (statisticsToggle) {
    statisticsToggle.addEventListener("click", function () {
      if (statisticsModal) { statisticsModal.hidden = false; loadStatistics(); }
    });
  }

  if (statisticsModalClose) {
    statisticsModalClose.addEventListener("click", function () {
      if (statisticsModal) statisticsModal.hidden = true;
    });
  }

  if (statisticsModal) {
    statisticsModal.addEventListener("click", function (e) {
      if (e.target === statisticsModal) statisticsModal.hidden = true;
    });
  }

  function loadStatistics() {
    if (!statisticsModalBody) return;
    statisticsModalBody.innerHTML = '<p>' + escapeHtml(t("statisticsLoading")) + '</p>';

    fetch("/api/statistics")
      .then(function (resp) { return resp.json(); })
      .then(function (stats) { renderStatistics(stats); })
      .catch(function () {
        statisticsModalBody.innerHTML = '<p>' + escapeHtml(t("statNoData")) + '</p>';
      });
  }

  function renderStatistics(stats) {
    if (!statisticsModalBody) return;
    statisticsModalBody.innerHTML = "";

    if (!stats || stats.total_reviews === 0) {
      statisticsModalBody.innerHTML = '<p>' + escapeHtml(t("statNoData")) + '</p>';
      return;
    }

    var html = '';
    html += '<div class="statistics-grid">';
    html += '<div class="statistics-card"><div class="statistics-card-value">' + (stats.total_reviews || 0) + '</div><div class="statistics-card-label">' + escapeHtml(t("statTotalReviews")) + '</div></div>';
    html += '<div class="statistics-card"><div class="statistics-card-value">' + (stats.avg_findings_per_review || 0) + '</div><div class="statistics-card-label">' + escapeHtml(t("statAvgFindings")) + '</div></div>';
    html += '</div>';

    var dist = stats.assessment_distribution || {};
    html += '<h3 class="statistics-section-title">' + escapeHtml(t("statAssessmentDist")) + '</h3>';
    [{ key: "GO", label: "GO", cls: "--GO" }, { key: "CONDITIONAL_GO", label: "CONDITIONAL GO", cls: "--CONDITIONAL_GO" }, { key: "NO_GO", label: "NO GO", cls: "--NO_GO" }].forEach(function (a) {
      html += '<div class="statistics-assessment-row"><span class="statistics-assessment-badge statistics-assessment-badge' + a.cls + '">' + escapeHtml(a.label) + '</span><span class="statistics-assessment-count">' + (dist[a.key] || 0) + '</span></div>';
    });

    var topFindings = stats.most_common_findings || [];
    if (topFindings.length > 0) {
      var maxFindingCount = topFindings[0].count || 1;
      html += '<h3 class="statistics-section-title">' + escapeHtml(t("statTopFindings")) + '</h3>';
      topFindings.forEach(function (f) {
        var pct = Math.round((f.count / maxFindingCount) * 100);
        html += '<div class="statistics-bar-row"><span class="statistics-bar-label" title="' + escapeHtml(f.rule_id) + '">' + escapeHtml(f.rule_id) + '</span><div class="statistics-bar-track"><div class="statistics-bar-fill" style="width:' + pct + '%"></div></div><span class="statistics-bar-count">' + f.count + '</span></div>';
      });
    }

    var artTypes = stats.most_common_artifact_types || [];
    if (artTypes.length > 0) {
      var maxArtCount = artTypes[0].count || 1;
      html += '<h3 class="statistics-section-title">' + escapeHtml(t("statArtifactTypes")) + '</h3>';
      artTypes.forEach(function (a) {
        var pct = Math.round((a.count / maxArtCount) * 100);
        var label = (a.artifact_type || "").replace(/_/g, " ");
        html += '<div class="statistics-bar-row"><span class="statistics-bar-label" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</span><div class="statistics-bar-track"><div class="statistics-bar-fill" style="width:' + pct + '%"></div></div><span class="statistics-bar-count">' + a.count + '</span></div>';
      });
    }

    statisticsModalBody.innerHTML = html;
  }

  // ===========================================================================
  // SECTION: Team Workflows
  // ===========================================================================
  function getReviewerName() {
    var input = document.getElementById("reviewerNameInput");
    return input ? input.value.trim() : "";
  }

  function initReviewerName() {
    var saved = localStorage.getItem("ra-reviewer-name");
    var input = document.getElementById("reviewerNameInput");
    if (input && saved) input.value = saved;
    if (input) {
      input.addEventListener("input", function () {
        localStorage.setItem("ra-reviewer-name", input.value.trim());
      });
    }
  }

  initReviewerName();

  function submitFeedback(reviewId, findingIndex, ruleId, helpful) {
    fetch("/api/review/" + encodeURIComponent(reviewId) + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ finding_index: findingIndex, rule_id: ruleId, helpful: helpful })
    }).catch(function () { /* noop */ });
  }

  function loadFeedbackForReview(reviewId, callback) {
    fetch("/api/review/" + encodeURIComponent(reviewId) + "/feedback")
      .then(function (resp) { return resp.json(); })
      .then(function (feedbacks) {
        (feedbacks || []).forEach(function (fb) {
          feedbackState[reviewId + "-" + fb.finding_index] = fb.helpful;
        });
        if (callback) callback();
      })
      .catch(function () { if (callback) callback(); });
  }

  function setFindingResolution(reviewId, findingIndex, status, comment) {
    if (!reviewId) return;
    fetch("/api/review/" + encodeURIComponent(reviewId) + "/findings/" + findingIndex + "/resolution", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status, reviewer_name: getReviewerName(), comment: comment || "" })
    })
      .then(function (resp) { return resp.json(); })
      .then(function () {
        resolutionState[findingIndex] = status;
        updateCompletionBar(reviewId);
      })
      .catch(function () { /* noop */ });
  }

  function loadResolutions(reviewId, callback) {
    if (!reviewId) { resolutionState = {}; if (callback) callback(); return; }
    fetch("/api/review/" + encodeURIComponent(reviewId) + "/resolutions")
      .then(function (resp) { return resp.json(); })
      .then(function (resolutions) {
        resolutionState = {};
        (resolutions || []).forEach(function (r) { resolutionState[r.finding_index] = r.status; });
        if (callback) callback();
      })
      .catch(function () { resolutionState = {}; if (callback) callback(); });
  }

  function updateCompletionBar(reviewId) {
    if (!reviewId) return;
    fetch("/api/review/" + encodeURIComponent(reviewId) + "/completion")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var fill = document.getElementById("completionBarFill");
        var pctEl = document.getElementById("completionPct");
        if (fill) fill.style.width = (data.completion_pct || 0) + "%";
        if (pctEl) pctEl.textContent = Math.round(data.completion_pct || 0) + "%";
      })
      .catch(function () { /* noop */ });
  }

  function shareReview(reviewId) {
    if (!reviewId) return;
    var url = window.location.origin + "/api/shared/" + encodeURIComponent(reviewId);
    copyToClipboard(url);
    showToast(t("shareUrlCopied"));
  }

  function updateFindingStatusBadge(findingIndex, status) {
    var existing = document.querySelector('[data-resolution-badge="' + findingIndex + '"]');
    if (existing) existing.parentNode.removeChild(existing);

    if (!status || status === "OPEN") return;

    var findingItems = document.querySelectorAll("#cardFindingsBody .finding-item");
    if (findingIndex >= findingItems.length) return;

    var header = findingItems[findingIndex].querySelector(".finding-header");
    if (!header) return;

    var badge = document.createElement("span");
    badge.className = "resolution-status-badge resolution-status-" + status;
    badge.setAttribute("data-resolution-badge", findingIndex);
    badge.textContent = status;

    var expandIcon = header.querySelector(".finding-expand-icon");
    if (expandIcon) {
      header.insertBefore(badge, expandIcon);
    } else {
      header.appendChild(badge);
    }
  }

  function showTeamWorkflowBar(show) {
    var bar = document.getElementById("teamWorkflowBar");
    var shareBtn = document.getElementById("btnShareReview");
    if (bar) bar.hidden = !show;
    if (shareBtn) shareBtn.hidden = !show;
  }

  var btnShareReview = document.getElementById("btnShareReview");
  if (btnShareReview) {
    btnShareReview.addEventListener("click", function () { shareReview(currentReviewId); });
  }

  // ===========================================================================
  // SECTION: Initialization
  // ===========================================================================
  var exampleSelect = document.getElementById("exampleSelect");

  function loadExampleList() {
    fetch("/api/examples")
      .then(function (resp) {
        if (!resp.ok) return [];
        return resp.json();
      })
      .then(function (examples) {
        if (!examples || !examples.length) return;
        var frag = document.createDocumentFragment();
        examples.forEach(function (ex) {
          var opt = document.createElement("option");
          opt.value = ex.case_id;
          var label = currentLang === "de" ? ex.title_de : ex.title;
          opt.textContent = label;
          opt.setAttribute("data-title-de", ex.title_de || "");
          opt.setAttribute("data-title-en", ex.title || "");
          frag.appendChild(opt);
        });
        exampleSelect.appendChild(frag);
      })
      .catch(function () { /* noop */ });
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
          var reviewTypeEl = document.getElementById("reviewType");
          var artifactTypeEl = document.getElementById("artifactType");
          var codeInputEl = document.getElementById("codeInput");
          var reviewContextEl = document.getElementById("reviewContext");

          if (reviewTypeEl && data.review_type) reviewTypeEl.value = data.review_type;
          if (artifactTypeEl && data.artifact_type) artifactTypeEl.value = data.artifact_type;
          if (codeInputEl && data.code) codeInputEl.value = data.code;
          if (reviewContextEl && data.review_context) reviewContextEl.value = data.review_context;
        })
        .catch(function () { /* noop */ });
    });
  }

})();
