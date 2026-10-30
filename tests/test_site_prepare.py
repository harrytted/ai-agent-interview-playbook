"""Content preparation contracts; all writes use isolated temporary directories."""
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_site as site


class SitePrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repository"
        self.root.mkdir()
        self.output = self.base / "prepared"

    def write(self, relative, text="not published\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def prepare(self):
        return site.prepare_site(self.root, self.output)

    def test_nested_readmes_and_markdown_links_keep_query_and_fragment(self):
        self.write("README.md", "# Home\n[Course](learning/README.md?mode=read#开始)\n")
        self.write("learning/README.md", "# Course\n[Home](../README.md#home)\n[Next](chapter.md?x=1#part)\n")
        self.write("learning/chapter.md", "# Part\n[Course](README.md)\n")
        self.assertEqual(self.prepare(), 3)
        self.assertIn("(learning/index.md?mode=read#开始)", (self.output / "index.md").read_text())
        course = (self.output / "learning/index.md").read_text()
        self.assertIn("(../index.md#home)", course)
        self.assertIn("(chapter.md?x=1#part)", course)
        self.assertFalse((self.output / "README.md").exists())

    def test_directory_links_prefer_index_and_code_links_use_github(self):
        self.write("README.md", "[Lab](examples/lab/)\n[Source](examples/lab/lab.py?raw=1#L5)\n[Folder](scripts/)\n[License](LICENSE)\n[Data](research/sources.json#entries)\n")
        self.write("examples/lab/README.md", "# Lab\n[Code](lab.py)\n")
        self.write("examples/lab/lab.py", "print('hello')\n")
        self.write("scripts/tool.py")
        self.write("LICENSE")
        self.write("research/sources.json", "{}")
        self.prepare()
        home = (self.output / "index.md").read_text()
        self.assertIn("(examples/lab/index.md)", home)
        self.assertIn("https://github.com/harrytted/ai-agent-interview-playbook/blob/main/examples/lab/lab.py?raw=1#L5", home)
        self.assertIn("https://github.com/harrytted/ai-agent-interview-playbook/tree/main/scripts", home)
        self.assertIn("https://github.com/harrytted/ai-agent-interview-playbook/blob/main/LICENSE", home)
        self.assertIn("https://github.com/harrytted/ai-agent-interview-playbook/blob/main/research/sources.json#entries", home)
        self.assertFalse((self.output / "examples/lab/lab.py").exists())

    def test_fenced_examples_are_unchanged_and_external_fragments_stay(self):
        fenced = "```markdown\n# Example\n[Do not alter](missing.md)\n<details><summary>Example</summary>\n```\n"
        tilde = "~~~text\n## Another\n[Placeholder](../outside.md)\n~~~\n"
        self.write("README.md", "# Home\n[Web](https://example.com/README.md?a=1#x)\n[Here](#home)\n" + fenced + tilde)
        self.prepare()
        generated = (self.output / "index.md").read_text()
        self.assertIn(fenced, generated)
        self.assertIn(tilde, generated)
        self.assertIn("(https://example.com/README.md?a=1#x)", generated)
        self.assertIn("(#home)", generated)

    def test_branch_preview_links_code_to_review_branch_without_changing_page_links(self):
        self.write("README.md", "[Code](examples/policy_agent/core.py)\n[Course](learning/00-first-agent.md)\n")
        self.write("examples/policy_agent/core.py", "# example\n")
        self.write("learning/00-first-agent.md", "# Start\n")
        site.prepare_site(self.root, self.output, source_ref="codex/agent-handbook-learning")
        home = (self.output / "index.md").read_text()
        self.assertIn("blob/codex/agent-handbook-learning/examples/policy_agent/core.py", home)
        self.assertIn("(learning/00-first-agent.md)", home)
        with self.assertRaises(ValueError):
            site.prepare_site(self.root, self.output, source_ref="../main?bad=1")

    def test_policy_example_and_nested_diagrams_use_existing_publish_contract(self):
        self.write("README.md", "[Start](learning/00-first-agent.md)\n")
        self.write("learning/00-first-agent.md", "![Flow](../website/assets/diagrams/G1-system-flow.svg)\n[Lab](../examples/policy_agent/README.md)\n")
        self.write("examples/policy_agent/README.md", "[Self](README.md)\n[Data](data/policies.json)\n[Trace](traces/normal.jsonl)\n")
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 600"><title>流程</title></svg>'
        self.write("website/assets/diagrams/G1-system-flow.svg", svg)
        self.write("examples/policy_agent/data/policies.json", "[]")
        self.write("examples/policy_agent/traces/normal.jsonl", "{}\n")
        self.prepare()
        intro = (self.output / "learning/00-first-agent.md").read_text()
        self.assertIn("(../assets/diagrams/G1-system-flow.svg)", intro)
        self.assertIn("(../examples/policy_agent/index.md)", intro)
        lab = (self.output / "examples/policy_agent/index.md").read_text()
        self.assertIn("[Self](index.md)", lab)
        self.assertIn("blob/main/examples/policy_agent/data/policies.json", lab)
        self.assertIn("blob/main/examples/policy_agent/traces/normal.jsonl", lab)
        self.assertEqual((self.output / "assets/diagrams/G1-system-flow.svg").read_text(), svg)

    def test_chinese_encoded_paths_angle_targets_and_titles(self):
        self.write("README.md", '[课](learning/%E4%B8%AD%E6%96%87%20%E7%AC%94%E8%AE%B0.md?x=1#章节)\n[课](<learning/中文 笔记.md#章节> "说明")\n')
        self.write("learning/中文 笔记.md", "# 章节\n")
        self.prepare()
        home = (self.output / "index.md").read_text()
        self.assertIn("learning/%E4%B8%AD%E6%96%87%20%E7%AC%94%E8%AE%B0.md?x=1#章节", home)
        self.assertIn('(<learning/%E4%B8%AD%E6%96%87%20%E7%AC%94%E8%AE%B0.md#章节> "说明")', home)

    def test_explicit_ids_duplicate_headings_and_details_are_minimal(self):
        self.write("README.md", '# Topic\n## Same\n## Same\n## Custom {#kept}\n<details open><summary>Keep *this* summary</summary>\n\n**Answer**\n\n</details>\n<details markdown="1"><summary>Existing</summary></details>\n')
        self.prepare()
        text = (self.output / "index.md").read_text()
        self.assertIn("# Topic {#topic}", text)
        self.assertIn("## Same {#same}\n## Same {#same-1}", text)
        self.assertIn("## Custom {#kept}\n", text)
        self.assertNotIn("{#kept} {#", text)
        self.assertIn('<details open markdown="1"><summary>Keep *this* summary</summary>', text)
        self.assertEqual(text.count('markdown="1"'), 2)
        self.assertIn("\n**Answer**\n", text)

    def test_allowlist_excludes_credentials_private_trees_and_extra_examples(self):
        for name in ("README.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/guide.md", "research/note.md", "examples/a/README.md"):
            self.write(name, "# Public\n")
        for name in (".git/private.md", ".local/note.md", "credentials/password.md", "docs/.git/key.md", "docs/env/key.md", "docs/credentials/key.md", "docs/credentials.md", "docs/__pycache__/cache.md", "examples/a/extra.md", "scripts/private.md", "mkdocs.yml", ".env"):
            self.write(name)
        self.assertEqual(self.prepare(), 6)
        pages = {p.relative_to(self.output).as_posix() for p in self.output.rglob("*.md")}
        self.assertEqual(pages, {"index.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/guide.md", "research/note.md", "examples/a/index.md"})

    def test_sources_remain_identical_and_only_owned_output_is_replaced(self):
        source = self.write("README.md", "# Home\n")
        before = source.read_bytes()
        self.prepare()
        stale = self.output / "stale.md"
        stale.write_text("old generated page")
        self.prepare()
        self.assertFalse(stale.exists())
        self.assertEqual(source.read_bytes(), before)
        stranger = self.base / "unmanaged"
        stranger.mkdir()
        note = stranger / "notes.txt"
        note.write_text("keep")
        with self.assertRaisesRegex(ValueError, "ownership"):
            site.prepare_site(self.root, stranger)
        self.assertEqual(note.read_text(), "keep")

    def test_static_assets_are_copied_by_extension_without_links_or_other_files(self):
        self.write("README.md", "# Home\n![Logo](website/assets/logo.svg)\n[Config](website/assets/settings.json)\n")
        originals = {}
        for name in ("site.css", "site.js", "logo.svg", "image.png", "icons/icon.ico", "fonts/site.woff2"):
            path = self.write("website/assets/" + name, "asset " + name)
            originals[path] = path.read_bytes()
        for name in ("settings.json", "README.md", "secret.py", "style.css.map", ".hidden.css", "credentials.js"):
            self.write("website/assets/" + name)
        (self.root / "website/assets/alias.css").symlink_to(self.root / "website/assets/site.css")
        outside = self.base / "private-assets"
        outside.mkdir()
        (outside / "private.css").write_text("private")
        (self.root / "website/assets/linked").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.prepare(), 1)
        copied = {p.relative_to(self.output / "assets").as_posix()
                  for p in (self.output / "assets").rglob("*") if p.is_file()}
        self.assertEqual(copied, {"site.css", "site.js", "logo.svg", "image.png", "icons/icon.ico", "fonts/site.woff2"})
        for source, content in originals.items():
            relative = source.relative_to(self.root / "website/assets")
            self.assertEqual((self.output / "assets" / relative).read_bytes(), content)
            self.assertEqual(source.read_bytes(), content)
        home = (self.output / "index.md").read_text()
        self.assertIn("![Logo](assets/logo.svg)", home)
        self.assertIn("blob/main/website/assets/settings.json", home)

    def test_dangerous_or_overlapping_output_is_rejected_before_changes(self):
        self.write("README.md", "# Home\n")
        self.write("learning/chapter.md", "keep")
        for output in (self.root, self.base, Path(self.root.anchor), self.root / "learning", self.root / "learning/generated", self.root / "scripts", self.root / "website/generated", self.root / ".git/site", Path("../escaped"), self.root / "README.md"):
            with self.subTest(output=output), self.assertRaises(ValueError):
                site.prepare_site(self.root, output)
        self.assertEqual((self.root / "learning/chapter.md").read_text(), "keep")

    def test_symlink_sources_outputs_and_relative_escape_are_rejected_or_excluded(self):
        self.write("README.md", "# Home\n")
        outside = self.base / "outside.md"
        outside.write_text("private")
        (self.root / "docs").mkdir()
        (self.root / "docs/leak.md").symlink_to(outside)
        self.prepare()
        self.assertFalse((self.output / "docs/leak.md").exists())
        alias = self.root / "alias"
        alias.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError):
            site.prepare_site(self.root, Path("alias/generated"))
        with self.assertRaises(ValueError):
            site.prepare_site(self.root, alias / "generated")
        output_link = self.base / "output-link"
        output_link.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError):
            site.prepare_site(self.root, output_link)

    def test_failed_transform_keeps_previous_output_and_readme_collision_fails(self):
        self.write("README.md", "# Safe\n")
        self.prepare()
        previous = (self.output / "index.md").read_bytes()
        self.write("README.md", "[Escape](../private.md)\n")
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.prepare()
        self.assertEqual((self.output / "index.md").read_bytes(), previous)
        self.write("README.md", "# Safe\n")
        self.write("docs/README.md", "# Index\n")
        self.write("docs/index.md", "# Collision\n")
        with self.assertRaisesRegex(ValueError, "same destination"):
            self.prepare()

    def test_real_question_anchors_include_q031_and_all_92_questions(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import check_repo
        from scripts import study
        bank = study.questions()
        self.assertEqual(len(bank), 92)
        mapping = site.page_mapping(ROOT)
        source = PurePosixPath("docs/foundations/04-tools-memory-protocols.md")
        content = (ROOT / source).read_text(encoding="utf-8")
        generated = site.transform_markdown(content, source, mapping, ROOT)
        self.assertIn("### Q031 上下文太长时如何压缩而不丢任务？ {#q031-上下文太长时如何压缩而不丢任务}", generated)
        index_source = PurePosixPath("docs/question-index.md")
        index = site.transform_markdown((ROOT / index_source).read_text(encoding="utf-8"), index_source, mapping, ROOT)
        self.assertIn("(foundations/04-tools-memory-protocols.md#q031-上下文太长时如何压缩而不丢任务)", index)
        for question in bank:
            relative = PurePosixPath(question.path.as_posix())
            page = site.transform_markdown((ROOT / relative).read_text(encoding="utf-8"), relative, mapping, ROOT)
            self.assertIn("{#" + check_repo.slug(question.id + " " + question.title) + "}", page)


if __name__ == "__main__":
    unittest.main()
