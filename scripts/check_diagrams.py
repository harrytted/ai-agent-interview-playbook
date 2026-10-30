#!/usr/bin/env python3
"""Check the editable SVG sources and their exact published copies; never repair."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
FILES = {
    1: "G1-system-flow.svg",
    2: "G2-model-output.svg",
    3: "G3-tool-roundtrip.svg",
    4: "G4-mcp-connections.svg",
    5: "G5-rag-pipelines.svg",
    6: "G6-state-memory.svg",
    7: "G7-planning-compare.svg",
    8: "G8-write-recovery.svg",
}
CONCEPT_FILES = {
    "C1": "concepts/C1-capability-map.svg",
    "C2": "concepts/C2-model-context.svg",
    "C3": "concepts/C3-tool-interface.svg",
    "C4": "concepts/C4-memory-context.svg",
    "C5": "concepts/C5-planning-feedback.svg",
    "C6": "concepts/C6-runtime-boundary.svg",
}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    diagrams: int = 0


def validate_svg(data: bytes, number: int | str) -> list[str]:
    """Validate local SVG only, with accessible text and no executable/external parts."""
    errors: list[str] = []
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["SVG is not UTF-8"]
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.I):
        return ["DOCTYPE/ENTITY is forbidden"]
    try:
        svg = ET.fromstring(source)
    except ET.ParseError as exc:
        return [f"invalid XML: {exc}"]
    if svg.tag != f"{{{SVG_NS}}}svg":
        errors.append("root must be an SVG element with the SVG namespace")
    label = f"G{number}" if isinstance(number, int) else number
    if svg.get("id") != label:
        errors.append(f"root id must match diagram number {label}")
    try:
        bounds = [float(item) for item in re.split(r"[\s,]+", svg.get("viewBox", "").strip())]
        if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds) or min(bounds[2:]) <= 0:
            raise ValueError
    except ValueError:
        errors.append("viewBox must contain four finite numbers with positive width/height")

    ids = Counter(el.get("id") for el in svg.iter() if el.get("id"))
    for identifier, count in ids.items():
        if count > 1:
            errors.append(f"duplicate id: {identifier}")
    metadata_ids = set()
    for tag in ("title", "desc"):
        el = svg.find(f"{{{SVG_NS}}}{tag}")
        if el is None or not "".join(el.itertext()).strip():
            errors.append(f"missing nonempty {tag}")
        elif not el.get("id"):
            errors.append(f"{tag} must have an id")
        else:
            metadata_ids.add(el.get("id"))
    if svg.get("role") != "img" or not metadata_ids.issubset(set(svg.get("aria-labelledby", "").split())):
        errors.append("role=img and aria-labelledby must reference title and desc")

    refs = []
    for el in svg.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag.lower() in {"script", "foreignobject", "iframe", "animate", "animatetransform", "set"}:
            errors.append(f"non-static or executable element: {tag}")
        for key, value in el.attrib.items():
            attr = key.rsplit("}", 1)[-1]
            if attr.lower().startswith("on"):
                errors.append(f"executable event attribute: {attr}")
            if attr in {"href", "src"}:
                refs.append(value.strip())
            for match in re.findall(r"url\s*\(\s*([^)]*?)\s*\)", value, re.I):
                refs.append(match.strip("\"' "))
        if tag == "style":
            style = "".join(el.itertext())
            if re.search(r"@import\b|@font-face\b", style, re.I):
                errors.append("external CSS imports/fonts are forbidden")
            refs.extend(item.strip("\"' ") for item in re.findall(r"url\s*\(\s*([^)]*?)\s*\)", style, re.I))
    for ref in refs:
        if not ref.startswith("#"):
            errors.append(f"external resource forbidden: {ref}")
        elif ref[1:] not in ids:
            errors.append(f"missing local resource: {ref}")
    return errors


def check_diagrams(root: Path = ROOT, suite: str = "all") -> Result:
    if suite not in {"pilot", "all"}:
        raise ValueError("suite must be pilot or all")
    source = root / "diagrams/source"
    published = root / "website/assets/diagrams"
    result = Result()
    required = {FILES[n] for n in ({1, 3} if suite == "pilot" else FILES)}
    names = {p.relative_to(directory).as_posix() for directory in (source, published) for p in directory.rglob("*.svg")}
    if names.intersection(CONCEPT_FILES.values()):
        required.update(CONCEPT_FILES.values())
    for name in sorted(required - names):
        result.errors.append(f"missing required diagram: {name}")
    numbers = {name: n for n, name in FILES.items()} | {name: n for n, name in CONCEPT_FILES.items()}
    for name in sorted(names):
        if name not in numbers:
            result.errors.append(f"unexpected diagram filename/number: {name}")
            continue
        paths = (source / name, published / name)
        if not all(p.is_file() for p in paths):
            result.errors.append(f"missing source/published pair: {name}")
            continue
        if any(not p.resolve().is_relative_to(root.resolve()) for p in paths):
            result.errors.append(f"diagram escapes repository: {name}")
            continue
        data = [p.read_bytes() for p in paths]
        if data[0] != data[1]:
            result.errors.append(f"source/published bytes differ: {name}")
        for label, value in zip(("source", "published"), data):
            result.errors.extend(f"{name} ({label}): {err}" for err in validate_svg(value, numbers[name]))
        result.diagrams += 1
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("pilot", "all"), default="all")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (also used by isolated tests)")
    args = parser.parse_args(argv)
    result = check_diagrams(args.root, args.suite)
    if result.errors:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    print(f"PASS diagrams ({args.suite}): {result.diagrams} exact source/published pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
