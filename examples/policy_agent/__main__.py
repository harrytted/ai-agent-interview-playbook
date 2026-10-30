"""Run from repository root: python3 -m examples.policy_agent list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from . import core
from .grade import grade


def evaluate(suite="all", *, root=core.DEFAULT_ROOT, mode="offline"):
    if mode != "offline":
        raise ValueError("automated suites are offline; live runs require explicit individual invocation")
    if suite == "pilot":
        items = [("T01", "default"), ("T01", "missing-date"), ("T01", "stale-first")]
    else:
        items = [tuple(key.split("/")) for key in core.read_json(core.DATA / "expected.json")]
    reports = []
    token = str(time.time_ns())
    for task_id, variant in items:
        run_id = f"eval-{token}-{task_id}-{variant}"
        result = core.run_task(task_id, variant, run_id=run_id, root=root)
        if result["status"] == "clarification_required":
            result = core.resume_task(run_id, root=root, reply={"trip_date": "2026-11-12"})
        if result["status"] == "approval_required":
            core.approve_task(run_id, result["approval_request"]["request_id"], root=root)
            if task_id == "T12":
                command = [sys.executable, "-m", "examples.policy_agent", "--root", str(Path(root).resolve()), "resume", "--run-id", run_id]
                first = subprocess.run(command, capture_output=True, text=True)
                if first.returncode != 73:
                    raise RuntimeError("crash demonstration did not terminate at injected commit gap: " + first.stdout + first.stderr)
                second = subprocess.run(command, capture_output=True, text=True)
                if second.returncode:
                    raise RuntimeError("recovery subprocess failed: " + second.stdout + second.stderr)
                result = core.read_json(core.run_directory(root, run_id) / "result.json")
            else:
                result = core.resume_task(run_id, root=root)
        reports.append(grade(core.run_directory(root, run_id)))
    return {"suite": suite, "mode": "offline", "total": len(reports), "passed": sum(r["passed"] for r in reports), "all_passed": all(r["passed"] for r in reports), "reports": reports}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline fictional policy-agent learning lab")
    parser.add_argument("--root", type=Path, default=core.DEFAULT_ROOT, help="persisted demonstration directories")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    run = commands.add_parser("run")
    run.add_argument("--task", required=True)
    run.add_argument("--variant", default="default")
    run.add_argument("--mode", choices=("offline", "live"), default="offline")
    run.add_argument("--run-id")
    resume = commands.add_parser("resume")
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--reply-json")
    approve = commands.add_parser("approve")
    approve.add_argument("--run-id", required=True)
    approve.add_argument("--request-id", required=True)
    evaluate_parser = commands.add_parser("eval")
    evaluate_parser.add_argument("--suite", choices=("pilot", "all"), default="pilot")
    evaluate_parser.add_argument("--mode", choices=("offline",), default="offline")
    evaluate_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = {"tasks": [{"task_id": t["task_id"], "goal": t["goal"]} for t in core.read_json(core.DATA / "tasks.json")], "variants": list(core.read_json(core.DATA / "variants.json")), "offline_default": True}
        elif args.command == "run":
            result = core.run_task(args.task, args.variant, args.mode, args.run_id, args.root)
        elif args.command == "resume":
            result = core.resume_task(args.run_id, args.root, json.loads(args.reply_json) if args.reply_json else None, crash_after_remote=True)
        elif args.command == "approve":
            result = core.approve_task(args.run_id, args.request_id, args.root)
        else:
            result = evaluate(args.suite, root=args.root, mode=args.mode)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            core.write_json(args.output, result)
            result = {key: result[key] for key in ("suite", "mode", "total", "passed", "all_passed")} | {"output": str(args.output), "failures": [{"task_id": item["task_id"], "variant": item["variant"], "failed_checks": [name for name, passed in item["checks"].items() if not passed]} for item in result["reports"] if not item["passed"]]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == "eval" and not result["all_passed"] else 0
    except (ValueError, PermissionError, RuntimeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
