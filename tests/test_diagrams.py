"""Reject misleading publication pairs and unsafe SVGs using isolated fixtures."""
from pathlib import Path
import tempfile
import unittest

from scripts.check_diagrams import FILES, check_diagrams, validate_svg


def sample(number):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" id="G{number}"
viewBox="0 0 440 600" role="img" aria-labelledby="title desc">
<title id="title">组件与反馈</title><desc id="desc">工具观察成为后续输入。</desc>
<defs><marker id="arrow"><path d="M0 0 L5 3 L0 6"/></marker></defs>
<path d="M10 20 V80" marker-end="url(#arrow)"/>
</svg>'''.encode()


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, number, content=None, pair=True):
        for dirname in ("diagrams/source", "website/assets/diagrams") if pair else ("diagrams/source",):
            target = self.root / dirname / FILES[number]
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
        self.assertEqual(result.diagrams, 8)


if __name__ == "__main__":
    unittest.main()
