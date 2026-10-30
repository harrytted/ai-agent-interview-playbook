"""A deliberately finite, observation-driven policy, not a language model.

It has no access to task IDs, variants, fixtures, stores, or the grading oracle.
"""

from __future__ import annotations


def finish(status, *, claims=None, refs=None, answer="", requested_fields=None):
    return {"tool_calls": [], "output": {"status": status, "claims": claims or [], "evidence_refs": refs or [], "answer": answer, "requested_fields": requested_fields or []}}


def decide(view: dict) -> dict:
    known = view["known"]
    if view["unknowns"]:
        return finish("clarification_required", answer="请补充出行日期后再判断制度版本。", requested_fields=list(view["unknowns"]))
    observations = view["observations"]
    if any(o["result"]["status"] == "conflicting_evidence" for o in observations):
        return finish("human_required", refs=sorted({r for o in observations for r in o["result"]["evidence_refs"]}), answer="同等级有效证据冲突，需要人工核对；暂不选取其中一个金额。")
    if any(o["result"].get("error", {}).get("code") == "permission_denied" for o in observations if o["result"].get("error")):
        # The runtime owns permission_denied; this output never fabricates access.
        return finish("insufficient_evidence", answer="当前身份无法取得所需证据。")
    dates = known.get("trip_dates", [known["trip_date"]])
    cities = known.get("cities", [known.get("city", "")])
    topic = known.get("topic", "lodging")
    evidence = view["evidence"]
    requests, claims = [], []
    for city in cities:
        for date in dates:
            docs = [d for d in evidence if d["topic"] == topic and d["city"] == city and d["valid_from"] <= date and (d["valid_to"] is None or date < d["valid_to"])]
            found = [d for d in docs if any("amount_cny" in c for c in d["clauses"])]
            if found:
                document = found[0]
                clause = next(c for c in document["clauses"] if "amount_cny" in c)
                claims.append({"kind": "lodging_limit", "city": city, "trip_date": date, "amount_cny": clause["amount_cny"], "document_id": document["document_id"], "clause_id": clause["clause_id"]})
                continue
            relevant = [o for o in observations if o["name"] in ("search_policy", "get_policy") and (o["result"].get("error") or {}).get("code") != "cancelled_state_changed" and o["arguments"].get("trip_date") == date and (o["arguments"].get("city") == city or o["name"] == "get_policy")]
            stale = next((o for o in relevant if o["result"]["status"] == "stale_evidence"), None)
            if stale and not any(o["name"] == "get_policy" for o in relevant):
                old = stale["result"]["data"]["documents"]
                requests.append({"name": "get_policy", "arguments": {"policy_id": old[0]["policy_id"], "trip_date": date}})
            elif relevant:
                return finish("insufficient_evidence", answer="已读取的资料不足以支持当前日期与问题，保留证据缺口。")
            elif known.get("policy_id"):
                requests.append({"name": "get_policy", "arguments": {"policy_id": known["policy_id"], "trip_date": date}})
            else:
                requests.append({"name": "search_policy", "arguments": {"query": topic, "city": city, "trip_date": date}})
    if requests:
        return _calls(requests, observations)
    if known.get("need_materials"):
        material = next((d for d in evidence if d["topic"] == "consultation"), None)
        if material:
            clause = material["clauses"][0]
            claims.append({"kind": "required_materials", "items": clause["items"], "document_id": material["document_id"], "clause_id": clause["clause_id"]})
        elif any(o["arguments"].get("policy_id") == "P20" for o in observations):
            return finish("insufficient_evidence", answer="金额资料齐全，但缺少咨询材料条款。")
        else:
            return _calls([{"name": "get_policy", "arguments": {"policy_id": "P20", "trip_date": known["trip_date"]}}], observations)
    refs = sorted({c["clause_id"] for c in claims})
    if known.get("create_ticket"):
        return _calls([{"name": "create_ticket", "arguments": {"title": known["title"], "city": known["city"], "trip_date": known["trip_date"], "amount_cny": known["amount_cny"], "evidence_refs": refs}}], observations)
    sentences = []
    for claim in claims:
        if claim["kind"] == "lodging_limit":
            comparison = ""
            if "amount_cny" in known:
                comparison = "；给定金额" + ("未超过" if known["amount_cny"] <= claim["amount_cny"] else "超过") + "此金额上限"
            sentences.append(f'{claim["trip_date"]}{claim["city"]}每晚上限{claim["amount_cny"]}元{comparison}。')
        else:
            sentences.append("咨询材料：日期、城市、金额、咨询事由；咨询不等于批准。")
    return finish("answered", claims=claims, refs=refs, answer="".join(sentences) + "本例只核对虚构制度的金额条件。")


def _calls(requests, observations):
    # IDs are local protocol correlation, never grading/task identifiers.
    return {"tool_calls": [{"call_id": f"call-{len(observations) + i + 1}", **request} for i, request in enumerate(requests)], "output": None}


def always_read(view):
    """Explicit controller-injected adversarial substitute used by the loop test."""
    return _calls([{"name": "search_policy", "arguments": {"query": "lodging", "city": view["known"]["city"], "trip_date": view["known"]["trip_date"]}}], view["observations"])
