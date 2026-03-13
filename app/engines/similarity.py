"""Similarity search engine for past reviews.

Uses simple token-based matching (no external ML/NLP dependencies).
Computes Jaccard and TF-IDF cosine similarity on tokenized code,
then combines with artifact-type and finding-overlap signals.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SimilarReview:
    """A past review that is similar to the current one."""

    review_id: str
    score: float  # 0.0 to 1.0
    artifact_type: str
    review_type: str
    finding_count: int
    assessment: str
    created_at: str
    shared_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "review_id": self.review_id,
            "score": round(self.score, 3),
            "artifact_type": self.artifact_type,
            "review_type": self.review_type,
            "finding_count": self.finding_count,
            "assessment": self.assessment,
            "created_at": self.created_at,
            "shared_findings": self.shared_findings,
        }


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

# Patterns for comment removal by language family
_ABAP_COMMENT = re.compile(r'^\s*[*"].*$', re.MULTILINE)
_C_LINE_COMMENT = re.compile(r'//.*$', re.MULTILINE)
_C_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
_XML_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)

# Token extraction: identifiers, keywords, operators
_TOKEN_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+')


def tokenize_code(code: str) -> list[str]:
    """Tokenize code into meaningful tokens for comparison.

    Removes comments, normalizes whitespace, extracts identifiers and numbers.
    Works across ABAP, CDS, UI5/JS, and XML artifact types.
    """
    if not code:
        return []

    # Remove comments (try all patterns, they are safe to apply broadly)
    text = _ABAP_COMMENT.sub("", code)
    text = _C_BLOCK_COMMENT.sub("", text)
    text = _C_LINE_COMMENT.sub("", text)
    text = _XML_COMMENT.sub("", text)

    # Normalize whitespace
    text = text.lower()

    # Extract tokens
    tokens = _TOKEN_PATTERN.findall(text)

    return tokens


# ---------------------------------------------------------------------------
# Similarity computation
# ---------------------------------------------------------------------------


def compute_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Compute Jaccard similarity between two token sets.

    Returns 0.0 to 1.0.
    """
    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0

    return intersection / union


def compute_tfidf_similarity(
    tokens_a: list[str],
    tokens_b: list[str],
    corpus_tokens: list[list[str]],
) -> float:
    """Compute cosine similarity using TF-IDF vectors.

    Falls back to Jaccard if corpus is too small (< 3 documents).
    """
    if not tokens_a or not tokens_b:
        return 0.0

    if len(corpus_tokens) < 3:
        return compute_similarity(tokens_a, tokens_b)

    # Build document frequency from corpus
    doc_count = len(corpus_tokens)
    df: Counter[str] = Counter()
    for doc_tokens in corpus_tokens:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            df[token] += 1

    # Also count df for the two target documents
    for token in set(tokens_a):
        if token not in df:
            df[token] += 1
    for token in set(tokens_b):
        if token not in df:
            df[token] += 1

    total_docs = doc_count + 2  # include the two target docs

    # Build TF-IDF vectors
    def tfidf_vector(tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1
        vec: dict[str, float] = {}
        for term, count in tf.items():
            normalized_tf = count / max_tf
            idf = math.log((total_docs + 1) / (df.get(term, 0) + 1))
            vec[term] = normalized_tf * idf
        return vec

    vec_a = tfidf_vector(tokens_a)
    vec_b = tfidf_vector(tokens_b)

    # Cosine similarity
    all_terms = set(vec_a.keys()) | set(vec_b.keys())

    dot_product = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in all_terms)
    magnitude_a = math.sqrt(sum(v * v for v in vec_a.values()))
    magnitude_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


# ---------------------------------------------------------------------------
# Past review search
# ---------------------------------------------------------------------------


def _extract_rule_ids_from_response(full_response: dict) -> list[str]:
    """Extract rule_ids from a stored review response."""
    findings = full_response.get("findings") or []
    rule_ids = []
    for f in findings:
        rid = f.get("rule_id")
        if rid:
            rule_ids.append(rid)
    return rule_ids


async def find_similar_reviews(
    code: str,
    artifact_type: str,
    current_findings: list[str],
    limit: int = 3,
) -> list[SimilarReview]:
    """Find similar past reviews from the database.

    Scoring:
    1. Same artifact_type gets a boost (+0.2)
    2. Code token similarity (Jaccard on tokenized code snippets)
    3. Finding overlap (shared rule_ids boost relevance)
    4. Reviews with positive feedback ranked higher

    Returns top ``limit`` similar reviews with score > 0.3.
    """
    try:
        from app.db.connection import get_session_factory
        from app.db.models import ReviewHistoryRecord

        session_factory = get_session_factory()
        if session_factory is None:
            return []

        from sqlalchemy import select

        async with session_factory() as session:
            stmt = select(ReviewHistoryRecord).order_by(
                ReviewHistoryRecord.created_at.desc()
            ).limit(200)
            rows = (await session.execute(stmt)).scalars().all()

            if not rows:
                return []

            current_tokens = tokenize_code(code)
            if not current_tokens:
                return []

            current_findings_set = set(current_findings)

            # Collect corpus tokens for TF-IDF
            corpus_tokens: list[list[str]] = []
            row_tokens: list[tuple[object, list[str]]] = []
            for row in rows:
                snippet = row.code_snippet or ""
                tokens = tokenize_code(snippet)
                corpus_tokens.append(tokens)
                row_tokens.append((row, tokens))

            results: list[SimilarReview] = []

            for row, tokens in row_tokens:
                if not tokens:
                    continue

                # Code similarity
                if len(corpus_tokens) >= 3:
                    code_sim = compute_tfidf_similarity(
                        current_tokens, tokens, corpus_tokens
                    )
                else:
                    code_sim = compute_similarity(current_tokens, tokens)

                # Artifact type boost
                artifact_boost = 0.2 if row.artifact_type == artifact_type else 0.0

                # Finding overlap
                past_rule_ids = _extract_rule_ids_from_response(
                    row.full_response or {}
                )
                past_rule_ids_set = set(past_rule_ids)
                shared = current_findings_set & past_rule_ids_set
                finding_overlap = 0.0
                if current_findings_set and past_rule_ids_set:
                    overlap_ratio = len(shared) / max(
                        len(current_findings_set), len(past_rule_ids_set)
                    )
                    finding_overlap = overlap_ratio * 0.3  # up to 0.3 boost

                # Combined score (weighted)
                score = (code_sim * 0.5) + artifact_boost + finding_overlap
                score = min(score, 1.0)

                if score > 0.3:
                    results.append(
                        SimilarReview(
                            review_id=str(row.id),
                            score=score,
                            artifact_type=row.artifact_type,
                            review_type=row.review_type,
                            finding_count=row.finding_count,
                            assessment=row.overall_assessment,
                            created_at=row.created_at.isoformat(),
                            shared_findings=sorted(shared),
                        )
                    )

            # Sort by score descending
            results.sort(key=lambda r: r.score, reverse=True)

            return results[:limit]

    except Exception:
        logger.warning("Similarity search failed", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Recurring pattern detection
# ---------------------------------------------------------------------------


def detect_recurring_patterns(
    current_rule_ids: list[str],
    similar_reviews: list[SimilarReview],
) -> list[dict]:
    """Identify findings that recur across multiple reviews.

    Returns list of ``{rule_id, occurrence_count, reviews}``
    for rules appearing in 2+ reviews (including current).
    """
    if not current_rule_ids or not similar_reviews:
        return []

    # Count occurrences of each rule_id across similar reviews
    rule_counts: Counter[str] = Counter()
    rule_reviews: dict[str, list[str]] = {}

    for sr in similar_reviews:
        for rid in sr.shared_findings:
            rule_counts[rid] += 1
            if rid not in rule_reviews:
                rule_reviews[rid] = []
            rule_reviews[rid].append(sr.review_id)

    # Include current review in count
    current_set = set(current_rule_ids)
    for rid in rule_counts:
        if rid in current_set:
            rule_counts[rid] += 1  # +1 for current review

    # Filter to rules appearing in 2+ reviews
    results = []
    for rid, count in rule_counts.most_common():
        if count >= 2:
            results.append(
                {
                    "rule_id": rid,
                    "occurrence_count": count,
                    "reviews": rule_reviews.get(rid, []),
                }
            )

    return results


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------


async def get_review_statistics() -> dict:
    """Aggregate statistics across all reviews.

    Returns::

        {
            total_reviews: int,
            most_common_findings: [{rule_id, count}, ...],
            most_common_artifact_types: [{artifact_type, count}, ...],
            avg_findings_per_review: float,
            assessment_distribution: {GO: int, CONDITIONAL_GO: int, NO_GO: int},
        }
    """
    empty_stats: dict = {
        "total_reviews": 0,
        "most_common_findings": [],
        "most_common_artifact_types": [],
        "avg_findings_per_review": 0.0,
        "assessment_distribution": {"GO": 0, "CONDITIONAL_GO": 0, "NO_GO": 0},
    }

    try:
        from app.db.connection import get_session_factory
        from app.db.models import ReviewHistoryRecord

        session_factory = get_session_factory()
        if session_factory is None:
            return empty_stats

        from sqlalchemy import select

        async with session_factory() as session:
            stmt = select(ReviewHistoryRecord)
            rows = (await session.execute(stmt)).scalars().all()

            if not rows:
                return empty_stats

            total = len(rows)
            rule_counter: Counter[str] = Counter()
            artifact_counter: Counter[str] = Counter()
            assessment_dist: Counter[str] = Counter()
            total_findings = 0

            for row in rows:
                artifact_counter[row.artifact_type] += 1
                assessment_dist[row.overall_assessment] += 1
                total_findings += row.finding_count

                # Extract rule_ids from findings
                rule_ids = _extract_rule_ids_from_response(
                    row.full_response or {}
                )
                for rid in rule_ids:
                    rule_counter[rid] += 1

            return {
                "total_reviews": total,
                "most_common_findings": [
                    {"rule_id": rid, "count": cnt}
                    for rid, cnt in rule_counter.most_common(10)
                ],
                "most_common_artifact_types": [
                    {"artifact_type": at, "count": cnt}
                    for at, cnt in artifact_counter.most_common(10)
                ],
                "avg_findings_per_review": round(total_findings / total, 2)
                if total
                else 0.0,
                "assessment_distribution": {
                    "GO": assessment_dist.get("GO", 0),
                    "CONDITIONAL_GO": assessment_dist.get("CONDITIONAL_GO", 0),
                    "NO_GO": assessment_dist.get("NO_GO", 0),
                },
            }

    except Exception:
        logger.warning("Failed to compute review statistics", exc_info=True)
        return empty_stats
