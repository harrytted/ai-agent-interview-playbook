# 54 道进阶面试题：把机制讲到能落地

<div id="36-道进阶面试题把机制讲到能落地"></div>

面试官问“框架支持什么”，回答功能列表就够了。再追问一句“远端成功后进程挂了呢”，问题就落到了执行过程。这 54 题沿着 [工程进阶（18 章）](../../advanced/README.md)展开：每章 3 题，分别检查机制、故障与设计取舍。

每题先给可口述的短答。展开后可以读详细机制、常见追问的回答、实战案例与练习。先自己想一遍再展开，别让眼睛替大脑打卡。

练习时先完成 P0 的核心机制与故障边界，再用 P1 做扩展设计。题号保持稳定，便于记录自己的薄弱点和下一次复习。

## 学习与面试双向入口

| 学习章 | 面试练习 | 要能讲清的决定 |
| --- | --- | --- |
| [01 Harness](../../advanced/01-harness-and-deep-agents.md) | [Q057–Q059](01-harness-and-deep-agents.md) | 运行时分工、文件与沙箱、跨会话交接 |
| [02 持久执行](../../advanced/02-durable-execution.md) | [Q060–Q062](02-durable-execution.md) | 重放、幂等、审批、Outbox 与陈旧写入 |
| [03 上下文工程](../../advanced/03-context-engineering.md) | [Q063–Q065](03-context-engineering.md) | 筛选与摘要、缓存隔离、预算和失效 |
| [04 记忆与 Skills](../../advanced/04-memory-and-skills.md) | [Q066–Q068](04-memory-and-skills.md) | 时间事实、反思记忆、技能权限与发布 |
| [05 工具路由与 MCP](../../advanced/05-tool-routing-and-mcp.md) | [Q069–Q071](05-tool-routing-and-mcp.md) | 搜索与加载、程序化调用、协议信任边界 |
| [06 Agentic RAG](../../advanced/06-agentic-rag.md) | [Q072–Q074](06-agentic-rag.md) | 追加检索、图索引、证据验证与停止 |
| [07 多 Agent](../../advanced/07-multi-agent-systems.md) | [Q075–Q077](07-multi-agent-systems.md) | 主管与交接、任务依赖、取消和协作成本 |
| [08 编码与计算机操作](../../advanced/08-coding-and-computer-use.md) | [Q078–Q080](08-coding-and-computer-use.md) | 补丁验证、隔离、观察新鲜度与实际终态 |
| [09 评测与反馈](../../advanced/09-evaluation-and-feedback.md) | [Q081–Q083](09-evaluation-and-feedback.md) | 多次尝试、Judge 校准、配对实验与数据切分 |
| [10 性能与推理服务](../../advanced/10-performance-and-serving.md) | [Q084–Q086](10-performance-and-serving.md) | 关键路径、四类缓存、共享预算与模型路由 |
| [11 安全与治理](../../advanced/11-security-and-governance.md) | [Q087–Q089](11-security-and-governance.md) | 身份与授权、注入、审批绑定和撤销 |
| [12 优化与训练](../../advanced/12-agent-training.md) | [Q090–Q092](12-agent-training.md) | SFT/DPO/RL、组内信号、Harness 与轨迹合同 |

系统机制仍为Q057–Q092，新增应用专题为Q093–Q110。编号稳定；先沿13→16最小服务→14的主线动手，SQL可按方向选读。

| 应用专题 | 面试练习 | 要能讲清的决定 |
| --- | --- | --- |
| [13 模型API](../../advanced/13-model-api-and-output-contracts.md) | [Q093–Q095](13-model-api-and-output-contracts.md) | 结构约束、多工具回填和流式完整性 |
| [14 知识摄取](../../advanced/14-ingestion-and-index-lifecycle.md) | [Q096–Q098](14-ingestion-and-index-lifecycle.md) | 表格条件、增量变更、撤权与索引发布 |
| [15 SQL分析](../../advanced/15-text-to-sql-and-data-analysis.md) | [Q099–Q101](15-text-to-sql-and-data-analysis.md) | 口径、JOIN粒度、有限修复与语义评测 |
| [16 任务服务](../../advanced/16-service-deployment-and-operations.md) | [Q102–Q104](16-service-deployment-and-operations.md) | 持久接收、任务归属、状态展示与发布恢复 |
| [17 事件订阅](../../advanced/17-event-driven-and-proactive-agents.md) | [Q105–Q107](17-event-driven-and-proactive-agents.md) | 事件与意图区分、乱序、撤销和通知 |
| [18 媒体与语音](../../advanced/18-multimodal-and-realtime-agents.md) | [Q108–Q110](18-multimodal-and-realtime-agents.md) | 媒体证据、转写更正、播放打断和迟到结果 |

## 一题怎样练到能迁移

先读学习章，把一次执行的输入、状态和结果画出来。然后合上正文，用一分钟回答题目；讲到一个“保证”时，补上它成立的条件。

展开详细答案，查出自己跳过了哪一步。让同伴从追问里挑一项，或把案例中的条件改掉：工具不支持幂等、文档被撤回、预算减半、审批人权限失效。能解释条件变化后的系统行为，才说明理解没有粘在原答案上。

最后完成微练习，留下状态表、计算结果或测试。面试现场可以压缩表达，学习时要把被压缩的机制补全；短答像压缩包，详细答案才是里面的文件。

## 用复习工具抽题

在仓库根目录运行：

```bash
# 只抽进阶题，先不显示答案
python3 scripts/study.py draw --topic docs/advanced/ --count 3

# 只抽第 02 章的题
python3 scripts/study.py draw --topic docs/advanced/02- --count 1

# 展开某题完整答案、追问与案例
python3 scripts/study.py show Q060

# 自评后安排复习
python3 scripts/study.py review Q060 --score 2
```

[110 题总索引](../question-index.md) · [工程进阶](../../advanced/README.md) · [进阶模拟面试](../../practice/mock-interviews.md#d-轮进阶系统深挖60-分钟) · [项目工作坊](../../advanced/project-workshop.md)
