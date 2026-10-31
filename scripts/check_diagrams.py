#!/usr/bin/env python3
"""Check SVG semantic sketches and generated PNG publication assets; never repair."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import math
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

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
ADVANCED_FILES = {
    "A01": "advanced/A01-harness.svg",
    "A02": "advanced/A02-recovery.svg",
    "A03": "advanced/A03-context.svg",
    "A04": "advanced/A04-memory-time.svg",
    "A05": "advanced/A05-tool-routing.svg",
    "A06": "advanced/A06-evidence-loop.svg",
    "A07": "advanced/A07-control.svg",
    "A08": "advanced/A08-action-feedback.svg",
    "A09": "advanced/A09-evaluation.svg",
    "A10": "advanced/A10-critical-path.svg",
    "A11": "advanced/A11-trust-boundaries.svg",
    "A12": "advanced/A12-training.svg",
}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    diagrams: int = 0
    generated_images: int = 0


def validate_png(data: bytes) -> list[str]:
    """Check PNG structure, chunk checksums and usable illustration dimensions."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ["invalid PNG signature"]
    position = 8
    kinds = []
    while position < len(data):
        if len(data) - position < 12:
            return ["truncated PNG chunk"]
        length = struct.unpack_from(">I", data, position)[0]
        end = position + 12 + length
        if end > len(data):
            return ["truncated PNG chunk data"]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:end - 4]
        checksum = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != checksum:
            return ["PNG chunk checksum mismatch"]
        if not kinds and kind != b"IHDR":
            return ["PNG must begin with IHDR"]
        if kind == b"IHDR":
            if kinds or length != 13:
                return ["invalid PNG IHDR"]
            width, height = struct.unpack_from(">II", payload)
            if not (768 <= width <= 8192 and 768 <= height <= 8192):
                return [f"PNG dimensions must be 768–8192 px per side, got {width}x{height}"]
        kinds.append(kind)
        position = end
        if kind == b"IEND":
            if length or position != len(data):
                return ["invalid PNG ending"]
            break
    if b"IDAT" not in kinds or not kinds or kinds[-1] != b"IEND":
        return ["PNG needs image data and IEND"]
    return []


def check_generated_images(root: Path) -> tuple[list[str], int]:
    """The manifest opts in to the complete generated illustration collection."""
    manifest = root / "diagrams/imagegen-manifest.json"
    if not manifest.exists():
        return [], 0
    try:
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read imagegen manifest: {exc}"], 0
    if not isinstance(metadata, dict) or not isinstance(metadata.get("assets"), list):
        return ["imagegen manifest must contain an assets list"], 0
    expected = {f"G{number}": filename for number, filename in FILES.items()} | CONCEPT_FILES
    if any(isinstance(entry, dict) and entry.get("id") in ADVANCED_FILES
           for entry in metadata["assets"]):
        expected |= ADVANCED_FILES
    errors = []
    seen = set()
    count = 0
    for entry in metadata["assets"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
                or entry["id"] not in expected):
            errors.append("unexpected imagegen manifest entry")
            continue
        identity = entry["id"]
        if identity in seen:
            errors.append(f"duplicate imagegen manifest id: {identity}")
            continue
        seen.add(identity)
        sketch = expected[identity]
        image = str(Path(sketch).with_suffix(".png"))
        expected_path = f"website/assets/diagrams/{image}"
        if (entry.get("path") != expected_path
                or entry.get("semantic_source") != f"diagrams/source/{sketch}"):
            errors.append(f"incorrect imagegen publication/source path: {identity}")
            continue
        path = root / expected_path
        if not path.is_file():
            errors.append(f"missing generated image: {expected_path}")
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            errors.append(f"generated image escapes repository: {expected_path}")
            continue
        errors.extend(f"{expected_path}: {error}" for error in validate_png(path.read_bytes()))
        count += 1
    errors.extend(f"missing imagegen manifest entry: {identity}" for identity in sorted(expected.keys() - seen))
    return errors, count


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
    if names.intersection(ADVANCED_FILES.values()):
        required.update(ADVANCED_FILES.values())
    for name in sorted(required - names):
        result.errors.append(f"missing required diagram: {name}")
    numbers = ({name: n for n, name in FILES.items()}
               | {name: n for n, name in (CONCEPT_FILES | ADVANCED_FILES).items()})
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
    generated_errors, result.generated_images = check_generated_images(root)
    result.errors.extend(generated_errors)
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
    print(f"PASS diagrams ({args.suite}): {result.diagrams} SVG source/published pairs; "
          f"{result.generated_images} generated PNGs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
