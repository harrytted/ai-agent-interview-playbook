#!/usr/bin/env python3
"""Recompute retrieval mechanics on authored terms, vectors and claim records.

No tokenizer, embedding model, ANN implementation, learned reranker or LLM is
called. Oracle ordering uses evaluation labels only to expose a coverage bound.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
import json
import math


def bm25_scores(documents: dict[str, list[str]], query: list[str], *,
                k1: float = 1.2, b: float = 0.75) -> dict[str, float]:
    """Textbook TF saturation with Lucene-style positive IDF, one text field.

    Inputs are already tokenized. Each distinct query term contributes once.
    This is not a reproduction of Lucene's analyzer or compressed field norms.
    """
    if not documents or not math.isfinite(k1) or k1 < 0 or not math.isfinite(b) or not 0 <= b <= 1:
        raise ValueError("require a corpus, k1 >= 0, and b in [0, 1]")
    terms = {key: Counter(value) for key, value in documents.items()}
    lengths = {key: sum(value.values()) for key, value in terms.items()}
    average = sum(lengths.values()) / len(documents)
    if not average:
        raise ValueError("the corpus must contain at least one term")
    frequencies = Counter(term for value in terms.values() for term in value)
    scores = dict.fromkeys(documents, 0.0)
    for term in set(query):
        df = frequencies[term]
        if not df:
            continue
        idf = math.log1p((len(documents) - df + 0.5) / (df + 0.5))
        for key, counts in terms.items():
            tf = counts[term]
            if not tf:
                continue
            norm = k1 * (1 - b + b * lengths[key] / average)
            scores[key] += idf * tf * (k1 + 1) / (tf + norm)
    return scores


def cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        raise ValueError("nonempty vectors with matching dimensions required")
    if not all(math.isfinite(x) for x in (*left, *right)):
        raise ValueError("vector entries must be finite")
    left_norm, right_norm = math.hypot(*left), math.hypot(*right)
    if not left_norm or not right_norm:
        raise ValueError("cosine is undefined for a zero vector")
    return math.fsum((a / left_norm) * (b / right_norm) for a, b in zip(left, right))


def rank(scores: dict[str, float], k: int) -> list[str]:
    if type(k) is not int or k < 1 or not all(math.isfinite(x) for x in scores.values()):
        raise ValueError("positive integer k and finite scores required")
    return sorted(scores, key=lambda key: (-scores[key], key))[:k]


def reciprocal_rank_fusion(rankings: list[list[str]], *, c: float = 60) -> dict[str, float]:
    if not math.isfinite(c) or c <= 0:
        raise ValueError("positive finite rank constant required")
    result = {}
    for ordering in rankings:
        if len(set(ordering)) != len(ordering):
            raise ValueError("a retrieval list cannot vote twice for the same ID")
        for position, key in enumerate(ordering, 1):
            result[key] = result.get(key, 0.0) + 1 / (c + position)
    return result


def evidence_metrics(ordering: list[str], relevant: set[str], k: int) -> dict:
    if not relevant or type(k) is not int or k < 1 or len(ordering) != len(set(ordering)):
        raise ValueError("nonempty labels, positive k and unique ranked IDs required")
    prefix = ordering[:k]
    found = set(prefix) & relevant
    return {"recall": len(found) / len(relevant),
            "reciprocal_rank": next((1 / i for i, key in enumerate(prefix, 1) if key in relevant), 0.0),
            "all_required_evidence_present": found == relevant}


def oracle_order(candidates: list[str], relevant: set[str]) -> list[str]:
    """Evaluation-label upper bound; never an inference-time reranker."""
    return sorted(candidates, key=lambda key: (key not in relevant, key))


@dataclass(frozen=True)
class Claim:
    record_id: str
    family: str
    attribute: str
    scope: str
    value: str
    valid_from: str
    valid_to: str | None = None


def resolve_claims(records: list[Claim], *, family: str, attribute: str, scope: str,
                   on_date: str, allowed_ids: set[str],
                   precedence: set[tuple[str, str]] | None = None) -> dict:
    """Resolve one fact key under host-supplied visibility and precedence.

    (A, B) means the trusted domain rule prefers record A to B for this key.
    Similarity, upload timestamps, vote counts and model preference are absent.
    This teaching relation is not an automatically inferred legal hierarchy.
    """
    ids = {record.record_id for record in records}
    if len(ids) != len(records):
        raise ValueError("claim record IDs must be unique")
    reaches = {key: set() for key in ids}
    by_id = {record.record_id: record for record in records}
    for preferred, lower in precedence or set():
        if preferred not in ids or lower not in ids:
            raise ValueError("precedence refers to an unknown record")
        left, right = by_id[preferred], by_id[lower]
        if (left.family, left.attribute, left.scope) != (right.family, right.attribute, right.scope):
            raise ValueError("precedence must compare the same fact key and scope")
        reaches[preferred].add(lower)
    for pivot in sorted(ids):
        for key in ids:
            if pivot in reaches[key]:
                reaches[key].update(reaches[pivot])
    if any(key in value for key, value in reaches.items()):
        raise ValueError("precedence must be acyclic")
    instant = date.fromisoformat(on_date)
    active = []
    for record in records:
        start = date.fromisoformat(record.valid_from)
        end = date.fromisoformat(record.valid_to) if record.valid_to else None
        if end is not None and end <= start:
            raise ValueError("validity intervals must be nonempty and half-open")
        if (record.record_id in allowed_ids and record.family == family
                and record.attribute == attribute and record.scope == scope
                and start <= instant and (end is None or instant < end)):
            active.append(record)
    maximal = [r for r in active if not any(r.record_id in reaches[other.record_id] for other in active)]
    if not maximal:
        return {"status": "insufficient", "values": [], "references": []}
    values = sorted({r.value for r in maximal})
    return {"status": "supported" if len(values) == 1 else "conflicting",
            "values": values, "references": sorted(r.record_id for r in maximal)}


def scoring_demo() -> dict:
    corpus = {"A": ["hotel", "hotel"], "B": ["hotel", "form"], "C": ["policy", "text"]}
    scores = bm25_scores(corpus, ["hotel"])
    saturated = bm25_scores({"one": ["hotel"], "two": ["hotel"] * 2,
                             "three": ["hotel"] * 3}, ["hotel"], b=0)
    lengths = bm25_scores({"short": ["hotel"], "long": ["hotel"] + ["form"] * 9}, ["hotel"])
    return {"section": "scoring", "manual_terms": corpus, "bm25_scores": scores,
            "idf": math.log(1.6), "ordering": rank(scores, 3),
            "tf_saturation_b_zero": saturated, "same_tf_different_length": lengths,
            "given_vector_cosine": cosine([1, 0], [0.8, 0.6]),
            "term_expansion": {"before": rank({k: v for k, v in bm25_scores(
                {"hotel": ["hotel"], "lodging": ["lodging"]}, ["hotel"]).items() if v > 0}, 2),
                "after": rank(bm25_scores({"hotel": ["hotel"], "lodging": ["lodging"]},
                                          ["hotel", "lodging"]), 2)}}


def candidates_demo() -> dict:
    scores = reciprocal_rank_fusion([["A", "B", "C"], ["C", "B", "D"]])
    vectors = {"old": [1, 0], "private": [0.99, 0.01], "valid": [0.8, 0.6]}
    distances = {key: cosine([1, 0], value) for key, value in vectors.items()}
    allowed = {"valid"}
    unrestricted = rank(distances, 2)
    pool, gold = ["B", "A"], {"A", "C"}
    return {"section": "candidates", "rrf_scores": scores, "rrf_order": rank(scores, 4),
            "exact_cosine_order": rank(distances, 3),
            "top2_then_filter": [key for key in unrestricted if key in allowed],
            "filter_then_exact_search": rank({k: v for k, v in distances.items() if k in allowed}, 2),
            "candidate_pool": pool, "needed_labels": sorted(gold),
            "pool_recall": evidence_metrics(pool, gold, 2),
            "oracle_top2_with_missing_C": evidence_metrics(oracle_order(pool, gold), gold, 2),
            "oracle_top2_with_C_added": evidence_metrics(oracle_order(pool + ["C"], gold), gold, 2),
            "boundary": "exact toy search; no ANN or learned reranker is implemented"}


def conflict_demo() -> dict:
    records = [Claim("old", "P17", "limit", "staff", "600", "2026-01-01", "2026-11-01"),
               Claim("formal", "P17", "limit", "staff", "700", "2026-11-01"),
               Claim("faq", "P17", "limit", "staff", "500", "2026-11-01"),
               Claim("manager", "P17", "limit", "manager", "900", "2026-01-01")]
    query = {"family": "P17", "attribute": "limit", "scope": "staff", "on_date": "2026-11-12"}
    visible = {"old", "formal", "faq", "manager"}
    return {"section": "conflicts",
            "same_scope_same_date": resolve_claims(records, **query, allowed_ids=visible),
            "explicit_domain_precedence": resolve_claims(records, **query, allowed_ids=visible,
                                                         precedence={("formal", "faq")}),
            "earlier_business_date": resolve_claims(records, **{**query, "on_date": "2026-10-31"}, allowed_ids=visible),
            "no_current_access": resolve_claims(records, **query, allowed_ids=set()),
            "boundary": "authored facts and trusted rules; no automatic contradiction extraction or authority inference"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=("scoring", "candidates", "conflicts", "all"), default="all")
    args = parser.parse_args(argv)
    for name, demo in (("scoring", scoring_demo), ("candidates", candidates_demo), ("conflicts", conflict_demo)):
        if args.section in (name, "all"):
            print(json.dumps({**demo(), "model_requests": 0}, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
