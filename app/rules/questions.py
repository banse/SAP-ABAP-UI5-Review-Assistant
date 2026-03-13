"""Question rules for the missing-information engine.

Each ``QuestionRule`` is a frozen dataclass that defines a contextual
question the review assistant may ask when information is missing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionRule:
    """A rule that triggers a contextual question during review."""

    question_id: str
    question: str
    question_de: str
    why_it_matters: str
    why_it_matters_de: str
    default_assumption: str | None = None
    default_assumption_de: str | None = None
    trigger_condition: str = "always"
    # "always", "no_tech_context", "performance_finding",
    # "no_auth", "test_gaps", "snippet_review",
    # "cds_artifact", "unclear_finding", "ticket_review"
    category: str = "context"


# ---------------------------------------------------------------------------
# Pre-defined question rules
# ---------------------------------------------------------------------------

Q_SAP_RELEASE = QuestionRule(
    question_id="Q-CTX-001",
    question="What SAP release is this code targeting? (e.g. S/4HANA 2023 FPS01)",
    question_de="Welches SAP-Release ist Zielplattform? (z. B. S/4HANA 2023 FPS01)",
    why_it_matters=(
        "The available APIs, syntax features, and clean-core rules depend on the "
        "target SAP release."
    ),
    why_it_matters_de=(
        "Die verfuegbaren APIs, Syntaxfeatures und Clean-Core-Regeln haengen vom "
        "Ziel-SAP-Release ab."
    ),
    default_assumption="S/4HANA 2023 or later",
    default_assumption_de="S/4HANA 2023 oder neuer",
    trigger_condition="no_tech_context",
    category="context",
)

Q_DATA_VOLUME = QuestionRule(
    question_id="Q-PERF-001",
    question="What is the expected data volume for this scenario? (rows/records)",
    question_de="Welches Datenvolumen wird fuer dieses Szenario erwartet? (Zeilen/Datensaetze)",
    why_it_matters=(
        "Performance recommendations differ significantly between small data sets "
        "and high-volume scenarios."
    ),
    why_it_matters_de=(
        "Performance-Empfehlungen unterscheiden sich erheblich zwischen kleinen "
        "Datenmengen und Hochvolumen-Szenarien."
    ),
    default_assumption="Medium volume (10k-100k records)",
    default_assumption_de="Mittleres Volumen (10k-100k Datensaetze)",
    trigger_condition="performance_finding",
    category="performance",
)

Q_AUTH_RELEVANCE = QuestionRule(
    question_id="Q-SEC-001",
    question="Is authorization checking relevant for this scenario?",
    question_de="Ist eine Berechtigungspruefung fuer dieses Szenario relevant?",
    why_it_matters=(
        "Missing authorization checks can lead to data exposure in "
        "multi-tenant or role-based environments."
    ),
    why_it_matters_de=(
        "Fehlende Berechtigungspruefungen koennen in mandantenfaehigen oder "
        "rollenbasierten Umgebungen zu Datenlecks fuehren."
    ),
    default_assumption="Authorization is relevant",
    default_assumption_de="Berechtigung ist relevant",
    trigger_condition="no_auth",
    category="security",
)

Q_EXISTING_TESTS = QuestionRule(
    question_id="Q-TEST-001",
    question="Are there existing unit or integration tests for this code?",
    question_de="Gibt es bereits Unit- oder Integrationstests fuer diesen Code?",
    why_it_matters=(
        "Existing test coverage changes the priority of test gap findings."
    ),
    why_it_matters_de=(
        "Bestehende Testabdeckung aendert die Prioritaet von Testluecken-Findings."
    ),
    trigger_condition="test_gaps",
    category="testing",
)

Q_CHANGE_PACKAGE = QuestionRule(
    question_id="Q-CTX-002",
    question="Is this code part of a larger change package or standalone?",
    question_de="Ist dieser Code Teil eines groesseren Aenderungspakets oder eigenstaendig?",
    why_it_matters=(
        "Snippets that are part of a larger change may have dependencies "
        "that affect the review assessment."
    ),
    why_it_matters_de=(
        "Snippets, die Teil einer groesseren Aenderung sind, koennen Abhaengigkeiten "
        "haben, die die Bewertung beeinflussen."
    ),
    trigger_condition="snippet_review",
    category="context",
)

Q_SERVICE_BINDING = QuestionRule(
    question_id="Q-CDS-001",
    question="Which service binding exposes this CDS view?",
    question_de="Welches Service Binding exponiert diese CDS-View?",
    why_it_matters=(
        "The service binding determines the OData version and available "
        "protocol features for consumers."
    ),
    why_it_matters_de=(
        "Das Service Binding bestimmt die OData-Version und verfuegbare "
        "Protokollfunktionen fuer Konsumenten."
    ),
    trigger_condition="cds_artifact",
    category="architecture",
)

Q_TICKET_REFERENCE = QuestionRule(
    question_id="Q-TKT-001",
    question="What is the ticket or requirement reference for this change?",
    question_de="Was ist die Ticket- oder Anforderungsreferenz fuer diese Aenderung?",
    why_it_matters=(
        "Linking code changes to requirements ensures traceability "
        "and supports impact analysis."
    ),
    why_it_matters_de=(
        "Die Verknuepfung von Codeaenderungen mit Anforderungen sichert "
        "Nachvollziehbarkeit und unterstuetzt die Impaktanalyse."
    ),
    trigger_condition="ticket_review",
    category="process",
)

Q_ODATA_VERSION = QuestionRule(
    question_id="Q-CTX-003",
    question="Which OData version is used? (V2 or V4)",
    question_de="Welche OData-Version wird verwendet? (V2 oder V4)",
    why_it_matters=(
        "OData V2 and V4 have different annotation models, binding syntax, "
        "and supported features."
    ),
    why_it_matters_de=(
        "OData V2 und V4 haben unterschiedliche Annotationsmodelle, "
        "Binding-Syntax und unterstuetzte Features."
    ),
    default_assumption="OData V4",
    default_assumption_de="OData V4",
    trigger_condition="no_tech_context",
    category="context",
)

Q_UI5_VERSION = QuestionRule(
    question_id="Q-UI5-001",
    question="Which SAPUI5 version is targeted?",
    question_de="Welche SAPUI5-Version ist Zielversion?",
    why_it_matters=(
        "Deprecated APIs and available controls differ across UI5 versions."
    ),
    why_it_matters_de=(
        "Veraltete APIs und verfuegbare Controls unterscheiden sich je nach UI5-Version."
    ),
    default_assumption="Latest SAPUI5 LTS",
    default_assumption_de="Neueste SAPUI5-LTS-Version",
    trigger_condition="no_tech_context",
    category="context",
)

Q_UNCLEAR_SEVERITY = QuestionRule(
    question_id="Q-CLR-001",
    question=(
        "Some findings could not be classified with certainty. "
        "Can you provide more context about the business requirements?"
    ),
    question_de=(
        "Einige Findings konnten nicht sicher klassifiziert werden. "
        "Koennen Sie mehr Kontext zu den fachlichen Anforderungen geben?"
    ),
    why_it_matters=(
        "Unclear findings may hide critical issues or be false positives. "
        "Additional context resolves ambiguity."
    ),
    why_it_matters_de=(
        "Unklare Findings koennen kritische Probleme verbergen oder "
        "Fehlalarme sein. Zusaetzlicher Kontext loest Mehrdeutigkeiten."
    ),
    trigger_condition="unclear_finding",
    category="context",
)

Q_DEPLOYMENT_TARGET = QuestionRule(
    question_id="Q-CTX-004",
    question="Where will this be deployed? (On-premise, BTP, hybrid)",
    question_de="Wo wird dies deployed? (On-Premise, BTP, hybrid)",
    why_it_matters=(
        "Deployment target affects available APIs, runtime constraints, "
        "and clean-core requirements."
    ),
    why_it_matters_de=(
        "Das Deployment-Ziel beeinflusst verfuegbare APIs, Laufzeit-"
        "einschraenkungen und Clean-Core-Anforderungen."
    ),
    default_assumption="On-premise S/4HANA",
    default_assumption_de="On-Premise S/4HANA",
    trigger_condition="no_tech_context",
    category="context",
)

Q_FIORI_ELEMENTS = QuestionRule(
    question_id="Q-UI5-002",
    question="Is this a Fiori Elements app or freestyle SAPUI5?",
    question_de="Ist dies eine Fiori-Elements-App oder Freestyle-SAPUI5?",
    why_it_matters=(
        "Fiori Elements apps rely heavily on annotations and have different "
        "extension patterns than freestyle UI5."
    ),
    why_it_matters_de=(
        "Fiori-Elements-Apps basieren stark auf Annotationen und haben andere "
        "Erweiterungsmuster als Freestyle-UI5."
    ),
    trigger_condition="no_tech_context",
    category="context",
)

# ---------------------------------------------------------------------------
# Registry — all question rules
# ---------------------------------------------------------------------------

ALL_QUESTION_RULES: tuple[QuestionRule, ...] = (
    Q_SAP_RELEASE,
    Q_DATA_VOLUME,
    Q_AUTH_RELEVANCE,
    Q_EXISTING_TESTS,
    Q_CHANGE_PACKAGE,
    Q_SERVICE_BINDING,
    Q_TICKET_REFERENCE,
    Q_ODATA_VERSION,
    Q_UI5_VERSION,
    Q_UNCLEAR_SEVERITY,
    Q_DEPLOYMENT_TARGET,
    Q_FIORI_ELEMENTS,
)
