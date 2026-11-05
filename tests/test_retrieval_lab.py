"""Verify numerical mechanics and evidence boundaries, not model quality."""
from dataclasses import replace
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

from examples.advanced.retrieval_lab import (Claim, bm25_scores, candidates_demo, cosine,
                                            evidence_metrics, oracle_order, rank,
                                            reciprocal_rank_fusion, resolve_claims)


class RetrievalMechanicsTests(unittest.TestCase):
    def test_bm25_matches_an_independent_equal_length_calculation(self):
        docs = {"A": ["hotel", "hotel"], "B": ["hotel", "form"], "C": ["policy", "text"]}
        scores = bm25_scores(docs, ["hotel"])
        self.assertAlmostEqual(scores["A"], math.log(1.6) * 4.4 / 3.2)
        self.assertAlmostEqual(scores["B"], math.log(1.6))
        self.assertEqual(scores["C"], 0)
        self.assertEqual(bm25_scores(docs, ["hotel", "hotel"]), scores)
        self.assertEqual(bm25_scores(docs, ["unknown"]), dict.fromkeys(docs, 0))

    def test_saturation_and_length_are_different_effects(self):
        scores = bm25_scores({str(i): ["term"] * i for i in (1, 2, 3)}, ["term"], b=0)
        self.assertGreater(scores["2"] - scores["1"], scores["3"] - scores["2"])
        docs = {"short": ["term"], "long": ["term"] + ["padding"] * 9}
        self.assertGreater(bm25_scores(docs, ["term"])["short"], bm25_scores(docs, ["term"])["long"])
        no_length = bm25_scores(docs, ["term"], b=0)
        self.assertEqual(no_length["short"], no_length["long"])

    def test_empty_chunk_with_full_length_normalization_does_not_divide_by_zero(self):
        scores = bm25_scores({"empty": [], "text": ["term"]}, ["term"], b=1)
        self.assertEqual(scores["empty"], 0)
        self.assertGreater(scores["text"], 0)

    def test_zero_k1_removes_frequency_weight_without_dividing_unmatched_terms(self):
        scores = bm25_scores({"one": ["term"], "many": ["term"] * 8, "empty": []},
                             ["term", "unknown"], k1=0, b=1)
        self.assertEqual(scores["one"], scores["many"])
        self.assertAlmostEqual(scores["one"], math.log(1.6))
        self.assertEqual(scores["empty"], 0)

    def test_cosine_has_scale_invariance_but_requires_valid_vectors(self):
        self.assertAlmostEqual(cosine([1, 0], [0.8, 0.6]), 0.8)
        self.assertAlmostEqual(cosine([100, 0], [8, 6]), 0.8)
        for left, right in (([0, 0], [1, 0]), ([1], [1, 2]), ([math.nan], [1])):
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                cosine(left, right)

    def test_fusion_uses_rank_and_one_vote_per_retriever(self):
        scores = reciprocal_rank_fusion([["A", "B", "C"], ["C", "B", "D"]])
        self.assertEqual(rank(scores, 4), ["C", "B", "A", "D"])
        self.assertAlmostEqual(scores["A"], 1 / 61)
        self.assertAlmostEqual(scores["C"], 1 / 63 + 1 / 61)
        with self.assertRaises(ValueError):
            reciprocal_rank_fusion([["A", "A"]])
        self.assertEqual(rank({"B": 1.0, "A": 1.0}, 2), ["A", "B"])

    def test_filtering_after_a_limited_search_can_exhaust_the_pool(self):
        result = candidates_demo()
        self.assertEqual(result["top2_then_filter"], [])
        self.assertEqual(result["filter_then_exact_search"], ["valid"])

    def test_perfect_ordering_cannot_restore_a_missing_candidate(self):
        labels = {"A", "C"}
        ordered = oracle_order(["B", "A"], labels)
        self.assertEqual(set(ordered), {"A", "B"})
        metrics = evidence_metrics(ordered, labels, 2)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["reciprocal_rank"], 1)
        self.assertFalse(metrics["all_required_evidence_present"])
        complete = evidence_metrics(oracle_order(["A", "B", "C"], labels), labels, 2)
        self.assertTrue(complete["all_required_evidence_present"])

    def test_validity_is_half_open_and_scope_is_part_of_the_key(self):
        old = Claim("old", "P", "limit", "staff", "600", "2026-01-01", "2026-11-01")
        new = Claim("new", "P", "limit", "staff", "700", "2026-11-01")
        manager = replace(new, record_id="manager", scope="manager", value="900")
        query = dict(family="P", attribute="limit", scope="staff", allowed_ids={"old", "new", "manager"})
        self.assertEqual(resolve_claims([old, new, manager], **query, on_date="2026-10-31")["values"], ["600"])
        self.assertEqual(resolve_claims([old, new, manager], **query, on_date="2026-11-01")["values"], ["700"])

    def test_conflict_does_not_get_resolved_by_duplicate_votes_or_input_order(self):
        a = Claim("A", "P", "limit", "staff", "700", "2026-11-01")
        b = replace(a, record_id="B", value="500")
        copy = replace(a, record_id="copy")
        query = dict(family="P", attribute="limit", scope="staff", on_date="2026-11-12", allowed_ids={"A", "B", "copy"})
        result = resolve_claims([a, b, copy], **query)
        self.assertEqual(result["status"], "conflicting")
        self.assertEqual(result, resolve_claims([copy, b, a], **query))
        self.assertEqual(result["values"], ["500", "700"])

    def test_only_explicit_acyclic_same_key_precedence_resolves_disagreement(self):
        a = Claim("A", "P", "limit", "staff", "700", "2026-11-01")
        b, c = replace(a, record_id="B", value="500"), replace(a, record_id="C", value="400")
        query = dict(family="P", attribute="limit", scope="staff", on_date="2026-11-12", allowed_ids={"A", "B", "C"})
        result = resolve_claims([a, b, c], **query, precedence={("A", "B"), ("B", "C")})
        self.assertEqual(result, {"status": "supported", "values": ["700"], "references": ["A"]})
        for edges in ({("A", "B"), ("B", "A")}, {("A", "missing")}):
            with self.assertRaises(ValueError):
                resolve_claims([a, b, c], **query, precedence=edges)
        with self.assertRaises(ValueError):
            resolve_claims([a, replace(b, scope="manager")], **query, precedence={("A", "B")})

    def test_visibility_revocation_and_absence_are_not_conflicts(self):
        a = Claim("A", "P", "limit", "staff", "700", "2026-11-01")
        b = replace(a, record_id="B", value="500")
        query = dict(family="P", attribute="limit", scope="staff", on_date="2026-11-12")
        self.assertEqual(resolve_claims([a, b], **query, allowed_ids={"A"})["references"], ["A"])
        self.assertEqual(resolve_claims([a, b], **query, allowed_ids=set()),
                         {"status": "insufficient", "values": [], "references": []})

    def test_cli_all_reports_only_authored_mechanics(self):
        path = Path(__file__).resolve().parents[1] / "examples/advanced/retrieval_lab.py"
        result = subprocess.run([sys.executable, str(path), "--section", "all"], capture_output=True, text=True, check=True)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([row["section"] for row in rows], ["scoring", "candidates", "conflicts"])
        self.assertTrue(all(row["model_requests"] == 0 for row in rows))


if __name__ == "__main__":
    unittest.main()
