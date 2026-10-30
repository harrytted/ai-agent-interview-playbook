"""Navigation regeneration must preserve a learner's prose and resolve both directions."""
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_repo


class NavigationTests(unittest.TestCase):
    def test_regeneration_is_idempotent_and_preserves_notes_outside_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "learning").mkdir()
            (root / "docs/foundations").mkdir(parents=True)
            primary = root / "learning/01-system-map.md"
            related = root / "learning/03-context-and-prompts.md"
            for path in (primary, related):
                path.write_text("# Lesson\n\nKeep this worked example.\n")
            question = SimpleNamespace(
                id="Q001", title="Who executes the action?",
                path=Path("docs/foundations/01-agent-and-llm.md"),
                body="[Primary](../../learning/01-system-map.md) "
                     "[Related](../../learning/03-context-and-prompts.md)",
            )
            (root / question.path).write_text(f"### {question.id} {question.title}\n")
            with mock.patch.object(check_repo, "ROOT", root), mock.patch.object(check_repo, "questions", return_value=[question]):
                check_repo.write_navigation()
                for path in (primary, related):
                    with path.open("a") as handle:
                        handle.write("\nKeep my notes after navigation.\n")
                before = {p: p.read_bytes() for p in (primary, related, root / "docs/question-index.md")}
                check_repo.write_navigation()
                check_repo.write_navigation()
                self.assertEqual(before, {p: p.read_bytes() for p in before})
            for path in (primary, related):
                content = path.read_text()
                self.assertIn("Keep this worked example.", content)
                self.assertIn("Keep my notes after navigation.", content)
                self.assertEqual(content.count(check_repo.LINKS_START), 1)
                href = re.search(r"\[Q001[^\]]+\]\(([^)]+)\)", content)[1]
                location, anchor = href.split("#")
                article = root / "questions/Q001.md"
                self.assertEqual((path.parent / location).resolve(), article)
                self.assertIn(anchor, check_repo.anchors(article.read_text()))


if __name__ == "__main__":
    unittest.main()
