#!/usr/bin/env python3
"""Offline teaching runtime. Scripted decisions replace a language model."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import re
import sys
from typing import Callable, Mapping


DOCUMENTS = (
    {"id": "D1", "text": "Agent loops need an explicit step budget and stop condition."},
    {"id": "D2", "text": "Retry transient read failures with a bounded attempt budget."},
    {"id": "D3", "text": "Write tools need runtime approval and a stable idempotency key."},
    {"id": "D4", "text": "RAG retrieval can return irrelevant evidence; evaluate retrieval separately."},
)


class ToolFailure(Exception):
    """Expected tool/runtime rejection, safe to expose in this synthetic demo."""


class InvalidArguments(ToolFailure):
    pass


class UnknownTool(ToolFailure):
    pass


class ApprovalRequired(ToolFailure):
    pass


class TransientReadFailure(ToolFailure):
    pass


class WriteOutcomeUnknown(ToolFailure):
    pass


class IdempotencyConflict(ToolFailure):
    pass


@dataclass(frozen=True)
class Action:
    tool: str
    arguments: object


@dataclass(frozen=True)
class Finish:
    answer: str


@dataclass(frozen=True)
class Approval:
    """Trusted runtime configuration; never populated from model arguments."""

    request_id: str
    title: str


@dataclass
class State:
    observations: list[dict] = field(default_factory=list)


@dataclass
class RunResult:
    stop_reason: str
    answer: str
    steps: int
    events: list[dict]
    created_count: int
    search_attempts: int
    write_attempts: int


def nonempty_string(value: object, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise InvalidArguments(f"{name} must be a nonempty string of at most {maximum} characters")
    return value


class Runtime:
    """One in-memory fake backend; no filesystem, network or code-execution tools."""

    TOOLS = frozenset({"search", "create_ticket"})

    def __init__(
        self,
        *,
        approvals: frozenset[Approval] = frozenset(),
        transient_read_failures: int = 0,
        lose_first_write_response: bool = False,
    ) -> None:
        if type(transient_read_failures) is not int or transient_read_failures < 0:
            raise ValueError("transient_read_failures must be a nonnegative integer")
        self.approvals = frozenset(approvals)
        self.transient_read_failures = transient_read_failures
        self.lose_first_write_response = lose_first_write_response
        self.tickets: dict[str, dict] = {}
        self.search_attempts = 0
        self.write_attempts = 0

    def validate(self, action: Action) -> dict:
        if not isinstance(action.tool, str) or action.tool not in self.TOOLS:
            raise UnknownTool("tool is not on the runtime allowlist")
        args = action.arguments
        if not isinstance(args, dict) or any(not isinstance(key, str) for key in args):
            raise InvalidArguments("arguments must be a JSON-like object with string keys")
        if action.tool == "search":
            if set(args) - {"query", "top_k"} or "query" not in args:
                raise InvalidArguments("search requires query and permits only query/top_k")
            nonempty_string(args["query"], "query", 256)
            top_k = args.get("top_k", 3)
            if type(top_k) is not int or not 1 <= top_k <= 5:
                raise InvalidArguments("top_k must be an integer from 1 to 5")
            return {"query": args["query"], "top_k": top_k}
        if set(args) != {"request_id", "title"}:
            raise InvalidArguments("create_ticket accepts exactly request_id/title; approval is runtime-owned")
        request_id = nonempty_string(args["request_id"], "request_id", 64)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", request_id):
            raise InvalidArguments("request_id permits only letters, digits, underscore and hyphen")
        nonempty_string(args["title"], "title", 120)
        return dict(args)

    def invoke(self, action: Action) -> dict:
        # Validation/authorization also live at the actual execution boundary.
        args = self.validate(action)
        if action.tool == "search":
            self.search_attempts += 1
            if self.transient_read_failures:
                self.transient_read_failures -= 1
                raise TransientReadFailure("synthetic temporary read failure")
            query_tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", args["query"].casefold()))
            ranked = []
            for document in DOCUMENTS:
                tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", document["text"].casefold()))
                overlap = len(query_tokens & tokens)
                if overlap:
                    ranked.append((overlap, document))
            ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
            return {"documents": [dict(item[1]) for item in ranked[:args["top_k"]]]}

        approval = Approval(args["request_id"], args["title"])
        if approval not in self.approvals:
            raise ApprovalRequired("no runtime approval matching this exact request_id/title")
        self.write_attempts += 1
        existing = self.tickets.get(args["request_id"])
        if existing is not None:
            if existing["title"] != args["title"]:
                raise IdempotencyConflict("same request_id was already used for different content")
            return {"ticket": dict(existing), "replayed": True}
        ticket = {"ticket_id": f"T{len(self.tickets) + 1}", **args}
        self.tickets[args["request_id"]] = ticket
        if self.lose_first_write_response:
            self.lose_first_write_response = False
            raise WriteOutcomeUnknown("ticket exists in fake backend, but response was lost; reconcile before retry")
        return {"ticket": dict(ticket), "replayed": False}

    def lookup_ticket(self, request_id: str) -> dict | None:
        """Trusted test operator inspects the fake backend, outside model decisions."""
        ticket = self.tickets.get(request_id)
        return dict(ticket) if ticket else None


DecisionMaker = Callable[[State], Action | Finish]


def scripted(decisions: list[Action | Finish]) -> DecisionMaker:
    sequence = iter(decisions)

    def decide(_state: State) -> Action | Finish:
        return next(sequence, Finish("Script finished."))

    return decide


def run(
    decide: DecisionMaker,
    runtime: Runtime,
    *,
    max_steps: int = 6,
    max_read_attempts: int = 2,
) -> RunResult:
    if type(max_steps) is not int or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if type(max_read_attempts) is not int or not 1 <= max_read_attempts <= 10:
        raise ValueError("max_read_attempts must be an integer from 1 to 10")
    state = State()
    events: list[dict] = []

    def stopped(reason: str, steps: int, answer: str = "") -> RunResult:
        events.append({"step": steps, "event": "stop", "reason": reason})
        return RunResult(reason, answer, steps, events, len(runtime.tickets), runtime.search_attempts, runtime.write_attempts)

    for step in range(1, max_steps + 1):
        decision = decide(state)
        if isinstance(decision, Finish):
            if not isinstance(decision.answer, str) or not decision.answer.strip():
                return stopped("invalid_decision", step)
            return stopped("final_answer", step, decision.answer)
        if not isinstance(decision, Action):
            return stopped("invalid_decision", step)
        events.append({"step": step, "event": "decision", "tool": decision.tool})
        attempts = max_read_attempts if decision.tool == "search" else 1
        for attempt in range(1, attempts + 1):
            try:
                result = runtime.invoke(decision)
            except TransientReadFailure as error:
                events.append({"step": step, "event": "transient_read_failure", "attempt": attempt, "retry": attempt < attempts, "detail": str(error)})
                if attempt == attempts:
                    return stopped("read_retry_exhausted", step)
                continue
            except (UnknownTool, InvalidArguments, ApprovalRequired, WriteOutcomeUnknown, IdempotencyConflict) as error:
                reasons = {
                    UnknownTool: "unknown_tool", InvalidArguments: "invalid_arguments",
                    ApprovalRequired: "approval_required", WriteOutcomeUnknown: "write_outcome_unknown",
                    IdempotencyConflict: "idempotency_conflict",
                }
                events.append({"step": step, "event": "tool_rejected", "tool": decision.tool, "detail": str(error)})
                return stopped(reasons[type(error)], step)
            state.observations.append({"tool": decision.tool, "result": result})
            events.append({"step": step, "event": "observation", "tool": decision.tool, "attempt": attempt, "result": result})
            break
    return stopped("step_budget_exhausted", max_steps)


def scenario(name: str) -> RunResult:
    if name == "happy":
        return run(scripted([Action("search", {"query": "agent loop"}), Finish("D1: define a step budget and stop condition.")]), Runtime())
    if name == "retry":
        return run(scripted([Action("search", {"query": "retry"}), Finish("D2: a temporary read failure recovered within two attempts.")]), Runtime(transient_read_failures=1))
    if name in {"approval", "denied"}:
        action = Action("create_ticket", {"request_id": "demo-001", "title": "Investigate synthetic retrieval failure"})
        approvals = frozenset({Approval("demo-001", "Investigate synthetic retrieval failure")}) if name == "approval" else frozenset()
        return run(scripted([action, action, Finish("The same approved intent created one fake ticket.")]), Runtime(approvals=approvals))
    if name == "loop":
        return run(lambda _state: Action("search", {"query": "agent"}), Runtime(), max_steps=3)
    raise ValueError(f"unknown scenario: {name}")


SCENARIOS: Mapping[str, tuple[str, int, int, int]] = {
    # stop reason, fake ticket count, actual read attempts, authorized write attempts
    "happy": ("final_answer", 0, 1, 0),
    "retry": ("final_answer", 0, 2, 0),
    "approval": ("final_answer", 1, 0, 2),
    "denied": ("approval_required", 0, 0, 0),
    "loop": ("step_budget_exhausted", 0, 3, 0),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    args = parser.parse_args(argv)
    failed = False
    for name in SCENARIOS if args.scenario == "all" else [args.scenario]:
        result = scenario(name)
        for event in result.events:
            print(json.dumps({"scenario": name, **event}, ensure_ascii=False))
        actual = (result.stop_reason, result.created_count, result.search_attempts, result.write_attempts)
        passed = actual == SCENARIOS[name]
        failed |= not passed
        print(json.dumps({"scenario": name, "summary": {"stop_reason": result.stop_reason, "created_count": result.created_count, "search_attempts": result.search_attempts, "write_attempts": result.write_attempts, "steps": result.steps, "answer": result.answer, "self_check": "pass" if passed else "FAIL"}}, ensure_ascii=False))
    if failed:
        print("Scenario self-check failed.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
