#!/usr/bin/env python3
"""Audit authored reading locations, not generated copies or learning quality.

Diagram ownership is an enforceable publication rule. Repeated prose is only a
review queue: a shared definition is not automatically an editorial defect.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {"questions", "site", ".site-src", ".local", ".git", ".venv",
           ".venv-docs", "venv", "node_modules", "__pycache__", ".agents", ".codex"}
QUESTION = re.compile(r"^### (Q\d{3})\b", re.M)
INLINE = re.compile(r"!\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)\n]*)?\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"][^>]*>", re.I)
REFERENCE = re.compile(r"^ {0,3}\[([^\]\n]+)\]:\s*<?([^\s>]+)>?", re.M)
REFERENCE_IMAGE = re.compile(r"!\[([^\]\n]*)\](?:\[([^\]\n]*)\])?(?![\[(])")


def mask_code(text: str) -> str:
    """Preserve character offsets while ignoring fenced examples."""
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = marker[1]
            result.append(re.sub(r"[^\n]", " ", line))
        elif fence is not None:
            result.append(re.sub(r"[^\n]", " ", line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        else:
            result.append(line)
    return "".join(result)


def location(path: str, text: str, offset: int) -> dict:
    owner = path
    if path.startswith("docs/"):
        prior = list(QUESTION.finditer(text, 0, offset))
        if prior:
            owner = f"questions/{prior[-1][1]}.md"
    return {"owner": owner, "source": path, "line": text.count("\n", 0, offset) + 1}


def diagram_path(root: Path, source: Path, value: str) -> str | None:
    value = html.unescape(value.strip("<>"))
    url = urlsplit(value)
    if url.scheme or url.netloc:
        return None
    path = (source.parent / unquote(url.path)).resolve()
    try:
        relative = path.relative_to(root.resolve())
    except ValueError:
        return None
    if relative.parts[:3] != ("website", "assets", "diagrams") or relative.suffix.lower() not in {".png", ".svg"}:
        return None
    return relative.with_suffix(".png").as_posix()


def image_uses(root: Path, path: Path, text: str) -> list[dict]:
    masked = mask_code(text)
    references = {m[1].casefold(): m[2] for m in REFERENCE.finditer(masked)}
    matches = [(m.start(), m[1]) for regex in (INLINE, HTML_IMAGE) for m in regex.finditer(masked)]
    for match in REFERENCE_IMAGE.finditer(masked):
        key = (match[2] or match[1]).casefold()
        if key in references:
            matches.append((match.start(), references[key]))
    uses = []
    for offset, value in sorted(set(matches)):
        image = diagram_path(root, path, value)
        if image:
            uses.append({"asset": image, **location(path.relative_to(root).as_posix(), text, offset)})
    return uses


def prose_blocks(path: str, text: str) -> list[dict]:
    masked = mask_code(text)
    masked = re.sub(r"<!-- question-links:start -->[\s\S]*?<!-- question-links:end -->",
                    lambda m: re.sub(r"[^\n]", " ", m[0]), masked)
    result = []
    for match in re.finditer(r"\S[^\n]*(?:\n(?!\s*\n)[^\n]*)*", masked):
        block = match[0]
        if block.startswith(("#", "|", "<", "[!", "![")):
            continue
        normalized = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", block)
        normalized = re.sub(r"[\s*`]+", "", normalized)
        if len(normalized) >= 120:
            result.append({"text": normalized, **location(path, text, match.start())})
    return result


def repeated_prose(blocks: list[dict]) -> dict:
    exact = defaultdict(list)
    for block in blocks:
        exact[block["text"]].append({k: block[k] for k in ("owner", "source", "line")})
    duplicates = [{"excerpt": text[:180], "locations": places} for text, places in exact.items()
                  if len({p["owner"] for p in places}) > 1]
    # Character shingles find candidates despite punctuation or small edits.
    # The threshold is a review heuristic, never a semantic equivalence claim.
    unique = [b for b in blocks if len(exact[b["text"]]) == 1]
    shingles = [{b["text"][i:i + 5] for i in range(len(b["text"]) - 4)} for b in unique]
    postings, similarities = defaultdict(list), []
    for index, grams in enumerate(shingles):
        shared = Counter(previous for gram in grams for previous in postings[gram])
        for previous, overlap in shared.items():
            left, right = unique[previous], unique[index]
            if left["owner"] == right["owner"]:
                continue
            score = overlap / (len(grams) + len(shingles[previous]) - overlap)
            if score >= 0.85:
                similarities.append({"jaccard_5gram": round(score, 4),
                                     "left": left, "right": right})
        for gram in grams:
            postings[gram].append(index)
    return {"exact": duplicates, "similar_candidates": similarities}


def audit(root: Path, *, review_prose: bool = False) -> dict:
    root = root.resolve()
    config = json.loads((root / "diagrams/reading-owners.json").read_text())
    owners = config.get("owners")
    if config.get("version") != 1 or not isinstance(owners, dict):
        raise ValueError("unsupported diagram ownership configuration")
    uses, blocks = [], []
    for path in sorted(root.rglob("*.md")):
        if any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        text = path.read_text()
        uses.extend(image_uses(root, path, text))
        if review_prose:
            blocks.extend(prose_blocks(path.relative_to(root).as_posix(), text))
    by_asset = defaultdict(list)
    for use in uses:
        by_asset[use["asset"]].append(use)
    errors = []
    fingerprints = defaultdict(list)
    for asset, owner in owners.items():
        if not (root / owner).is_file() or not (root / asset).is_file():
            errors.append(f"missing declared owner or asset: {asset} -> {owner}")
        elif (root / asset).is_file():
            fingerprints[hashlib.sha256((root / asset).read_bytes()).hexdigest()].append(asset)
        occurrences = by_asset.get(asset, [])
        if len(occurrences) != 1 or occurrences[0]["owner"] != owner:
            places = ", ".join(f"{x['source']}:{x['line']} ({x['owner']})" for x in occurrences) or "none"
            errors.append(f"{asset} must be embedded once in {owner}; found {places}")
    for asset in sorted(by_asset.keys() - owners.keys()):
        errors.append(f"diagram has no declared reading owner: {asset}")
    for identical in fingerprints.values():
        if len(identical) > 1:
            errors.append("byte-identical diagrams need one canonical asset: " + ", ".join(identical))
    report = {"authored_image_occurrences": len(uses), "unique_assets": len(by_asset),
              "image_uses": uses, "errors": errors,
              "scope": "authored Markdown; questions/ and built-site aliases excluded"}
    if review_prose:
        report["prose_review"] = repeated_prose(blocks)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="enforce one primary reading location per diagram")
    parser.add_argument("--report", type=Path, help="write image inventory and prose-review candidates as JSON")
    args = parser.parse_args(argv)
    report = audit(args.root, review_prose=args.report is not None)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for error in report["errors"]:
        print(error)
    print(f"Content audit: {report['unique_assets']} diagrams, {report['authored_image_occurrences']} authored embeds; "
          f"{len(report['errors'])} ownership violations.")
    if args.report:
        prose = report["prose_review"]
        print(f"Prose review queue: {len(prose['exact'])} exact groups, "
              f"{len(prose['similar_candidates'])} similar pairs; not an automatic quality score.")
    return int(args.check and bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
