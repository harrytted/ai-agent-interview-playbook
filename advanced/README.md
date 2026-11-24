# Agent 工程进阶

<div id="agent-进阶课程"></div>

**按目标学习长任务、系统设计、故障恢复与质量优化。19 章的编号用于定位和回查，按自己的学习目标选择顺序即可。**

工程进阶解释系统怎样工作：状态如何提交与恢复，证据如何选择，检索和索引怎样影响召回，协作如何归并，时延与授权怎样约束执行。读者应能根据输入、算法或状态变化推导结果，再用实验检查推导。

建议先读 [基础原理](../learning/README.md)，重点了解工具循环、RAG、状态、评测与可靠性，再根据下面的目标选择入口。**每章先解释核心概念及其用途，再展开机制。** 章末列出的面试题用于闭卷检验和专题复习。阅读官方文档时，优先追踪正文所解释的机制和产品边界，再学习框架接口。

## 一张学习地图

| 你的目标 | 建议阅读路线 | 先取得什么结果 |
| --- | --- | --- |
| 快速搭建 | [13 模型接入](13-model-api-and-output-contracts.md) → [16A 最小服务](16-service-deployment-and-operations.md#16a--持久接收与只读任务) → [14 知识摄取](14-ingestion-and-index-lifecycle.md) → [16B 批准与运维](16-service-deployment-and-operations.md#16b--批准写入与恢复) | 先提交、补参和跨重启继续，再验证知识变更与受控写入 |
| 知识助手 | [06 证据驱动检索](06-agentic-rag.md) → [14 摄取生命周期](14-ingestion-and-index-lifecycle.md) → [16B 服务交付](16-service-deployment-and-operations.md#16b--批准写入与恢复) → [17 事件订阅](17-event-driven-and-proactive-agents.md) | 把来源、版本和权限接到查询及后续任务 |
| 数据分析 | [15 Text-to-SQL](15-text-to-sql-and-data-analysis.md) → [16 任务服务](16-service-deployment-and-operations.md) | 先核验统计粒度与结果，再学习任务交付合同 |
| 系统优化 | [09 评测](09-evaluation-and-feedback.md) → [10 性能与预算](10-performance-and-serving.md) → [11 安全治理](11-security-and-governance.md) → [12 优化与训练](12-agent-training.md) | 先定位失败与成本，确认瓶颈后再决定是否训练 |
| 上线维护 | [09 评测](09-evaluation-and-feedback.md) → [16 任务服务](16-service-deployment-and-operations.md) → [19 故障排查与发布验证](19-incident-review-and-release.md) | 定位失败、验证修复，决定是否扩大上线范围 |

基础工具章读完即可进入13，不要求先学12训练。知识助手或数据分析读者若还没有服务基础，先补快速搭建路线的13与16A；15是独立方向分支，需要最小SQL基础，不阻塞其他路径。路线表示知识衔接，各实验的实际组件与集成范围以各自README为准。

安全与评测应贯穿每条路线，不能等到最后才补授权和验收。17依赖稳定的任务与知识版本；[18 多模态与实时语音](18-multimodal-and-realtime-agents.md)先学媒体证据，再选修播放与打断，不要求所有读者完成。

<div id="18章目录与交付物"></div>

## 19 章目录与交付物

<div id="应用专题-1318把机制接成可运行的任务"></div>

| 章 | 核心内容 | 可用于 |
| --- | --- | --- |
| [01 Harness 与 Deep Agents](01-harness-and-deep-agents.md) | 运行框架、就绪调度与跨会话交接 | 版本化状态转换、就绪调度与交接恢复推演 |
| [02 持久执行](02-durable-execution.md) | 重放、外部写入恢复与租约隔离 | 确定性重放、历史匹配、事务去重与过期执行者隔离 |
| [03 上下文工程](03-context-engineering.md) | 输入预算、证据依赖与压缩 | 依赖闭包装配、压缩损失检查与净成本复算 |
| [04 记忆与技能](04-memory-and-skills.md) | 事实修订、技能装载与效果验证 | 记忆准入/巩固、双时间修订、遗忘传播与技能状态 |
| [05 工具路由与 MCP](05-tool-routing-and-mcp.md) | 候选工具、协议版本与执行授权 | 逐级路由、协议协商/目录变化、并发关联与取消竞态 |
| [06 Agentic RAG](06-agentic-rag.md) | 词项、向量、冲突裁决与补查 | BM25推导、ANN/过滤诊断、排序上限、冲突与停止合同 |
| [07 多 Agent 系统](07-multi-agent-systems.md) | 控制权、依赖验收、归并与预算 | 依赖验收、归并不变量、共享预留与工作量/跨度下界 |
| [08 编码与计算机操作](08-coding-and-computer-use.md) | 编码改动、执行隔离与界面核验 | 干净初态、版本化测试证据与观察—动作—核验闭环 |
| [09 评测与反馈](09-evaluation-and-feedback.md) | 失败归因、评分器与配对验证 | Judge误差传播、分层/聚类、配对统计与因果验证边界 |
| [10 性能与推理服务](10-performance-and-serving.md) | 关键路径、生成阶段、显存与排队 | Prefill/Decode、KV容量、迭代调度、平均在途量与扇出尾部推导 |
| [11 安全与治理](11-security-and-governance.md) | 信任边界、对象授权与审计 | 威胁路径、最小能力、授权关口及攻击/正常任务双重验证 |
| [12 优化与训练](12-agent-training.md) | 动作目标、偏好比较与轨迹回报 | SFT/DPO目标、策略梯度与信用分配、采样偏差和奖励验证 |
| [13 模型 API 与输出合同](13-model-api-and-output-contracts.md) | 流式消息、工具参数与异常终态 | 增量缓冲、消息/块状态机、调用ID与异常终态 |
| [14 知识摄取与索引生命周期](14-ingestion-and-index-lifecycle.md) | 资料版本、原子发布与撤权 | 结构化解析、血缘更新、完整代次与读者快照生命周期 |
| [15 Text-to-SQL 与数据分析](15-text-to-sql-and-data-analysis.md) | 统计口径、连接粒度与结果核验 | SQL逻辑顺序、多重集、外连接/NULL推导与独立语义检查 |
| [16 服务交付与运维](16-service-deployment-and-operations.md) | 持久接收、取消边界与在途恢复 | 原子领取、续租/迟到提交、资源接收与发布兼容边界 |
| [17 事件驱动与主动任务](17-event-driven-and-proactive-agents.md) | 事件投递、迟到处理与去重 | 分区顺序、消费确认、窗口/水位线、因果循环与通知意图 |
| [18 多模态与实时语音](18-multimodal-and-realtime-agents.md) | 媒体定位、条件修订和播放控制 | 视觉投影、流式识别、坐标/时钟、转写修订与缓冲反压 |
| [19 故障排查与发布验证](19-incident-review-and-release.md) | 故障定位、回归、灰度与回退 | 故障记录、修复验证与发布决定 |

正文按机制、工程边界和验收组织。适用条件发生变化时，回到对应小节核对。实验的运行条件、命令和预期结果收录在各自的说明里。

<div id="同一个案例各章留下什么成品"></div>

## 工作坊与实验

需要把机制接成完整任务时，使用 [贯穿项目工作坊](project-workshop.md) 和 [政策实验](../examples/policy_agent/README.md)。检索、训练目标和配对统计可以独立复算。各实验提供可验证的输入、输出和运行边界。

快速搭建路线从协议解析和只读 HTTP 任务开始，再学习索引发布、批准写入与恢复。相关组件分别由各实验验证。真实流量或模型质量按目标环境单独评测。

## 按目标选择主线

上方的路线用于选择起点，下面这些章节帮助处理项目中出现的具体问题。长任务可串联 [01 Harness](01-harness-and-deep-agents.md)、[02 持久执行](02-durable-execution.md)、[03 上下文工程](03-context-engineering.md)和[04 记忆与技能](04-memory-and-skills.md)；工具扩展关注[05 路由与MCP](05-tool-routing-and-mcp.md)。确认单Agent瓶颈后，再决定是否引入[07 多Agent](07-multi-agent-systems.md)，需要代码或界面操作时再读[08 编码与操作](08-coding-and-computer-use.md)。

平台工程读者可以重点串联02、05、07、09–11，关注恢复、共享资源和服务边界。模型优化读者先完成09，再按失败证据决定是否进入12，并回查03、08、10中的输入、环境和推理约束。

这些路径共享同一套判断顺序：任务是否定义清楚 → 证据与工具是否正确 → 运行状态能否解释 → 行为是否满足验收 → 性能或参数还有什么瓶颈。不要用增加 Agent 数量代替错误定位。

## 学完一章，接着练对应的三道题

[54 篇进阶题文章](../questions/README.md#进阶系统)覆盖 Q057–Q110，对应第 01–18 章，每章三题。每题有口述短答、分节详细解析、带答案的追问、实战案例和验收练习。正文与对应面试题可以直接互相跳转。

章末可以展开面试题、实验和资料。复习时先按实际状态解释下一步，再对照解析查缺口。

## 从问题找到对应知识

| 观察到的现象 | 先检查什么 | 深入章节 |
| --- | --- | --- |
| 任务跑久后忘记进展 | 状态、摘要、交接信息是否完整 | 01、03、04 |
| 超时重试创建了两个业务对象 | 操作 ID、远端幂等、结果未知的恢复路径 | 02、11 |
| 工具越来越多却选不准 | 工具描述、检索召回、参数合同与路由数据 | 05、09 |
| 报告引用很多却答非所问 | 检索覆盖、证据支持、版本和适用条件 | 06、09 |
| 多 Agent 更慢、更贵 | 依赖、交接损耗、共享预算和关键路径 | 07、10 |
| 浏览器显示成功却没办成 | 页面状态、后端对象、观察与动作的关联 | 08、09 |
| 外部材料改变了工具行为 | 信任边界、授权执行点、数据出口 | 05、11 |
| 提示越写越长仍反复失败 | 失效分类、数据缺口与训练必要性 | 03、09、12 |

## 六周学习与项目节奏

下面保留一条专注长任务与系统设计的六周选读路线，供有相应目标的读者安排节奏。希望先做出可运行服务时，从上方快速搭建路线开始即可。

| 阶段 | 阅读 | 本周产物 |
| --- | --- | --- |
| 第 1 周 | 01–02 | 运行时职责图；副作用前后崩溃的恢复表 |
| 第 2 周 | 03–04 | 上下文包；记忆更正与技能版本方案 |
| 第 3 周 | 05–06 | 工具合同；跨文档证据和追加检索策略 |
| 第 4 周 | 07–08 | 单/多 Agent 对照；隔离环境的操作记录 |
| 第 5 周 | 09–10 | 逐题评测表；延迟与预算实验 |
| 第 6 周 | 11–12 | 越权与奖励漏洞用例；改进和发布决策 |

先读机制，记录输入、状态和结果。再用对应实验核对变化或故障，保留影响判断的证据。[贯穿项目工作坊](project-workshop.md)把这些产物接成同一个项目。

<div id="三组能运行的进阶机制实验"></div>

## 能运行的进阶机制实验

在仓库根目录运行，Python 3.10+，只使用标准库：

```bash
python3 examples/advanced/runtime_lab.py --scenario evaluation
python3 examples/advanced/runtime_lab.py --scenario budget
python3 examples/advanced/runtime_lab.py --scenario replay
```

实验分别复算多次尝试指标与组内相对信号、验证预算预留与理想关键路径、模拟两个独立 SQLite 数据库之间的副作用后崩溃恢复。具体输入、预期输出和实现边界见 [实验说明](../examples/advanced/README.md)。

[逐题配对统计实验](../examples/advanced/evaluation_lab.py)由固定逐题结果复算修复、退步与不确定性，输入不是模型新跑出的成绩。[训练目标实验](../examples/advanced/training-objectives.md)进一步计算动作mask、目标与梯度，实际更新小型二值参数；它不调用模型或GPU，也不证明真实LLM的训练收益。两者分别连接09与12的推导，运行方法和可证明范围以对应说明为准。

[检索机制实验](../examples/advanced/retrieval-mechanisms.md)连接06章的词项评分、精确向量排序、候选上限与冲突裁决，使用公开的教学输入复算计算过程；它没有运行真实编码器、ANN或重排模型。

## 六组应用实验

默认使用Python标准库，离线验证协议、真实本地组件与状态合同。运行命令、失败场景和证据等级见各实验：

[模型协议](../examples/model_protocol_lab/README.md) · [知识摄取](../examples/knowledge_pipeline_lab/README.md) · [SQL分析](../examples/sql_agent_lab/README.md) · [任务服务](../examples/service_lab/README.md) · [事件订阅](../examples/event_agent_lab/README.md) · [媒体与播放](../examples/multimodal_lab/README.md)。

用固定输入可以检验控制逻辑；真实模型的工具选择、生成质量和费用需要独立任务集与多次运行。外部框架的阅读案例也不等于已在本机部署对应平台。具体能力与验收矩阵见 [应用扩充说明](../research/application-expansion.md)。

## 跟着一手资料继续读

[GitHub 与技术博客调研](../research/advanced-landscape.md)解释所选项目带来了哪些能力、怎样与基础原理衔接；[官方知识体系与选读地图](official-learning-map.md)把文档、协议和论文放到对应学习阶段。外部项目的版本、接口和维护方式不同，运行示例时使用相应项目的环境与版本说明。

延伸阅读可以访问作者的 [Agent 技术博客](https://agent.harrylab.cn/articles/)，选读工程实践和原理图解；遇到 Harness、Context、MCP 等术语时，可打开 [AI 编程字典](https://agent.harrylab.cn/dictionary/)查看解释与概念关系，再回到正文和配套题巩固理解。

[返回首页](../README.md) · [基础原理](../learning/README.md) · [110 题总索引](../docs/question-index.md) · [进阶面试题](../docs/advanced/README.md)
