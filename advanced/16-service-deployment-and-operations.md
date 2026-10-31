# 16 · Agent 服务交付与运维

[上一章：Text-to-SQL](15-text-to-sql-and-data-analysis.md) · [工程进阶目录](README.md) · [下一章：事件驱动](17-event-driven-and-proactive-agents.md)

## 把一次运行交付成可继续的任务

**任务服务**接收目标、保存任务身份，在后台推进工作，并提供等待、补充信息、批准、取消与查询结果的入口。**HTTP（超文本传输协议）**回答这一次请求有没有被处理；任务状态回答业务工作进行到哪里。服务把这两个生命周期分开，用户关掉页面以后，任务仍有可查询的身份和可靠记录。

建议先读[模型接入](13-model-api-and-output-contracts.md)、[持久执行](02-durable-execution.md)和[安全治理](11-security-and-governance.md)。本章先完成16A只读服务，再完成16B批准、恢复与发布。学完后应能用真实 HTTP 提交任务、跨进程补参、解释结果未知，且不会把程序退出0或HTTP 202误报成“工单已创建”。

本地实验使用 Python 标准库、SQLite 和一名后台 Worker，模型决策使用有限规则。它复用政策助手的虚构资料、适用日期与授权函数；工单是独立 SQLite 服务对象。Python 官方明确[http.server 不用于生产部署](https://docs.python.org/3.10/library/http.server.html)，本章用它暴露机制，生产认证、多实例、高可用与公网部署需要额外设计。

## 16A：先交付最小只读任务服务

小明提交“海岚普通员工住宿每晚650元，是否超过制度金额”，但忘记日期。API先持久接收请求，返回任务ID；Worker发现日期缺失后保存等待状态并释放执行。重启服务、补上2026-11-12后，同一任务继续读取制度，取得700元条款及来源；结论只涉及虚构制度金额，不保证真实报销资格。

```text
用户请求 → HTTP API → SQLite接收账本 → 202 + task_id
                           ↓
                       单Worker扫描
                           ↓
                 读取制度 / 等待输入 / 准备批准
                           ↓
用户查询 ← 状态与事件 ← SQLite任务与可靠事件
```

内存 `Event` 只用来唤醒 Worker；进程重启后，通过数据库中的 `queued` 找回未完成工作。若内存通知丢了，定期扫描仍会继续。任务在接收事务提交之前不会创建运行目录，避免API还没可靠接单，后台就已经行动。

### 任务入口、身份与幂等键

**可信身份**来自服务识别的测试 Bearer token，不能来自模型或请求体中的 `user_id`。公开演示凭据 `demo-alice` 对应普通员工，`demo-bob` 对应同租户经理；任务另有严格的owner。经理能读不同制度，不意味着他能查看另一位用户的任务；跨owner读取、事件查询或操作统一返回404。

**幂等键**将网络重发对应到原来的接收意图。服务在同一事务里保存 `(owner, Idempotency-Key)`、初始请求规范化hash与task ID；同键同内容返回原任务，同键异内容返回409。同一键在不同owner下属于不同任务；它与后续业务操作ID解决的不是同一个层次。

| 标识 | 回答的问题 | 本例约束 |
| --- | --- | --- |
| owner / user_id | 谁在调用，适用什么身份 | token映射，客户端不能自填 |
| Idempotency-Key | 这是不是同一次接收重试 | 每owner唯一，核对初始内容 |
| task_id / run_id | 找回哪项任务与运行目录 | 接收后稳定保存 |
| revision | 这份条件与证据属于哪一版 | 更正后递增，旧结果失效 |
| operation_id | 独立工单服务中的同一写意图 | 恢复沿用，不能重新生成 |

### 启动并走完缺日期路径

在仓库根目录运行，看到 `ready` 与本地URL后保持终端开启。另一个终端使用curl；下面的token是公开测试身份，不是真实密钥。

```bash
python3 -m examples.service_lab.lab serve --root .local/service_lab/server --port 8765
```

```bash
curl -s http://127.0.0.1:8765/health
curl -s -X POST http://127.0.0.1:8765/tasks \
  -H 'Authorization: Bearer demo-alice' \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: lodging-1' \
  -d '{"city":"海岚","amount_cny":650}'
```

读取返回的 `task.id`，把后续URL中的 `TASK_ID` 替换为实际值。查询会看到 `clarification_required`；补参后再查询，才会看到 `answered`。

```bash
curl -s http://127.0.0.1:8765/tasks/TASK_ID -H 'Authorization: Bearer demo-alice'
curl -s -X POST http://127.0.0.1:8765/tasks/TASK_ID/reply \
  -H 'Authorization: Bearer demo-alice' -H 'Content-Type: application/json' \
  -d '{"trip_date":"2026-11-12"}'
```

`reply` 只补当前缺失日期。`correct` 可以更正城市、日期、金额和事由，递增revision、清掉旧证据与草稿，并重新排队；不会重置累计预算。不能把缺参补全、修改业务目标与批准混成一条含糊的“继续”消息。

### API与Worker如何避免覆盖彼此的更新

只设一名Worker，API线程仍可能与它同时改同一任务。若两者各自读取旧JSON再覆盖保存，刚保存的取消可能被旧Worker状态覆盖。实验用 `BEGIN IMMEDIATE` 串行化“读当前任务→验证允许转换→写状态与事件”，所有修改入口都遵守同一个事务边界。

[SQLite事务文档](https://www.sqlite.org/lang_transaction.html)说明同时只能有一个写事务，IMMEDIATE会尝试先取得写事务。它能保护本地状态转换，不能把另一个数据库或远程API并进事务。本例还用POSIX文件锁限制同一数据目录只有一个服务进程；不提供多副本Worker抢占与分布式租约。

## 16B：加入批准、写入与恢复

将提交体的 `mode` 设为 `ticket`，Worker生成政策例外咨询草稿，而不直接创建对象。草稿包括城市、日期、金额、事由、当前政策条款与revision。返回的 `request_id` 和 `payload_hash` 绑定这份完整内容；客户端展示草稿后，才能提交这两个字段到 `/approve`。

| API | 合同 |
| --- | --- |
| `POST /tasks` | 接收查询或咨询任务；需Idempotency-Key |
| `GET /tasks/{id}`、`/events` | 查询本人状态、结果或持久事件 |
| `POST /tasks/{id}/reply` | 仅给等待日期的任务补日期 |
| `POST /tasks/{id}/correct` | 可改城市/日期/金额/事由；在途写与已创建对象不可改 |
| `POST /tasks/{id}/approve` | 当前request_id与payload_hash，且owner一致 |
| `POST /tasks/{id}/cancel` | 空对象；停止未提交工作，已提交写入继续对账 |
| `POST /tasks/{id}/resume` | 空对象；仅恢复排队或结果未知的原意图 |

批准后若城市从海岚改为云洲，旧批准与证据必须失效，不能先创建海岚工单再把文字改成云洲。批准验证后先进入 `write_prepared`，此时尚未派发，仍可取消或更正。下一步Worker通过独立事务提交 `dispatch_committed` 并进入 `writing`，才取得派发权；这次提交是取消与派发的本地线性化边界。取消或更正先提交，Worker不会新建；派发提交先发生，请求可能继续完成，此后拒绝直接修改并保留原意图核对。

`writing`表示派发已由执行器接管，不表示远端已提交。业务对象的实际提交由另一份库证明；取消到来后不能倒推它没发生。已成功对象的撤销属于新业务动作，本例不实现自动补偿。

### 外部已提交，本地未确认的真实故障窗口

本地任务数据库提交派发边界，保存 `writing`、原操作ID和获批完整参数；独立业务数据库再创建工单。若业务提交后进程退出，对象存在，本地却没有成功确认。这两个数据库没有共同事务，不能因为各自用了SQLite就宣称原子提交。

第二进程启动时，将未确认的 `writing` 展示成 `write_outcome_unknown`，等待沿原意图恢复。业务服务以租户+operation ID原子去重，核对规范化参数hash；相同意图返回已有对象，不同内容拒绝。恢复先查对象：未取消且查不到时，可按本地业务服务的幂等合同提交原意图；取消后只查不新建，查无对象也保持未知，因为单次缺失不能证明先前派发不会迟到。恢复不重新领取决策和逻辑工具预算。其原理见[持久执行](02-durable-execution.md)，本章补的是跨HTTP与进程的实际交付路径。

取消同样区分位置。排队任务立即终止，清掉当前结果；已经派发的写意图保留取消标记，仍需确认对象。当对象实际已创建，返回 `cancelled` 及真实对象和 `cancel_requested=true`，不会声称工单消失。界面应把“停止后续工作”和“已有对象”同时展示。

### 任务状态如何对应用户界面

| 任务状态 | 用户应看到 | 能否算任务成功 |
| --- | --- | --- |
| queued | 已接收，待执行 | 否 |
| clarification_required | 请补具体日期 | 否 |
| approval_required | 可核对的完整草稿，等待批准 | 否 |
| write_prepared | 已批准，尚未派发，可取消或更正 | 否 |
| writing / reconciling / write_outcome_unknown | 已接管派发 / 正在核对 / 结果仍未知 | 否 |
| answered / write_succeeded | 有证据的回答 / 已确认业务对象 | 是 |
| cancelled | 后续停止，另列已有对象与未知项 | 否 |
| blocked_version / budget_exhausted | 需迁移 / 预算耗尽 | 否 |

`GET /metrics`按owner分别统计接收、成功、等待、排队及累计决策，不把HTTP状态码当作质量指标。它是最小计数看板，尚未实现生产p95、账单和告警系统。要增加计时，分别记录接收、入队、执行、工具与终态，并沿[性能章](10-performance-and-serving.md)的口径计算；等待人工的时长不能偷偷从产品延迟定义里消失。

## 运行版本、发布与回退怎样一起管理

每项任务在接收时固定manifest：运行状态schema、离线策略模型标识、提示hash、工具合同hash、索引内容hash及release ID。已发布的release保存完整政策快照且不可覆盖；现有任务继续使用它绑定的版本。`runtime_schema`不兼容时进入 `blocked_version`，不会静默重置或把旧动作当新任务执行。

`POST /releases`只允许单独的公开测试操作员 `demo-operator`，它不能读取用户任务。新版本先验证所有条目的必要元数据、日期和条款结构，再用Alice的可信身份沿实际 `core.applicable` 路径运行三条独立固定金额门槛；失败返回422，不切换active。仅保留正确金额却移除Alice权限，也不能通过这组预期成功任务。合法撤权发布应另建明确预期拒绝的验收集，本例不在发布时静默修改成功预期。正常版本可以先登记而不activate，再切换；回退只把新任务入口指回已验证的旧release，在途任务保持原manifest。

本例的固定门槛能拦住海岚700被改成7000，以及缺元数据的条目，**不能证明所有新资料的语义正确或检索质量**。影子与灰度的完整方法仍见[评测闭环](09-evaluation-and-feedback.md)；实验实际完成候选检查、版本固定、切换与回退，不宣称模拟了生产流量灰度。

## 有界验收与一次故障处置

```bash
python3 -m examples.service_lab.lab --scenario all --output .local/service_lab/checks
python3 -m unittest discover -s tests -p 'test_service_lab.py' -v
```

六组自检使用操作系统分配的临时端口，真实发送HTTP，完成后关闭服务与Worker。覆盖正常读取、重复提交/两用户隔离、等待中重启、批准后更正、提交后故障恢复、坏索引拒绝与回退。测试另在write_prepared取消，核对对象数0，并用并发屏障验证派发事务先提交时保留取消意图与真实对象；未知对象查无结果时仍未知且不新建。跨进程测试让第一进程在业务提交后退出73，第二进程用同一数据目录恢复，核对只有一个业务对象与同一预算。

各组保留 `http.jsonl`、`result.json`、`grade.json` 与数据库；任务运行目录另有 `manifest.json`、`trace.jsonl`、`result.json`。数据库事件是可靠记录，导出文件是可重新生成的观察副本。`--scenario all`每次使用新的批次目录，服务启动则明确指定要继续的root，不会靠删除旧数据“恢复”。

故障处置演练：看到Worker未就绪时，先检查可靠任务状态与业务对象，再决定重启。若业务对象已存在、本地为结果未知，保留原root、操作ID和参数；恢复后核对对象ID、内容、owner和累计预算。若是版本不兼容，停止新派发并选择兼容运行器或经过验证的迁移，不用重建任务掩盖问题。

## 自检与答案

<details><summary>1. POST返回202后响应丢失，客户端应该换键再提交吗？</summary>

应该使用原幂等键和相同初始内容重试，找回已持久接收的任务。换键会表达另一份接收意图，不能自动去重。
</details>

<details><summary>2. 为什么经理也不能查小明的任务？</summary>

角色决定制度适用与业务权限，任务owner决定本服务中的私有运行访问。两者不能混用；测试刻意使用同租户不同角色验证这一点。
</details>

<details><summary>3. 回退active版本会让旧工单自动撤销吗？</summary>

不会。回退影响新任务采用的release，在途任务仍固定原manifest；已创建对象需要独立授权的补偿，本例没有实现自动撤销。
</details>

## 配套面试题与资料

- [Q102 接收账本与后台恢复](../questions/Q102.md)、[Q103 联合版本与在途任务](../questions/Q103.md)、[Q104 HTTP与任务指标](../questions/Q104.md)。
- [本章合订题源](../docs/advanced/16-service-deployment-and-operations.md) · [实验README](../examples/service_lab/README.md)。
- [Python SQLite接口](https://docs.python.org/3/library/sqlite3.html) · [SQLite事务](https://www.sqlite.org/lang_transaction.html) · [Python HTTP服务器](https://docs.python.org/3.10/library/http.server.html)。一手资料核查日期：2026-10-31。
