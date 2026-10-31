#!/usr/bin/env python3
"""Media evidence and turn state experiments. No ASR, vision or TTS model."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def number(value, *, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (value > 0 if positive else value >= 0)


class Session:
    def __init__(self):
        self.media = {}
        self.evidence = {}
        self.transcripts = []
        self.condition_version = 0
        self.conditions = None
        self.calls = {}
        self.policy = None
        self.stale_results = 0
        self.audio = {"generation": None, "duration": 0, "played_seconds": 0,
                      "history_seconds": 0, "cancelled": False, "ignored_late_chunks": 0}
        # IDs are unique for the whole session. Keep cancelled and superseded
        # records so a late generated event cannot resurrect an old output.
        self.audio_generations = {}
        self.trace = []

    def apply(self, event):
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError("an event object with a type is required")
        kind = event["type"]
        self.trace.append(dict(event))
        if kind == "media":
            if event["kind"] not in ("image", "audio"):
                raise ValueError("unknown media kind")
            if event["kind"] == "image" and not all(number(event[key], positive=True) for key in ("width", "height")):
                raise ValueError("image dimensions must be positive")
            if event["kind"] == "audio" and not number(event["duration"], positive=True):
                raise ValueError("audio duration must be positive")
            if event["id"] in self.media and self.media[event["id"]] != event:
                raise ValueError("media ID conflict")
            self.media[event["id"]] = dict(event)
        elif kind == "evidence":
            media = self.media[event["media_id"]]
            if media["kind"] == "image":
                x, y, width, height = event["region"]
                if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
                       for v in (x, y, width, height)) or min(x, y) < 0 or min(width, height) <= 0:
                    raise ValueError("invalid image region")
                if x+width > media["width"] or y+height > media["height"]:
                    raise ValueError("region outside image")
            else:
                start, end = event["time"]
                if not number(start) or not number(end) or not 0 <= start < end <= media["duration"]:
                    raise ValueError("invalid audio time span")
            if event.get("confidence") not in ("clear", "uncertain"):
                raise ValueError("confidence must be explicit")
            if "amount" in event and not number(event["amount"]):
                raise ValueError("observed amount must be nonnegative")
            self.evidence[event["id"]] = dict(event)
        elif kind == "transcript":
            if event["stage"] not in ("interim", "final"):
                raise ValueError("unknown transcript stage")
            self.transcripts.append(dict(event))
            if event["stage"] == "final":
                if event["evidence_id"] not in self.evidence:
                    raise ValueError("final transcript needs source time evidence")
                evidence = self.evidence[event["evidence_id"]]
                if self.media[evidence["media_id"]]["kind"] != "audio":
                    raise ValueError("transcript needs an audio time span")
                if not number(event["amount"]) or any(not isinstance(event[key], str) or not event[key].strip() for key in ("city", "date")):
                    raise ValueError("invalid final business conditions")
                conditions = {key: event[key] for key in ("city", "date", "amount")}
                if conditions != self.conditions:
                    self.condition_version += 1
                    self.conditions = conditions
                    self.policy = None
        elif kind == "tool_start":
            if self.conditions is None:
                raise ValueError("final conditions required")
            if event["call_id"] in self.calls:
                raise ValueError("call ID already exists")
            self.calls[event["call_id"]] = {"version": self.condition_version,
                                             "city": self.conditions["city"], "done": False}
        elif kind == "tool_result":
            if not number(event["limit"]) or not isinstance(event["source"], str) or not event["source"].strip():
                raise ValueError("tool observation requires a limit and source")
            call = self.calls[event["call_id"]]
            if call["done"]:
                raise ValueError("tool result already consumed")
            call["done"] = True
            if (call["version"] != self.condition_version or event["city"] != call["city"]
                    or event["city"] != self.conditions["city"]):
                self.stale_results += 1
            else:
                self.policy = {"city": event["city"], "limit": event["limit"],
                               "condition_version": self.condition_version, "source": event["source"]}
        elif kind == "audio_generated":
            generation = event.get("generation")
            if not isinstance(generation, str) or not generation.strip():
                raise ValueError("a nonempty generation ID is required")
            if generation in self.audio_generations:
                raise ValueError("generation ID has already started and cannot be reused")
            if not number(event["duration"], positive=True):
                raise ValueError("duration must be positive")
            self.audio = {"generation": generation, "duration": event["duration"],
                          "played_seconds": 0, "history_seconds": 0, "cancelled": False,
                          "ignored_late_chunks": 0}
            self.audio_generations[generation] = self.audio
        elif kind in ("playback", "interrupt"):
            generation = event.get("generation")
            if not isinstance(generation, str) or not generation.strip():
                raise ValueError("a nonempty generation ID is required")
            # Route by generation before touching its position: a late g1 block
            # may exceed g2's shorter duration but is irrelevant to g2's clock.
            if generation != self.audio["generation"] or self.audio["cancelled"]:
                self.audio["ignored_late_chunks"] += 1
                return
            position = event["position"]
            if not number(position) or position > self.audio["duration"]:
                raise ValueError("playback position outside generated media")
            if position < self.audio["played_seconds"]:
                raise ValueError("playback clock went backwards")
            self.audio["played_seconds"] = position
            if kind == "interrupt":
                self.audio["cancelled"] = True
                self.audio["history_seconds"] = position
        else:
            raise ValueError("unknown event type: "+kind)

    def result(self):
        receipt = next((e for e in self.evidence.values() if "amount" in e), None)
        conflict = bool(self.conditions and receipt and
                        (receipt["confidence"] != "clear" or receipt["amount"] != self.conditions["amount"]))
        status = ("waiting_final_transcript" if not self.conditions else "needs_confirmation" if conflict
                  else "waiting_policy" if not self.policy else "supported_draft")
        return {"status": status, "condition_version": self.condition_version,
                "city": self.conditions["city"] if self.conditions else None,
                "stale_results": self.stale_results,
                "draft": {**self.conditions, "policy_source": self.policy["source"], "policy_limit_cny": self.policy["limit"],
                          "exceeds_limit": self.conditions["amount"] > self.policy["limit"]}
                         if status == "supported_draft" else None,
                "evidence_ids": sorted(self.evidence), "audio": dict(self.audio),
                "audio_generations": {key: dict(value) for key, value in self.audio_generations.items()}}


SCENARIOS = ("normal", "interim", "correction", "uncertain", "interruption")


def grade_result(result, expected):
    checks = {}
    for key, value in expected.items():
        actual = result
        for part in key.split("."):
            actual = actual.get(part, {"missing": key}) if isinstance(actual, dict) else {"missing": key}
        checks[key] = actual == value
    return checks


def run_scenario(name):
    session = Session()
    for line in (Path(__file__).parent / "fixtures" / (name+".jsonl")).read_text().splitlines():
        if line.strip():
            session.apply(json.loads(line))
    result = session.result()
    expected = json.loads((Path(__file__).parent / "expected.json").read_text())[name]
    checks = grade_result(result, expected)
    return {"scenario": name, "actual": result, "checks": checks, "passed": all(checks.values()),
            "evidence_level": "offline_media_state_machine"}, session.trace


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all",)+SCENARIOS, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/multimodal_lab/all-report.json"))
    args = parser.parse_args(argv)
    results, trace = [], []
    for name in SCENARIOS if args.scenario == "all" else (args.scenario,):
        result, events = run_scenario(name)
        results.append(result)
        trace.extend({"scenario": name, **e} for e in events)
    passed = all(row["passed"] for row in results)
    report = {"passed": passed, "evidence_level": "offline_media_state_machine", "model_recognition_tested": False,
              "browser_playback_tested_by_cli": False, "scenarios": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    (args.output.parent / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n")
    (args.output.parent / "trace.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False)+"\n" for e in trace))
    (args.output.parent / "grade.json").write_text(json.dumps({"passed": passed, "checks": {r["scenario"]: r["checks"] for r in results}}, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"passed": passed, "scenarios": len(results), "report": str(args.output)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
