"""Standalone articles remain faithful views of the editable grouped question bank."""
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from question_articles import article_pages, check_articles, write_articles
from study import questions


class QuestionArticleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def question(self, qid="Q001", body=None, path="docs/foundations/01-agent-and-llm.md"):
        if body is None:
            body = """**优先级：P0**

**30–60 秒回答：**

短答。

<details><summary>展开详细答案、追问与案例</summary>

**详细答案：**

#### 模型怎样工作

解释原理。

<details><summary>预测后看答案</summary>

保留内部自检。

</details>

**常见追问：**

1. 为什么？因为需要证据。
2. 怎样？沿依赖继续。
3. 还有什么？检查条件。

**实战案例：**

完整案例。

</details>

**常见误区：** 不区分信息与行动。

**微练习：**

解释一次。

**学习与参考：** [学习](../../learning/01-system-map.md)
"""
        return SimpleNamespace(id=qid, title="问题与解释？", path=Path(path), body=body)

    def test_main_answer_is_open_and_nested_self_check_is_preserved(self):
        generated = article_pages([self.question()], self.root)[Path("questions/Q001.md")]
        self.assertIn("# Q001 问题与解释？", generated)
        for heading in ("简要回答", "详细解析", "常见追问", "实战案例", "常见误区", "动手想一想", "学习参考"):
            self.assertIn("## " + heading, generated)
        self.assertIn("### 模型怎样工作", generated)
        self.assertNotIn("展开详细答案、追问与案例", generated)
        self.assertEqual(generated.count("<details>"), 1)
        self.assertEqual(generated.count("</details>"), 1)
        self.assertIn("<summary>预测后看答案</summary>", generated)
        self.assertIn("不区分信息与行动。", generated)

    def test_code_fences_keep_headers_links_and_fake_details_byte_for_byte(self):
        for fence in ("```markdown", "~~~markdown"):
            closing = fence[:3]
            code = f"{fence}\n#### not a heading\n[Example](../../do-not-rebase.py)\n**详细答案：**\n<details><summary>展开详细答案</summary>\n</details>\n{closing}"
            question = self.question(body=f"**30–60 秒回答：**\n\n短答\n\n<details><summary>展开详细答案、追问与案例</summary>\n\n**详细答案：**\n\n{code}\n\n真实正文\n\n</details>")
            with self.subTest(fence=fence):
                generated = article_pages([question], self.root)[Path("questions/Q001.md")]
                self.assertIn(code, generated)
                self.assertIn("真实正文", generated)

    def test_detail_subsections_remain_below_main_article_sections(self):
        question = self.question(body="**详细答案：**\n\n#### 组件\n\n解释\n\n##### 输入\n\n说明\n")
        generated = article_pages([question], self.root)[Path("questions/Q001.md")]
        self.assertIn("## 详细解析\n\n### 组件", generated)
        self.assertIn("#### 输入", generated)
        self.assertNotIn("\n## 组件", generated)

    def test_images_code_and_chinese_paths_are_rebased_without_losing_query_or_fragment(self):
        body = '''![架构](../../website/assets/diagrams/concepts/C1-capability-map.svg)
[代码](../../examples/policy_agent/core.py?raw=1#L5)
[笔记](<../../learning/中文 笔记.md#说明> "标题")
[外部](https://example.com/a?q=1#section)
[本节](#当前小节)
'''
        generated = article_pages([self.question(body=body)], self.root)[Path("questions/Q001.md")]
        self.assertIn("(../website/assets/diagrams/concepts/C1-capability-map.svg)", generated)
        self.assertIn("(../examples/policy_agent/core.py?raw=1#L5)", generated)
        self.assertIn('(<../learning/%E4%B8%AD%E6%96%87%20%E7%AC%94%E8%AE%B0.md#说明> "标题")', generated)
        self.assertIn("(https://example.com/a?q=1#section)", generated)
        self.assertIn("(#当前小节)", generated)

    def test_question_links_target_independent_articles_and_same_question_fragment_stays(self):
        first = self.question(body="[Next](01-agent-and-llm.md?mode=read#q002-问题与解释)\n[Same](#当前小节)\n[Peer](#q002-问题与解释)\n")
        second = self.question("Q002")
        generated = article_pages([first, second], self.root)[Path("questions/Q001.md")]
        self.assertIn("(Q002.md?mode=read#q002-问题与解释)", generated)
        self.assertIn("(Q002.md#q002-问题与解释)", generated)
        self.assertIn("(#当前小节)", generated)

    def test_writer_is_idempotent_and_check_reports_source_edits_and_extra_ids(self):
        bank = [self.question()]
        write_articles(bank, self.root)
        before = {path: path.read_bytes() for path in (self.root / "questions").glob("*.md")}
        write_articles(bank, self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.assertEqual(check_articles(bank, self.root), [])
        bank[0].body += "\n新增事实。\n"
        self.assertIn("Q001.md 独立文章需更新", "\n".join(check_articles(bank, self.root)))
        write_articles(bank, self.root)
        (self.root / "questions/Q999.md").write_text("extra")
        self.assertIn("多余独立题目：questions/Q999.md", check_articles(bank, self.root))

    def test_grouped_index_uses_original_knowledge_structure(self):
        source = self.root / "docs/foundations/01-agent-and-llm.md"
        source.parent.mkdir(parents=True)
        source.write_text("# 模型与Agent\n")
        bank = [self.question(), self.question("Q002")]
        generated = article_pages(bank, self.root)
        self.assertEqual(set(generated), {Path("questions/Q001.md"), Path("questions/Q002.md"), Path("questions/README.md")})
        self.assertIn("## 基础原理\n", generated[Path("questions/README.md")])
        self.assertIn("### 模型与Agent", generated[Path("questions/README.md")])
        self.assertIn("(Q002.md)", generated[Path("questions/Q001.md")])
        self.assertIn("(Q001.md)", generated[Path("questions/Q002.md")])

    def test_unbalanced_main_fold_and_escaping_links_are_explicit_errors(self):
        bad = self.question(body="<details><summary>展开详细答案</summary>\n正文")
        with self.assertRaisesRegex(ValueError, "unclosed"):
            article_pages([bad], self.root)
        with self.assertRaisesRegex(ValueError, "escapes"):
            article_pages([self.question(body="[bad](../../../outside.md)")], self.root)

    def test_real_bank_produces_exactly_92_independent_articles_without_new_question_ids(self):
        root = Path(__file__).resolve().parents[1]
        bank = questions(root)
        generated = article_pages(bank, root)
        articles = [path for path in generated if path.name != "README.md"]
        self.assertEqual(len(articles), 92)
        self.assertEqual({path.stem for path in articles}, {f"Q{i:03}" for i in range(1, 93)})
        self.assertIn("## 简要回答", generated[Path("questions/Q092.md")])
        self.assertNotIn("<summary>展开详细答案", generated[Path("questions/Q092.md")])
        index = generated[Path("questions/README.md")]
        self.assertEqual(re.findall(r"^## (.+)$", index, re.M), ["基础原理", "工程应用", "进阶系统"])
        self.assertEqual(re.findall(r"^- \[(Q\d{3})", index, re.M), [q.id for q in bank])


if __name__ == "__main__":
    unittest.main()
