"""HTTP fixtures exercise the optional adapter without paid API requests."""
import copy
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from examples.policy_agent.live import API_VERSION, LiveError, LivePolicy


def reply(content, stop="tool_use"):
    return {"id": "msg-fixture", "model": "fixture-model", "stop_reason": stop,
            "content": content, "usage": {"input_tokens": 12, "output_tokens": 4}}


def tool(call_id="c1", name="search_policy"):
    return {"type": "tool_use", "id": call_id, "name": name,
            "input": {"query": "住宿标准", "city": "海岚", "trip_date": "2026-11-12"}}


class Response(BytesIO):
    headers = {"request-id": "req-fixture"}


class PolicyLiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fixture-secret", "ANTHROPIC_MODEL": "fixture-model"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.requests = []
        self.view = {"goal": "查询金额", "known": {"city": "海岚", "trip_date": "2026-11-12"},
                     "messages": [], "unknowns": [], "observations": [], "evidence": []}

    def policy(self, replies):
        queue = list(replies)

        def opener(req, timeout):
            self.requests.append((req, timeout, json.loads(req.data)))
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return Response(json.dumps(item).encode("utf-8"))

        return LivePolicy(self.root, {"opener": opener})

    def observations(self, ids):
        self.view["observations"] = [
            {"call_id": call_id, "result": {"call_id": call_id, "status": "error" if i else "ok",
                                           "data": {}, "evidence_refs": [], "error": None}}
            for i, call_id in enumerate(ids)]

    def test_all_tool_results_preserve_assistant_and_match_ids_across_resume(self):
        original = [{"type": "text", "text": "核对两处资料"}, tool("a"), tool("b")]
        first = self.policy([reply(original)])
        result = first(self.view)
        self.assertEqual([c["call_id"] for c in result["tool_calls"]], ["a", "b"])
        self.observations(["a", "b"])
        self.view["known"]["city"] = "云洲"
        second = self.policy([reply([{"type": "text", "text": json.dumps({
            "status": "insufficient_evidence", "claims": [], "evidence_refs": [],
            "answer": "需要继续取证", "requested_fields": []})}], "end_turn")])
        self.assertEqual(second(self.view)["output"]["status"], "insufficient_evidence")
        req, timeout, payload = self.requests[-1]
        self.assertLessEqual(timeout, 20)
        self.assertEqual(payload["messages"][1], {"role": "assistant", "content": original})
        results = payload["messages"][2]["content"]
        self.assertEqual([r["tool_use_id"] for r in results[:2]], ["a", "b"])
        self.assertTrue(results[1]["is_error"])
        self.assertIn("云洲", results[2]["text"])
        self.assertEqual(req.get_header("Anthropic-version"), API_VERSION)
        self.assertEqual({t["name"] for t in payload["tools"]}, {"search_policy", "get_policy"})
        for key in ("temperature", "top_p", "top_k"):
            self.assertNotIn(key, payload)
        saved = (self.root / "provider.json").read_text()
        self.assertNotIn("fixture-secret", saved)
        self.assertIn("req-fixture", saved)

    def test_missing_result_prevents_second_http_call(self):
        policy = self.policy([reply([tool("a"), tool("b")])])
        policy(self.view)
        self.observations(["a"])
        with self.assertRaisesRegex(LiveError, "Every pending"):
            policy(self.view)
        self.assertEqual(len(self.requests), 1)

    def test_disallowed_write_duplicate_ids_and_malformed_batch_rejected(self):
        for blocks in ([tool(name="create_ticket")], [tool(), tool()], [{"type": "tool_use", "id": "a"}]):
            with self.subTest(blocks=blocks):
                (self.root / "provider.json").unlink(missing_ok=True)
                with self.assertRaises(LiveError) as caught:
                    self.policy([reply(blocks)])(self.view)
                self.assertEqual(caught.exception.status, "invalid_output")

    def test_stop_reasons_and_unstructured_final_never_become_success(self):
        for stop, text in (("max_tokens", "partial"), ("refusal", "拒绝"), ("unknown", ""), ("end_turn", "已完成")):
            with self.subTest(stop=stop):
                (self.root / "provider.json").unlink(missing_ok=True)
                with self.assertRaises(LiveError):
                    self.policy([reply([{"type": "text", "text": text}], stop)])(self.view)

    def test_network_and_auth_errors_not_retried_or_logged_with_secrets(self):
        for exc in (URLError("fixture-secret"), HTTPError("https://fixture.invalid", 401, "fixture-secret", {}, None)):
            with self.subTest(error=type(exc).__name__):
                (self.root / "provider.json").unlink(missing_ok=True)
                before = len(self.requests)
                with self.assertRaises(LiveError) as caught:
                    self.policy([exc])(self.view)
                self.assertEqual(len(self.requests), before + 1)
                self.assertNotIn("fixture-secret", str(caught.exception))
                self.assertNotIn("fixture-secret", (self.root / "provider.json").read_text())

    def test_six_attempt_limit_survives_reconstruction(self):
        for _ in range(6):
            with self.assertRaises(LiveError):
                self.policy([URLError("offline")])(self.view)
        with self.assertRaisesRegex(LiveError, "budget"):
            self.policy([])(self.view)
        self.assertEqual(len(self.requests), 6)

    def test_missing_key_does_not_silently_use_offline_or_network(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            with self.assertRaisesRegex(LiveError, "ANTHROPIC_API_KEY"):
                LivePolicy(self.root)

    def test_expired_segment_stops_before_network(self):
        ticks = iter([0, 61])
        policy = LivePolicy(self.root, {"clock": lambda: next(ticks), "opener": lambda *a, **k: self.fail("network")})
        with self.assertRaisesRegex(LiveError, "deadline"):
            policy(self.view)

    def test_revoked_historical_result_is_not_replayed_to_provider(self):
        policy = self.policy([reply([tool("a")]), reply([tool("b")])])
        policy(self.view)
        self.observations(["a"])
        self.view["observations"][0]["result"]["data"] = {"documents": [{"text": "restricted-body"}]}
        policy(self.view)
        self.observations(["a", "b"])
        self.view["observations"][0]["result"]["data"] = {"documents": []}
        resumed = self.policy([])
        with self.assertRaisesRegex(LiveError, "access changed"):
            resumed(self.view)
        self.assertEqual(len(self.requests), 2)


if __name__ == "__main__":
    unittest.main()
