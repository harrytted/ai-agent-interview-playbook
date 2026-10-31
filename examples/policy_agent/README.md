# 政策助手：从观察到结果的完整实验

先取得一份制度，再决定回答、补充查询、澄清或停止。这个实验把每次决定、工具执行和环境结果留下来，让你检查“下一步为什么改变”。从 [首次任务](../../learning/00-first-agent.md) 开始阅读，再回本页运行变式。

人物、城市、制度和金额均为虚构教学数据。默认离线、仅Python 3.10+标准库，无密钥或网络。离线策略是读取观察的有限规则，不能代表语言模型的能力；MCP、向量数据库、浏览器和训练管线均未接入此实验。

## 三条路径，先运行再解释

在仓库根目录执行。每个run-id对应保留目录，已存在则拒绝覆盖；重新演示时换一个名称。

```bash
python3 -m examples.policy_agent run --task 住宿金额核对 --mode offline --run-id intro-normal
python3 -m examples.policy_agent run --task 住宿金额核对 --variant missing-date --mode offline --run-id intro-missing
```

正常查询应得到“已回答”（answered）：依据海岚新版住宿标准，每晚上限700元，650元未超限。第二条会先要求补充日期（clarification_required），还不会检索或写入。此时先看 `.local/policy_agent/intro-missing/context.json`，再补日期：

```bash
python3 -m examples.policy_agent resume --run-id intro-missing --reply-json '{"trip_date":"2026-11-12"}'
python3 -m examples.policy_agent run --task 住宿金额核对 --variant stale-first --mode offline --run-id intro-stale
python3 -m examples.policy_agent eval --suite pilot --mode offline --output .local/policy_agent/pilot-report.json
```

补参从同一状态继续，预算不归零。旧索引变式需要补查适用制度，不能预填700元这个答案。pilot包含正常、缺日期及恢复、旧证据三项；eval输出摘要，完整逐项断言保存在指定JSON中。

[![一次工具请求、执行、回填与第二次决定](../../website/assets/diagrams/G3-tool-roundtrip.png)](../../website/assets/diagrams/G3-tool-roundtrip.png)

## 打开已经运行的样本

下列记录来自本仓库离线实现，未调用付费模型。JSONL包含实际事件；context是暂停或结束时依据当前权限重新组装的可见上下文快照，不保存每一轮输入历史。缺日期样本的context会在恢复后更新，等待阶段仍可在trace中找到；写入结束后的快照也会包含新取得的工单结果。

| 样本 | 事件 | 输入与结果 |
| --- | --- | --- |
| 正常查询 | [完整JSONL](traces/normal/trace.jsonl) | [context](traces/normal/context.json)、[result](traces/normal/result.json) |
| 缺日期后补充 | [完整JSONL](traces/missing-date/trace.jsonl) | [context](traces/missing-date/context.json)、[result](traces/missing-date/result.json) |
| 搜索先得旧版 | [完整JSONL](traces/stale-first/trace.jsonl) | [context](traces/stale-first/context.json)、[result](traces/stale-first/result.json) |
| 用户更正城市 | [完整JSONL](traces/user-correction/trace.jsonl) | [context](traces/user-correction/context.json)、[result](traces/user-correction/result.json) |

正常路径依次记录运行开始、首次决定、开始查询、取得结果、再次决定和停止；两次决定、一次读取、零写入。阅读时沿同一次调用，观察查到的住宿标准何时进入下一次输入。模型请求工具和宿主执行工具是两件事。

## 十二个主任务与受控变式

```bash
python3 -m examples.policy_agent list
python3 -m examples.policy_agent eval --suite all --mode offline --output .local/policy_agent/all-report.json
```

| 场景 | 改变什么 | 应检查什么 |
| --- | --- | --- |
| 住宿金额核对 | 海岚11月12日650元 | 新版上限700，金额未超限 |
| 历史日期核对 | 日期改为10月31日 | 旧版上限600，金额超限 |
| 经理住宿标准 | 可信身份换为经理 | 适用900元标准，类别不由模型自填 |
| 两个日期比较 | 比较两个日期 | 600与700分别对应有效版本 |
| 两地住宿比较 | 比较海岚与云洲 | 同日期分别700与650 |
| 超标咨询材料 | 报价800元并问咨询材料 | 上限、材料分别取证，咨询不等于批准 |
| 冲突证据核对 | 注入同等级有效证据冲突 | 保留真实冲突来源，需人工判断 |
| 用户更正城市 | 已记录的可信用户更正城市 | 旧城市证据退出当前结论，待办真正替换 |
| 缺少出差日期 | 初始缺日期 | 先澄清，再恢复 |
| 餐补资料不足 | 询问未提供制度的餐补 | 说明证据不足 |
| 批准后创建工单 | 明确创建咨询工单 | 批准具体草稿后创建一份对象 |
| 工单崩溃恢复 | 远端提交后进程崩溃 | 原操作ID恢复，仍只有一份对象 |

完整评测共22项：上表12个主场景、住宿金额核对的9个读取变式，以及创建工单获批后又修改金额的场景。崩溃恢复自身包含一次中断，不重复算一项。城市更正等条件由 [任务数据](data/tasks.json)定义，额外故障与参数修改由 [变式数据](data/variants.json)注入，并在执行轨迹中标明；策略看不到任务代号、变式名、未来事件或标准答案。

[政策数据](data/policies.json)有八份文档，包括海岚住宿标准的新旧两版。[用户数据](data/users.json)是可信测试身份源，非生产认证。[任务数据](data/tasks.json)描述目标与条件。[独立期望](data/expected.json)由评分器在运行后读取，策略不读取。日期使用左闭右开区间，业务日期不取机器当天。

## 工具与状态的边界

[完整schema](data/tools.json)与 [校验器](core.py)使用同一合同。search_policy.query是本教材的topic键枚举，**不是自然语言搜索框**。四个工具分别为search_policy、get_policy、create_ticket、lookup_ticket；live仅开放前两个。

请求先验字段、类型、当前身份和业务条件；拒绝未知参数以及approved=true等自授权字段。工具结果固定含call_id/status/data/evidence_refs/error。空结果、旧证据、冲突和接口失败各有状态。JSON合法不代表有权或适用；引用必须来自实际取得、获授权且仍适用的观察。

PolicyView仅包含目标、可信消息、已知条件、未知项、可见观察和证据。它不暴露task_id/run_id、注入标记或评分答案。规则策略依据证据选下一步；宿主核验主张后计算金额比较并渲染交付文字，避免“700元主张正确、650元却被写成超限”。模型原提议保留在decision事件中供诊断。

每任务最多6次决定（含结束决定）、12次逻辑工具调用、6次模型请求；只读调用最多尝试两次。只读批次最多四项，写入批次只能是单个写请求，非法批次执行前整批拒绝。累计预算、待办队列和调用结果持久保存，恢复不重置，已完成项不重复执行。

## 具体批准与跨进程恢复

```bash
python3 -m examples.policy_agent run --task 批准后创建工单 --run-id ticket-approval
python3 -m examples.policy_agent approve --run-id ticket-approval --request-id APR-ticket-approval-1
python3 -m examples.policy_agent resume --run-id ticket-approval
```

先看approval_required返回的完整草稿和请求ID。approve只保存受控测试操作者的决定，resume再核对当前权限、版本和完整参数。日期、金额、对象或内容变化使旧批准失效；批准不由模型文本产生。

任务状态与批准保存于 `.local/policy_agent/<run-id>/task.sqlite`，模拟工单在同目录的service.sqlite，两个数据库没有共同事务。服务按tenant_id+operation_id唯一，并比较规范化完整参数；同ID异内容拒绝，相同内容返回已有对象。

[![服务已提交但本地尚未确认时，第二进程按原操作ID恢复](../../website/assets/diagrams/G8-write-recovery.png)](../../website/assets/diagrams/G8-write-recovery.png)

下面演示工单已在服务端提交、本地尚未确认时的恢复。四条命令逐条执行；`ticket-recovery`应是本次新用的运行名称。先核对第一条返回的完整草稿和审批请求，示例中的请求标识为`APR-ticket-recovery-1`；如果更改run-id，审批参数也要使用实际返回的值。

```bash
python3 -m examples.policy_agent run --task 工单崩溃恢复 --mode offline --run-id ticket-recovery
python3 -m examples.policy_agent approve --run-id ticket-recovery --request-id APR-ticket-recovery-1
# 首次恢复预期退出73：服务已提交，本地还未确认
python3 -m examples.policy_agent resume --run-id ticket-recovery
# 沿同一运行记录再次恢复，预期完成写入确认
python3 -m examples.policy_agent resume --run-id ticket-recovery
```

退出码73是这次故障注入的预期现象。保留运行目录与操作ID，第二次resume才能沿原意图核对已有对象。恢复后可运行独立评分，检查终态、对象内容、写入身份与批准顺序：

```bash
python3 - <<'PY'
from pathlib import Path
from examples.policy_agent.grade import grade

report = grade(Path(".local/policy_agent/ticket-recovery"))
print({key: report[key] for key in ("status", "passed", "created_count")})
assert report["passed"], report["checks"]
PY
```

应核对`status=write_succeeded`、`passed=True`和`created_count=1`。自动all套件也会启动两个真实Python子进程检查这一过程。该实验验证本地模拟合同，不能推导所有远端服务都支持相同保证。

正常暂停和结束保存trace/context/result，评分另有grade；崩溃可能没有最终result快照，恢复依据持久意图、服务对象和已flush事件。run退出0表示完成一次合法处理，等待或正确拒绝也可能退出0；eval只有全部断言通过才退出0。

## 可选真实模型：接口测试与实际效果分开

显式设置ANTHROPIC_API_KEY后才启用网络；密钥不要写入源码或命令历史。可用ANTHROPIC_MODEL覆盖默认模型。

```bash
python3 -m examples.policy_agent run --task 住宿金额核对 --mode live --run-id live-normal
```

[live.py](live.py)采用标准库HTTP，每次决定一个请求，保存完整assistant块并按tool_use_id回填全部工具结果，再继续。无自动整请求重试；每个活跃段60秒协作式期限，HTTP至多20秒且受剩余时间限制，单次输出最多1024 token。超时不表示远端已取消。

适配器固定API版本2026-10-21，默认claude-haiku-5-5，核验日期2026-10-30；没有旧采样参数。依据：[迁移说明](https://platform.claude.com/docs/en/api/migration-2026-10-21)、[工具往返](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)、[模型标识](https://platform.claude.com/docs/en/models/overview)。模型不可用时报告配置错误，不静默换模型。

provider.json记录协议、模型、请求ID、用量和耗时，不保存密钥。不将end_turn视为任务通过。恢复前若历史工具内容因当前权限变化而被撤回，适配器停止旧会话回放，避免旧assistant引述再次泄露；需要从当前授权输入重新开始。此处不会声称已实现远端上下文删除。

HTTP夹具测试覆盖多工具、对应回包、错误、截断、预算和撤权回放；它不调用付费API。本次分支没有真实模型运行证据，状态是接口测试通过，未标live_verified。离线结果不证明模型效果。

## 验证与继续学习

```bash
python3 -m unittest tests.test_policy_agent tests.test_policy_cli tests.test_policy_live -v
```

评分同时检查终态、事实、当前有效来源和实际副作用，禁止动作失败不会被其他分数抵消。改任务ID应不改变策略行为；只改工具观察应改变下一动作。你可以从 [循环](../../learning/04-agent-loop.md)、[状态](../../learning/07-memory-and-state.md)、[评测](../../learning/09-evaluation.md)或 [持久执行](../../advanced/02-durable-execution.md)继续。
