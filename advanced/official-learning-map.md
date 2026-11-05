# 按问题选择 Agent 官方资料

先从自己遇到的工程问题找到对应章节，再读相应论文或官方文档。先弄清算法和状态变化，再映射到框架接口；API能接通不等于原理已经掌握。每次阅读留下一个可以检查的推导、状态图、失败轨迹或实验结果。

## 十二章阅读路径

| 章节与问题 | 官方阅读路径 | 读完要能做什么 |
| --- | --- | --- |
| [01 Harness 与 Deep Agents](01-harness-and-deep-agents.md)：模型外面还需要哪些组件？ | 先读 [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk)，区分 SDK 的运行能力与应用负责的部署、存储和审批；再读 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)，追踪文件工具背后的存储位置。 | 为模型、运行循环、状态、工具和执行环境划分责任，并画出一次请求的数据流。 |
| [02 持久执行](02-durable-execution.md)：中断后从哪里继续？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的 checkpointer / store 区别；再读 Microsoft [step checkpoint 样例](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/functional/steps_and_checkpointing.py)，比较恢复时哪些函数重新执行。 | 写出 checkpoint 边界与副作用清单；区分内存样例和重启可恢复的存储；为重复动作设计幂等键。 |
| [03 上下文工程](03-context-engineering.md)：当前步骤究竟需要看到什么？ | 先读 Anthropic [Context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)，再用 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)观察内容外置后如何按需读回。 | 为指令、历史、检索片段、工具输出分别安排预算、引用与淘汰规则；评估摘要后丢失的约束。 |
| [04 记忆与 Skills](04-memory-and-skills.md)：保存事实与保存做事方法有何不同？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)区分线程与跨线程数据；再读 Anthropic [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)，观察指令、元数据和附属资源的按需装载。 | 设计记忆命名空间、来源与有效期；为重复任务写一个有输入、步骤和验证方法的 Skill；解释其与模型训练的区别。 |
| [05 工具路由与 MCP](05-tool-routing-and-mcp.md)：发现工具、连接工具和批准执行分别由谁负责？ | 先读 [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)，区分 host、client、server；再读 Anthropic [Advanced tool use](https://www.anthropic.com/research/advanced-tool-use)，比较按需工具发现与直接暴露。 | 画出工具发现与工具调用两条路径；分别设计 schema 校验、业务权限、执行预算和结果裁剪。 |
| [06 Agentic RAG](06-agentic-rag.md)：候选怎样取得，遗漏和冲突怎样定位？ | 从 [Lucene BM25](https://lucene.apache.org/core/10_5_2/core/org/apache/lucene/search/similarities/BM25Similarity.html)与 [DPR](https://arxiv.org/abs/2004.04906)区分匹配信号，再读 [Faiss索引分类](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)区分表示与近似搜索误差；图检索另读 [GraphRAG Global Search](https://microsoft.github.io/graphrag/query/global_search/)。 | 推导词频与长度影响；对同一资格域比较精确搜索和ANN，区分候选覆盖、排序与上下文丢失；解释冲突为何不能靠相似度裁定。 |
| [07 多 Agent 系统](07-multi-agent-systems.md)：谁拥有任务，谁拥有最终答复？ | 先读 OpenAI [Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)，比较 handoff 与 agent-as-tool；再读 [DeepAgents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)，观察上下文隔离与委派开销。 | 为主管和专家写清输入、产物、共享状态与取消条件；确定是接管还是调用；与单 Agent 基线比较。 |
| [08 Coding 与 Computer Use](08-coding-and-computer-use.md)：怎样判断动作真的改变了环境？ | 先读 Anthropic [Long-running agent harnesses](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)，把任务清单、进度和测试放进工作空间；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)，区分模型请求与执行批准。 | 为观察、行动、结果验证和恢复建立闭环；用文件、测试或界面状态确认完成；把执行权限与任务文本分开保存。 |
| [09 评测与反馈](09-evaluation-and-feedback.md)：怎么知道改动有用？ | 先读 [OpenAI Agent evals](https://developers.openai.com/api/docs/guides/agent-evals)，把轨迹诊断接到数据集与评测运行；再读 Hugging Face [Agent Observability & Evaluation](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)。配对统计对照 [statsmodels McNemar](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html) 的 exact 二项检验与 [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) 的 paired 相同索引重采样。 | 给任务集定义验收条件与失败分类；校准评分器；从逐题不一致对计算差异与区间，说明独立任务、预算固定、小样本和同源相关限制。手写教学夹具不证明模型提升。 |
| [10 性能与服务](10-performance-and-serving.md)：慢在模型还是慢在系统？ | 先从 Hugging Face [可观测性课程](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)建立分阶段测量；再读 Transformers [Optimizing inference](https://huggingface.co/docs/transformers/main/en/llm_optims)的 KV cache 等机制。该入口为 main 文档，复现实验时需对齐安装版本。 | 分开测量模型生成、工具执行、排队与重试；在相同质量要求下比较并发、缓存和上下文缩减。 |
| [11 安全与治理](11-security-and-governance.md)：能连上工具是否就代表有权执行？ | 先读 [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)的 HTTP transport 授权范围；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)的执行规则与运行时审批。 | 将服务身份、资源访问、用户同意、工具策略与执行隔离画成独立边界；覆盖拒绝、撤销和越权测试。 |
| [12 Agent 训练](12-agent-training.md)：示范、偏好与回报怎样形成更新？ | 先读 [TRL SFT](https://huggingface.co/docs/trl/sft_trainer) 的目标掩码与 [DPO §4](https://arxiv.org/html/2305.18290v2#S4)的参考策略，再对照 [DeepSeekMath v3 §4.1](https://arxiv.org/html/2402.03300v3#S4.SS1) 的策略比、裁剪与 KL；[本手册目标实验](../examples/advanced/training-objectives.md)复算其中的 SFT/裁剪小策略，真实多轮训练另读 [TRL Agent Training](https://huggingface.co/docs/trl/grpo_trainer#agent-training)。 | 从动作概率解释NLL、DPO偏好差距与轨迹回报；区分参考策略、采样旧策略、环境观察和模型动作，说明分布偏移及奖励漏洞。数值算例与现有实验支持范围分别核对。 |

## 应用专题六章阅读路径

| 章节 | 一手资料 | 阅读后检查什么 |
| --- | --- | --- |
| [13 模型API](13-model-api-and-output-contracts.md) | [Claude工具往返](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works) · [结构化输出](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | SDK与宿主职责、调用ID、输出完整性和异常终态；字段按实际API版本核对 |
| [14 摄取生命周期](14-ingestion-and-index-lifecycle.md) | [LlamaIndex Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/) | 文档身份、哈希、变更传播、索引发布和撤权；不把所有后端能力视为相同 |
| [15 SQL分析](15-text-to-sql-and-data-analysis.md) | [PostgreSQL 18 SELECT语义](https://www.postgresql.org/docs/18/sql-select.html) · [SQL语义测试集论文](https://arxiv.org/abs/2010.02840) · [Spider2](https://spider2-sql.github.io/) | 从逻辑顺序和重复行解释聚合结果，再用多个数据实例检验业务口径；不要只比较SQL字符串 |
| [16 任务服务](16-service-deployment-and-operations.md) | [LangSmith Agent Server](https://docs.langchain.com/langsmith/agent-server) · [长任务Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents) | 任务归属、持久接收、取消、流事件与跨重启恢复 |
| [17 事件任务](17-event-driven-and-proactive-agents.md) | [Kafka 4.0设计](https://kafka.apache.org/40/design/design/) · [Flink 1.20事件时间](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/datastream/event-time/generating_watermarks/) | 分区顺序、连续完成位置、事件时间窗口与迟到修订；本地订阅实验未实现Kafka/Flink流处理 |
| [18 媒体与语音](18-multimodal-and-realtime-agents.md) | [LLaVA v2 §4.1](https://arxiv.org/html/2304.08485v2#S4.SS1) · [Transformer Transducer](https://arxiv.org/abs/2010.03192) · [LiveKit Turns](https://docs.livekit.io/agents/logic/turns/) | 视觉投影、流式右上下文与修订、轮次和已播确认；表示对齐不等于事实核验，离线夹具不证明识别效果 |

先走13→16A→14→16B，SQL作为方向分支，事件与媒体作为后续扩展。具体机制、采用理由与限定见 [应用扩充说明](../research/application-expansion.md)。

## 从自己的项目出发

**代码或桌面助手**：按 01 → 02 → 03 → 08 → 11 → 09 阅读。先做到任务状态可恢复、动作可验证，再加入更多自主行为。一次失败至少保留初始状态、动作、观察和停止原因，便于重放比较。

**企业知识助手**：按 03 → 04 → 05 → 06 → 09 阅读。先确定问题类型和数据访问边界，再选择检索策略。对外部内容保留来源，对记忆保留作用域；评测既看答案，也看引用是否真正支持答案。

**多 Agent 或训练项目**：多 Agent 项目先读 07 和 09，证明分工收益并建立任务集；再读 10 评估资源需求。训练方向先建立独立测试集，再进入 12：SFT 准备高质量示范，DPO 准备偏好对，在线 Agent RL 再准备可执行、可重置的任务环境与奖励。模型反思记录可以进入后续输入，参数是否更新则由具体训练流程决定。

训练章的数值阅读分两步：先按两轮动作划目标 mask，完整复算均值 NLL；再固定旧策略与优势，分别计算正负优势的概率比、裁剪项、参考分布 KL 和一个参数步骤。小实验只更新二元表格参数，不能填成真实 LLM 训练经历；原论文的输出长度均值、实现文档的归一化选项与本例一动作状态均值要分别记录。

Agent Lightning 的版本阅读以 [v1.0 技术报告 v1](https://arxiv.org/html/2608.17528v1) 为机制依据，旧版见 [`v0.x`](https://github.com/microsoft/agent-lightning/tree/v0.x)。报告 §3.2 的相同 prompt 只保留最后一次 `model_request`，是具体样本选择规则；一般审计数据保留建议单独讨论。TRL、统计库与项目 README 为 2026-11-05 核对的可变文档，复现实验仍需对齐实际安装版本。

## 阅读时对齐三种边界

**概念与实现边界**：handoff、session、checkpoint 等词在不同 SDK 中各有具体语义。先说明交接的所有权、持久化的数据和恢复位置，再映射到 API。文档示例中的内存对象要与实际部署的存储生命周期一起解释。

**协议与应用边界**：MCP 定义上下文和工具交互接口；任务编排、业务权限与执行策略仍要由应用和相关服务配置。Claude SDK 的自动审批规则也不能直接当作工具可见性的定义。

**实验与结论边界**：同一任务集、同一预算、同一验收条件下比较一个机制的增量收益。需要更换模型、硬件或任务分布时重新测量，报告质量、延迟、成本与失败类型，才容易解释为什么选择某种架构。

[返回工程进阶](README.md) · [GitHub 与博客图谱](../research/advanced-landscape.md) · [来源元数据](../research/advanced-sources.json)
