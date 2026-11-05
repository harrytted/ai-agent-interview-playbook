from contextlib import redirect_stdout
import importlib.util
import io
import json
import math
from pathlib import Path
import unittest


PATH = Path(__file__).resolve().parents[1] / "examples/advanced/training_objectives.py"
SPEC = importlib.util.spec_from_file_location("training_objectives", PATH)
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


def finite_difference(loss, parameters, index, step=1e-6):
    upper, lower = list(parameters), list(parameters)
    upper[index] += step
    lower[index] -= step
    return (loss(upper) - loss(lower)) / (2 * step)


class TrainingObjectivesTests(unittest.TestCase):
    def test_two_action_turns_use_four_targets_not_all_seven_rows(self):
        result = lab.sft_demo()
        before = result["before"]
        self.assertEqual(before["target_count"], 4)
        self.assertAlmostEqual(before["loss"], math.log(20) / 4)
        for actual, expected in zip(before["gradient"], [0, -0.125, 0.1875, 0, 0, -0.05, 0.125]):
            self.assertAlmostEqual(actual, expected)

    def test_ignored_targets_do_not_contribute_with_action_probabilities_fixed(self):
        first = lab.masked_sft_objective([0.0, None, math.log(3)], [1, None, 0], [1, 0, 1])
        second = lab.masked_sft_objective([0.0, 99.0, math.log(3)], [1, 1, 0], [1, 0, 1])
        self.assertEqual(first, second)
        self.assertEqual(first["gradient"][1], 0)

    def test_sft_analytic_gradient_matches_finite_differences(self):
        logits, labels, mask = [0.0, 2.0, math.log(3), math.log(4)], [1, 0, 0, 1], [1, 0, 1, 1]
        objective = lambda values: lab.masked_sft_objective(values, labels, mask)["loss"]
        gradients = lab.masked_sft_objective(logits, labels, mask)["gradient"]
        for index, gradient in enumerate(gradients):
            self.assertAlmostEqual(gradient, finite_difference(objective, logits, index), places=8)

    def test_sft_handles_large_logits_without_log_zero(self):
        correct = lab.masked_sft_objective([1000, -1000], [1, 0], [1, 1])
        incorrect = lab.masked_sft_objective([1000, -1000], [0, 1], [1, 1])
        self.assertEqual(correct["loss"], 0)
        self.assertEqual(incorrect["loss"], 1000)

    def test_sft_rejects_missing_targets_bad_masks_and_invalid_action_values(self):
        cases = [([], [], []), ([None], [None], [0]), ([0], [1], [True]),
                 ([0], [1], [2]), ([0], [True], [1]), ([float("nan")], [1], [1]),
                 ([None], [1], [1]), ([0], [], [1])]
        for columns in cases:
            with self.subTest(columns=columns), self.assertRaises(ValueError):
                lab.masked_sft_objective(*columns)

    def test_clipping_covers_both_advantage_signs_and_keeps_bad_directions_active(self):
        cases = [(1.4, 1, 1.2, 0), (0.6, -1, -0.8, 0),
                 (0.6, 1, 0.6, 1), (1.4, -1, -1.4, -1)]
        for ratio, advantage, expected, derivative in cases:
            with self.subTest(ratio=ratio, advantage=advantage):
                value, gradient = lab.clipped_surrogate(ratio, advantage)
                self.assertAlmostEqual(value, expected)
                self.assertEqual(gradient, derivative)
                numeric = (lab.clipped_surrogate(ratio + 1e-6, advantage)[0]
                           - lab.clipped_surrogate(ratio - 1e-6, advantage)[0]) / 2e-6
                self.assertAlmostEqual(gradient, numeric, places=8)

    def test_clip_kinks_use_documented_flat_side_subgradient(self):
        self.assertEqual(lab.clipped_surrogate(1.2, 1), (1.2, 0))
        self.assertEqual(lab.clipped_surrogate(0.8, -1), (-0.8, 0))
        self.assertEqual(lab.clipped_surrogate(1.4, 0), (0, 0))

    def test_policy_objective_matches_hand_calculated_surrogate_and_exact_kl(self):
        result = lab.policy_demo()["before"]
        expected_kl = 0.7 * math.log(1.4) + 0.3 * math.log(0.6)
        for actual, expected in zip(result["surrogates"], [1.2, -0.8, 0.6, -1.4]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result["policy_loss"], 0.1)
        self.assertAlmostEqual(result["mean_kl"], expected_kl)
        self.assertAlmostEqual(result["loss"], 0.1 + 0.1 * expected_kl)

    def test_policy_gradient_matches_finite_differences_for_both_binary_actions(self):
        probabilities = [0.7, 0.3, 0.3, 0.7, 0.55, 0.45]
        logits = [math.log(p / (1 - p)) for p in probabilities]
        actions, advantages = [1, 1, 1, 1, 0, 0], [1, -1, 1, -1, 1, -1]
        old, reference = [0.5] * 6, [0.45] * 6
        objective = lambda values: lab.bernoulli_policy_objective(
            values, actions, advantages, old, reference)["loss"]
        gradients = lab.bernoulli_policy_objective(logits, actions, advantages, old, reference)["gradient"]
        for index, gradient in enumerate(gradients):
            self.assertAlmostEqual(gradient, finite_difference(objective, logits, index), places=8)

    def test_zero_advantages_do_not_imply_zero_total_gradient_when_kl_is_enabled(self):
        parameters = ([math.log(3)], [1], [0], [0.5], [0.5])
        unregularized = lab.bernoulli_policy_objective(*parameters, beta=0)
        regularized = lab.bernoulli_policy_objective(*parameters, beta=0.1)
        self.assertEqual(unregularized["gradient"], [0])
        self.assertGreater(regularized["gradient"][0], 0)
        self.assertGreater(regularized["mean_kl"], 0)
        self.assertEqual(lab.bernoulli_policy_objective([0], [1], [0], [0.5], [0.5])["mean_kl"], 0)

    def test_demonstrated_parameter_steps_reduce_only_the_fixed_sample_objectives(self):
        for demo in (lab.sft_demo, lab.policy_demo):
            result = demo()
            self.assertLess(result["after"]["loss"], result["before"]["loss"])

    def test_policy_rejects_undefined_ratios_and_bad_hyperparameters(self):
        for old, reference in [(0, 0.5), (1, 0.5), (0.5, 0), (0.5, 1)]:
            with self.assertRaises(ValueError):
                lab.bernoulli_policy_objective([0], [1], [1], [old], [reference])
        for keyword in ({"epsilon": 0}, {"epsilon": 1}, {"beta": -1}, {"beta": float("nan")}):
            with self.assertRaises(ValueError):
                lab.bernoulli_policy_objective([0], [1], [1], [0.5], [0.5], **keyword)
        for ratio in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                lab.clipped_surrogate(ratio, 1)

    def test_cli_emits_bounded_json_for_both_exercises(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(lab.main(["--section", "all"]), 0)
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([row["section"] for row in rows], ["sft", "policy"])


if __name__ == "__main__":
    unittest.main()
