#!/usr/bin/env python3
"""Paired binary-outcome analysis; the default outcomes are authored teaching data.

No model is called. Resample whole task pairs, never the two systems separately.
This small percentile-bootstrap example is not a general inference package.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random


DEMO_PAIRS = [
    {"task_id": f"task-{i:02}", "baseline": i <= 5 or i == 12,
     "candidate": i <= 5 or 9 <= i <= 11}
    for i in range(1, 13)
]


def mcnemar_exact(improved: int, regressed: int) -> float:
    """Two-sided exact conditional test on discordant task pairs."""
    if any(type(n) is not int or n < 0 for n in (improved, regressed)):
        raise ValueError("discordant counts must be nonnegative integers")
    n = improved + regressed
    if not n:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(improved, regressed) + 1))
    return min(1.0, 2 * tail / (1 << n))


def _percentile(ordered: list[float], fraction: float) -> float:
    position = (len(ordered) - 1) * fraction
    left = math.floor(position)
    weight = position - left
    return ordered[left] * (1 - weight) + ordered[math.ceil(position)] * weight


def analyze_pairs(records: list[dict], *, resamples: int = 2000,
                  confidence: float = 0.95, seed: int = 7) -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("provide a nonempty list of paired task outcomes")
    seen = set()
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("each task must be an object")
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in seen:
            raise ValueError("task_id must be a nonempty unique string")
        if any(type(row.get(key)) is not bool for key in ("baseline", "candidate")):
            raise ValueError("both outcomes must be explicit booleans; do not omit failures")
        seen.add(task_id)
    if type(resamples) is not int or not 1 <= resamples <= 100_000:
        raise ValueError("resamples must be an integer in [1, 100000]")
    if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence) or not 0 < confidence < 1):
        raise ValueError("confidence must be a finite number in (0, 1)")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")

    # Stable IDs keep a seeded run reproducible even if input rows are reordered.
    pairs = sorted(records, key=lambda row: row["task_id"])
    n = len(pairs)
    improved = [r["task_id"] for r in pairs if r["candidate"] and not r["baseline"]]
    regressed = [r["task_id"] for r in pairs if r["baseline"] and not r["candidate"]]
    differences = [int(r["candidate"]) - int(r["baseline"]) for r in pairs]
    rng = random.Random(seed)
    distribution = sorted(
        sum(differences[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(resamples)
    )
    alpha = 1 - confidence
    return {
        "task_count": n,
        "both_pass": sum(r["baseline"] and r["candidate"] for r in pairs),
        "both_fail": sum(not r["baseline"] and not r["candidate"] for r in pairs),
        "improved_ids": improved,
        "regressed_ids": regressed,
        "baseline_success_rate": sum(r["baseline"] for r in pairs) / n,
        "candidate_success_rate": sum(r["candidate"] for r in pairs) / n,
        "paired_difference": sum(differences) / n,
        "exact_mcnemar_pvalue": mcnemar_exact(len(improved), len(regressed)),
        "bootstrap": {
            "method": "paired_percentile", "confidence": confidence,
            "resamples": resamples, "seed": seed,
            "low": _percentile(distribution, alpha / 2),
            "high": _percentile(distribution, 1 - alpha / 2),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON array: task_id, baseline, candidate")
    parser.add_argument("--resamples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    try:
        records = json.loads(args.input.read_text()) if args.input else DEMO_PAIRS
        report = analyze_pairs(records, resamples=args.resamples, seed=args.seed)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    report["evidence"] = "provided_outcomes" if args.input else "authored_teaching_outcomes"
    report["model_requests"] = 0
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
