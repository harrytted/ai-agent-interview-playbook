# 离线 Agent 工具循环实验

用固定脚本替代模型决策，观察「决定下一步 → 运行时校验与执行 → 记录观察 → 停止」的边界。只需要 **Python 3.10+ 标准库**，没有安装步骤、API Key 或网络调用。

在仓库根目录运行：

```bash
python3 examples/agent_lab/lab.py --scenario all
python3 -m unittest discover -s tests -p 'test_agent_lab.py' -v
```

可以单独选择 `happy`、`retry`、`approval`、`denied` 或 `loop`：

```bash
python3 examples/agent_lab/lab.py --scenario denied
```

输出是 JSON Lines：每行一条 decision、observation、错误、stop 或 summary。所有场景都会核对停止原因、实际工具尝试次数与工单创建数；任一核对失败，进程返回非零。`all` 每个场景使用独立 Runtime，不共享工单。

## 五条可观察路径

| 场景 | 注入条件 | 预期停止原因 | 预期结果 |
|---|---|---|---|
| happy | 检索一次后结束 | `final_answer` | 实际检索 1 次、创建 0 个工单 |
| retry | 首次检索临时失败 | `final_answer` | 最多 2 次尝试，本例第二次成功 |
| approval | 运行时已明确批准的同一请求调用两次 | `final_answer` | 写工具执行 2 次、工单只创建 1 个，第二次返回 `replayed=true` |
| denied | 无对应运行时批准 | `approval_required` | 写工具执行 0 次、创建 0 个工单 |
| loop | 策略持续要求检索 | `step_budget_exhausted` | 第 3 步之后停止，不再索取下一项决策 |

`steps` 计算策略决策次数，最终回答也占一步；读工具重试计入独立的 `search_attempts`。每次读调用的尝试上限包含首次调用。这个实验没有总时限、取消、token 预算、退避调度或并发执行，不能由步数上限推断已经覆盖这些限制。

## 代码中的边界

- `scripted()` 或固定 lambda 是决策器。`run()` 拥有循环和停止预算，`Runtime.invoke()` 拥有执行前的工具白名单、参数与批准检查。
- `search` 在 4 条合成文本上按关键词交集排序，结果可为空。
- 参数校验拒绝未知字段、缺失字段、非法取值和把 `true` 当整数的情况。未知工具不会分发到其他函数，也没有 shell 或任意代码执行入口。
- 只有 `search` 的 `TransientReadFailure` 会自动重试；参数错误、未知工具、未批准操作、幂等冲突和写结果不确定都会停止。
- `Approval(request_id, title)` 由可信运行时配置传入，绑定请求 ID 与完整标题。`approval` 场景模拟“执行前批准已完成”，没有交互式批准 UI。决策参数中的 `approved=true` 会被拒绝，不能产生批准。
- `create_ticket` 只修改当前 Python 进程里的字典。重复请求 ID 与相同标题返回已有工单；重复 ID 对应不同内容会拒绝。输出的创建数是字典终态计数，不是根据返回文字猜测。

`write_attempts` 表示通过参数与批准检查后进入模拟写路径的次数，包含幂等重放；它不等于新建对象数。被拒绝的请求会出现在 trace 中，但不会增加该计数。

## 写成功但响应丢失

测试 `test_lost_write_response_stops_then_reconciles_without_duplicate` 会：

1. 在模拟后端创建工单，再注入 `WriteOutcomeUnknown`，替代“提交成功但调用方没收到响应”。
2. 检查执行器已经停止，没有自动重试写操作。
3. 由可信测试代码调用 `lookup_ticket(request_id)` 查看同一模拟后端终态。
4. 对同一 Runtime 再提交同一批准操作，确认返回原工单且数量仍为 1。

本例使用同一进程中的同一个 Runtime 实例顺序调用。进程重启、多个服务实例和并发请求需要额外的持久幂等记录、唯一性约束及外部系统对账设计。

## 用它准备面试

先猜测每个场景的终态，再运行确认。选一个失败场景，按这四句解释：

1. 谁做决定，谁真正执行，谁拥有批准权？
2. 哪个输入触发了失败，执行前后的状态分别是什么？
3. 哪条限制使它停止，有没有已发生的副作用？
4. 哪项输出或测试能证明自己的结论，哪部分仍未覆盖？

继续完成 [7 天个人项目实验](../../docs/engineering/08-project-lab.md)。接入真实 LLM、真实检索和持久存储是后续工作，需要另写适配器、测试集和评测记录。

## 测试覆盖与扩展

当前测试覆盖正常与空检索、工具白名单、参数拒绝、批准绑定、幂等重放与冲突、临时读错误恢复和耗尽、循环上限、写响应丢失及 CLI 场景自检。

决策器与工具在同一进程内运行，工单存储使用内存字典。扩展到真实服务时，可依次增加模型适配器、持久存储、并发控制、身份与租户隔离、执行沙箱、日志脱敏及调用费用统计。

合成文本及代码适用仓库根目录 [LICENSE](../../LICENSE)。
