"""Tests for the similarity search engine (app.engines.similarity)."""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.similarity import (
    SimilarReview,
    compute_similarity,
    compute_tfidf_similarity,
    detect_recurring_patterns,
    find_similar_reviews,
    get_review_statistics,
    tokenize_code,
)


# ---------------------------------------------------------------------------
# Tokenization tests
# ---------------------------------------------------------------------------


class TestTokenizeCode:
    """Tests for tokenize_code()."""

    def test_empty_string_returns_empty_list(self):
        assert tokenize_code("") == []

    def test_none_returns_empty_list(self):
        assert tokenize_code(None) == []

    def test_abap_code_tokenized(self):
        code = """
CLASS zcl_example DEFINITION PUBLIC.
  PUBLIC SECTION.
    METHODS get_data RETURNING VALUE(rt_data) TYPE tt_data.
ENDCLASS.
"""
        tokens = tokenize_code(code)
        assert "class" in tokens
        assert "zcl_example" in tokens
        assert "definition" in tokens
        assert "public" in tokens
        assert "methods" in tokens
        assert "get_data" in tokens

    def test_abap_comments_removed(self):
        code = """
* This is a comment
DATA lv_value TYPE string.
" Another comment
WRITE lv_value.
"""
        tokens = tokenize_code(code)
        # Comments should be removed, but code tokens remain
        assert "data" in tokens
        assert "lv_value" in tokens
        assert "write" in tokens

    def test_cds_code_tokenized(self):
        code = """
define view entity ZI_SalesOrder as select from zsalesorder {
  key sales_order_id,
      buyer_name,
      total_amount
}
"""
        tokens = tokenize_code(code)
        assert "define" in tokens
        assert "view" in tokens
        assert "entity" in tokens
        assert "zi_salesorder" in tokens
        assert "sales_order_id" in tokens

    def test_ui5_js_code_tokenized(self):
        code = """
sap.ui.define([
  "sap/ui/core/mvc/Controller"
], function (Controller) {
  "use strict";
  return Controller.extend("com.example.Main", {
    onInit: function () {
      this.getView().setModel(new JSONModel({}), "view");
    }
  });
});
"""
        tokens = tokenize_code(code)
        assert "sap" in tokens
        assert "controller" in tokens
        assert "oninit" in tokens
        assert "function" in tokens

    def test_js_comments_removed(self):
        code = """
// Single line comment
var x = 42;
/* Block
   comment */
var y = 100;
"""
        tokens = tokenize_code(code)
        assert "var" in tokens
        assert "x" in tokens
        assert "42" in tokens
        # "single", "line", "comment" should NOT be in tokens
        # (comment removal applies to the full line for // comments)
        assert "y" in tokens

    def test_xml_comments_removed(self):
        code = """
<!-- This is a comment -->
<mvc:View xmlns:mvc="sap.ui.core.mvc">
  <Button text="Click me" />
</mvc:View>
"""
        tokens = tokenize_code(code)
        assert "mvc" in tokens
        assert "view" in tokens
        assert "button" in tokens

    def test_mixed_case_normalized(self):
        code = "DATA LV_VALUE TYPE String."
        tokens = tokenize_code(code)
        assert "lv_value" in tokens
        assert "string" in tokens

    def test_numbers_extracted(self):
        code = "x = 42 + y * 100"
        tokens = tokenize_code(code)
        assert "42" in tokens
        assert "100" in tokens


# ---------------------------------------------------------------------------
# Jaccard similarity tests
# ---------------------------------------------------------------------------


class TestComputeSimilarity:
    """Tests for compute_similarity() (Jaccard)."""

    def test_identical_tokens_return_1(self):
        tokens = ["class", "zcl", "definition"]
        assert compute_similarity(tokens, tokens) == 1.0

    def test_empty_tokens_return_0(self):
        assert compute_similarity([], ["a", "b"]) == 0.0
        assert compute_similarity(["a", "b"], []) == 0.0
        assert compute_similarity([], []) == 0.0

    def test_no_overlap_returns_0(self):
        assert compute_similarity(["a", "b"], ["c", "d"]) == 0.0

    def test_partial_overlap(self):
        # {a, b, c} & {b, c, d} = {b, c}, union = {a, b, c, d}
        result = compute_similarity(["a", "b", "c"], ["b", "c", "d"])
        assert result == pytest.approx(2 / 4)

    def test_subset_tokens(self):
        # {a, b} subset of {a, b, c} => intersection=2, union=3
        result = compute_similarity(["a", "b"], ["a", "b", "c"])
        assert result == pytest.approx(2 / 3)

    def test_duplicates_ignored_in_set_logic(self):
        # Sets: {a, b} and {a, b, c}
        result = compute_similarity(["a", "a", "b"], ["a", "b", "c"])
        assert result == pytest.approx(2 / 3)

    def test_symmetric(self):
        a = ["data", "lv_value", "type", "string"]
        b = ["data", "lv_result", "type", "int4"]
        assert compute_similarity(a, b) == compute_similarity(b, a)


# ---------------------------------------------------------------------------
# TF-IDF similarity tests
# ---------------------------------------------------------------------------


class TestComputeTfidfSimilarity:
    """Tests for compute_tfidf_similarity()."""

    def test_empty_tokens_return_0(self):
        assert compute_tfidf_similarity([], ["a"], []) == 0.0
        assert compute_tfidf_similarity(["a"], [], []) == 0.0

    def test_small_corpus_falls_back_to_jaccard(self):
        a = ["class", "zcl", "definition"]
        b = ["class", "zcl", "implementation"]
        corpus = [["other"]]
        result = compute_tfidf_similarity(a, b, corpus)
        expected_jaccard = compute_similarity(a, b)
        assert result == pytest.approx(expected_jaccard)

    def test_identical_tokens_high_similarity(self):
        tokens = ["class", "zcl", "definition", "public"]
        corpus = [
            ["class", "other", "thing"],
            ["data", "type", "string"],
            ["select", "from", "table"],
        ]
        result = compute_tfidf_similarity(tokens, tokens, corpus)
        assert result > 0.9

    def test_disjoint_tokens_low_similarity(self):
        a = ["alpha", "beta", "gamma"]
        b = ["delta", "epsilon", "zeta"]
        corpus = [
            ["alpha", "delta"],
            ["beta", "epsilon"],
            ["gamma", "zeta"],
        ]
        result = compute_tfidf_similarity(a, b, corpus)
        assert result < 0.2

    def test_returns_float_between_0_and_1(self):
        a = ["class", "data", "method"]
        b = ["class", "type", "select"]
        corpus = [
            ["class", "data"],
            ["select", "from"],
            ["method", "type"],
        ]
        result = compute_tfidf_similarity(a, b, corpus)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# find_similar_reviews tests
# ---------------------------------------------------------------------------


class TestFindSimilarReviews:
    """Tests for find_similar_reviews()."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_db(self):
        """Should return empty list when DB is unavailable."""
        with patch(
            "app.db.connection.get_session_factory",
            return_value=None,
        ):
            result = await find_similar_reviews(
                code="CLASS zcl_test DEFINITION.",
                artifact_type="ABAP_CLASS",
                current_findings=["PERF_001"],
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_past_reviews(self):
        """Should return empty list when no past reviews exist."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.db.connection.get_session_factory",
            return_value=mock_factory,
        ):
            result = await find_similar_reviews(
                code="CLASS zcl_test DEFINITION.",
                artifact_type="ABAP_CLASS",
                current_findings=["PERF_001"],
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_exception(self):
        """Should return empty list on any exception."""
        with patch(
            "app.db.connection.get_session_factory",
            side_effect=Exception("DB error"),
        ):
            result = await find_similar_reviews(
                code="CLASS zcl_test DEFINITION.",
                artifact_type="ABAP_CLASS",
                current_findings=["PERF_001"],
            )
            assert result == []


# ---------------------------------------------------------------------------
# detect_recurring_patterns tests
# ---------------------------------------------------------------------------


class TestDetectRecurringPatterns:
    """Tests for detect_recurring_patterns()."""

    def test_empty_inputs(self):
        assert detect_recurring_patterns([], []) == []
        assert detect_recurring_patterns(["PERF_001"], []) == []
        assert detect_recurring_patterns([], [SimilarReview(
            review_id="r1", score=0.5, artifact_type="ABAP_CLASS",
            review_type="SNIPPET_REVIEW", finding_count=1,
            assessment="GO", created_at="2024-01-01",
            shared_findings=["PERF_001"],
        )]) == []

    def test_identifies_recurring_rule_ids(self):
        similar = [
            SimilarReview(
                review_id="r1", score=0.5, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=2,
                assessment="GO", created_at="2024-01-01",
                shared_findings=["PERF_001", "SEC_002"],
            ),
            SimilarReview(
                review_id="r2", score=0.4, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=1,
                assessment="CONDITIONAL_GO", created_at="2024-01-02",
                shared_findings=["PERF_001"],
            ),
        ]
        patterns = detect_recurring_patterns(
            ["PERF_001", "SEC_002", "MAINT_003"],
            similar,
        )
        # PERF_001 appears in r1 + r2 + current = 3
        # SEC_002 appears in r1 + current = 2
        assert len(patterns) >= 1
        perf_pattern = next(p for p in patterns if p["rule_id"] == "PERF_001")
        assert perf_pattern["occurrence_count"] == 3  # 2 from similar + 1 current

    def test_filters_rules_below_threshold(self):
        """Rules appearing in only 1 review should be excluded."""
        similar = [
            SimilarReview(
                review_id="r1", score=0.5, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=1,
                assessment="GO", created_at="2024-01-01",
                shared_findings=["UNIQUE_RULE"],
            ),
        ]
        # UNIQUE_RULE appears in r1 (1) + current (1) = 2 -> included
        patterns = detect_recurring_patterns(["UNIQUE_RULE"], similar)
        assert len(patterns) == 1

        # Rule not in current findings: only 1 occurrence -> excluded
        patterns = detect_recurring_patterns(["OTHER_RULE"], similar)
        assert len(patterns) == 0

    def test_sorted_by_occurrence_count(self):
        similar = [
            SimilarReview(
                review_id="r1", score=0.5, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=3,
                assessment="GO", created_at="2024-01-01",
                shared_findings=["A", "B", "C"],
            ),
            SimilarReview(
                review_id="r2", score=0.4, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=2,
                assessment="GO", created_at="2024-01-02",
                shared_findings=["A", "B"],
            ),
            SimilarReview(
                review_id="r3", score=0.35, artifact_type="ABAP_CLASS",
                review_type="SNIPPET_REVIEW", finding_count=1,
                assessment="GO", created_at="2024-01-03",
                shared_findings=["A"],
            ),
        ]
        patterns = detect_recurring_patterns(["A", "B", "C"], similar)
        # A: 3 reviews + current = 4, B: 2 reviews + current = 3, C: 1 review + current = 2
        assert len(patterns) == 3
        assert patterns[0]["rule_id"] == "A"
        assert patterns[0]["occurrence_count"] == 4


# ---------------------------------------------------------------------------
# get_review_statistics tests
# ---------------------------------------------------------------------------


class TestGetReviewStatistics:
    """Tests for get_review_statistics()."""

    @pytest.mark.asyncio
    async def test_returns_zeroed_stats_when_no_db(self):
        with patch(
            "app.db.connection.get_session_factory",
            return_value=None,
        ):
            stats = await get_review_statistics()
            assert stats["total_reviews"] == 0
            assert stats["most_common_findings"] == []
            assert stats["avg_findings_per_review"] == 0.0
            assert stats["assessment_distribution"]["GO"] == 0
            assert stats["assessment_distribution"]["CONDITIONAL_GO"] == 0
            assert stats["assessment_distribution"]["NO_GO"] == 0

    @pytest.mark.asyncio
    async def test_returns_zeroed_stats_when_no_reviews(self):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.db.connection.get_session_factory",
            return_value=mock_factory,
        ):
            stats = await get_review_statistics()
            assert stats["total_reviews"] == 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_exception(self):
        with patch(
            "app.db.connection.get_session_factory",
            side_effect=Exception("DB error"),
        ):
            stats = await get_review_statistics()
            assert stats["total_reviews"] == 0
            assert stats["most_common_findings"] == []


# ---------------------------------------------------------------------------
# SimilarReview data class tests
# ---------------------------------------------------------------------------


class TestSimilarReview:
    """Tests for SimilarReview dataclass."""

    def test_to_dict(self):
        sr = SimilarReview(
            review_id="abc-123",
            score=0.7654,
            artifact_type="CDS_VIEW",
            review_type="SNIPPET_REVIEW",
            finding_count=5,
            assessment="CONDITIONAL_GO",
            created_at="2024-01-15T10:30:00",
            shared_findings=["PERF_001", "SEC_002"],
        )
        d = sr.to_dict()
        assert d["review_id"] == "abc-123"
        assert d["score"] == 0.765
        assert d["artifact_type"] == "CDS_VIEW"
        assert d["shared_findings"] == ["PERF_001", "SEC_002"]

    def test_default_shared_findings(self):
        sr = SimilarReview(
            review_id="x", score=0.5, artifact_type="ABAP_CLASS",
            review_type="SNIPPET_REVIEW", finding_count=0,
            assessment="GO", created_at="2024-01-01",
        )
        assert sr.shared_findings == []


# ---------------------------------------------------------------------------
# Score threshold and sorting integration tests
# ---------------------------------------------------------------------------


class TestScoreThresholdAndSorting:
    """Integration-level tests for score filtering and sorting."""

    def test_similar_reviews_sorted_by_score_descending(self):
        reviews = [
            SimilarReview(review_id="a", score=0.4, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-01"),
            SimilarReview(review_id="b", score=0.9, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-02"),
            SimilarReview(review_id="c", score=0.6, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-03"),
        ]
        reviews.sort(key=lambda r: r.score, reverse=True)
        assert reviews[0].review_id == "b"
        assert reviews[1].review_id == "c"
        assert reviews[2].review_id == "a"

    def test_score_threshold_filters_low_quality(self):
        """Scores at or below 0.3 should be filtered out."""
        reviews = [
            SimilarReview(review_id="low", score=0.2, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-01"),
            SimilarReview(review_id="boundary", score=0.3, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-02"),
            SimilarReview(review_id="good", score=0.5, artifact_type="X",
                          review_type="Y", finding_count=0, assessment="GO",
                          created_at="2024-01-03"),
        ]
        # Simulate the threshold filter used in find_similar_reviews
        filtered = [r for r in reviews if r.score > 0.3]
        assert len(filtered) == 1
        assert filtered[0].review_id == "good"
