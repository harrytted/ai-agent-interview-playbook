# Agent 进阶技术图谱：从工具循环走向完整系统

[基础原理](../learning/README.md)说明模型如何选择工具、应用如何执行动作。进阶学习要继续回答：任务跨会话怎样推进，进程中断后怎样恢复，哪些信息应进入上下文，多个 Agent 怎样交接，以及怎样用评测数据推动改进。

项目按技术层次排列。Star 使用项目页面显示的近似快照，表示关注规模；选材同时考虑机制是否清楚、关键实现能否阅读、是否能形成可比较的实验。[来源元数据](advanced-sources.json)保存具体阅读入口与版本信息。

## 相对基础课增加了什么

| 基础问题 | 进阶问题 | 对应章节 |
| --- | --- | --- |
| 能跑通一次工具循环吗？ | 谁管理工作目录、任务清单、上下文和执行环境？ | [01 Harness](../advanced/01-harness-and-deep-agents.md) |
| 调用失败后重试吗？ | 重启后从哪里恢复，哪些副作用允许重放？ | [02 持久执行](../advanced/02-durable-execution.md) |
| Prompt 怎样写清楚？ | 信息怎样选择、压缩、外置、失效和重新加载？ | [03 上下文工程](../advanced/03-context-engineering.md) |
| 怎样保存聊天记录？ | 记忆的作用域、来源、时效和 Skills 的装载方式怎样设计？ | [04 记忆与 Skills](../advanced/04-memory-and-skills.md) |
| 怎样声明一个工具？ | 工具很多时怎样发现、路由、授权和控制返回规模？ | [05 工具路由与 MCP](../advanced/05-tool-routing-and-mcp.md) |
| 怎样检索相似片段？ | 何时改写问题、换检索器、查关系或汇总整个语料？ | [06 Agentic RAG](../advanced/06-agentic-rag.md) |
| 多个角色怎样协作？ | 怎样约定所有权、输入输出、取消、并发和预算？ | [07 多 Agent](../advanced/07-multi-agent-systems.md) |
| 怎样调用 API？ | 怎样在代码仓库或桌面环境中观察、行动和验证结果？ | [08 Coding 与 Computer Use](../advanced/08-coding-and-computer-use.md) |
| 这次回答正确吗？ | 怎样建立任务集、校准评审器并定位轨迹错误？ | [09 评测与反馈](../advanced/09-evaluation-and-feedback.md) |
| 怎样节省 Token？ | 关键路径、工具延迟、并发和推理服务怎样共同影响成本？ | [10 性能与服务](../advanced/10-performance-and-serving.md) |
| 怎样提醒模型遵守规则？ | 谁验证权限，谁隔离执行环境，外部内容怎样跨越信任边界？ | [11 安全与治理](../advanced/11-security-and-governance.md) |
| 反思后能改进回答吗？ | 轨迹、奖励和训练算法怎样真正更新模型参数？ | [12 Agent 训练](../advanced/12-agent-training.md) |

## 八个值得拆开阅读的 GitHub 项目

### Harness、SDK 与工作流

| 项目与规模 | 机制和适用场景 | 应纳入知识体系的内容 |
| --- | --- | --- |
| [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)，约 30.7k Star，MIT | 在 LangChain / LangGraph 上组合任务规划、文件系统、子 Agent 和上下文管理。适合研究长任务的运行骨架。 | 阅读 [Backends](https://docs.langchain.com/oss/python/deepagents/backends)：区分线程内状态、跨线程存储和真实文件系统；路径路由解决存储位置，执行隔离由相应环境承担。对应 01、03、04、08。 |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow)，约 84.5k Star，MIT | 2.0 是相对 1.x 的整体重写，组合 lead agent、子任务、Skills、记忆和沙箱；后端与网关、前端构成完整应用。适合拆解端到端系统。 | 阅读 [后端架构](https://github.com/bytedance/deer-flow/blob/main/backend/README.md)：沿请求经过网关、运行时、中间件和执行环境追踪责任。环境包含 Python 3.12+、Node.js 22+ 等组件，不能只比较几行 Agent 配置。对应 01、02、07、08。 |
| [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)，约 8.4k Star，MIT | 封装 Claude Code 的 Agent 运行能力；单次查询与可交互客户端有不同会话语义。适合代码、文件和命令行任务集成。 | 阅读 [query.py](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/query.py) 与[权限规则](https://code.claude.com/docs/en/agent-sdk/permissions)：区分模型可见工具和执行审批；`allowed_tools` 用于自动审批，未列出的工具还会进入其他权限判断。对应 02、08、11。 |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python)，约 30.3k Star，MIT | 以 Agent、工具、交接、会话和追踪组织运行过程。适合比较“主管调用专家”和“专家接管会话”。 | 阅读 [handoffs 源码](https://github.com/openai/openai-agents-python/blob/main/src/agents/handoffs/__init__.py)：交接包含输入历史与新产生内容的传递；要明确下一位 Agent 接收什么、谁负责最终答复。对应 02、05、07、09。 |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework)，约 14.3k Star，MIT | 将 Agent 与可组合工作流放在同一套 Python / .NET 体系中；样例覆盖图式与函数式编排。适合研究确定性步骤与模型决策如何混合。 | 阅读 [工作流目录](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/README.md) 和 [step checkpoint 样例](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/functional/steps_and_checkpointing.py)：比较恢复时普通函数重跑与已记录步骤返回结果。样例使用内存 checkpoint，跨进程恢复需要相应持久存储。对应 02、07、09。 |

### 图记忆、图检索与训练

| 项目与规模 | 机制和适用场景 | 应纳入知识体系的内容 |
| --- | --- | --- |
| [getzep/graphiti](https://github.com/getzep/graphiti)，约 32.3k Star，Apache-2.0 | 增量构建带时间和来源的知识图，结合语义、关键词与图遍历检索。适合信息持续变化、需要追踪事实来源的记忆系统。 | 阅读 [EntityEdge 数据结构](https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py)：区分事实有效时间、系统失效记录与来源 episode；配合图数据库、模型和嵌入服务管理摄入成本。对应 04、06。 |
| [microsoft/graphrag](https://github.com/microsoft/graphrag)，约 36.5k Star，MIT | 从语料抽取关系并形成社区报告；[Global Search](https://microsoft.github.io/graphrag/query/global_search/)利用报告分批生成、汇总回答，适合全局主题类问题。 | 将“整个语料有哪些主题”和“某事实的证据在哪”分开评测，并核算离线索引成本。当前仓库已进入 maintenance mode，阅读其方法时同时考虑依赖与维护策略。对应 06、09。 |
| [microsoft/agent-lightning](https://github.com/microsoft/agent-lightning)，约 18.8k Star，MIT | v1.0 把训练、模型请求代理和 rollout 控制拆开，让真实 harness 产生训练轨迹。适合已有任务环境、奖励与训练算力后的优化实验。 | 阅读 [v1 基础架构](https://microsoft.github.io/agent-lightning/stable/05-basics/)：识别 Trainer、API Gateway、Rollout Controller 的边界。主分支 v1.0 与 legacy 的 v0.x 需分开阅读；当前[论文](https://arxiv.org/abs/2608.17528)与[早期论文](https://arxiv.org/abs/2508.03680)对应不同阶段。对应 09、10、12。 |

这几层可以组合：Harness 管理任务执行，记忆系统保存可再利用的信息，检索管线组织知识访问，训练系统根据轨迹更新策略。学习时先确定缺少哪一层，再选择项目，能减少把多套框架重复叠在一起的成本。

## 八篇博客如何变成课程内容

| 想解决的问题 | 阅读材料 | 采用的方法与讨论范围 |
| --- | --- | --- |
| 长任务跨上下文窗口怎样交接？ | Anthropic：[Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents) | 用初始化、功能清单、进度记录、版本控制与增量测试组织编码任务。课程将“交接后能继续推进”作为实验目标；具体效果需在自己的任务集上比较。对应 01、02、08。 |
| 上下文为什么越长越难管理？ | Anthropic：[Effective context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 从整个输入集合出发安排高信号内容，按需读取外部信息，讨论压缩与子 Agent 的信息损失。上下文工程也包含工具返回和状态组织。对应 03、04。 |
| 数百个工具怎样让模型选得动？ | Anthropic：[Advanced tool use](https://www.anthropic.com/research/advanced-tool-use) | 比较工具按需发现、在执行环境中聚合调用结果、用示例补充接口约束。工具搜索会增加发现环节，适合与小工具集直接暴露做成本比较。对应 05、10。 |
| Deep Agent 比工具循环多了什么？ | LangChain：[Deep Agents](https://www.langchain.com/blog/deep-agents) | 将规划、文件、子 Agent 和详细任务指导视作可组合的运行机制；逐项移除做消融比较，观察成功率、上下文与调用数变化。对应 01、03、07。 |
| 模型外面的运行骨架负责什么？ | LangChain：[The anatomy of an agent harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness) | 从工作空间、执行环境、持久状态与 hooks 分配职责。Harness 是工程划分方式，具体边界随 SDK 和部署方式变化。对应 01、02、08、11。 |
| 规划、记忆和工具之间怎样联系？ | Lilian Weng：[LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) | 作为经典分类和论文入口，回看有限上下文、长程规划及接口可靠性的难点，再与当前实现比较。反思文本进入后续输入，与训练更新参数分别讲解。对应 03、04、07、12。 |
| LLM Judge 的评分怎样值得使用？ | Hamel Husain：[Using LLM-as-a-Judge for Evaluation](https://hamel.dev/blog/posts/llm-judge/) | 从领域专家、覆盖实际场景的样本和具体错误说明开始，再校准评审器并按错误类型分析。业务标签需由任务标准定义，不能直接套用通用分数。对应 09。 |
| 规划失败到底发生在哪一层？ | Chip Huyen：[Agents](https://huyenchip.com/2025/01/07/agents.html) | 区分动作选择、参数推断、计划粒度与执行反馈；据此给失败轨迹分类。动作合法与参数业务正确是两个检查点。对应 05、07、09。 |

## 怎样把调研转成自己的项目能力

先保留一个可重复运行的任务集，再为每项新增机制安排对照实验。长任务可以比较“完整历史”和“摘要加文件索引”；知识助手可以比较固定检索、Agent 自选检索和图式全局汇总；多 Agent 可以比较单 Agent 与主管加专家，并同时记录最终质量、工具调用、延迟和成本。

训练应放在后面：先证明瓶颈来自策略能力，准备独立测试任务，再比较提示、工具改造和参数训练。SFT 需要高质量示范，DPO 需要可比较的偏好对；进行在线 Agent RL 时，再准备可执行、可重置的任务环境与奖励。把工具返回错误、权限错误或检索缺证误记为模型能力不足，往往会让训练目标偏离真正问题。

阅读时建议形成三类材料：一张责任与数据流图，一组可复现的失败轨迹，一份包含基线和预算的实验表。它们可以直接支持项目复盘，也比背项目功能清单更容易回答面试追问。

继续阅读：[工程进阶](../advanced/README.md) · [按问题选择官方资料](../advanced/official-learning-map.md) · [来源元数据](advanced-sources.json)
