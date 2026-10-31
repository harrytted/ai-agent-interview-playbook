"""Exercise the built-site validator using isolated HTML fixtures."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import check_site


def question_html(number, rendered=True):
    heading = f'<h3 id="q{number:03}-题目">Q{number:03} 题目</h3>'
    if not rendered:
        return heading + """<details><summary>展开</summary>
**详细答案：**
这是没有被 Markdown 渲染的答案。
**常见追问：**
1. 追问与答案
2. 追问与答案
3. 追问与答案
**实战案例：** 示例
</details>"""
    return heading + """<details><summary>展开详细答案、追问与案例</summary>
<p><strong>详细答案：</strong></p><p>机制与取舍。</p>
<p><strong>常见追问：</strong></p>
<ol><li>追问一：具体回答。</li><li>追问二：具体回答。</li><li>追问三：具体回答。</li></ol>
<p><strong>实战案例：</strong>场景、处理与验收。</p>
</details>"""


class SiteCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.site = self.work / "site"
        self.write("index.html", '<h1 id="首页">首页</h1>')
        self.write_bank()

    def write(self, path, text):
        target = self.site / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def write_bank(self, missing=None, raw=None):
        return self.write(
            "docs/questions/index.html",
            "\n".join(question_html(n, rendered=n != raw) for n in range(1, 93) if n != missing),
        )

    def errors(self):
        return "\n".join(check_site.check_site(self.site).errors)

    def test_valid_site_checks_all_resource_types_and_encoded_chinese_fragment(self):
        self.write("assets/app.js", "console.log('ok');")
        self.write("assets/style.css", "body {}")
        self.write("assets/logo.svg", '<svg><symbol id="标志"></symbol></svg>')
        self.write("learning/index.html", '<h2 id="工具与记忆">章节</h2>')
        self.write("index.html", """
<a href="learning/?view=full#%E5%B7%A5%E5%85%B7%E4%B8%8E%E8%AE%B0%E5%BF%86">学习</a>
<a href="docs/questions/#q001-题目">Q001</a>
<img src="assets/logo.svg#%E6%A0%87%E5%BF%97">
<script src="assets/app.js?v=1"></script>
<link rel="stylesheet" href="assets/style.css">
""")
        result = check_site.check_site(self.site)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.questions, 92)
        self.assertEqual(result.references, 5)

    def test_missing_resources_are_checked_for_every_supported_element(self):
        self.write("index.html", """
<a href="missing.html">missing</a><img src="missing.png">
<script src="missing.js"></script><link href="missing.css" rel="stylesheet">
""")
        errors = self.errors()
        for filename in ("missing.html", "missing.png", "missing.js", "missing.css"):
            self.assertIn(filename, errors)
        self.assertEqual(errors.count("missing file"), 4)

    def test_standalone_articles_are_complete_and_keep_the_grouped_anchors(self):
        sections = "".join(f"<h2>{name}</h2><p>解释</p>" for name in
                           ("简要回答", "详细解析", "常见追问", "实战案例", "常见误区", "动手想一想", "学习参考"))
        for number in range(1, 93):
            self.write(f"questions/Q{number:03}/index.html", f'<h1 id="q{number:03}-题目">Q{number:03} 题目</h1>' + sections)
        result = check_site.check_site(self.site)
        self.assertEqual(result.errors, [])
        self.assertEqual((result.questions, result.articles), (92, 92))
        self.write("questions/Q001/index.html", '<h1>Q002 wrong</h1><p>## 简要回答</p>')
        errors = self.errors()
        self.assertIn("H1 disagrees", errors)
        self.assertIn("sections are missing or not rendered", errors)

    def test_directory_requires_index_and_relative_links_use_page_directory(self):
        self.write("learning/index.html", '<a href="../docs/questions/#q092-题目">last</a>')
        self.write("index.html", '<a href="learning/">valid</a><a href="empty/">invalid</a>')
        (self.site / "empty").mkdir()
        errors = self.errors()
        self.assertIn("empty/index.html", errors)
        self.assertNotIn("q092", errors)

    def test_project_root_and_same_site_absolute_urls_are_resolved(self):
        self.write("index.html", """
<a href="/ai-agent-interview-playbook/">root</a>
<a href="https://harrytted.github.io/ai-agent-interview-playbook/docs/questions/#q010-题目">absolute</a>
<a href="//harrytted.github.io/ai-agent-interview-playbook/docs/questions/#q011-题目">protocol relative</a>
""")
        self.assertEqual(self.errors(), "")

    def test_external_and_non_document_schemes_do_not_require_local_files(self):
        self.write("index.html", """
<a href="https://example.org/missing/#unknown">external</a>
<a href="//cdn.example.org/absent">cdn</a><a href="mailto:someone@example.org">mail</a>
<a href="javascript:void(0)">js</a><img src="data:image/svg+xml,test">
""")
        result = check_site.check_site(self.site)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.references, 0)

    def test_encoded_paths_queries_and_local_fragments(self):
        self.write("资料 A.html", '<h1 id="中文 id">标题</h1>')
        self.write("index.html", """
<h2 id="本页">本页</h2><a href="#%E6%9C%AC%E9%A1%B5">self</a>
<a href="%E8%B5%84%E6%96%99%20A.html?download=1#%E4%B8%AD%E6%96%87%20id">file</a>
<a href="#:~:text=example">text fragment</a>
""")
        self.assertEqual(self.errors(), "")

    def test_missing_fragment_fails_even_when_the_target_file_exists(self):
        self.write("index.html", '<a href="docs/questions/#q093-题目">missing anchor</a>')
        errors = self.errors()
        self.assertIn("missing fragment", errors)
        self.assertIn("q093-题目", errors)

    def test_duplicate_element_ids_fail_with_both_source_lines(self):
        self.write("index.html", '<input id="__toc" type="checkbox">\n'
                   '<label for="__toc">目录</label>\n'
                   '<input id="__toc" type="checkbox">')
        self.assertIn("index.html:3: duplicate element id '__toc' (first at line 1)", self.errors())

    def test_ids_are_scoped_to_pages_and_named_anchors_are_not_element_ids(self):
        self.write("index.html", '<h1 id="shared">首页</h1>'
                   '<a id="legacy" name="legacy"></a><a name="legacy"></a>'
                   '<a href="#legacy">旧式锚点</a>')
        self.write("learning/index.html", '<h1 id="shared">学习</h1>'
                   '<a name="named-only"></a><a name="named-only"></a>'
                   '<a href="#named-only">旧式锚点</a>')
        self.assertEqual(self.errors(), "")

    def test_encoded_path_traversal_and_other_project_roots_are_rejected(self):
        (self.work / "outside.txt").write_text("outside", encoding="utf-8")
        self.write("index.html", """
<a href="%2e%2e/outside.txt">escape</a>
<a href="/ai-agent-interview-playbook/../../outside.txt">absolute escape</a>
<a href="/another-project/index.html">wrong project</a>
""")
        errors = self.errors()
        self.assertEqual(errors.count("escapes site directory"), 2)
        self.assertIn("outside project base", errors)

    def test_symlink_cannot_make_an_external_resource_local(self):
        outside = self.work / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.site / "linked.txt").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        self.write("index.html", '<a href="linked.txt">escape through symlink</a>')
        self.assertIn("escapes site directory", self.errors())

    def test_missing_and_duplicate_question_anchors_fail_independently(self):
        self.write_bank(missing=92)
        self.write("docs/duplicate.html", question_html(1))
        errors = self.errors()
        self.assertIn("Missing question h3 IDs: Q092", errors)
        self.assertIn("Duplicate Q001", errors)

    def test_questions_in_navigation_or_wrong_heading_ids_do_not_fill_the_bank(self):
        self.write_bank(missing=92)
        self.write("index.html", question_html(92))
        self.write("docs/wrong.html", '<h3 id="q091-wrong">Q092 wrong ID</h3>')
        errors = self.errors()
        self.assertIn("question title and h3 id disagree", errors)
        self.assertIn("Missing question h3 IDs: Q092", errors)

    def test_raw_markdown_in_details_is_not_accepted_as_rendered_content(self):
        self.write_bank(raw=17)
        errors = self.errors()
        self.assertIn("Q017: details answer is not rendered as structured HTML", errors)
        self.assertNotIn("Missing question h3 IDs", errors)

    def test_unclosed_last_answer_cannot_swallow_the_rest_of_the_page(self):
        bank = self.site / "docs/questions/index.html"
        content = bank.read_text(encoding="utf-8")
        before, marker, after = content.rpartition("</details>")
        self.assertTrue(marker)
        bank.write_text(before + after, encoding="utf-8")
        self.assertIn("Q092: details answer is not rendered as structured HTML", self.errors())

    def test_rendered_code_can_contain_markdown_without_being_misclassified(self):
        bank = self.site / "docs/questions/index.html"
        bank.write_text(
            bank.read_text(encoding="utf-8").replace(
                "<p>机制与取舍。</p>", '<p>机制与取舍。</p><pre><code>## code heading\n**详细答案：**</code></pre>', 1
            ),
            encoding="utf-8",
        )
        self.assertEqual(self.errors(), "")

    def test_cli_reports_success_and_fails_for_a_missing_site(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = check_site.main([str(self.site)])
        self.assertEqual(code, 0)
        self.assertIn("92 rendered questions", out.getvalue())
        self.assertEqual(err.getvalue(), "")
        with redirect_stderr(err):
            code = check_site.main([str(self.work / "absent")])
        self.assertEqual(code, 1)
        self.assertIn("Site directory does not exist", err.getvalue())


if __name__ == "__main__":
    unittest.main()
