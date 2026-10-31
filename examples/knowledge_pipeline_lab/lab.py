"""Real Markdown ingestion and lexical search, with inspectable generations.

Contract: one writer, local filesystem, immutable index files, atomic state pointer.
The effective-date interval is business time, NOT a bitemporal database.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


HERE = Path(__file__).resolve().parent
SCHEMA = "lexical-v1"
SCENARIOS = ("normal", "duplicate", "update", "interruption", "delete", "revoke", "switch", "invalid-source")


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_json(path, value):
    """Replace one JSON file; a reader sees the old or new complete file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def terms(text):
    """ASCII words plus individual Han characters; no semantic embeddings."""
    return re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower())


def validate_date(value):
    """Require the canonical representation used by lexical date comparisons."""
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("business date must use YYYY-MM-DD")
    return value


def parse_markdown(text, doc_key, source_uri):
    """Parse a documented subset: headings, marked paragraphs, simple tables.

    Each payload needs an explicit <!-- block: stable-key --> marker. Tables
    require a first column named 条款ID. That cell supplies stable row identity.
    Escaped pipes, merged cells, fenced code and multiline cells are unsupported.
    """
    lines = text.splitlines()
    heading = []
    pending = None
    blocks = []
    identities = set()
    i = 0

    def add(local_key, body, first, last):
        if local_key in identities:
            raise ValueError("duplicate block identity: " + local_key)
        identities.add(local_key)
        blocks.append({
            "block_id": digest([doc_key, local_key])[:24], "local_key": local_key,
            "text": " / ".join(heading) + "\n" + body,
            "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(), "line_start": first, "line_end": last,
            "source_uri": source_uri, "source_location": f"{source_uri}#L{first}-L{last}",
        })

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("#"):
            match = re.fullmatch(r"(#{1,6})\s+(.+)", line)
            if not match:
                raise ValueError("unsupported heading")
            depth = len(match[1])
            heading = heading[:depth - 1] + [match[2]]
            i += 1
            continue
        marker = re.fullmatch(r"<!-- block: ([a-zA-Z0-9_-]+) -->", line)
        if marker:
            if pending is not None:
                raise ValueError("unused block marker")
            pending = marker[1]
            i += 1
            continue
        if pending is None:
            raise ValueError(f"payload without stable block marker at line {i + 1}")
        start = i
        if line.startswith("|"):
            def cells(row):
                if "\\|" in row or not row.strip().endswith("|"):
                    raise ValueError("only simple pipe tables are supported")
                return [cell.strip() for cell in row.strip().strip("|").split("|")]
            headers = cells(lines[i])
            if not headers or headers[0] != "条款ID" or i + 1 >= len(lines):
                raise ValueError("table must begin with 条款ID")
            separators = cells(lines[i + 1])
            if len(separators) != len(headers) or not all(re.fullmatch(r":?-{3,}:?", s) for s in separators):
                raise ValueError("invalid table separator")
            i += 2
            row_count = 0
            while i < len(lines) and lines[i].strip().startswith("|"):
                values = cells(lines[i])
                if len(values) != len(headers) or not values[0]:
                    raise ValueError("invalid table row")
                body = "；".join(f"{key}：{value}" for key, value in zip(headers, values))
                # The lineage spans the header and current row; the text repeats
                # the actual header labels, so the amount keeps its meaning.
                add(pending + "/" + values[0], body, start + 1, i + 1)
                row_count += 1
                i += 1
            if not row_count:
                raise ValueError("empty table")
        else:
            if line.startswith("```") or line.startswith("<!--"):
                raise ValueError("unsupported Markdown construct")
            body_lines = []
            while i < len(lines) and lines[i].strip():
                if lines[i].strip().startswith(("#", "<!--", "|", "```")):
                    break
                body_lines.append(lines[i].strip())
                i += 1
            if not body_lines:
                raise ValueError("empty paragraph")
            add(pending, " ".join(body_lines), start + 1, i)
        pending = None
    if pending is not None or not blocks:
        raise ValueError("unused marker or empty source")
    return blocks


class Pipeline:
    """Single-writer store; ACL/tombstones are checked even for pinned indices."""

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.events = []

    def state(self):
        path = self.root / "state.json"
        return read_json(path) if path.exists() else {"generation": None, "catalog": {}, "policy_revision": 0}

    def generation(self, generation=None):
        selected = generation or self.state()["generation"]
        if not selected:
            return {"schema": SCHEMA, "documents": {}, "postings": {}}
        result = read_json(self.root / "generations" / (selected + ".json"))
        if result["schema"] != SCHEMA:
            raise ValueError("unsupported index schema; rebuild before activation")
        return result

    def publish(self, sources, fail_after=None):
        """Ingest a COMPLETE source manifest; omitted keys become tombstones.

        Unchanged source fingerprints reuse existing parsed objects. A durable
        staging journal allows a new Pipeline instance to resume interrupted
        parsing. Nothing is queryable until state.json is replaced last.
        """
        normalized = {}
        for source in sources:
            source = dict(source)
            required = ("doc_id", "version", "path", "source_uri", "valid_from", "access")
            if any(key not in source for key in required):
                raise ValueError("source missing identity, date, location or access")
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", source["doc_id"]) or not re.fullmatch(r"[a-zA-Z0-9_-]+", source["version"]):
                raise ValueError("invalid source identity")
            validate_date(source["valid_from"])
            if source.get("valid_to") is not None:
                validate_date(source["valid_to"])
                if source["valid_to"] <= source["valid_from"]:
                    raise ValueError("empty or reversed validity interval")
            if not isinstance(source["access"], list) or not all(isinstance(p, str) for p in source["access"]):
                raise ValueError("access must be a list of trusted principal labels")
            text = Path(source["path"]).read_bytes().decode("utf-8")
            metadata = {key: source.get(key) for key in ("doc_id", "version", "source_uri", "valid_from", "valid_to", "access")}
            metadata["access"] = sorted(set(metadata["access"]))
            key = source["doc_id"] + "@" + source["version"]
            entry = {"metadata": metadata, "source_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "text": text}
            entry["fingerprint"] = digest([SCHEMA, metadata, entry["source_hash"]])
            if key in normalized and normalized[key]["fingerprint"] != entry["fingerprint"]:
                raise ValueError("conflicting duplicate source version: " + key)
            normalized[key] = entry
        # One active business version per document and date. Reject ambiguity.
        keys = sorted(normalized)
        for position, key in enumerate(keys):
            a = normalized[key]["metadata"]
            for other in keys[position + 1:]:
                b = normalized[other]["metadata"]
                if a["doc_id"] == b["doc_id"] and max(a["valid_from"], b["valid_from"]) < min(a["valid_to"] or "9999-12-31", b["valid_to"] or "9999-12-31"):
                    raise ValueError("overlapping effective dates")
        generation_id = digest([[key, normalized[key]["fingerprint"]] for key in keys])[:24]
        journal_path = self.root / "staging" / (generation_id + ".json")
        journal = read_json(journal_path) if journal_path.exists() else {"generation": generation_id, "documents": {}}
        state = self.state()
        previous = self.generation(state["generation"])["documents"]
        documents = {}
        stats = {"parsed": 0, "reused": 0, "resumed": 0, "removed": len(set(previous) - set(keys))}
        self.events.append({"event": "build_started", "candidate": generation_id, "previous": state["generation"]})
        for key in keys:
            entry = normalized[key]
            if key in previous and previous[key]["fingerprint"] == entry["fingerprint"]:
                document = previous[key]
                stats["reused"] += 1
            elif key in journal["documents"] and journal["documents"][key]["fingerprint"] == entry["fingerprint"]:
                document = journal["documents"][key]
                stats["resumed"] += 1
            else:
                document = {"metadata": entry["metadata"], "source_hash": entry["source_hash"], "source_text": entry["text"], "fingerprint": entry["fingerprint"],
                            "blocks": parse_markdown(entry["text"], key, entry["metadata"]["source_uri"])}
                stats["parsed"] += 1
                journal["documents"][key] = document
                atomic_json(journal_path, journal)
                self.events.append({"event": "document_staged", "key": key, "source_hash": entry["source_hash"]})
                if fail_after is not None and stats["parsed"] >= fail_after:
                    self.events.append({"event": "injected_crash", "visible_generation": state["generation"]})
                    raise InterruptedError("injected interruption before publication")
            documents[key] = document
        postings = {}
        for key, document in documents.items():
            for block in document["blocks"]:
                for term, count in Counter(terms(block["text"])).items():
                    postings.setdefault(term, {})[block["block_id"]] = {"document": key, "count": count}
        candidate = {"schema": SCHEMA, "generation": generation_id, "documents": documents, "postings": postings}
        # Serialize and parse once before making the pointer visible.
        target = self.root / "generations" / (generation_id + ".json")
        atomic_json(target, candidate)
        self.generation(generation_id)
        catalog = {key: {"doc_id": value["metadata"]["doc_id"], "access": value["metadata"]["access"]} for key, value in documents.items()}
        atomic_json(self.root / "state.json", {"generation": generation_id, "catalog": catalog, "policy_revision": state["policy_revision"] + 1})
        self.events.append({"event": "published", "generation": generation_id, **stats})
        return {"generation": generation_id, "document_count": len(documents), "block_count": sum(len(d["blocks"]) for d in documents.values()), **stats}

    def revoke(self, doc_id, principal):
        state = self.state()
        for entry in state["catalog"].values():
            if entry["doc_id"] == doc_id:
                entry["access"] = [p for p in entry["access"] if p != principal]
        state["policy_revision"] += 1
        atomic_json(self.root / "state.json", state)
        self.events.append({"event": "access_revoked", "doc_id": doc_id, "principal": principal, "policy_revision": state["policy_revision"]})

    def activate(self, generation):
        self.generation(generation)  # reject missing/incompatible generations
        state = self.state()
        state["generation"] = generation
        # Current access and deletion policy deliberately survive rollback.
        atomic_json(self.root / "state.json", state)
        self.events.append({"event": "activated", "generation": generation, "policy_revision": state["policy_revision"]})

    def query(self, text, at, principal, generation=None):
        validate_date(at)
        state = self.state()  # read once for one consistent policy snapshot
        index = self.generation(generation or state["generation"])
        wanted = set(terms(text))
        if not wanted:
            return []
        posting_sets = [set(index["postings"].get(term, {})) for term in wanted]
        candidates = set.intersection(*posting_sets)
        results = []
        for key, document in index["documents"].items():
            meta = document["metadata"]
            policy = state["catalog"].get(key)
            if not policy or principal not in policy["access"]:
                continue
            if not (meta["valid_from"] <= at and (meta["valid_to"] is None or at < meta["valid_to"])):
                continue
            for block in document["blocks"]:
                if block["block_id"] in candidates:
                    score = sum(index["postings"][term][block["block_id"]]["count"] for term in wanted)
                    results.append({**block, "source_hash": document["source_hash"], "doc_id": meta["doc_id"], "version": meta["version"], "valid_from": meta["valid_from"], "valid_to": meta["valid_to"], "policy_revision": state["policy_revision"], "generation": index["generation"], "score": score})
        results.sort(key=lambda row: (-row["score"], row["block_id"]))
        self.events.append({"event": "query", "at": at, "principal": principal, "generation": index.get("generation"), "policy_revision": state["policy_revision"], "returned": [r["block_id"] for r in results]})
        return results


def fixture_sources(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for source in (HERE / "data").glob("*.md"):
        shutil.copyfile(source, directory / source.name)
    sources = read_json(HERE / "data" / "manifest.json")
    return [{**source, "path": str(directory / source["file"])} for source in sources]


def change_amount(sources, before="700", after="720"):
    path = Path(next(source["path"] for source in sources if source["version"] == "v2"))
    path.write_text(path.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")


def exercise(scenario, root):
    sources = fixture_sources(Path(root) / "sources")
    pipeline = Pipeline(Path(root) / "store")
    first = pipeline.publish(sources)
    observation = {"initial": first}
    query = lambda at="2026-11-12", principal="employee", generation=None: pipeline.query("海岚 住宿 上限", at, principal, generation)
    if scenario == "normal":
        observation.update(old=query("2026-10-31"), current=query(), private=pipeline.query("财务", "2026-11-12", "employee"))
    elif scenario == "duplicate":
        observation["second"] = pipeline.publish(sources + sources)
        observation["current"] = query()
    elif scenario == "update":
        observation["before"] = query()
        change_amount(sources)
        observation["second"] = pipeline.publish(sources)
        observation["current"] = query()
    elif scenario == "interruption":
        change_amount(sources, after="730")
        private_path = Path(next(source["path"] for source in sources if source["doc_id"] == "finance-private"))
        private_path.write_text(private_path.read_text(encoding="utf-8") + "\n<!-- block: revision -->\n内部修订记录。\n", encoding="utf-8")
        try:
            pipeline.publish(sources, fail_after=1)
        except InterruptedError:
            observation["interrupted"] = True
        observation["during"] = query()
        before_events = pipeline.events
        pipeline = Pipeline(Path(root) / "store")  # a fresh process can reload the journal
        pipeline.events = before_events
        observation["second"] = pipeline.publish(sources)
        observation["current"] = query()
    elif scenario == "delete":
        observation["second"] = pipeline.publish([s for s in sources if s["version"] != "v2"])
        observation.update(current=query(), pinned=query(generation=first["generation"]), old=query("2026-10-31"))
    elif scenario == "revoke":
        change_amount(sources)
        pipeline.publish(sources)
        pipeline.revoke("lodging-hailan", "employee")
        observation["current"] = query()
        observation["pinned"] = query(generation=first["generation"])
        pipeline.activate(first["generation"])
        observation.update(rolled_back=query(), admin=query(principal="admin"))
    elif scenario == "switch":
        change_amount(sources)
        observation["second"] = pipeline.publish(sources)
        observation["updated"] = query()
        pipeline.activate(first["generation"])
        observation["current"] = query()
    elif scenario == "invalid-source":
        broken = [dict(s) for s in sources]
        broken[0].pop("valid_from")
        try:
            pipeline.publish(broken)
        except ValueError as error:
            observation["rejected"] = str(error)
        observation["generation_unchanged"] = pipeline.state()["generation"] == first["generation"]
        observation["current"] = query()
    return observation, pipeline.events


def grade(scenario, observation):
    """Read independent fixture expectations only AFTER ingestion/querying."""
    expected = read_json(HERE / "data" / "expected.json")
    contains = lambda rows, amount: len(rows) == 1 and f"金额上限：{amount}" in rows[0]["text"]
    checks = {"source_documents": observation["initial"]["document_count"] == expected["document_count"]}
    if scenario == "normal":
        checks.update(old_version=contains(observation["old"], expected["old_limit"]), current_version=contains(observation["current"], expected["current_limit"]), access_filtered=not observation["private"], source_location=all(r["line_end"] >= r["line_start"] > 0 and "城市：海岚" in r["text"] for r in observation["current"]))
    elif scenario == "duplicate":
        second = observation["second"]
        checks.update(no_duplicates=second["block_count"] == observation["initial"]["block_count"], all_reused=second["reused"] == expected["document_count"] and second["parsed"] == 0, same_generation=second["generation"] == observation["initial"]["generation"])
    elif scenario == "update":
        checks.update(only_changed_document=observation["second"]["parsed"] == 1 and observation["second"]["reused"] == 2, new_value=contains(observation["current"], expected["updated_limit"]), stable_block=observation["before"][0]["block_id"] == observation["current"][0]["block_id"], changed_hash=observation["before"][0]["content_hash"] != observation["current"][0]["content_hash"])
    elif scenario == "interruption":
        checks.update(interruption_injected=observation.get("interrupted", False), no_partial_exposure=contains(observation["during"], expected["current_limit"]), resumed_from_disk=observation["second"]["resumed"] == 1, new_value=contains(observation["current"], expected["resumed_limit"]))
    elif scenario == "delete":
        checks.update(current_deleted=not observation["current"], pinned_also_filtered=not observation["pinned"], historical_retained=contains(observation["old"], expected["old_limit"]))
    elif scenario == "revoke":
        checks.update(current_revoked=not observation["current"], pinned_revoked=not observation["pinned"], rollback_keeps_revocation=not observation["rolled_back"], allowed_admin=contains(observation["admin"], expected["current_limit"]))
    elif scenario == "switch":
        checks.update(updated=contains(observation["updated"], expected["updated_limit"]), coherent_rollback=contains(observation["current"], expected["current_limit"]))
    elif scenario == "invalid-source":
        checks.update(invalid_date_rejected=bool(observation.get("rejected")), no_publication=observation["generation_unchanged"], old_still_readable=contains(observation["current"], expected["current_limit"]))
    return {"scenario": scenario, "passed": all(checks.values()), "checks": checks, "evidence_level": "local-real-lexical-index"}


def run_scenario(scenario, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # Each invocation owns a fresh workspace, while evidence files stay readable.
    with tempfile.TemporaryDirectory(prefix="knowledge-work-", dir=output) as temporary:
        observation, events = exercise(scenario, temporary)
        shutil.copytree(Path(temporary) / "store", output / "store", dirs_exist_ok=True)
        shutil.copytree(Path(temporary) / "sources", output / "sources", dirs_exist_ok=True)
    evaluation = grade(scenario, observation)
    atomic_json(output / "result.json", observation)
    atomic_json(output / "grade.json", evaluation)
    (output / "trace.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
    return evaluation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all",) + SCENARIOS, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/knowledge_pipeline_lab"))
    args = parser.parse_args(argv)
    selected = SCENARIOS if args.scenario == "all" else (args.scenario,)
    reports = [run_scenario(name, args.output / name) for name in selected]
    summary = {"passed": all(r["passed"] for r in reports), "scenarios": reports, "evidence_level": "local-real-lexical-index", "model_calls": 0}
    atomic_json(args.output / "result.json", summary)
    atomic_json(args.output / "grade.json", {"passed": summary["passed"], "scenarios": len(reports)})
    (args.output / "trace.jsonl").write_text("".join(json.dumps({"scenario": r["scenario"], "passed": r["passed"]}, ensure_ascii=False) + "\n" for r in reports), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
