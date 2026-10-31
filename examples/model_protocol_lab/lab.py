"""Parse real SSE bytes, assemble Messages tool blocks, and grade host behavior.

This deliberately supports text and client tool_use blocks, not all provider
features. Fixtures are authored teaching data, never provider measurements.
"""
from __future__ import annotations

import argparse
import codecs
from copy import deepcopy
import json
from pathlib import Path
import re

FIXTURES = Path(__file__).parent / "fixtures"


class ProtocolError(ValueError):
    pass


class TransportError(ValueError):
    pass


def parse_sse(chunks):
    """Yield decoded event dictionaries; UTF-8, lines and events cross reads.

    Only a blank line dispatches an event. Incomplete EOF is not dispatched.
    CR, LF and CRLF line endings and multiple data lines are supported.
    """
    decoder = codecs.getincrementaldecoder("utf-8-sig")("strict")
    buffer, fields, total = "", [], 0

    def dispatch(lines):
        name, data = "message", []
        for line in lines:
            if line.startswith(":"):
                continue
            key, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if key == "event":
                name = value
            elif key == "data":
                data.append(value)
        if not data:
            return None
        try:
            value = json.loads("\n".join(data))
        except ValueError as exc:
            raise ProtocolError("SSE data is not a complete JSON object") from exc
        if not isinstance(value, dict) or value.get("type") != name:
            raise ProtocolError("event name and JSON type disagree")
        return value

    try:
        for chunk in chunks:
            if not isinstance(chunk, bytes):
                raise ProtocolError("stream reads must be bytes")
            total += len(chunk)
            if total > 2_000_000:
                raise ProtocolError("teaching stream exceeds 2 MB limit")
            buffer += decoder.decode(chunk)
            while True:
                match = re.search(r"[\r\n]", buffer)
                if not match or (buffer[match.start():] == "\r"):
                    break
                position = match.start()
                width = 2 if buffer[position:position + 2] == "\r\n" else 1
                line, buffer = buffer[:position], buffer[position + width:]
                if line:
                    fields.append(line)
                else:
                    event = dispatch(fields)
                    fields = []
                    if event is not None:
                        yield event
        buffer += decoder.decode(b"", final=True)
        # At EOF a trailing CR is a complete line ending, not half a CRLF.
        while re.search(r"[\r\n]", buffer):
            match = re.search(r"[\r\n]", buffer)
            position = match.start()
            width = 2 if buffer[position:position + 2] == "\r\n" else 1
            line, buffer = buffer[:position], buffer[position + width:]
            if line:
                fields.append(line)
            else:
                event = dispatch(fields)
                fields = []
                if event is not None:
                    yield event
    except UnicodeError as exc:
        raise TransportError("invalid or incomplete UTF-8") from exc
    if buffer or fields:
        raise TransportError("EOF inside an SSE event")


def assemble(events):
    """A bounded subset of the provider Messages stream state machine."""
    blocks, opened, seen_ids = {}, set(), set()
    started = stopped = False
    stop_reason = None
    ending = False
    usage = {}
    for event in events:
        kind = event.get("type")
        if stopped:
            raise ProtocolError("event after message_stop")
        if kind == "ping":
            continue
        if kind == "error":
            raise TransportError("provider emitted an error event")
        if kind == "message_start":
            if started or not isinstance(event.get("message"), dict):
                raise ProtocolError("invalid message_start")
            started = True
            if not isinstance(event["message"].get("usage", {}), dict):
                raise ProtocolError("invalid message usage")
            usage.update(event["message"].get("usage", {}))
            continue
        if not started:
            raise ProtocolError("content before message_start")
        if ending and kind in {"content_block_start", "content_block_delta", "content_block_stop"}:
            raise ProtocolError("content after message_delta")
        if kind == "content_block_start":
            index, block = event.get("index"), deepcopy(event.get("content_block"))
            if type(index) is not int or index != len(blocks) or opened or not isinstance(block, dict):
                raise ProtocolError("invalid or repeated block index")
            if block.get("type") not in {"text", "tool_use"}:
                raise ProtocolError("unsupported block; do not silently discard it")
            if block["type"] == "tool_use":
                call_id = block.get("id")
                if not isinstance(call_id, str) or not call_id or call_id in seen_ids:
                    raise ProtocolError("missing or duplicate tool ID")
                if not isinstance(block.get("name"), str) or not isinstance(block.get("input"), dict):
                    raise ProtocolError("invalid tool block")
                seen_ids.add(call_id)
                block["partial_json"] = ""
            elif not isinstance(block.get("text"), str):
                raise ProtocolError("invalid text block")
            blocks[index] = block
            opened.add(index)
        elif kind == "content_block_delta":
            index, delta = event.get("index"), event.get("delta")
            if type(index) is not int or index not in opened or not isinstance(delta, dict):
                raise ProtocolError("delta outside an open block")
            block = blocks[index]
            if block["type"] == "tool_use" and delta.get("type") == "input_json_delta" and isinstance(delta.get("partial_json"), str):
                block["partial_json"] += delta["partial_json"]
            elif block["type"] == "text" and delta.get("type") == "text_delta" and isinstance(delta.get("text"), str):
                block["text"] += delta["text"]
            else:
                raise ProtocolError("delta type disagrees with block")
        elif kind == "content_block_stop":
            index = event.get("index")
            if type(index) is not int or index not in opened:
                raise ProtocolError("stop outside an open block")
            opened.remove(index)
        elif kind == "message_delta":
            if opened:
                raise ProtocolError("message_delta before content blocks finished")
            if not isinstance(event.get("delta"), dict) or not isinstance(event.get("usage", {}), dict):
                raise ProtocolError("invalid message delta or usage")
            ending = True
            reason = event.get("delta", {}).get("stop_reason")
            if reason is not None:
                if stop_reason is not None:
                    raise ProtocolError("duplicate stop reason")
                if not isinstance(reason, str):
                    raise ProtocolError("stop reason must be a string")
                stop_reason = reason
            usage.update(event.get("usage", {}))
        elif kind == "message_stop":
            if opened or stop_reason is None:
                raise ProtocolError("message ended before its blocks or stop reason")
            stopped = True
        else:
            raise ProtocolError("unsupported event in teaching subset: " + str(kind))
    if not stopped:
        raise TransportError("EOF without message_stop; outcome incomplete")
    # Inspect the termination before parsing possibly truncated tool arguments.
    if stop_reason == "max_tokens":
        return {"status": "truncated", "calls": [], "usage": usage}
    if stop_reason == "refusal":
        return {"status": "refused", "calls": [], "usage": usage}
    if stop_reason not in {"tool_use", "end_turn"}:
        return {"status": "unsupported_stop", "calls": [], "usage": usage}
    calls, content = [], []
    for index in sorted(blocks):
        block = deepcopy(blocks[index])
        if block["type"] == "tool_use":
            partial = block.pop("partial_json")
            if partial:
                try:
                    block["input"] = json.loads(partial)
                except ValueError as exc:
                    raise ProtocolError("tool input never became complete JSON") from exc
            if not isinstance(block["input"], dict):
                raise ProtocolError("tool input must be an object")
            calls.append({"id": block["id"], "name": block["name"], "arguments": block["input"]})
        content.append(block)
    if (stop_reason == "tool_use") != bool(calls):
        raise ProtocolError("tool blocks and stop reason disagree")
    return {"status": "tool_calls" if calls else "model_finished", "calls": calls,
            "content": content, "usage": usage}


def match_results(calls, results):
    ids = [call.get("id") for call in calls]
    returned = [item.get("tool_use_id") for item in results]
    if (any(not isinstance(i, str) or not i for i in ids + returned)
            or len(set(ids)) != len(ids) or len(set(returned)) != len(returned)
            or set(ids) != set(returned)):
        raise ProtocolError("each requested tool ID needs exactly one matching result")
    by_id = {item["tool_use_id"]: item for item in results}
    return [by_id[call_id] for call_id in ids]


def execute_calls(calls, observations):
    results = []
    for call in calls:
        args = call.get("arguments")
        if (call.get("name") != "lookup_policy" or not isinstance(args, dict)
                or set(args) != {"city", "trip_date"} or not isinstance(args["city"], str)
                or args["city"] not in observations or args["trip_date"] != "2026-11-12"):
            raise ProtocolError("tool is outside the fixed authorized fixture contract")
        results.append({"type": "tool_result", "tool_use_id": call["id"],
                        "content": json.dumps(observations[args["city"]], ensure_ascii=False)})
    return results


def validate_answer(value, evidence):
    """Minimal explicit output contract, then independent business checks."""
    if not isinstance(value, dict) or set(value) != {"claims"} or not isinstance(value["claims"], list):
        raise ProtocolError("answer must contain only a claims list")
    if len(value["claims"]) != len(evidence):
        raise ProtocolError("answer omits evidence")
    seen = set()
    for claim in value["claims"]:
        if not isinstance(claim, dict) or set(claim) != {"city", "limit_cny", "reference"}:
            raise ProtocolError("claim shape invalid")
        ref = claim["reference"]
        if not isinstance(ref, str) or ref in seen or ref not in evidence:
            raise ProtocolError("unobserved or repeated reference")
        seen.add(ref)
        if claim["city"] != evidence[ref]["city"] or type(claim["limit_cny"]) is not int or claim["limit_cny"] != evidence[ref]["limit_cny"]:
            raise ProtocolError("JSON parsed but claim disagrees with observed evidence")
    return value


def run_scenario(name, output):
    expected = json.loads((FIXTURES / "expected.json").read_text())[name]
    raw = (FIXTURES / "two-tools.sse").read_bytes()
    raw_final = (FIXTURES / "answer.sse").read_bytes()
    # Inject faults into the saved input bytes so a reader can replay exactly
    # the response that produced the trace and final status.
    if name == "duplicate-id":
        raw = raw.replace(b'"id":"call-2"', b'"id":"call-1"')
    if name in {"truncated", "refusal"}:
        raw = raw.replace(b'"stop_reason":"tool_use"',
                          b'"stop_reason":"max_tokens"' if name == "truncated" else b'"stop_reason":"refusal"')
    if name == "semantic-error":
        raw_final = raw_final.replace(b"700", b"7000", 1)
    if name in {"final-truncated", "final-refusal"}:
        raw_final = raw_final.replace(b'"end_turn"', b'"max_tokens"' if name == "final-truncated" else b'"refusal"')
    if name == "disconnect":
        raw = raw[:raw.index(b"event: message_stop")]
    events, trace = [], []
    try:
        for event in parse_sse(raw[i:i + 1] for i in range(len(raw))):
            events.append(event)
        result = assemble(events)
        trace.extend({"event": "provider_event", "data": e} for e in events)
        if result["status"] == "tool_calls":
            observations = json.loads((FIXTURES / "observations.json").read_text())
            results = execute_calls(result["calls"], observations)
            if name == "missing-result":
                results.pop()
            result["matched_results"] = match_results(result["calls"], results)
            result["next_request"] = {"messages": [
                {"role": "user", "content": "查2026-11-12海岚与云洲普通员工住宿金额"},
                {"role": "assistant", "content": result["content"]},
                {"role": "user", "content": result["matched_results"]}]}
            trace.append({"event": "tool_results_matched", "ids": [r["tool_use_id"] for r in results]})
            final_events = list(parse_sse([raw_final]))
            final = assemble(final_events)
            trace.extend({"event": "provider_event", "round": 2, "data": e} for e in final_events)
            if final["status"] == "model_finished":
                try:
                    value = json.loads("".join(b["text"] for b in final["content"]))
                except ValueError as exc:
                    raise ProtocolError("final answer is not JSON") from exc
                evidence = {v["reference"]: v for v in observations.values()}
                result["answer"] = validate_answer(value, evidence)
                result["status"] = "answered"
            elif final["status"] == "tool_calls":
                raise ProtocolError("this bounded fixture expects a final answer after one tool round")
            else:
                result.update(status=final["status"], calls=[])
    except (ProtocolError, TransportError) as exc:
        result = {"status": "transport_failed" if isinstance(exc, TransportError) else "protocol_error", "detail": str(exc), "calls": []}
        if not trace:
            trace.extend({"event": "provider_event", "data": e} for e in events)
    trace.append({"event": "host_stopped", "status": result["status"]})
    result.update({"scenario": name, "mode": "offline_fixture", "raw_bytes": len(raw), "model_requests": 0})
    grade = {"passed": result["status"] == expected["status"], "expected_status": expected["status"], "observed_status": result["status"]}
    if grade["passed"] and name == "normal":
        grade["passed"] = result["answer"] == expected["answer"]
    folder = Path(output) / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "raw.sse").write_bytes(raw)
    (folder / "answer.sse").write_bytes(raw_final)
    for filename, value in (("result.json", result), ("grade.json", grade)):
        (folder / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    (folder / "trace.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in trace))
    return grade


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    names = list(json.loads((FIXTURES / "expected.json").read_text()))
    parser.add_argument("--scenario", choices=["all"] + names, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/model_protocol"))
    args = parser.parse_args(argv)
    reports = {name: run_scenario(name, args.output) for name in names if args.scenario in {"all", name}}
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0 if all(report["passed"] for report in reports.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
