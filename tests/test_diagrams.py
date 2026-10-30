"""Reject misleading publication pairs and unsafe SVGs using isolated fixtures."""
from pathlib import Path
import json
import struct
import tempfile
import unittest
import zlib

from scripts.check_diagrams import (CONCEPT_FILES, FILES, check_diagrams,
                                    check_generated_images, validate_png, validate_svg)


def sample(number):
    label = f"G{number}" if isinstance(number, int) else number
    return f'''<svg xmlns="http://www.w3.org/2000/svg" id="{label}"
viewBox="0 0 440 600" role="img" aria-labelledby="title desc">
<title id="title">组件与反馈</title><desc id="desc">工具观察成为后续输入。</desc>
<defs><marker id="arrow"><path d="M0 0 L5 3 L0 6"/></marker></defs>
<path d="M10 20 V80" marker-end="url(#arrow)"/>
</svg>'''.encode()


def png(width=1024, height=1024):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + b"\xff" * width * 3) * height))
            + chunk(b"IEND", b""))


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, number, content=None, pair=True):
        for dirname in ("diagrams/source", "website/assets/diagrams") if pair else ("diagrams/source",):
            filename = FILES[number] if isinstance(number, int) else CONCEPT_FILES[number]
            target = self.root / dirname / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content if content is not None else sample(number))

    def test_pilot_needs_only_first_two_delivered_figures(self):
        self.write(1)
        self.write(3)
        result = check_diagrams(self.root, "pilot")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.diagrams, 2)
        self.assertEqual(len(check_diagrams(self.root, "all").errors), 6)

    def test_optional_existing_figure_still_needs_pair_in_pilot(self):
        self.write(1)
        self.write(3)
        self.write(2, pair=False)
        self.assertIn("missing source/published pair", "\n".join(check_diagrams(self.root, "pilot").errors))

    def test_publication_drift_fails_without_repairing_files(self):
        self.write(1)
        self.write(3)
        target = self.root / "website/assets/diagrams" / FILES[1]
        changed = sample(1).replace("组件".encode(), "改动".encode())
        target.write_bytes(changed)
        self.assertIn("bytes differ", "\n".join(check_diagrams(self.root, "pilot").errors))
        self.assertEqual(target.read_bytes(), changed)

    def test_duplicate_ids_and_wrong_number_fail(self):
        self.assertIn("root id must match", "\n".join(validate_svg(sample(2), 1)))
        data = sample(1).replace(b'</svg>', b'<g id="arrow"/></svg>')
        self.assertIn("duplicate id", "\n".join(validate_svg(data, 1)))

    def test_malformed_xml_and_entity_declarations_fail(self):
        self.assertIn("invalid XML", "\n".join(validate_svg(b'<svg>', 1)))
        self.assertIn("DOCTYPE/ENTITY", "\n".join(validate_svg(b'<!DOCTYPE svg>'+sample(1), 1)))

    def test_missing_accessible_description_and_invalid_viewbox_fail(self):
        data = sample(1).replace(b'<desc id="desc">', b'<desc id="desc">').replace("工具观察成为后续输入。".encode(), b'')
        self.assertIn("missing nonempty desc", "\n".join(validate_svg(data, 1)))
        for bounds in (b'0 0 0 600', b'0 0 NaN 600', b'0 0 440'):
            with self.subTest(bounds=bounds):
                self.assertIn("viewBox", "\n".join(validate_svg(sample(1).replace(b'0 0 440 600', bounds), 1)))

    def test_all_external_resource_channels_are_rejected(self):
        additions = (
            b'<image href="https://example.org/image.png"/>',
            b'<image xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="data:image/png,a"/>',
            b'<rect fill="url(https://example.org/pattern.svg)"/>',
            b'<style>@import "https://example.org/style.css";</style>',
            b'<style>text{fill:url(https://example.org/fill.svg)}</style>',
        )
        for addition in additions:
            with self.subTest(addition=addition):
                self.assertTrue(validate_svg(sample(1).replace(b'</svg>', addition+b'</svg>'), 1))

    def test_local_reference_must_resolve(self):
        self.assertEqual(validate_svg(sample(1), 1), [])
        self.assertIn("missing local resource", "\n".join(validate_svg(sample(1).replace(b'url(#arrow)', b'url(#gone)'), 1)))

    def test_static_only_and_no_event_handlers(self):
        for addition in (b'<script>alert(1)</script>', b'<foreignObject/>', b'<animate/>', b'<g onload="alert(1)"/>'):
            with self.subTest(addition=addition):
                self.assertTrue(validate_svg(sample(1).replace(b'</svg>', addition+b'</svg>'), 1))

    def test_complete_real_repository_contract(self):
        result = check_diagrams(Path(__file__).resolve().parents[1], "all")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.diagrams, 8 + len(CONCEPT_FILES))
        self.assertEqual(result.generated_images, 14)

    def test_concept_group_is_checked_recursively_and_requires_complete_pairs(self):
        self.write(1)
        self.write(3)
        self.assertEqual(check_diagrams(self.root, "pilot").errors, [])
        self.write("C1", pair=False)
        errors = "\n".join(check_diagrams(self.root, "pilot").errors)
        self.assertIn("missing source/published pair: concepts/C1-capability-map.svg", errors)
        self.assertIn("missing required diagram: concepts/C2-model-context.svg", errors)
        for label in CONCEPT_FILES:
            self.write(label)
        result = check_diagrams(self.root, "pilot")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.diagrams, 8)


class GeneratedImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def manifest(self):
        expected = {f"G{number}": filename for number, filename in FILES.items()} | CONCEPT_FILES
        metadata = {"assets": []}
        for identity, name in expected.items():
            path = "website/assets/diagrams/" + str(Path(name).with_suffix(".png"))
            metadata["assets"].append({"id": identity, "path": path,
                                       "semantic_source": "diagrams/source/" + name})
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(png())
        self.save(metadata)
        return metadata

    def save(self, metadata):
        path = self.root / "diagrams/imagegen-manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metadata), encoding="utf-8")

    def test_png_rejects_wrong_signature_truncation_and_corrupt_chunks(self):
        data = png()
        self.assertEqual(validate_png(data), [])
        self.assertIn("signature", " ".join(validate_png(b"not a png")))
        self.assertIn("truncated", " ".join(validate_png(data[:-3])))
        damaged = data[:40] + bytes([data[40] ^ 1]) + data[41:]
        self.assertIn("checksum", " ".join(validate_png(damaged)))
        self.assertIn("dimensions", " ".join(validate_png(png(100, 100))))

    def test_manifest_covers_all_assets_and_detects_missing_nested_image(self):
        metadata = self.manifest()
        self.assertEqual(check_generated_images(self.root), ([], 14))
        (self.root / metadata["assets"][-1]["path"]).unlink()
        errors, count = check_generated_images(self.root)
        self.assertEqual(count, 13)
        self.assertIn("missing generated image", "\n".join(errors))

    def test_manifest_rejects_duplicate_entries_and_unexpected_paths(self):
        metadata = self.manifest()
        metadata["assets"][0]["path"] = "../outside.png"
        metadata["assets"].append(metadata["assets"][1])
        metadata["assets"].pop(2)
        self.save(metadata)
        errors, _ = check_generated_images(self.root)
        self.assertIn("incorrect imagegen publication/source path", "\n".join(errors))
        self.assertIn("duplicate imagegen manifest id", "\n".join(errors))
        self.assertIn("missing imagegen manifest entry: G3", "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
