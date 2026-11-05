"""Check pairing, discordance and uncertainty rather than one rounded score."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from examples.advanced.evaluation_lab import DEMO_PAIRS, analyze_pairs, main, mcnemar_exact


class PairedEvaluationTests(unittest.TestCase):
    def test_repairs_and_regressions_reconstruct_the_success_difference(self):
        result = analyze_pairs(DEMO_PAIRS)
        self.assertEqual((result["both_pass"], result["both_fail"]), (5, 3))
        self.assertEqual(len(result["improved_ids"]), 3)
        self.assertEqual(result["regressed_ids"], ["task-12"])
        self.assertEqual(result["baseline_success_rate"], 0.5)
        self.assertAlmostEqual(result["candidate_success_rate"], 2 / 3)
        self.assertAlmostEqual(result["paired_difference"], 2 / 12)
        self.assertEqual(result["exact_mcnemar_pvalue"], 0.625)
        self.assertLess(result["bootstrap"]["low"], 0)
        self.assertGreater(result["bootstrap"]["high"], 0)

    def test_identical_outputs_have_no_paired_sampling_variation(self):
        records = [{"task_id": str(i), "baseline": bool(i % 2), "candidate": bool(i % 2)}
                   for i in range(8)]
        result = analyze_pairs(records)
        self.assertEqual(result["paired_difference"], 0)
        self.assertEqual(result["exact_mcnemar_pvalue"], 1)
        self.assertEqual((result["bootstrap"]["low"], result["bootstrap"]["high"]), (0, 0))

    def test_swapping_systems_reverses_difference_but_not_discordance_test(self):
        original = analyze_pairs(DEMO_PAIRS)
        swapped = analyze_pairs([
            {"task_id": r["task_id"], "baseline": r["candidate"], "candidate": r["baseline"]}
            for r in DEMO_PAIRS
        ])
        self.assertEqual(original["exact_mcnemar_pvalue"], swapped["exact_mcnemar_pvalue"])
        self.assertAlmostEqual(original["paired_difference"], -swapped["paired_difference"])
        self.assertAlmostEqual(original["bootstrap"]["low"], -swapped["bootstrap"]["high"])
        self.assertAlmostEqual(original["bootstrap"]["high"], -swapped["bootstrap"]["low"])

    def test_seeded_analysis_is_reproducible_and_order_independent(self):
        self.assertEqual(analyze_pairs(DEMO_PAIRS), analyze_pairs(list(reversed(DEMO_PAIRS))))

    def test_exact_test_matches_small_binomial_tail_and_is_symmetric(self):
        self.assertEqual(mcnemar_exact(0, 0), 1)
        self.assertEqual(mcnemar_exact(6, 0), 0.03125)
        self.assertEqual(mcnemar_exact(0, 6), 0.03125)
        self.assertEqual(mcnemar_exact(4, 4), 1)
        for counts in [(-1, 1), (True, 1), (1.5, 2)]:
            with self.assertRaises(ValueError):
                mcnemar_exact(*counts)

    def test_missing_labels_duplicate_ids_and_invalid_sampling_fail_explicitly(self):
        invalid = [[], {}, [None], [{"task_id": "a", "baseline": True}],
                   [{"task_id": "a", "baseline": 1, "candidate": False}],
                   [DEMO_PAIRS[0], DEMO_PAIRS[0]]]
        for records in invalid:
            with self.subTest(records=records), self.assertRaises(ValueError):
                analyze_pairs(records)
        for kwargs in [{"resamples": 0}, {"resamples": True}, {"resamples": 100001},
                       {"confidence": 0}, {"confidence": float("nan")},
                       {"confidence": True}, {"seed": True}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                analyze_pairs(DEMO_PAIRS, **kwargs)

    def test_cli_accepts_observed_pairs_and_marks_their_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pairs.json"
            source.write_text(json.dumps(DEMO_PAIRS))
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--input", str(source), "--resamples", "100"]), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["evidence"], "provided_outcomes")
            self.assertEqual(report["model_requests"], 0)


if __name__ == "__main__":
    unittest.main()
