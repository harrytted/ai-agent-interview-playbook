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


class ChapterNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = {
            "docs_dir": self.temp.name,
            "nav": [
                {"基础原理": ["learning/index.md",
                            {"09 · 评测": "learning/09-evaluation.md"},
                            {"10 · 可靠性": "learning/10-reliability-and-security.md"}]},
                {"工程进阶": [{"目录": "advanced/index.md"},
                            {"01 · Harness": "advanced/01-harness.md"},
                            {"02 · 持久执行": "advanced/02-durable.md"},
                            {"03 · 上下文工程": "advanced/03-context.md"}]},
                {"练习": [{"试读": "learning/00-first-agent.md"}]},
            ],
        }
        sources = ["learning/index.md", "advanced/index.md", "learning/00-first-agent.md",
                   "learning/09-evaluation.md", "learning/10-reliability-and-security.md",
                   "advanced/01-harness.md", "advanced/02-durable.md", "advanced/03-context.md"]
        self.targets = {source: SimpleNamespace(
            url=source.replace("index.md", "").removesuffix(".md") +
            ("" if source.endswith("index.md") else "/")) for source in sources}
        self.files = SimpleNamespace(get_file_from_path=self.targets.get)

    def render(self, source, html="<h1>正文</h1><p>原理讲解。</p>", hidden=None):
        self.page = SimpleNamespace(
            file=SimpleNamespace(src_uri=source, dest_uri=source.removesuffix(".md") + "/index.html"),
            meta={"hide": list(hidden or [])})
        return hooks.on_page_content(html, page=self.page, config=self.config, files=self.files)

    def test_middle_chapter_has_one_footer_after_exercises_and_keeps_prose_links(self):
        html = ('<h1>正文</h1><p><a href="../01-harness/">上一章：Harness</a> · '
                '<a href="../">工程进阶目录</a> · '
                '<a href="../03-context/">下一章：上下文工程</a></p>'
                '<p>参照<a href="../01-harness/">上一章</a>中的原理。</p>'
                '<h2>配套面试练习</h2><details><summary>展开</summary>题目</details>')
        result = self.render("advanced/02-durable.md", html, hidden=["toc"])
        content = Content(result)
        self.assertEqual(len(content.elements("nav")), 1)
        self.assertIn('aria-label="章节切换"', result)
        footer = result[result.index('<nav class="chapter-pagination"'):]
        links = Content(footer).elements("a")
        self.assertEqual([attrs["href"] for attrs, _ in links],
                         ["../01-harness/", "../", "../03-context/"])
        self.assertIn('参照<a href="../01-harness/">上一章</a>中的原理。', result)
        self.assertGreater(result.index('<nav class="chapter-pagination"'), result.index('</details>'))
        self.assertEqual(self.page.meta["hide"], ["toc", "footer"])
        self.assertEqual(hooks.on_page_content(result, page=self.page, config=self.config,
                                              files=self.files), result)

    def test_first_and_last_chapters_stay_in_their_section(self):
        first = self.render("advanced/01-harness.md")
        self.assertNotIn('class="chapter-pagination__prev"', first)
        self.assertIn('class="chapter-pagination__next"', first)
        last = self.render("learning/10-reliability-and-security.md")
        self.assertIn('class="chapter-pagination__prev"', last)
        self.assertNotIn('class="chapter-pagination__next"', last)
        self.assertNotIn("00-first-agent", last)
        self.assertNotIn("advanced/", last)

    def test_unlisted_lessons_and_question_pages_keep_existing_navigation(self):
        for source in ("learning/00-first-agent.md", "questions/Q094.md"):
            with self.subTest(source=source):
                original = '<p><a href="../">阅读目录</a></p>'
                self.assertEqual(self.render(source, original), original)
                self.assertEqual(self.page.meta["hide"], [])

    def test_flat_urls_and_markup_in_titles_are_safe(self):
        self.config["nav"][1]["工程进阶"][1] = {"01 · A & B <边界>": "advanced/01-harness.md"}
        for source, target in self.targets.items():
            target.url = source.removesuffix(".md") + ".html"
        self.page = SimpleNamespace(file=SimpleNamespace(src_uri="advanced/02-durable.md",
                                                        dest_uri="advanced/02-durable.html"), meta={})
        result = hooks.on_page_content("<p>正文</p>", page=self.page,
                                       config=self.config, files=self.files)
        links = Content(result).elements("a")
        self.assertEqual([attrs["href"] for attrs, _ in links],
                         ["01-harness.html", "index.html", "03-context.html"])
        self.assertEqual(links[0][0]["aria-label"], "上一章：01 · A & B <边界>")
        self.assertNotIn("<边界>", result)


if __name__ == "__main__":
    unittest.main()
