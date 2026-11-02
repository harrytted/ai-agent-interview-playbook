"""Exercise published diagram structure with isolated local image fixtures."""
from html.parser import HTMLParser
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

from website import hooks


class Content(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.nodes = []
        self.parents = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs), tuple(self.parents)))
        if tag not in {"img", "br", "hr", "input", "meta", "link", "source"}:
            self.parents.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.parents and self.parents[-1] == tag:
            self.parents.pop()

    def handle_endtag(self, tag):
        if tag in self.parents:
            self.parents = self.parents[:len(self.parents) - 1 - self.parents[::-1].index(tag)]

    def elements(self, tag):
        return [(attrs, parents) for name, attrs, parents in self.nodes if name == tag]


class SiteHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name)
        (self.docs / "assets").mkdir()
        # The hook reads only the PNG signature and IHDR dimensions.
        self.image = self.docs / "assets/flow.png"
        self.image.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + struct.pack(">II", 1536, 1024))
        self.src = "../../assets/flow.png"
        self.page = SimpleNamespace(file=SimpleNamespace(dest_uri="learning/chapter/index.html"))

    def render(self, html):
        return hooks.on_page_content(html, page=self.page, config={"docs_dir": self.docs}, files=None)

    def linked(self, src=None, extra=""):
        src = self.src if src is None else src
        return f'<p><a href="{src}"><img alt="模型 &amp; 工具" src="{src}" {extra}/></a></p>'

    def test_linked_diagrams_have_a_keyboard_scroll_region_and_keep_image_contracts(self):
        result = self.render(self.linked() + self.linked())
        content = Content(result)
        self.assertEqual(len(content.elements("figure")), 2)
        regions = content.elements("div")
        self.assertEqual(len(regions), 2)
        for attrs, parents in regions:
            self.assertEqual(attrs["role"], "region")
            self.assertEqual(attrs["tabindex"], "0")
            self.assertIn("aria-label", attrs)
            self.assertEqual(parents, ("figure",))
        for index, (attrs, parents) in enumerate(content.elements("img")):
            self.assertEqual(parents, ("figure", "div", "a"))
            self.assertEqual(attrs["src"], self.src)
            self.assertEqual(attrs["alt"], "模型 & 工具")
            self.assertEqual((attrs["width"], attrs["height"]), ("1536", "1024"))
            self.assertEqual(attrs["loading"], "eager" if index == 0 else "lazy")
            self.assertEqual(attrs["decoding"], "async")
        self.assertEqual([attrs["href"] for attrs, _ in content.elements("a")], [self.src, self.src])
        self.assertEqual(len(content.elements("figcaption")), 2)

    def test_navigation_images_inline_images_and_other_paragraph_content_stay_in_place(self):
        html = (
            f'<p><a href="../next/"><img src="{self.src}" alt="next"></a></p>'
            f'<p>参照 <a href="{self.src}"><img src="{self.src}" alt="inline"></a> 继续阅读。</p>'
            + self.linked("https://example.org/flow.png")
        )
        result = self.render(html)
        content = Content(result)
        self.assertEqual(content.elements("figure"), [])
        self.assertEqual(content.elements("a")[0][0]["href"], "../next/")
        self.assertIn("继续阅读。", result)
        self.assertNotIn("width", content.elements("img")[-1][0])

    def test_missing_invalid_or_outside_images_are_not_promoted_to_diagrams(self):
        (self.docs / "assets/bad.png").write_bytes(b"not a png")
        for src in ("../../assets/missing.png", "../../assets/bad.png", "../../../outside.png"):
            with self.subTest(src=src):
                original = self.linked(src)
                self.assertEqual(self.render(original), original)

    def test_existing_image_attributes_and_repeated_hooks_are_preserved(self):
        result = self.render(self.linked(extra='width="600" loading="lazy"'))
        attrs = Content(result).elements("img")[0][0]
        self.assertEqual(attrs["width"], "600")
        self.assertEqual(attrs["loading"], "lazy")
        self.assertEqual(self.render(result), result)


if __name__ == "__main__":
    unittest.main()
