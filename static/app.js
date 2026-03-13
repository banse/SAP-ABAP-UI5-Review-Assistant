/* ============================================================
   SAP ABAP/UI5 Review Assistant — Application Logic
   ============================================================ */

(function () {
  "use strict";

  // ---- Translations ----
  var TRANSLATIONS = {
    de: {
      codeInput: "Code / Artefakt",
      codeInputPlaceholder: "ABAP-Code, CDS-View, UI5-XML-View oder Controller hier einf\u00fcgen...",
      objectType: "Objekttyp",
      autoDetect: "Automatisch erkennen",
      reviewCategories: "Review-Kategorien",
      bestPractices: "Best Practices",
      performance: "Performance",
      security: "Security",
      naming: "Namenskonventionen",
      cleanCore: "Clean Core",
      runReview: "Review starten",
      startReview: "Review starten",
      startReviewDesc: "F\u00fcgen Sie ABAP-Code, eine CDS-View oder ein UI5-Artefakt ein und klicken Sie auf \u00abReview starten\u00bb, um strukturierte Pr\u00fcfergebnisse zu erhalten.",
      reviewError: "Fehler beim Review",
      close: "Schlie\u00dfen",
      themeToggleTitle: "Farbschema wechseln",
      unknownError: "Unbekannter Fehler beim Review.",
    },
    en: {
      codeInput: "Code / Artifact",
      codeInputPlaceholder: "Paste ABAP code, CDS view, UI5 XML view or controller here...",
      objectType: "Object Type",
      autoDetect: "Auto-detect",
      reviewCategories: "Review Categories",
      bestPractices: "Best Practices",
      performance: "Performance",
      security: "Security",
      naming: "Naming Conventions",
      cleanCore: "Clean Core",
      runReview: "Run Review",
      startReview: "Start Review",
      startReviewDesc: "Paste ABAP code, a CDS view, or a UI5 artifact and click \u00abRun Review\u00bb to receive structured review findings.",
      reviewError: "Review Error",
      close: "Close",
      themeToggleTitle: "Toggle color scheme",
      unknownError: "Unknown error during review.",
    },
  };

  var currentLang = "de";

  // ---- DOM References ----
  var form = document.getElementById("reviewForm");
  var submitBtn = document.getElementById("submitBtn");
  var placeholder = document.getElementById("placeholder");
  var errorState = document.getElementById("errorState");
  var errorMessage = document.getElementById("errorMessage");
  var resultsContainer = document.getElementById("resultsContainer");
  var themeToggle = document.getElementById("themeToggle");
  var langToggle = document.getElementById("langToggle");

  // ---- Theme Toggle ----
  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("theme", theme);
  }

  function initTheme() {
    var saved = localStorage.getItem("theme");
    if (saved) {
      applyTheme(saved);
    }
  }

  themeToggle.addEventListener("click", function () {
    var current = document.documentElement.getAttribute("data-theme");
    var isDark =
      current === "dark" ||
      (!current && window.matchMedia("(prefers-color-scheme: dark)").matches);
    applyTheme(isDark ? "light" : "dark");
  });

  initTheme();

  // ---- Language Toggle ----
  function applyLanguage(lang) {
    currentLang = lang;
    langToggle.textContent = lang.toUpperCase();
    document.documentElement.setAttribute("lang", lang);

    var t = TRANSLATIONS[lang] || TRANSLATIONS.de;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (t[key]) el.textContent = t[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (t[key]) el.placeholder = t[key];
    });
    document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-title");
      if (t[key]) el.title = t[key];
    });

    localStorage.setItem("lang", lang);
  }

  function initLanguage() {
    var saved = localStorage.getItem("lang");
    if (saved) {
      applyLanguage(saved);
    }
  }

  langToggle.addEventListener("click", function () {
    applyLanguage(currentLang === "de" ? "en" : "de");
  });

  initLanguage();

  // ---- Form Submit ----
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    var code = document.getElementById("codeInput").value.trim();
    if (!code) return;

    var objectType = document.getElementById("objectType").value;
    var categories = [];
    document.querySelectorAll('input[name="categories"]:checked').forEach(function (cb) {
      categories.push(cb.value);
    });

    var payload = {
      code: code,
      object_type: objectType,
      categories: categories,
    };

    // UI: loading state
    submitBtn.classList.add("is-loading");
    submitBtn.disabled = true;
    placeholder.hidden = true;
    errorState.hidden = true;
    resultsContainer.hidden = true;

    fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        renderResults(data);
      })
      .catch(function (err) {
        var t = TRANSLATIONS[currentLang] || TRANSLATIONS.de;
        errorMessage.textContent = err.message || t.unknownError;
        errorState.hidden = false;
      })
      .finally(function () {
        submitBtn.classList.remove("is-loading");
        submitBtn.disabled = false;
      });
  });

  // ---- Render Results (placeholder) ----
  function renderResults(data) {
    resultsContainer.innerHTML = "";

    if (data.findings && data.findings.length > 0) {
      data.findings.forEach(function (finding) {
        var block = document.createElement("article");
        block.className = "result-block";

        var severity = finding.severity || "info";
        var item = document.createElement("div");
        item.className = "finding-item finding-item--" + severity;

        var title = document.createElement("div");
        title.className = "finding-title";
        title.textContent = finding.title || finding.rule || "Finding";

        var desc = document.createElement("div");
        desc.className = "finding-description";
        desc.textContent = finding.description || finding.message || "";

        item.appendChild(title);
        item.appendChild(desc);

        if (finding.rule) {
          var rule = document.createElement("div");
          rule.className = "finding-rule";
          rule.textContent = finding.rule;
          item.appendChild(rule);
        }

        block.appendChild(item);
        resultsContainer.appendChild(block);
      });
    } else {
      var block = document.createElement("article");
      block.className = "result-block";
      var inner = document.createElement("div");
      inner.className = "finding-item finding-item--ok";
      var title = document.createElement("div");
      title.className = "finding-title";
      title.textContent = data.message || "Review complete — no findings.";
      inner.appendChild(title);
      block.appendChild(inner);
      resultsContainer.appendChild(block);
    }

    resultsContainer.hidden = false;
  }
})();
