"""Regression coverage for cross-section figure reuse, including source aliases."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_content import audit, image_uses, repeated_prose, prose_blocks


class ContentAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.asset = "website/assets/diagrams/G5-rag-pipelines.png"
        self.write(self.asset, "fixture")
        self.write("diagrams/reading-owners.json", json.dumps({
            "version": 1, "owners": {self.asset: "learning/rag.md"}}))
        self.write("learning/rag.md", "# RAG\n\n![flow](../" + self.asset + ")\n")

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_cross_column_reuse_names_the_source_question_and_generated_alias_is_excluded(self):
        self.write("advanced/rag.md", "![flow](../" + self.asset + ")")
        self.write("docs/foundations/rag.md", "### Q017 A question\n\n![flow](../../" + self.asset + ")")
        self.write("questions/Q017.md", "![flow](../" + self.asset + ")")
        self.write(".site-src/learning/rag.md", "![flow](../../" + self.asset + ")")
        result = audit(self.root)
        self.assertEqual(result["authored_image_occurrences"], 3)
        self.assertEqual({u["owner"] for u in result["image_uses"]},
                         {"learning/rag.md", "advanced/rag.md", "questions/Q017.md"})
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("docs/foundations/rag.md:3 (questions/Q017.md)", result["errors"][0])

    def test_link_to_primary_lesson_does_not_embed_the_image(self):
        self.write("advanced/rag.md", "[Read the diagram](../learning/rag.md)")
        self.assertEqual(audit(self.root)["errors"], [])

    def test_fenced_markdown_examples_are_not_publication_occurrences(self):
        self.write("advanced/rag.md", "```md\n![flow](../" + self.asset + ")\n```\n")
        self.assertEqual(audit(self.root)["errors"], [])

    def test_html_reference_and_svg_forms_cannot_hide_duplicate_diagrams(self):
        self.write("advanced/rag.md", '<img src="../' + self.asset + '">\n\n'
                   + '![flow][pipeline]\n\n[pipeline]: ../' + self.asset + '\n\n'
                   + '![flow](../' + self.asset.replace('.png', '.svg') + '#view)\n')
        result = audit(self.root)
        self.assertEqual(result["authored_image_occurrences"], 4)
        self.assertEqual(len(result["errors"]), 1)

    def test_only_one_occurrence_in_the_wrong_owner_is_still_an_error(self):
        self.write("learning/rag.md", "# RAG")
        self.write("advanced/rag.md", "![flow](../" + self.asset + ")")
        self.assertIn("must be embedded once in learning/rag.md", audit(self.root)["errors"][0])

    def test_unregistered_diagram_requires_an_explicit_owner(self):
        self.write("learning/rag.md", "![new](../website/assets/diagrams/new.png)")
        self.assertIn("diagram has no declared reading owner", "\n".join(audit(self.root)["errors"]))

    def test_renamed_byte_identical_copy_does_not_evade_the_audit(self):
        copy = "website/assets/diagrams/renamed.png"
        self.write(copy, "fixture")
        self.write("advanced/rag.md", "![renamed](../" + copy + ")")
        self.write("diagrams/reading-owners.json", json.dumps({"version": 1, "owners": {
            self.asset: "learning/rag.md", copy: "advanced/rag.md"}}))
        self.assertIn("byte-identical diagrams", "\n".join(audit(self.root)["errors"]))

    def test_line_numbers_survive_code_masking(self):
        path = self.write("docs/foundations/rag.md", "```\nnot prose\n```\n\n### Q017 Question\n\n![flow](../../" + self.asset + ")")
        result = image_uses(self.root, path, path.read_text())
        self.assertEqual(result[0]["line"], 7)
        self.assertEqual(result[0]["owner"], "questions/Q017.md")

    def test_repeated_prose_is_a_review_queue_and_normalizes_link_targets(self):
        core = "检索候选与生成回答必须分别检查，否则无法知道正确证据在哪一阶段消失。" * 5
        left = prose_blocks("learning/a.md", core + "[图解](diagram.md)")
        right = prose_blocks("advanced/a.md", core + "[图解](../diagram.md)")
        review = repeated_prose(left + right)
        self.assertEqual(len(review["exact"]), 1)
        self.assertEqual(len(review["exact"][0]["locations"]), 2)

    def test_real_repository_has_single_primary_owners(self):
        result = audit(Path(__file__).resolve().parents[1])
        self.assertEqual(result["errors"], [])

    def test_small_prose_edits_enter_review_without_becoming_an_exact_match(self):
        content = "".join(f"证据项{i:03}需要核对来源与适用条件。" for i in range(20))
        left = prose_blocks("learning/a.md", content)
        right = prose_blocks("advanced/a.md", content.replace("证据项010", "材料项010"))
        result = repeated_prose(left + right)
        self.assertEqual(result["exact"], [])
        self.assertEqual(len(result["similar_candidates"]), 1)
        self.assertGreaterEqual(result["similar_candidates"][0]["jaccard_5gram"], 0.85)


if __name__ == "__main__":
    unittest.main()
