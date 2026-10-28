#!/usr/bin/env python3
"""Tiny, deterministic arithmetic examples; no model, training or vector database."""
from __future__ import annotations

import argparse
import json
import math
from numbers import Real
from typing import Sequence


def vector(values: Sequence[float]) -> list[float]:
    if not values or any(isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x) for x in values):
        raise ValueError("a nonempty finite real-valued vector is required")
    return [float(x) for x in values]


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    a, b = vector(left), vector(right)
    if len(a) != len(b):
        raise ValueError("vector dimensions must match")
    return math.fsum(x * y for x, y in zip(a, b))


def softmax(scores: Sequence[float]) -> list[float]:
    values = vector(scores)
    maximum = max(values)
    weights = [math.exp(x - maximum) for x in values]
    denominator = math.fsum(weights)
    return [x / denominator for x in weights]


def attention(query, keys, values, allowed=None) -> tuple[list[float], list[float]]:
    """Single query/head, supplied Q/K/V, explicit mask; no learned projections."""
    q = vector(query)
    if not keys or len(keys) != len(values):
        raise ValueError("keys/values must be nonempty and have equal row counts")
    key_rows, value_rows = [vector(k) for k in keys], [vector(v) for v in values]
    if any(len(k) != len(q) for k in key_rows):
        raise ValueError("query/key dimensions must match")
    if len({len(v) for v in value_rows}) != 1:
        raise ValueError("all values must have the same dimension")
    mask = [True] * len(key_rows) if allowed is None else list(allowed)
    if len(mask) != len(key_rows) or any(type(x) is not bool for x in mask) or not any(mask):
        raise ValueError("mask must match rows and permit at least one position")
    scores = [dot(q, k) / math.sqrt(len(q)) for k, keep in zip(key_rows, mask) if keep]
    active = iter(softmax(scores))
    weights = [next(active) if keep else 0.0 for keep in mask]
    result = [math.fsum(w * v[col] for w, v in zip(weights, value_rows)) for col in range(len(value_rows[0]))]
    return weights, result


def cosine(left, right) -> float:
    a, b = vector(left), vector(right)
    if len(a) != len(b):
        raise ValueError("vector dimensions must match")
    normalized = []
    for values in (a, b):
        scale = max(abs(x) for x in values)
        if scale == 0:
            raise ValueError("cosine is undefined for a zero vector")
        # Even hypot can exceed float range; scale before computing the norm.
        scaled = [x / scale for x in values]
        magnitude = math.hypot(*scaled)
        normalized.append([x / magnitude for x in scaled])
    return max(-1.0, min(1.0, math.fsum(x * y for x, y in zip(*normalized))))


def rrf(rankings: Sequence[Sequence[str]], constant: float = 60) -> list[tuple[str, float]]:
    if isinstance(constant, bool) or not isinstance(constant, Real) or not math.isfinite(constant) or constant < 0:
        raise ValueError("RRF constant must be finite and nonnegative")
    scores: dict[str, float] = {}
    for ranking in rankings:
        if any(not isinstance(doc, str) or not doc for doc in ranking) or len(set(ranking)) != len(ranking):
            raise ValueError("each ranking must contain unique nonempty document IDs")
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (constant + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def retrieval_metrics(ranking: Sequence[str], relevant: set[str], k: int) -> dict[str, float | None]:
    if type(k) is not int or k < 1 or len(set(ranking)) != len(ranking):
        raise ValueError("k must be positive and ranked IDs must be unique")
    hits = [doc in relevant for doc in ranking[:k]]
    # Precision denominator is k, including missing positions as no hit.
    recall = sum(hits) / len(relevant) if relevant else None
    reciprocal_rank = next((1 / rank for rank, hit in enumerate(hits, 1) if hit), 0.0)
    dcg = sum(int(hit) / math.log2(rank + 1) for rank, hit in enumerate(hits, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return {"precision_at_k": sum(hits) / k, "recall_at_k": recall,
            "reciprocal_rank_at_k": reciprocal_rank, "ndcg_at_k": dcg / ideal if ideal else None}


def demo(section: str) -> dict:
    if section == "attention":
        q, keys, values = [1, 0], [[1, 0], [0, 1]], [[2, 0], [0, 4]]
        weights, result = attention(q, keys, values)
        masked_weights, masked_result = attention(q, keys, values, [True, False])
        return {"query": q, "keys": keys, "values": values, "weights": weights, "output": result,
                "masked_weights": masked_weights, "masked_output": masked_result}
    if section == "retrieval":
        return {"cosine_parallel": cosine([1, 0], [2, 0]), "cosine_orthogonal": cosine([1, 0], [0, 2]),
                "rrf_constant": 60, "rankings": [["A", "B", "C"], ["C", "B", "D"]],
                "fused": rrf([["A", "B", "C"], ["C", "B", "D"]])}
    if section == "metrics":
        ranking, relevant = ["B", "A", "C"], {"A", "C", "D"}
        return {"ranking": ranking, "relevant": sorted(relevant), "k": 3,
                **retrieval_metrics(ranking, relevant, 3), "note": "single-query RR@3; MRR requires a mean over queries"}
    raise ValueError(f"unknown section: {section}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=["all", "attention", "retrieval", "metrics"], default="all")
    args = parser.parse_args(argv)
    for section in ["attention", "retrieval", "metrics"] if args.section == "all" else [args.section]:
        print(json.dumps({"section": section, **demo(section)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
