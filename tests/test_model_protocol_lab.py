import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from examples.model_protocol_lab.lab import (
    FIXTURES, ProtocolError, TransportError, assemble, match_results,
    parse_sse, run_scenario, validate_answer, execute_calls,
)


class ProtocolLabTests(unittest.TestCase):
    def test_every_possible_network_boundary_preserves_chinese_and_tool_arguments(self):
        raw = (FIXTURES / "two-tools.sse").read_bytes()
        reference = assemble(parse_sse([raw]))
        self.assertEqual([c["arguments"]["city"] for c in reference["calls"]], ["海岚", "云洲"])
        for boundary in range(len(raw) + 1):
            self.assertEqual(assemble(parse_sse([raw[:boundary], raw[boundary:]])), reference)

    def test_sse_multiline_data_comments_cr_and_lf(self):
        raw = b': comment\revent: ping\rdata: {"type":\rdata: "ping"}\r\r'
        self.assertEqual(list(parse_sse([raw])), [{"type": "ping"}])

    def test_sse_ignores_one_leading_bom_across_network_boundaries(self):
        raw = (FIXTURES / "two-tools.sse").read_bytes()
        expected = assemble(parse_sse([raw]))
        prefixed = b'\xef\xbb\xbf' + raw
        for boundary in range(5):
            with self.subTest(boundary=boundary):
                self.assertEqual(assemble(parse_sse([prefixed[:boundary], prefixed[boundary:]])), expected)

    def test_incomplete_event_and_utf8_never_produce_completed_message(self):
        for raw in (b'event: ping\ndata: {"type":"ping"}', b'\xe6\xb5'):
            with self.assertRaises(TransportError):
                list(parse_sse([raw]))

    def test_transport_end_without_message_stop_and_out_of_order_events(self):
        events = list(parse_sse([(FIXTURES / "two-tools.sse").read_bytes()]))
        with self.assertRaises(TransportError):
            assemble(events[:-1])
        with self.assertRaises(ProtocolError):
            assemble(events[1:])
        with self.assertRaises(ProtocolError):
            assemble(events + [{"type": "ping"}])

    def test_message_termination_cannot_precede_blocks_or_allow_more_content(self):
        original = list(parse_sse([(FIXTURES / "two-tools.sse").read_bytes()]))
        for position in (1, 2, 6):
            events = deepcopy(original)
            ending = next(event for event in events if event["type"] == "message_delta")
            events.remove(ending)
            events.insert(position, ending)
            with self.subTest(position=position), self.assertRaises(ProtocolError):
                assemble(events)
        events = deepcopy(original)
        for event in events:
            if "index" in event:
                event["index"] += 1
        with self.assertRaises(ProtocolError):
            assemble(events)

    def test_malformed_indices_and_message_delta_raise_classified_protocol_error(self):
        original = list(parse_sse([(FIXTURES / "two-tools.sse").read_bytes()]))
        for kind in ("content_block_delta", "content_block_stop"):
            for bad in ([], {}, True):
                events = deepcopy(original)
                next(e for e in events if e["type"] == kind)["index"] = bad
                with self.assertRaises(ProtocolError):
                    assemble(events)
        for bad in ([], None, True):
            events = deepcopy(original)
            next(e for e in events if e["type"] == "message_delta")["delta"] = bad
            with self.assertRaises(ProtocolError):
                assemble(events)

    def test_result_id_set_bijective_and_ordered_by_call_not_arrival(self):
        calls = [{"id": "A"}, {"id": "B"}]
        results = [{"tool_use_id": "B"}, {"tool_use_id": "A"}]
        self.assertEqual(match_results(calls, results), list(reversed(results)))
        for bad in (results[:1], results + results[:1], [{"tool_use_id": "A"}, {"tool_use_id": "C"}]):
            with self.assertRaises(ProtocolError):
                match_results(calls, bad)

    def test_host_does_not_execute_unknown_tool_or_unrequested_identity_fields(self):
        observations = {"海岚": {"limit_cny": 700}}
        call = {"id": "one", "name": "lookup_policy", "arguments": {"city": "海岚", "trip_date": "2026-11-12"}}
        self.assertEqual(execute_calls([call], observations)[0]["tool_use_id"], "one")
        call["arguments"]["user_id"] = "administrator"
        with self.assertRaises(ProtocolError):
            execute_calls([call], observations)

    def test_truncated_parameters_are_not_parsed_or_dispatched(self):
        events = list(parse_sse([(FIXTURES / "two-tools.sse").read_bytes()]))
        deltas = [e for e in events if e["type"] == "content_block_delta"]
        deltas[-1]["delta"]["partial_json"] = "unfinished"
        reason = next(e for e in events if e["type"] == "message_delta")
        reason["delta"]["stop_reason"] = "max_tokens"
        self.assertEqual(assemble(events)["calls"], [])
        reason["delta"]["stop_reason"] = "tool_use"
        with self.assertRaises(ProtocolError):
            assemble(events)

    def test_evidence_check_transfers_to_changed_amount_and_identifier(self):
        evidence = {"new#3": {"city": "北湾", "limit_cny": 815}}
        good = {"claims": [{"city": "北湾", "limit_cny": 815, "reference": "new#3"}]}
        self.assertEqual(validate_answer(good, evidence), good)
        good["claims"][0]["limit_cny"] = 700
        with self.assertRaises(ProtocolError):
            validate_answer(good, evidence)

    def test_all_cli_scenarios_write_independent_grades(self):
        names = json.loads((FIXTURES / "expected.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            for name in names:
                self.assertTrue(run_scenario(name, folder)["passed"], name)
                self.assertTrue((Path(folder) / name / "trace.jsonl").is_file())

    def test_final_round_termination_is_checked_before_reading_answer_content(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, status in (("final-truncated", "truncated"), ("final-refusal", "refused")):
                self.assertTrue(run_scenario(name, folder)["passed"])
                result = json.loads((Path(folder) / name / "result.json").read_text())
                self.assertEqual(result["status"], status)
                self.assertNotIn("answer", result)
                self.assertIn("matched_results", result)

    def test_saved_failure_bytes_reproduce_the_reported_provider_response(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ("duplicate-id", "truncated", "refusal", "semantic-error"):
                with self.subTest(name=name):
                    run_scenario(name, folder)
                    path = Path(folder) / name
                    events = list(parse_sse([(path / "raw.sse").read_bytes()]))
                    if name == "duplicate-id":
                        with self.assertRaises(ProtocolError):
                            assemble(events)
                    elif name in ("truncated", "refusal"):
                        self.assertEqual(assemble(events)["status"], "truncated" if name == "truncated" else "refused")
                    else:
                        final = assemble(parse_sse([(path / "answer.sse").read_bytes()]))
                        answer = json.loads("".join(block["text"] for block in final["content"]))
                        observed = json.loads((FIXTURES / "observations.json").read_text())
                        evidence = {value["reference"]: value for value in observed.values()}
                        with self.assertRaises(ProtocolError):
                            validate_answer(answer, evidence)


if __name__ == "__main__":
    unittest.main()
