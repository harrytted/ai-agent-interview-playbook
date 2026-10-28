"""Independent arithmetic and edge-case checks for the educational examples."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import math
from pathlib import Path
import unittest


PATH = Path(__file__).resolve().parents[1] / "examples/foundations/math_lab.py"
SPEC = importlib.util.spec_from_file_location("foundations_math", PATH)
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class FoundationsMathTests(unittest.TestCase):
    def test_softmax_is_normalized_and_stable_under_large_shift(self):
        self.assertEqual(lab.softmax([1000, 1000]), [0.5, 0.5])
        for actual, expected in zip(lab.softmax([1000, 1001]), [1 / (1 + math.e), math.e / (1 + math.e)]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(sum(lab.softmax([-1000, 0, 1000])), 1)

    def test_attention_hand_computed_weighted_average_and_mask(self):
        weights, result = lab.attention([1, 0], [[1, 0], [0, 1]], [[2, 0], [0, 4]])
        self.assertAlmostEqual(weights[0], 0.6697615493266569)
        self.assertAlmostEqual(result[0], 1.3395230986533138)
        self.assertAlmostEqual(result[1], 1.3209538026933725)
        self.assertEqual(lab.attention([1, 0], [[1, 0], [0, 1]], [[2, 0], [0, 4]], [True, False]), ([1.0, 0.0], [2.0, 0.0]))

    def test_attention_rejects_inconsistent_dimensions_and_empty_mask(self):
        invalid = [([1], [[1, 2]], [[1]]), ([1], [[1]], []), ([1], [[1], [2]], [[1], [1, 2]]),
                   ([1], [[1]], [[1]], [False]), ([1], [[1]], [[1]], [1])]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(ValueError):
                lab.attention(*args)

    def test_cosine_known_geometry_scale_and_undefined_zero(self):
        self.assertAlmostEqual(lab.cosine([3, 4], [6, 8]), 1)
        self.assertEqual(lab.cosine([1, 0], [0, 1]), 0)
        self.assertAlmostEqual(lab.cosine([1, 0], [-2, 0]), -1)
        self.assertAlmostEqual(lab.cosine([1e200, 1e200], [1e200, 1e200]), 1)
        self.assertAlmostEqual(lab.cosine([1.7e308, 1.7e308], [1.7e308, 1.7e308]), 1)
        self.assertAlmostEqual(lab.cosine([1.7e308, 1.7e308], [-1.7e308, -1.7e308]), -1)
        for a, b in [([0, 0], [1, 0]), ([1], [1, 0])]:
            with self.assertRaises(ValueError):
                lab.cosine(a, b)

    def test_invalid_numeric_values_are_rejected(self):
        for values in ([], [True], [float("inf")], [float("nan")], ["1"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                lab.softmax(values)

    def test_rrf_uses_one_based_ranks_and_fuses_shared_documents(self):
        fused = lab.rrf([["A", "B", "C"], ["C", "B", "D"]])
        self.assertEqual([doc for doc, _ in fused], ["C", "B", "A", "D"])
        values = dict(fused)
        self.assertAlmostEqual(values["C"], 1 / 63 + 1 / 61)
        self.assertAlmostEqual(values["B"], 2 / 62)
        self.assertAlmostEqual(values["A"], 1 / 61)
        self.assertEqual(lab.rrf([]), [])

    def test_rrf_rejects_duplicate_ids_and_invalid_constant(self):
        for args in [([["A", "A"]],), ([[""]],), ([["A"]], -1), ([["A"]], True), ([["A"]], float("inf"))]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                lab.rrf(*args)

    def test_metrics_distinguish_recall_reciprocal_rank_and_ndcg(self):
        metrics = lab.retrieval_metrics(["B", "A", "C"], {"A", "C", "D"}, 3)
        self.assertAlmostEqual(metrics["precision_at_k"], 2 / 3)
        self.assertAlmostEqual(metrics["recall_at_k"], 2 / 3)
        self.assertEqual(metrics["reciprocal_rank_at_k"], 0.5)
        self.assertAlmostEqual(metrics["ndcg_at_k"], (1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3) + 0.5))

    def test_no_relevant_documents_short_rankings_and_cutoff_are_explicit(self):
        missing = lab.retrieval_metrics(["B"], set(), 3)
        self.assertIsNone(missing["recall_at_k"])
        self.assertIsNone(missing["ndcg_at_k"])
        self.assertEqual(missing["reciprocal_rank_at_k"], 0)
        self.assertEqual(lab.retrieval_metrics(["A"], {"A"}, 3)["precision_at_k"], 1 / 3)
        self.assertEqual(lab.retrieval_metrics(["B", "A"], {"A"}, 1)["recall_at_k"], 0)
        for args in [(["A", "A"], {"A"}, 2), (["A"], {"A"}, 0), (["A"], {"A"}, True)]:
            with self.assertRaises(ValueError):
                lab.retrieval_metrics(*args)

    def test_cli_outputs_all_three_examples_as_finite_json(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            self.assertEqual(lab.main(["--section", "all"]), 0)
        examples = [json.loads(line) for line in capture.getvalue().splitlines()]
        self.assertEqual([x["section"] for x in examples], ["attention", "retrieval", "metrics"])
        for example in examples:
            json.dumps(example, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
