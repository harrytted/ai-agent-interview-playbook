# 00 · 先走完一次 Agent 任务

小明问：“我在 2026 年 11 月 12 日去海岚出差，住宿每晚 650 元，超过普通员工上限吗？”先别猜答案。这个问题最适合用来观察 Agent 的基本机制：系统要取得制度、检查适用条件，再决定能否回答。

本单元面向会 Python 函数、字典和 JSON 的读者，默认只用 Python 3.10+ 标准库，无需密钥或网络。完成后，你应能解释模型和执行器的分工，指出工具结果何时成为下一轮输入，并改变一个条件预测行为。所有人名、城市、制度和金额均为虚构教学数据；这里只判断本例金额条件，不代表真实报销资格。

## 先建立一个工作定义

本课程用 **Agent 系统**指围绕目标、根据当前观察选择行动并接收反馈的系统。应用中的模型可以提出下一步，运行时负责检查、执行、更新状态和停止。模型生成 `search_policy(...)` 只是动作请求；Python 执行工具后取得资料，才有可用观察。

规划是安排下一步及其依赖，可以由模型承担，也可以由程序约束；长期记忆是跨任务保留信息的一种选择。本例先不引入独立规划器或跨会话用户记忆，仍能说明观察、决定、执行、反馈的关系。离线模式用有限规则代替模型，便于检查控制机制；它不展示真实模型的自然语言理解能力。[定义与复杂度取舍参考](https://www.anthropic.com/research/building-effective-agents)

![G1：用户目标进入运行时，策略提出动作，运行时校验后调用工具，观察更新状态并进入下一次决定](../website/assets/diagrams/G1-system-flow.svg)

读图时先找到三条不同的信息：用户目标、拟执行的动作、执行后取得的观察。可信身份由运行时提供，不由模型自行填写。问自己：“系统说了已完成，环境中应有什么证据？”在查询任务中是有效条款与正确比较；创建任务中还必须有真实后端对象。

## 两份资料，先手算一次

| 文档 | 生效区间 | 普通员工海岚每晚上限 |
| --- | --- | --- |
| P17-v1，第4条 | 2026-01-01 ≤ 日期 < 2026-11-01 | 600 元 |
| P17-v2，第4条 | 日期 ≥ 2026-11-01 | 700 元 |

11 月 12 日适用 v2，因此 650 ≤ 700，金额条件未超限。将日期改成 10 月 31 日，适用 v1，650 > 600。不能只看到“700元”就答可以；先确认对象、日期与来源。完整记录在 [政策数据](../examples/policy_agent/data/policies.json)，标准答案由 [独立期望](../examples/policy_agent/data/expected.json)保存，策略不能读取它。

## 正常路径：让工具结果改变下一步

在仓库根目录运行。`run-id` 标识一份保留的运行目录；重做时换一个新名称，不覆盖之前的证据。

```bash
python3 -m examples.policy_agent run --task T01 --mode offline --run-id intro-t01
```

这里应观察三个阶段：没有制度时提出检索；取得有效条款后比较金额；输出带证据的结论。先用下表阅读，再打开 `.local/policy_agent/intro-t01/trace.jsonl` 对照实际事件。下面是阅读提纲，并非供应商消息原文：

| 时刻 | 当前可见信息 | 下一步 | 为什么 |
| --- | --- | --- | --- |
| 检索前 | 海岚、11月12日、650元；没有制度观察 | `search_policy` | 回答需要外部证据 |
| 工具返回后 | P17-v2#4、有效日期、700元 | 比较并回答 | 必要金额证据已齐 |
| 任务结束 | 条款、比较结果、终态 | 不再调用工具 | 当前问答已满足验收 |

![G3：模型或策略提出工具调用，运行时执行后将对应 call_id 的结果送入下一轮输入](../website/assets/diagrams/G3-tool-roundtrip.svg)

图中的“回填”是关键：工具结果必须关联原调用，并成为下一轮实际可见的信息。只把它写到日志、却不给策略看，下一步仍可能按旧前提走。离线策略的 [实现](../examples/policy_agent/policies.py)读取可见观察，不按 T01 等题号决定答案。

金额主张校验后，程序用用户金额与有效上限计算并渲染比较结论，不直接信任模型自述“已完成”。正常回答应包含以下事实：日期为2026-11-12；海岚 staff 上限700元；依据P17-v2#4；650元未超过本例金额上限。`answered` 只说明这次查询已作答，不代表咨询工单已创建。

## 对照一份实际离线记录

仓库保存了[正常路径的完整trace](../examples/policy_agent/traces/normal/trace.jsonl)、[策略输入快照](../examples/policy_agent/traces/normal/context.json)与[结果](../examples/policy_agent/traces/normal/result.json)。它们来自 `teaching-normal` 这次离线运行；你重跑的run_id可以不同。六条事件完整如下，策略替代了模型，`simulated=true`明确标注教学环境：

<details><summary>展开正常路径的六条实际事件</summary>

```jsonl
{"task_id": "T01", "run_id": "teaching-normal", "seq": 1, "state_revision": 1, "event": "run_started", "mode": "offline", "fixture": null, "simulated": true}
{"task_id": "T01", "run_id": "teaching-normal", "seq": 2, "state_revision": 1, "event": "decision", "decision": {"tool_calls": [{"call_id": "call-1", "name": "search_policy", "arguments": {"query": "lodging", "city": "海岚", "trip_date": "2026-11-12"}}], "output": null}}
{"task_id": "T01", "run_id": "teaching-normal", "seq": 3, "state_revision": 1, "event": "tool_started", "call_id": "call-1", "name": "search_policy", "arguments": {"query": "lodging", "city": "海岚", "trip_date": "2026-11-12"}, "attempt": 1}
{"task_id": "T01", "run_id": "teaching-normal", "seq": 4, "state_revision": 1, "event": "tool_result", "call_id": "call-1", "name": "search_policy", "result": {"call_id": "call-1", "status": "ok", "data": {"documents": [{"policy_id": "P17", "document_id": "P17-v2", "version": 2, "tenant_id": "demo-a", "topic": "lodging", "city": "海岚", "employee_category": "staff", "valid_from": "2026-11-01", "valid_to": null, "allowed_roles": ["staff", "manager"], "clauses": [{"clause_id": "P17-v2#4", "text": "本虚构制度下，staff在海岚的住宿金额上限为每晚700元。", "amount_cny": 700}]}], "rejected": []}, "evidence_refs": ["P17-v2#4"], "error": null}}
{"task_id": "T01", "run_id": "teaching-normal", "seq": 5, "state_revision": 1, "event": "decision", "decision": {"tool_calls": [], "output": {"status": "answered", "claims": [{"kind": "lodging_limit", "city": "海岚", "trip_date": "2026-11-12", "amount_cny": 700, "document_id": "P17-v2", "clause_id": "P17-v2#4"}], "evidence_refs": ["P17-v2#4"], "answer": "2026-11-12海岚每晚上限700元；给定金额未超过此金额上限。本例只核对虚构制度的金额条件。", "requested_fields": []}}}
{"task_id": "T01", "run_id": "teaching-normal", "seq": 6, "state_revision": 1, "event": "stopped", "status": "answered", "detail": null}
```

</details>

按seq阅读：2是拟调用，3才开始执行，4取得工具结果，5利用结果作答，6记录终态。result中的累计计数为 `decisions_used=2`、`tool_calls_started=1`、`model_requests_used=0`，`created_count=0`。一个查询动作和一个完成决定各算一次；没有模型请求，也没有工单写入。

完整输入在[基础03](03-context-and-prompts.md)展开。它包含实际取得的观察与当前有效证据，没有把输出答案、task_id或变式标签提供给策略。

## 改变条件一：删掉日期

先预测：能否直接套用最新制度？再运行：

```bash
python3 -m examples.policy_agent run --task T01 --variant missing-date --mode offline --run-id intro-missing
```

先查看当前的 `context.json` 与 `result.json`，再补充日期：

```bash
python3 -m examples.policy_agent resume --run-id intro-missing --reply-json '{"trip_date":"2026-11-12"}'
```

第一次应为 `clarification_required`，没有检索和写入。日期同时从问题和已知条件中移除，不能只删一个字段却让策略从原问题偷看。补充后从同一保存状态继续，累计预算不归零。`context.json`是最近一次快照，恢复后会更新；先读等待时的快照，再读恢复后的快照，观察未知日期变为已知日期。完整[补参记录](../examples/policy_agent/traces/missing-date/trace.jsonl)的seq2–3先等待，seq4记录可信回复，seq5以后才开始检索。

这是澄清，不是批准。用户告诉系统日期，只补足事实，不能据此授权创建工单。

## 改变条件二：搜索先返回旧版

```bash
python3 -m examples.policy_agent run --task T01 --variant stale-first --mode offline --run-id intro-stale
```

该变式模拟索引未更新。[实际旧证据轨迹](../examples/policy_agent/traces/stale-first/trace.jsonl)的seq4返回 `stale_evidence` 与P17-v1；seq5提出 `get_policy`，seq7取得P17-v2，seq8再作答。对照正常路径，关键差异是新增观察导致新增查询。若工具始终没有当前材料，合法结束应是 `insufficient_evidence`，不能根据记得的标准答案填700元。

## 用独立评分检查，而不只看结尾文字

```bash
python3 -m examples.policy_agent eval --suite pilot --mode offline --output .local/policy_agent/pilot-report.json
```

试点包含以上三项，缺日期项同时检查等待和恢复。评分至少核对：事实和有效引用、是否真的取得引用、缺参前是否零调用、过期材料是否被排除、实际副作用是否为零。评分器从独立期望读取要求，不能让被测策略自报“全部正确”就通过。

运行目录保存 `context.json`（实际输入快照）、`trace.jsonl`（事件）、`result.json`（结果），评分另有报告。在线模式另需凭据，并单独记录协议、模型与实际用量；离线结果不代表模型能力。[实验入口与边界](../examples/policy_agent/README.md)

## 先预测，再揭晓

1. 将出差日改为10月31日，650元会得到什么比较结果？
2. 检索只返回一份无生效日期的“700元”摘录，够不够回答？
3. 用户只问金额，策略能否顺便创建咨询工单？

<details><summary>核对你的解释</summary>

1. 适用P17-v1，金额上限600元，650元超过。先选适用版本，再比较。
2. 不够。缺少可核对的适用时间和完整来源，应继续核对或说明证据缺口。
3. 不能。问答与写入是不同目标；写入还需要具体草稿、可信批准和环境结果。

</details>

**完成标准：** 不看正文，画出一次工具往返，标明模型/策略、运行时、工具与状态；说清两个变式分别改变了哪个观察或未知项；引用一条记录解释为什么当前任务结束。只背出组件名还没有完成这次练习。

[继续：01 组成与协作](01-system-map.md) · [课程目录](README.md) · [按题查漏](../docs/question-index.md)

<!-- question-links:start -->
## 配套面试练习

先合上正文讲一分钟，再用追问和案例检查理解。每题都可以跳回对应学习内容。

<details><summary>展开本章相关面试题</summary>

- [Q001 什么是 Agent，和普通 LLM 调用有何区别？](../questions/Q001.md#q001-什么是-agent和普通-llm-调用有何区别)
- [Q009 最小 Agent Loop 应包含哪些环节？](../questions/Q009.md#q009-最小-agent-loop-应包含哪些环节)
- [Q025 Function Calling 的真正执行者是谁？](../questions/Q025.md#q025-function-calling-的真正执行者是谁)
- [Q027 Schema 合法为什么仍然不够？](../questions/Q027.md#q027-schema-合法为什么仍然不够)

</details>
<!-- question-links:end -->
