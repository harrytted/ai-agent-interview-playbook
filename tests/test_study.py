"""Behavioral checks for the offline study CLI; no personal progress is touched."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import study


class StudyTests(unittest.TestCase):
    DAY = date(2026, 10, 28)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.progress = self.work / "personal" / "progress.json"

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with mock.patch.object(study, "today", return_value=self.DAY):
                try:
                    code = study.main(["--progress", str(self.progress), *args])
                except SystemExit as error:
                    code = error.code
        return code, out.getvalue(), err.getvalue()

    def question_ids(self, text):
        return re.findall(r"^\s*(Q\d{3}) ", text, re.MULTILINE)

    def test_complete_bank_keeps_original_ids_and_adds_36_advanced_questions(self):
        bank = study.questions()
        self.assertEqual([q.id for q in bank], [f"Q{i:03d}" for i in range(1, 93)])
        self.assertTrue(all(q.title and q.body for q in bank))
        self.assertTrue(all((ROOT / q.path).is_file() for q in bank))

    def test_advanced_bank_can_be_selected_and_drawn_without_changing_progress(self):
        code, out, err = self.cli("list", "--topic", "docs/advanced/")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.question_ids(out), [f"Q{i:03d}" for i in range(57, 93)])
        code, out, err = self.cli("draw", "--topic", "docs/advanced/", "--count", "3", "--seed", "7")
        self.assertEqual((code, err), (0, ""))
        ids = self.question_ids(out)
        self.assertEqual(len(set(ids)), 3)
        self.assertTrue(all(57 <= int(qid[1:]) <= 92 for qid in ids))
        self.assertFalse(self.progress.exists())

    def test_advanced_show_expands_details_and_keeps_followups_and_case(self):
        code, out, err = self.cli("show", "q092")
        self.assertEqual((code, err), (0, ""))
        for label in ("详细答案", "常见追问", "实战案例", "微练习"):
            self.assertIn(label, out)
        self.assertNotIn("<details", out)
        self.assertNotIn("</details>", out)
        self.assertNotIn("<summary", out)
        self.assertNotIn("### Q091", out)
        self.assertFalse(self.progress.exists())

    def test_original_bank_show_expands_full_answers_across_all_modules(self):
        for qid in ("Q001", "Q017", "Q033", "Q049", "Q056"):
            with self.subTest(qid=qid):
                code, out, err = self.cli("show", qid)
                self.assertEqual((code, err), (0, ""))
                for label in ("详细答案", "常见追问", "实战案例", "微练习", "学习与参考"):
                    self.assertIn(label, out)
                self.assertNotIn("<details", out)
                self.assertNotIn("<summary", out)
                self.assertNotRegex(out, r"(?m)^### Q\d{3}")
        self.assertFalse(self.progress.exists())

    def test_duplicate_ids_fail_instead_of_overwriting_an_answer(self):
        folder = self.work / "docs" / "foundations"
        folder.mkdir(parents=True)
        (folder / "duplicate.md").write_text(
            "### Q001 first\nfirst answer\n### Q001 second\nsecond answer\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "重复"):
            study.questions(self.work)

    def test_fenced_headings_neither_create_questions_nor_truncate_answers(self):
        folder = self.work / "docs" / "foundations"
        folder.mkdir(parents=True)
        source = folder / "examples.md"
        for opening, closing in (("```markdown", "```"), ("~~~markdown", "~~~"), ("````markdown", "````")):
            inner = "```\n" if opening.startswith("````") else ""
            sample = opening + "\n## 示例小节\n### Q999 示例题号\n" + inner + "正文示例\n" + closing
            source.write_text("### Q001 first\n\n正文开始。\n\n" + sample
                              + "\n\n真实答案结尾。\n\n### Q002 second\n\n第二题答案。\n\n## 参考资料\n不属于答案。\n")
            with self.subTest(fence=opening):
                bank = study.questions(self.work)
                self.assertEqual([question.id for question in bank], ["Q001", "Q002"])
                self.assertIn(sample, bank[0].body)
                self.assertTrue(bank[0].body.endswith("真实答案结尾。"))
                self.assertEqual(bank[1].body, "第二题答案。")

    def test_terminal_expands_real_folds_but_preserves_html_examples(self):
        sample = "```html\n<details><summary>示例</summary>\n示例内容\n</details>\n```"
        body = "<details><summary>展开答案</summary>\n\n真实答案。\n\n" + sample + "\n\n</details>"
        expanded = study.readable_answer(body)
        self.assertIn(sample, expanded)
        self.assertTrue(expanded.startswith("展开答案\n"))
        self.assertTrue(expanded.endswith("```"))
        self.assertNotIn("<summary>展开答案</summary>", expanded)

    def test_list_filters_by_topic_path_without_writing_progress(self):
        code, out, err = self.cli("list", "--topic", "engineering/05-")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.question_ids(out), [f"Q{i:03d}" for i in range(33, 41)])
        self.assertIn("共 8 题", out)
        self.assertFalse(self.progress.parent.exists())

    def test_draw_is_seeded_unique_and_stays_in_the_requested_topic(self):
        args = ("draw", "--topic", "engineering/06-", "--count", "3", "--seed", "42")
        first = self.cli(*args)
        self.assertEqual(first, self.cli(*args))
        code, out, err = first
        self.assertEqual((code, err), (0, ""))
        ids = self.question_ids(out)
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)
        self.assertTrue(set(ids) <= {f"Q{i:03d}" for i in range(41, 49)})
        self.assertFalse(self.progress.exists())

    def test_show_displays_only_the_requested_answer(self):
        code, out, err = self.cli("show", "q033")
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.startswith("Q033 "))
        self.assertIn("30–60 秒回答", out)
        self.assertNotIn("Q034", out)
        self.assertNotIn("## 核验记录", out)
        self.assertFalse(self.progress.exists())

    def test_bad_progress_fails_safely_and_preserves_original_bytes(self):
        self.progress.parent.mkdir()
        for content in ('{"Q001":', '[]', '{"Q001": {"stage": 0}}'):
            with self.subTest(content=content):
                self.progress.write_text(content, encoding="utf-8")
                before = self.progress.read_bytes()
                code, out, err = self.cli("review", "Q001", "--score", "2")
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertIn("无法完成", err)
                self.assertNotIn("Traceback", err)
                self.assertEqual(self.progress.read_bytes(), before)
                self.assertEqual(list(self.progress.parent.glob(".progress-*")), [])

    def test_unknown_id_never_creates_or_changes_progress(self):
        code, out, err = self.cli("review", "Q999", "--score", "3")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("未知题号", err)
        self.assertFalse(self.progress.parent.exists())
        self.progress.parent.mkdir()
        self.progress.write_text("{}\n", encoding="utf-8")
        before = self.progress.read_bytes()
        self.assertEqual(self.cli("review", "Q999", "--score", "3")[0], 2)
        self.assertEqual(self.progress.read_bytes(), before)

    def test_first_review_intervals_and_metadata_follow_the_contract(self):
        for score, days in ((0, 0), (1, 1), (2, 3), (3, 1)):
            with self.subTest(score=score):
                entry = study.schedule({}, score, self.DAY)
                self.assertEqual(entry["score"], score)
                self.assertEqual(entry["last_review"], self.DAY.isoformat())
                self.assertEqual(entry["due"], (self.DAY + timedelta(days=days)).isoformat())
                self.assertEqual(entry["reviews"], 1)
                if score == 2:
                    self.assertGreaterEqual(entry["stage"], 1)

    def test_perfect_reviews_expand_then_cap_and_low_scores_reset(self):
        entry = {}
        for count, days in enumerate((1, 3, 7, 14, 14), start=1):
            entry = study.schedule(entry, 3, self.DAY)
            self.assertEqual(entry["due"], (self.DAY + timedelta(days=days)).isoformat())
            self.assertEqual(entry["reviews"], count)
        for score in (0, 1):
            with self.subTest(score=score):
                reset = study.schedule(entry, score, self.DAY)
                self.assertEqual(reset["stage"], 0)
                self.assertEqual(reset["due"], (self.DAY + timedelta(days=score)).isoformat())

    def test_review_cli_saves_and_reads_the_same_record_atomically(self):
        code, out, err = self.cli("review", "q001", "--score", "2")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("2026-10-31", out)
        record = study.read_progress(self.progress)
        self.assertEqual(set(record), {"Q001"})
        self.assertEqual(record["Q001"], study.schedule({}, 2, self.DAY))
        self.assertEqual(json.loads(self.progress.read_text(encoding="utf-8")), record)
        self.assertEqual(list(self.progress.parent.glob(".progress-*")), [])
        self.assertEqual(self.cli("review", "Q001", "--score", "2")[0], 0)
        self.assertEqual(study.read_progress(self.progress)["Q001"]["reviews"], 2)

    def test_failed_atomic_replace_preserves_old_progress_and_cleans_temp(self):
        old = {"Q001": study.schedule({}, 1, self.DAY)}
        study.save_progress(self.progress, old)
        before = self.progress.read_bytes()
        new = {"Q002": study.schedule({}, 2, self.DAY)}
        with mock.patch.object(study.os, "replace", side_effect=OSError("simulated disk failure")):
            with self.assertRaisesRegex(OSError, "simulated disk failure"):
                study.save_progress(self.progress, new)
        self.assertEqual(self.progress.read_bytes(), before)
        self.assertEqual(study.read_progress(self.progress), old)
        self.assertEqual(list(self.progress.parent.glob(".progress-*")), [])

    def test_due_and_stats_distinguish_unseen_future_due_and_retired_ids(self):
        entries = {
            "Q001": study.schedule({}, 0, self.DAY - timedelta(days=1)),
            "Q002": study.schedule({}, 1, self.DAY),
            "Q003": study.schedule({}, 0, self.DAY),
            "Q999": study.schedule({}, 0, self.DAY),
        }
        study.save_progress(self.progress, entries)
        before = self.progress.read_bytes()
        code, out, err = self.cli("due")
        self.assertEqual((code, err), (0, ""))
        due_section, unseen_section = out.split("未学习", 1)
        self.assertEqual(self.question_ids(due_section), ["Q001", "Q003"])
        unseen = self.question_ids(unseen_section)
        self.assertEqual(len(unseen), 89)
        self.assertNotIn("Q002", unseen)
        self.assertNotIn("Q999", out)
        code, stats, err = self.cli("stats")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("题目 92；已自评 3；未学习 89；到期 2", stats)
        self.assertEqual(self.progress.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
