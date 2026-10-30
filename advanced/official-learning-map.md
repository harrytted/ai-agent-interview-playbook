# 按问题选择 Agent 官方资料

先从自己遇到的工程问题进入课程，再读相应官方文档。每次阅读都留下一个设计产物或实验结果：状态图、接口契约、失败轨迹、评测样本或性能数据。这样可以把不同产品的术语放回同一个系统模型中。

## 十二章阅读路径

| 章节与问题 | 官方阅读路径 | 读完要能做什么 |
| --- | --- | --- |
| [01 Harness 与 Deep Agents](01-harness-and-deep-agents.md)：模型外面还需要哪些组件？ | 先读 [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk)，区分 SDK 的运行能力与应用负责的部署、存储和审批；再读 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)，追踪文件工具背后的存储位置。 | 为模型、运行循环、状态、工具和执行环境划分责任，并画出一次请求的数据流。 |
| [02 持久执行](02-durable-execution.md)：中断后从哪里继续？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的 checkpointer / store 区别；再读 Microsoft [step checkpoint 样例](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/functional/steps_and_checkpointing.py)，比较恢复时哪些函数重新执行。 | 写出 checkpoint 边界与副作用清单；区分内存样例和重启可恢复的存储；为重复动作设计幂等键。 |
| [03 上下文工程](03-context-engineering.md)：当前步骤究竟需要看到什么？ | 先读 Anthropic [Context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)，再用 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)观察内容外置后如何按需读回。 | 为指令、历史、检索片段、工具输出分别安排预算、引用与淘汰规则；评估摘要后丢失的约束。 |
| [04 记忆与 Skills](04-memory-and-skills.md)：保存事实与保存做事方法有何不同？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)区分线程与跨线程数据；再读 Anthropic [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)，观察指令、元数据和附属资源的按需装载。 | 设计记忆命名空间、来源与有效期；为重复任务写一个有输入、步骤和验证方法的 Skill；解释其与模型训练的区别。 |
| [05 工具路由与 MCP](05-tool-routing-and-mcp.md)：发现工具、连接工具和批准执行分别由谁负责？ | 先读 [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)，区分 host、client、server；再读 Anthropic [Advanced tool use](https://www.anthropic.com/research/advanced-tool-use)，比较按需工具发现与直接暴露。 | 画出工具发现与工具调用两条路径；分别设计 schema 校验、业务权限、执行预算和结果裁剪。 |
| [06 Agentic RAG](06-agentic-rag.md)：什么时候需要让 Agent 决定检索动作？ | 先读 LangChain [Retrieval](https://docs.langchain.com/oss/python/deepagents/retrieval)中固定检索与 Agentic RAG 的选择；再读 Microsoft GraphRAG [Global Search](https://microsoft.github.io/graphrag/query/global_search/)，观察社区报告如何支持全局问题。 | 为事实定位与全局汇总建立不同测试样本；比较检索覆盖、证据支持、端到端延迟和索引成本。 |
| [07 多 Agent 系统](07-multi-agent-systems.md)：谁拥有任务，谁拥有最终答复？ | 先读 OpenAI [Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)，比较 handoff 与 agent-as-tool；再读 [DeepAgents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)，观察上下文隔离与委派开销。 | 为主管和专家写清输入、产物、共享状态与取消条件；确定是接管还是调用；与单 Agent 基线比较。 |
| [08 Coding 与 Computer Use](08-coding-and-computer-use.md)：怎样判断动作真的改变了环境？ | 先读 Anthropic [Long-running agent harnesses](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)，把任务清单、进度和测试放进工作空间；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)，区分模型请求与执行批准。 | 为观察、行动、结果验证和恢复建立闭环；用文件、测试或界面状态确认完成；把执行权限与任务文本分开保存。 |
| [09 评测与反馈](09-evaluation-and-feedback.md)：怎么知道改动有用？ | 先读 [OpenAI Agent evals](https://developers.openai.com/api/docs/guides/agent-evals)，把轨迹诊断接到数据集与评测运行；再读 Hugging Face [Agent Observability & Evaluation](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)，连接工具轨迹、成本、延迟与离线比较。 | 给任务集定义验收条件和失败分类；把轨迹错误与最终结果分别记录；用人工样本校准模型评审器。 |
| [10 性能与服务](10-performance-and-serving.md)：慢在模型还是慢在系统？ | 先从 Hugging Face [可观测性课程](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)建立分阶段测量；再读 Transformers [Optimizing inference](https://huggingface.co/docs/transformers/main/en/llm_optims)的 KV cache 等机制。该入口为 main 文档，复现实验时需对齐安装版本。 | 分开测量模型生成、工具执行、排队与重试；在相同质量要求下比较并发、缓存和上下文缩减。 |
| [11 安全与治理](11-security-and-governance.md)：能连上工具是否就代表有权执行？ | 先读 [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)的 HTTP transport 授权范围；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)的执行规则与运行时审批。 | 将服务身份、资源访问、用户同意、工具策略与执行隔离画成独立边界；覆盖拒绝、撤销和越权测试。 |
| [12 Agent 训练](12-agent-training.md)：什么时候需要更新参数？ | 先读 Hugging Face TRL [GRPO Trainer / Agent Training](https://huggingface.co/docs/trl/grpo_trainer#agent-training)，理解工具、环境与奖励；再读 Microsoft [Agent Lightning v1 基础架构](https://microsoft.github.io/agent-lightning/stable/05-basics/)，区分策略训练与 rollout 执行。 | 定义可重置环境、轨迹格式、奖励和独立测试集；解释提示改动、记忆更新与梯度更新分别改变了什么。 |

## 从自己的项目出发

**代码或桌面助手**：按 01 → 02 → 03 → 08 → 11 → 09 阅读。先做到任务状态可恢复、动作可验证，再加入更多自主行为。一次失败至少保留初始状态、动作、观察和停止原因，便于重放比较。

**企业知识助手**：按 03 → 04 → 05 → 06 → 09 阅读。先确定问题类型和数据访问边界，再选择检索策略。对外部内容保留来源，对记忆保留作用域；评测既看答案，也看引用是否真正支持答案。

**多 Agent 或训练项目**：多 Agent 项目先读 07 和 09，证明分工收益并建立任务集；再读 10 评估资源需求。训练方向先建立独立测试集，再进入 12：SFT 准备高质量示范，DPO 准备偏好对，在线 Agent RL 再准备可执行、可重置的任务环境与奖励。模型反思记录可以进入后续输入，参数是否更新则由具体训练流程决定。

## 阅读时对齐三种边界

**概念与实现边界**：handoff、session、checkpoint 等词在不同 SDK 中各有具体语义。先说明交接的所有权、持久化的数据和恢复位置，再映射到 API。文档示例中的内存对象要与实际部署的存储生命周期一起解释。

**协议与应用边界**：MCP 定义上下文和工具交互接口；任务编排、业务权限与执行策略仍要由应用和相关服务配置。Claude SDK 的自动审批规则也不能直接当作工具可见性的定义。

**实验与结论边界**：同一任务集、同一预算、同一验收条件下比较一个机制的增量收益。需要更换模型、硬件或任务分布时重新测量，报告质量、延迟、成本与失败类型，才容易解释为什么选择某种架构。

[返回进阶课程](README.md) · [GitHub 与博客图谱](../research/advanced-landscape.md) · [来源元数据](../research/advanced-sources.json)
