#!/usr/bin/env python3
"""Masked SFT and a clipped policy objective for tiny Bernoulli tables.

Standard library only; no LLM, GPU, rollout sampler, or complete GRPO trainer.
Each active row has its own two-choice logit. Observations remain conditioning
data in a real agent, but have no supervised target in this fixed exercise.
"""
from __future__ import annotations

import argparse
import json
import math


def _number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _probability(value: float, name: str) -> float:
    value = _number(value, name)
    if not 0 < value < 1:
        raise ValueError(f"{name} must be strictly between zero and one")
    return value


def _bit(value: int, name: str) -> int:
    if type(value) is not int or value not in (0, 1):
        raise ValueError(f"{name} must be integer zero or one")
    return value


def _same_length(*columns: list) -> int:
    count = len(columns[0])
    if not count or any(len(column) != count for column in columns[1:]):
        raise ValueError("columns must have the same nonzero length")
    return count


def sigmoid(logit: float) -> float:
    logit = _number(logit, "logit")
    if logit >= 0:
        return 1 / (1 + math.exp(-logit))
    exponential = math.exp(logit)
    return exponential / (1 + exponential)


def _softplus(value: float) -> float:
    return max(value, 0) + math.log1p(math.exp(-abs(value)))


def masked_sft_objective(logits: list, labels: list, mask: list[int]) -> dict:
    """Mean binary NLL over mask=1 rows, and its analytic logit gradient.

    A mask of zero removes a *target*, not the observation from model input.
    The omitted rows may use None for both logit and label. Active logits are
    independent table parameters, not the shared parameters of a Transformer.
    """
    count = _same_length(logits, labels, mask)
    for keep in mask:
        _bit(keep, "mask")
    targets = sum(mask)
    if not targets:
        raise ValueError("at least one supervised action target is required")
    nll, gradient, target_probabilities = [0.0] * count, [0.0] * count, [None] * count
    for index, keep in enumerate(mask):
        if not keep:
            continue
        logit = _number(logits[index], "active logit")
        label = _bit(labels[index], "active label")
        probability = sigmoid(logit)
        # Stable even when sigmoid rounds to 0 or 1 for a large finite logit.
        nll[index] = _softplus(-logit) if label else _softplus(logit)
        gradient[index] = (probability - label) / targets
        target_probabilities[index] = probability if label else 1 - probability
    return {"loss": math.fsum(nll) / targets, "target_count": targets,
            "gradient": gradient, "target_probabilities": target_probabilities}


def clipped_surrogate(ratio: float, advantage: float, epsilon: float = 0.2) -> tuple[float, float]:
    """Return min(r*A, clip(r)*A) and its derivative with respect to r.

    At a clipping kink, return the flat-side subgradient zero. A classical
    derivative does not exist there; finite-difference checks avoid the kinks.
    Clipping stops further *helpful* movement, not all out-of-range ratios.
    """
    ratio = _number(ratio, "ratio")
    advantage = _number(advantage, "advantage")
    epsilon = _number(epsilon, "epsilon")
    if ratio <= 0 or not 0 < epsilon < 1:
        raise ValueError("require ratio > 0 and 0 < epsilon < 1")
    lower, upper = 1 - epsilon, 1 + epsilon
    clipped = max(lower, min(upper, ratio))
    value = min(ratio * advantage, clipped * advantage)
    flat = (advantage > 0 and ratio >= upper) or (advantage < 0 and ratio <= lower)
    return value, 0.0 if flat else advantage


def bernoulli_policy_objective(logits: list[float], actions: list[int], advantages: list[float],
                               old_probabilities: list[float], reference_probabilities: list[float],
                               *, epsilon: float = 0.2, beta: float = 0.1) -> dict:
    """Four-state teaching objective: -mean(clipped surrogate) + beta*mean(KL).

    Each row is one fixed state and one sampled action, with equal row weight.
    old_probabilities and reference_probabilities mean P(action=1), remain
    frozen during an update, and may differ. KL is exact KL(current || ref)
    over both binary actions, not a sampled per-token GRPO KL estimator.
    Advantages are supplied and frozen; this function does not estimate them.
    """
    count = _same_length(logits, actions, advantages, old_probabilities, reference_probabilities)
    beta = _number(beta, "beta")
    if beta < 0:
        raise ValueError("beta must be nonnegative")
    terms, divergences, gradient, ratios = [], [], [], []
    for logit, action, advantage, old, reference in zip(
            logits, actions, advantages, old_probabilities, reference_probabilities):
        logit = _number(logit, "logit")
        action = _bit(action, "action")
        advantage = _number(advantage, "advantage")
        old = _probability(old, "old probability")
        reference = _probability(reference, "reference probability")
        probability = sigmoid(logit)
        sampled_probability = probability if action else 1 - probability
        old_sampled_probability = old if action else 1 - old
        ratio = sampled_probability / old_sampled_probability
        term, derivative_ratio = clipped_surrogate(ratio, advantage, epsilon)
        log_p, log_one_minus_p = -_softplus(-logit), -_softplus(logit)
        divergence = (probability * (log_p - math.log(reference))
                      + (1 - probability) * (log_one_minus_p - math.log1p(-reference)))
        variance = probability * (1 - probability)
        derivative_r = variance * (1 if action else -1) / old_sampled_probability
        reference_logit = math.log(reference) - math.log1p(-reference)
        derivative_kl = variance * (logit - reference_logit)
        gradient.append((-derivative_ratio * derivative_r + beta * derivative_kl) / count)
        terms.append(term)
        divergences.append(divergence)
        ratios.append(ratio)
    policy_loss = -math.fsum(terms) / count
    mean_kl = math.fsum(divergences) / count
    return {"loss": policy_loss + beta * mean_kl, "policy_loss": policy_loss,
            "mean_kl": mean_kl, "gradient": gradient, "ratios": ratios,
            "surrogates": terms, "epsilon": epsilon, "beta": beta,
            "normalization": "equal mean over fixed one-action states"}


def sft_demo() -> dict:
    rows = [
        ("user", "询问住宿", None, None, 0),
        ("assistant/tool_call", "查", 0.0, 1, 1),
        ("assistant/tool_call", "制度", math.log(3), 0, 1),
        ("tool", "上限", None, None, 0),
        ("tool", "700", None, None, 0),
        ("assistant/final", "未", math.log(4), 1, 1),
        ("assistant/final", "超标", 0.0, 0, 1),
    ]
    logits, labels, mask = [list(column) for column in zip(*[row[2:] for row in rows])]
    before = masked_sft_objective(logits, labels, mask)
    learning_rate = 0.4
    updated = [logit - learning_rate * grad if keep else logit
               for logit, grad, keep in zip(logits, before["gradient"], mask)]
    after = masked_sft_objective(updated, labels, mask)
    return {"section": "sft", "scope": "independent binary table; symbolic teaching tokens",
            "rows": [{"role": role, "symbol": symbol, "mask": keep}
                     for role, symbol, _, _, keep in rows],
            "before": before, "learning_rate": learning_rate,
            "updated_logits": updated, "after": after}


def policy_demo() -> dict:
    probabilities = [0.7, 0.3, 0.3, 0.7]
    logits = [math.log(p) - math.log1p(-p) for p in probabilities]
    actions, advantages, old, reference = [1, 1, 1, 1], [1, -1, 1, -1], [0.5] * 4, [0.5] * 4
    before = bernoulli_policy_objective(logits, actions, advantages, old, reference)
    learning_rate = 0.4
    updated = [logit - learning_rate * grad for logit, grad in zip(logits, before["gradient"])]
    after = bernoulli_policy_objective(updated, actions, advantages, old, reference)
    return {"section": "policy", "scope": "fixed binary states; no sampled rollouts or group estimator",
            "actions": actions, "advantages": advantages, "old_probabilities": old,
            "reference_probabilities": reference, "before": before,
            "learning_rate": learning_rate, "updated_logits": updated, "after": after}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=("sft", "policy", "all"), default="all")
    args = parser.parse_args(argv)
    for name, demo in (("sft", sft_demo), ("policy", policy_demo)):
        if args.section in (name, "all"):
            print(json.dumps(demo(), ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
