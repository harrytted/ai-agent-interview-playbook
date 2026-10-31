import json
from pathlib import Path
import tempfile
import unittest

from examples.knowledge_pipeline_lab.lab import (
    Pipeline, SCENARIOS, change_amount, fixture_sources, parse_markdown, run_scenario,
)


class KnowledgePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sources = fixture_sources(self.root / "sources")
        self.pipeline = Pipeline(self.root / "store")

    def query(self, at="2026-11-12", who="employee", generation=None):
        return self.pipeline.query("海岚 住宿 上限", at, who, generation)

    def test_effective_date_boundary_and_lineage(self):
        self.pipeline.publish(self.sources)
        self.assertIn("金额上限：600", self.query("2026-10-31")[0]["text"])
        row = self.query("2026-11-01")[0]
        self.assertIn("金额上限：700", row["text"])
        self.assertIn("单位：元/晚", row["text"])
        self.assertEqual(row["version"], "v2")
        self.assertEqual(row["valid_from"], "2026-11-01")
        self.assertIsNone(row["valid_to"])
        self.assertGreater(row["policy_revision"], 0)
        self.assertEqual((row["line_start"], row["line_end"]), (7, 9))
        self.assertIn("fixture://policies/hailan/v2#L7-L9", row["source_location"])

    def test_duplicate_ingestion_and_reuse_after_restart(self):
        first = self.pipeline.publish(self.sources)
        self.pipeline = Pipeline(self.root / "store")
        second = self.pipeline.publish(self.sources * 2)
        self.assertEqual(first["generation"], second["generation"])
        self.assertEqual((second["document_count"], second["parsed"], second["reused"]), (3, 0, 3))

    def test_content_edit_keeps_identity_but_replaces_old_postings(self):
        self.pipeline.publish(self.sources)
        before = self.query()[0]
        change_amount(self.sources)
        result = self.pipeline.publish(self.sources)
        after = self.query()[0]
        self.assertEqual((result["parsed"], result["reused"]), (1, 2))
        self.assertEqual(before["block_id"], after["block_id"])
        self.assertNotEqual(before["content_hash"], after["content_hash"])
        saved_source = self.pipeline.generation(before["generation"])["documents"]["lodging-hailan@v2"]["source_text"]
        self.assertIn("| 700 |", saved_source)
        self.assertEqual(len(before["source_hash"]), 64)
        self.assertEqual(self.pipeline.query("700", "2026-11-12", "employee"), [])
        self.assertEqual(len(self.pipeline.query("720", "2026-11-12", "employee")), 1)

    def test_interruption_hides_staging_and_resumes_in_fresh_instance(self):
        first = self.pipeline.publish(self.sources)
        change_amount(self.sources, after="730")
        with self.assertRaises(InterruptedError):
            self.pipeline.publish(self.sources, fail_after=1)
        self.assertEqual(self.pipeline.state()["generation"], first["generation"])
        self.assertIn("金额上限：700", self.query()[0]["text"])
        self.pipeline = Pipeline(self.root / "store")
        report = self.pipeline.publish(self.sources)
        self.assertEqual(report["resumed"], 1)
        self.assertIn("金额上限：730", self.query()[0]["text"])

    def test_deletion_filters_pinned_old_index_and_rollback(self):
        first = self.pipeline.publish(self.sources)
        self.pipeline.publish([s for s in self.sources if s["version"] != "v2"])
        self.assertEqual(self.query(generation=first["generation"]), [])
        self.pipeline.activate(first["generation"])
        self.assertEqual(self.query(), [])
        self.assertEqual(len(self.query("2026-10-31")), 1)

    def test_revocation_survives_restart_and_rollback(self):
        first = self.pipeline.publish(self.sources)
        change_amount(self.sources)
        self.pipeline.publish(self.sources)
        self.pipeline.revoke("lodging-hailan", "employee")
        self.pipeline = Pipeline(self.root / "store")
        self.pipeline.activate(first["generation"])
        self.assertEqual(self.query(), [])
        self.assertEqual(len(self.query(who="admin")), 1)

    def test_missing_date_and_overlapping_versions_fail_before_publication(self):
        first = self.pipeline.publish(self.sources)
        bad = [dict(s) for s in self.sources]
        bad[0].pop("valid_from")
        with self.assertRaises(ValueError):
            self.pipeline.publish(bad)
        bad = [dict(s) for s in self.sources]
        bad[0]["valid_to"] = "2026-12-01"
        with self.assertRaisesRegex(ValueError, "overlapping"):
            self.pipeline.publish(bad)
        self.assertEqual(self.pipeline.state()["generation"], first["generation"])

    def test_conflicting_duplicate_and_duplicate_block_keys_rejected(self):
        changed = dict(self.sources[0], access=["other"])
        with self.assertRaisesRegex(ValueError, "conflicting"):
            self.pipeline.publish(self.sources + [changed])
        with self.assertRaisesRegex(ValueError, "duplicate block"):
            parse_markdown("# A\n<!-- block: one -->\na\n\n<!-- block: one -->\nb\n", "doc@v1", "fixture://a")

    def test_table_rows_keep_independent_identity_and_header_meaning(self):
        text = "# 标准\n<!-- block: limits -->\n| 条款ID | 城市 | 金额 |\n| --- | --- | --- |\n| R1 | 海岚 | 700 |\n| R2 | 云洲 | 600 |\n"
        rows = parse_markdown(text, "doc@v1", "fixture://table")
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["block_id"], rows[1]["block_id"])
        self.assertIn("城市：云洲；金额：600", rows[1]["text"])
        with self.assertRaises(ValueError):
            parse_markdown(text.replace("条款ID", "名称"), "doc@v1", "fixture://table")

    def test_incompatible_schema_cannot_be_activated(self):
        (self.root / "store" / "generations").mkdir()
        (self.root / "store" / "generations" / "bad.json").write_text(json.dumps({"schema": "future-version"}))
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.pipeline.activate("bad")

    def test_all_scenarios_produce_inspectable_evidence(self):
        for name in SCENARIOS:
            with self.subTest(name=name):
                destination = self.root / name
                report = run_scenario(name, destination)
                self.assertTrue(report["passed"], report)
                self.assertTrue((destination / "trace.jsonl").read_text())
                self.assertTrue((destination / "store" / "state.json").exists())


if __name__ == "__main__":
    unittest.main()
