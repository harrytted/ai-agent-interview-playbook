import importlib.util
import json
from pathlib import Path
import unittest
import wave


ROOT = Path(__file__).resolve().parents[1] / "examples/multimodal_lab"
SPEC = importlib.util.spec_from_file_location("multimodal_lab", ROOT / "lab.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class MultimodalLabTests(unittest.TestCase):
    def session(self, name="normal"):
        state = lab.Session()
        for line in (ROOT / "fixtures" / (name+".jsonl")).read_text().splitlines():
            state.apply(json.loads(line))
        return state

    def test_fixed_scenarios_match_separate_expected_values(self):
        for name in lab.SCENARIOS:
            with self.subTest(name=name):
                result, _ = lab.run_scenario(name)
                self.assertTrue(result["passed"], result)

    def test_corrected_city_cannot_use_late_old_policy(self):
        state = self.session()
        state.apply({"type": "tool_start", "call_id": "old"})
        state.apply({"type": "transcript", "stage": "final", "evidence_id": "turn-1",
                     "city": "另一个城市", "date": "2026-11-13", "amount": 650})
        state.apply({"type": "tool_result", "call_id": "old", "city": "海岚", "limit": 900, "source": "old-policy"})
        result = state.result()
        self.assertEqual(result["status"], "waiting_policy")
        self.assertIsNone(result["draft"])
        state.apply({"type": "tool_start", "call_id": "new"})
        state.apply({"type": "tool_result", "call_id": "new", "city": "另一个城市", "limit": 600, "source": "new-policy"})
        self.assertTrue(state.result()["draft"]["exceeds_limit"])
        self.assertEqual(state.result()["draft"]["policy_source"], "new-policy")

    def test_interim_never_changes_authoritative_conditions(self):
        state = self.session()
        version = state.condition_version
        state.apply({"type": "transcript", "stage": "interim", "city": "错误城市", "amount": 6500})
        self.assertEqual(state.condition_version, version)
        self.assertEqual(state.result()["draft"]["amount"], 650)

    def test_conflicting_media_requires_confirmation_even_with_valid_policy(self):
        state = self.session("uncertain")
        self.assertEqual(state.result()["status"], "needs_confirmation")
        self.assertIsNone(state.result()["draft"])

    def test_grading_rejects_wrong_amount_source_or_limit_conclusion(self):
        result = self.session("correction").result()
        expected = json.loads((ROOT / "expected.json").read_text())["correction"]
        for field, value in (("amount", 6500), ("policy_source", "wrong-policy"), ("exceeds_limit", True),
                             ("date", "2026-10-12")):
            changed = json.loads(json.dumps(result))
            changed["draft"][field] = value
            with self.subTest(field=field):
                self.assertFalse(all(lab.grade_result(changed, expected).values()))

    def test_nonfinite_amounts_and_media_positions_cannot_become_business_facts(self):
        for value in (True, -1, float("nan"), float("inf"), "650"):
            state = self.session()
            with self.subTest(value=value), self.assertRaises(ValueError):
                state.apply({"type": "transcript", "stage": "final", "evidence_id": "turn-1",
                             "city": "海岚", "date": "2026-11-12", "amount": value})

    def test_region_and_audio_span_must_stay_inside_source(self):
        state = self.session()
        for event in [{"type": "evidence", "id": "bad", "media_id": "receipt", "region": [600, 0, 100, 50], "confidence": "clear"},
                      {"type": "evidence", "id": "bad", "media_id": "audio", "time": [3, 8], "confidence": "clear"}]:
            with self.subTest(event=event), self.assertRaises(ValueError):
                state.apply(event)

    def test_unknown_transcript_source_and_duplicate_call_result_rejected(self):
        state = self.session()
        with self.assertRaises(ValueError):
            state.apply({"type": "transcript", "stage": "final", "evidence_id": "missing", "city": "海岚", "date": "2026-11-12", "amount": 650})
        with self.assertRaises(ValueError):
            state.apply({"type": "tool_result", "call_id": "policy-1", "city": "海岚", "limit": 700, "source": "duplicate"})

    def test_cancelled_generation_cannot_expand_heard_history(self):
        state = self.session("interruption")
        state.apply({"type": "playback", "generation": "g1", "position": 4})
        self.assertEqual(state.audio["history_seconds"], 1.25)
        self.assertEqual(state.audio["played_seconds"], 1.25)
        self.assertEqual(state.audio["ignored_late_chunks"], 2)

    def test_generated_replay_cannot_reopen_cancelled_id_or_reset_history(self):
        state = self.session("interruption")
        before = dict(state.audio)
        with self.assertRaises(ValueError):
            state.apply({"type": "audio_generated", "generation": "g1", "duration": 4})
        self.assertEqual(state.audio, before)
        state.apply({"type": "playback", "generation": "g1", "position": 3.8})
        self.assertTrue(state.audio["cancelled"])
        self.assertEqual(state.audio["history_seconds"], 1.25)
        self.assertEqual(state.audio["played_seconds"], 1.25)
        state.apply({"type": "audio_generated", "generation": "g2", "duration": 2})
        state.apply({"type": "playback", "generation": "g2", "position": 0.5})
        self.assertFalse(state.audio["cancelled"])
        self.assertEqual(state.audio["played_seconds"], 0.5)
        self.assertEqual(state.result()["audio_generations"]["g1"]["history_seconds"], 1.25)

    def test_late_long_generation_is_ignored_before_current_duration_validation(self):
        state = lab.Session()
        state.apply({"type": "audio_generated", "generation": "g1", "duration": 4})
        state.apply({"type": "playback", "generation": "g1", "position": 1})
        state.apply({"type": "audio_generated", "generation": "g2", "duration": 2})
        state.apply({"type": "playback", "generation": "g1", "position": 3.8})
        state.apply({"type": "interrupt", "generation": "g1", "position": 3.9})
        self.assertEqual(state.audio["generation"], "g2")
        self.assertEqual(state.audio["played_seconds"], 0)
        self.assertEqual(state.audio["history_seconds"], 0)
        self.assertFalse(state.audio["cancelled"])
        self.assertEqual(state.audio["ignored_late_chunks"], 2)
        self.assertEqual(state.audio_generations["g1"]["played_seconds"], 1)
        state.apply({"type": "playback", "generation": "g2", "position": 1.5})
        self.assertEqual(state.audio["played_seconds"], 1.5)
        with self.assertRaises(ValueError):
            state.apply({"type": "playback", "generation": "g2", "position": 3.8})
        with self.assertRaises(ValueError):
            state.apply({"type": "audio_generated", "generation": "g1", "duration": 4})

    def test_generated_audio_is_reproducible_pcm_cue_not_a_recording(self):
        with wave.open(str(ROOT / "assets/playback-tone.wav"), "rb") as cue:
            self.assertEqual(cue.getnchannels(), 1)
            self.assertEqual(cue.getsampwidth(), 2)
            self.assertEqual(cue.getnframes()/cue.getframerate(), 4)
            self.assertGreater(len(set(cue.readframes(1000))), 10)


if __name__ == "__main__":
    unittest.main()
