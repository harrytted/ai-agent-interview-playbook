# 按问题选择 Agent 官方资料

先从自己遇到的工程问题找到对应章节，再读相应论文或官方文档。先弄清算法和状态变化，再映射到框架接口；API能接通不等于原理已经掌握。每次阅读留下一个可以检查的推导、状态图、失败轨迹或实验结果。

## 十二章阅读路径

| 章节与问题 | 官方阅读路径 | 读完要能做什么 |
| --- | --- | --- |
| [01 Harness 与 Deep Agents](01-harness-and-deep-agents.md)：模型外面还需要哪些组件？ | 先读 [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk)，区分 SDK 的运行能力与应用负责的部署、存储和审批；再读 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)，追踪文件工具背后的存储位置。 | 为模型、运行循环、状态、工具和执行环境划分责任，并画出一次请求的数据流。 |
| [02 持久执行](02-durable-execution.md)：中断后从哪里继续？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) 的 checkpointer / store 区别；再读 Microsoft [step checkpoint 样例](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/functional/steps_and_checkpointing.py)，比较恢复时哪些函数重新执行。 | 写出 checkpoint 边界与副作用清单；区分内存样例和重启可恢复的存储；为重复动作设计幂等键。 |
| [03 上下文工程](03-context-engineering.md)：当前步骤究竟需要看到什么？ | 先读 Anthropic [Context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)，再用 [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)观察内容外置后如何按需读回。 | 为指令、历史、检索片段、工具输出分别安排预算、引用与淘汰规则；评估摘要后丢失的约束。 |
| [04 记忆与 Skills](04-memory-and-skills.md)：保存事实与保存做事方法有何不同？ | 先读 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)区分线程与跨线程数据；再读 Anthropic [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)，观察指令、元数据和附属资源的按需装载。技能的验证方法见 [编写技能说明](https://agentskills.io/skill-creation/optimizing-descriptions)和[评估技能效果](https://agentskills.io/skill-creation/evaluating-skills)。 | 设计记忆命名空间、来源与有效期。为重复任务写一个有输入、步骤和验证方法的技能，再按[技能选择与效果专题](04-memory-and-skills.md#技能选择与效果验证)分别检查技能是否选对、结果是否改善。 |
| [05 工具路由与 MCP](05-tool-routing-and-mcp.md)：发现工具、连接工具和批准执行分别由谁负责？ | 先读 [MCP 架构](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)，区分宿主、客户端和服务端，对照两版的能力发现方式；再读 Anthropic [Advanced tool use](https://www.anthropic.com/research/advanced-tool-use)，比较按需工具发现与直接暴露。 | 画出工具发现与工具调用两条路径；分别设计 schema 校验、业务权限、执行预算和结果裁剪。 |
| [06 Agentic RAG](06-agentic-rag.md)：候选怎样取得，遗漏和冲突怎样定位？ | 从 [Lucene BM25](https://lucene.apache.org/core/10_5_2/core/org/apache/lucene/search/similarities/BM25Similarity.html)与 [DPR](https://arxiv.org/abs/2004.04906)区分匹配信号，再读 [Faiss索引分类](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)区分表示与近似搜索误差；图检索另读 [GraphRAG Global Search](https://microsoft.github.io/graphrag/query/global_search/)。 | 推导词频与长度影响；对同一资格域比较精确搜索和ANN，区分候选覆盖、排序与上下文丢失；解释冲突为何不能靠相似度裁定。 |
| [07 多 Agent 系统](07-multi-agent-systems.md)：谁拥有任务，谁拥有最终答复？ | 先读 OpenAI [Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)，比较 handoff 与 agent-as-tool；再读 [DeepAgents Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)，观察上下文隔离与委派开销。 | 为主管和专家写清输入、产物、共享状态与取消条件；确定是接管还是调用；与单 Agent 基线比较。 |
| [08 Coding 与 Computer Use](08-coding-and-computer-use.md)：怎样判断动作真的改变了环境？ | 先读 Anthropic [Long-running agent harnesses](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)，把任务清单、进度和测试放进工作空间；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)，区分模型请求与执行批准。 | 为观察、行动、结果验证和恢复建立闭环；用文件、测试或界面状态确认完成；把执行权限与任务文本分开保存。 |
| [09 评测与反馈](09-evaluation-and-feedback.md)：怎么知道改动有用？ | 先读 [OpenAI Agent evals](https://developers.openai.com/api/docs/guides/agent-evals)，把轨迹诊断接到数据集与评测运行；再读 Hugging Face [Agent Observability & Evaluation](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)。配对统计对照 [statsmodels McNemar](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html) 的 exact 二项检验与 [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) 的 paired 相同索引重采样。 | 给任务集定义验收条件与失败分类；校准评分器；从逐题不一致对计算差异与区间，说明独立任务、预算固定、小样本和同源相关限制。手写教学夹具不证明模型提升。 |
| [10 性能与服务](10-performance-and-serving.md)：慢在模型还是慢在系统？ | 先从 Hugging Face [可观测性课程](https://huggingface.co/learn/agents-course/en/bonus-unit2/introduction)建立分阶段测量；再读 Transformers [Optimizing inference](https://huggingface.co/docs/transformers/main/en/llm_optims)的 KV cache 等机制。该入口为 main 文档，复现实验时需对齐安装版本。 | 分开测量模型生成、工具执行、排队与重试；在相同质量要求下比较并发、缓存和上下文缩减。 |
| [11 安全与治理](11-security-and-governance.md)：能连上工具是否就代表有权执行？ | 先读 [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)的 HTTP transport 授权范围；再读 Claude SDK [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)的执行规则与运行时审批。 | 将服务身份、资源访问、用户同意、工具策略与执行隔离画成独立边界；覆盖拒绝、撤销和越权测试。 |
| [12 Agent 训练](12-agent-training.md)：示范、偏好与回报怎样形成更新？ | 先读 [TRL SFT](https://huggingface.co/docs/trl/sft_trainer) 的目标掩码与 [DPO §4](https://arxiv.org/html/2305.18290v2#S4)的参考策略，再对照 [DeepSeekMath v3 §4.1](https://arxiv.org/html/2402.03300v3#S4.SS1) 的策略比、裁剪与 KL；[本手册目标实验](../examples/advanced/training-objectives.md)复算其中的 SFT/裁剪小策略，真实多轮训练另读 [TRL Agent Training](https://huggingface.co/docs/trl/grpo_trainer#agent-training)。 | 从动作概率解释NLL、DPO偏好差距与轨迹回报；区分参考策略、采样旧策略、环境观察和模型动作，说明分布偏移及奖励漏洞。数值算例与现有实验支持范围分别核对。 |

<div id="应用专题六章阅读路径"></div>

## 应用专题阅读路径

| 章节 | 一手资料 | 阅读后检查什么 |
| --- | --- | --- |
| [13 模型API](13-model-api-and-output-contracts.md) | [Claude工具往返](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works) · [结构化输出](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | SDK与宿主职责、调用ID、输出完整性和异常终态；字段按实际API版本核对 |
| [14 摄取生命周期](14-ingestion-and-index-lifecycle.md) | [LlamaIndex Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/) | 文档身份、哈希、变更传播、索引发布和撤权；不把所有后端能力视为相同 |
| [15 SQL分析](15-text-to-sql-and-data-analysis.md) | [PostgreSQL 18 SELECT语义](https://www.postgresql.org/docs/18/sql-select.html) · [SQL语义测试集论文](https://arxiv.org/abs/2010.02840) · [Spider2](https://spider2-sql.github.io/) | 从逻辑顺序和重复行解释聚合结果，再用多个数据实例检验业务口径；不要只比较SQL字符串 |
| [16 任务服务](16-service-deployment-and-operations.md) | [LangSmith Agent Server](https://docs.langchain.com/langsmith/agent-server) · [长任务Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents) | 任务归属、持久接收、取消、流事件与跨重启恢复 |
| [17 事件任务](17-event-driven-and-proactive-agents.md) | [Kafka 4.0设计](https://kafka.apache.org/40/design/design/) · [Flink 1.20事件时间](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/datastream/event-time/generating_watermarks/) | 分区顺序、连续完成位置、事件时间窗口与迟到修订；本地订阅实验未实现Kafka/Flink流处理 |
| [18 媒体与语音](18-multimodal-and-realtime-agents.md) | [LLaVA v2 §4.1](https://arxiv.org/html/2304.08485v2#S4.SS1) · [Transformer Transducer](https://arxiv.org/abs/2010.03192) · [LiveKit Turns](https://docs.livekit.io/agents/logic/turns/) | 视觉投影、流式右上下文与修订、轮次和已播确认；表示对齐不等于事实核验，离线夹具不证明识别效果 |
| [19 故障排查与发布验证](19-incident-review-and-release.md) | [Anthropic Agent 评测实践](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) · [Google SRE 灰度发布指南](https://sre.google/workbook/canarying-releases/) | 从任务记录定位问题，验证修复，决定何时扩大上线范围 |

先走13→16A→14→16B，SQL作为方向分支，事件与媒体作为后续扩展。准备发布与维护时，再读第 19 章。具体机制、采用理由与限定见 [应用扩充说明](../research/application-expansion.md)。

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

## 各章补充来源

### 进阶 01 的来源

<details><summary>Agent 运行框架与 Deep Agents</summary>

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [PostgreSQL 18 UPDATE](https://www.postgresql.org/docs/18/sql-update.html)
- [Deep Agents 概览](https://docs.langchain.com/oss/python/deepagents/overview)
- [Harness 结构的迭代](https://www.anthropic.com/research/harness-design-long-running-apps)

</details>

### 进阶 02 的来源

<details><summary>持久执行与恢复</summary>

- [节点重执行](https://docs.langchain.com/oss/python/langgraph/graph-api#re-execution-and-idempotency)
- [Functional API 的确定性](https://docs.langchain.com/oss/python/langgraph/functional-api#determinism)
- [Temporal 的确定性约束](https://docs.temporal.io/workflow-definition#deterministic-constraints)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [幂等请求的意图与参数](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- [Fencing token 的原始讨论](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

</details>

### 进阶 03 的来源

<details><summary>上下文选择、压缩与复用</summary>

- [Lost in the Middle及其受测范围](https://arxiv.org/abs/2307.03172)
- [Deep Agents 上下文机制](https://docs.langchain.com/oss/python/deepagents/context-engineering)
- [Anthropic 的压缩与结构化笔记实践](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents#compaction)
- [Progressive disclosure](https://agentskills.io/specification#progressive-disclosure)
- [vLLM 自动前缀缓存](https://docs.vllm.ai/en/stable/features/automatic_prefix_caching/)
- [缓存隔离设计](https://docs.vllm.ai/en/stable/design/prefix_caching/)
- [Agent Skills 规范](https://agentskills.io/specification)

</details>

### 进阶 04 的来源

<details><summary>记忆与技能</summary>

- [Generative Agents 原论文](https://arxiv.org/abs/2304.03442)
- [Graphiti 的时间图](https://github.com/getzep/graphiti)
- [关系数据结构](https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py)
- [矛盾关系的时间处理](https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py)
- [LangGraph Store](https://docs.langchain.com/oss/python/langgraph/persistence#checkpointer-vs-store)
- [AWS outbox 模式](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- [Reflexion 原论文](https://arxiv.org/abs/2303.11366)
- [Agent Skills 规范](https://agentskills.io/specification)
- [技能的加载过程](https://docs.langchain.com/oss/python/deepagents/skills)
- [SkillsBench 研究](https://arxiv.org/abs/2602.12670)
- [Agent Skills 的文件结构与渐进加载](https://agentskills.io/specification#progressive-disclosure)
- [双时间的版本与区间](https://docs.xtdb.com/about/time-in-xtdb.html)
- [OpenViking](https://github.com/volcengine/OpenViking)

</details>

### 进阶 05 的来源

<details><summary>工具路由与 MCP</summary>

- [Tool search 官方文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
- [MCP 工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [初始化与能力协商](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [MCP 分页](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/pagination)
- [MCP 消息身份](https://modelcontextprotocol.io/specification/2025-11-25/basic)
- [流恢复与会话管理](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports#resumability-and-redelivery)
- [2025-11-25 取消合同](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation)
- [MCP 错误报告](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling)
- [结构化内容与输出合同](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#structured-content)
- [Programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- [MCP 安全实践](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices)
- [A2A 核心概念](https://a2a-protocol.org/latest/topics/key-concepts/)
- [A2A 与 MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)

</details>

### 进阶 06 的来源

<details><summary>Agentic RAG 与证据检索</summary>

- [Elasticsearch search_analyzer合同](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/search-analyzer)
- [Robertson与Zaragoza的BM25原理综述](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
- [Lucene 9.12.3 BM25Similarity](https://lucene.apache.org/core/9_12_3/core/org/apache/lucene/search/similarities/BM25Similarity.html)
- [官方度量说明](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances)
- [HNSW原论文](https://arxiv.org/abs/1603.09320)
- [官方参数合同](https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md)
- [Faiss的IVF机制](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#cell-probe-methods-indexivf-indexes)
- [Faiss FAQ](https://github.com/facebookresearch/faiss/wiki/FAQ#what-does-it-mean-when-a-search-returns--1-ids)
- [Faiss动态过滤说明](https://github.com/facebookresearch/faiss/wiki/FAQ#is-it-possible-to-dynamically-exclude-vectors-based-on-some-criterion)
- [RRF原论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [BERT段落重排原论文](https://arxiv.org/abs/1901.04085)
- [Sentence Transformers检索—重排说明](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [HyDE原论文](https://arxiv.org/abs/2212.10496)
- [IRCoT原论文](https://arxiv.org/abs/2212.10509)
- [LangChain ParentDocumentRetriever合同](https://reference.langchain.com/python/langchain-classic/retrievers/parent_document_retriever/ParentDocumentRetriever)
- [RAG原论文](https://arxiv.org/abs/2005.11401)
- [官方索引dataflow](https://microsoft.github.io/graphrag/index/default_dataflow/)
- [官方Local Search](https://microsoft.github.io/graphrag/query/local_search/)
- [Faiss的同距与精度分析](https://github.com/facebookresearch/faiss/wiki/FAQ#analyzing-accuracy-issues-with-indexivfpq)
- [BEIR论文](https://arxiv.org/abs/2104.08663)
- [评测实现](https://github.com/beir-cellar/beir/blob/main/beir/retrieval/evaluation.py)

</details>

### 进阶 07 的来源

<details><summary>多 Agent 的协作与归并</summary>

- [Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
- [Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)
- [LangGraph Reducers](https://docs.langchain.com/oss/python/langgraph/graph-api#reducers)
- [A2A任务生命周期](https://a2a-protocol.org/latest/topics/life-of-a-task/)
- [Secret Collusion 原始论文](https://arxiv.org/abs/2402.07510)
- [多 Agent 研究系统](https://www.anthropic.com/research/multi-agent-research-system)

</details>

### 进阶 08 的来源

<details><summary>编码与界面操作的反馈闭环</summary>

- [SWE-agent 架构](https://swe-agent.com/latest/background/architecture/)
- [pytest fixtures 官方文档](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Browser use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [Computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)
- [Playwright Locators](https://playwright.dev/docs/locators)
- [Browser use 引用与错误处理](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool#handle-errors)
- [Playwright](https://playwright.dev/docs/actionability)
- [Computer use 安全考虑](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#security-considerations)

</details>

### 进阶 09 的来源

<details><summary>评测、归因与反馈</summary>

- [AI Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- [HumanEval 原论文](https://arxiv.org/abs/2107.03374)
- [MT-Bench 原研究](https://arxiv.org/abs/2306.05685)
- [《Practical Guide to Controlled Experiments on the Web》](https://exp-platform.com/practical-guide/)

</details>

### 进阶 10 的来源

<details><summary>性能、预算与推理服务</summary>

- [vLLM APC](https://docs.vllm.ai/en/stable/features/automatic_prefix_caching/)
- [Transformers 缓存机制](https://huggingface.co/docs/transformers/cache_explanation)
- [PagedAttention 原论文](https://arxiv.org/abs/2309.06180)
- [Orca（OSDI 2022）原论文](https://www.usenix.org/conference/osdi22/presentation/yu)
- [分块 prefill 文档](https://docs.vllm.ai/en/stable/configuration/optimization/#chunked-prefill)
- [vLLM 缓存设计](https://docs.vllm.ai/en/stable/design/prefix_caching/)
- [级联失败与队列管理](https://sre.google/sre-book/addressing-cascading-failures/)
- [过载处理](https://sre.google/sre-book/handling-overload/)
- [MIT 排队论讲义中的面积推导](https://ocw.mit.edu/courses/1-225j-transportation-flow-systems-fall-2002/55cc67c8b32d96052f72a4a7ead51393_lec8queues.pdf)
- [《The Tail at Scale》](https://research.google/pubs/the-tail-at-scale/)
- [Python monotonic](https://docs.python.org/3/library/time.html#time.monotonic)
- [asyncio loop.time](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.time)
- [NVIDIA NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard)

</details>

### 进阶 11 的来源

<details><summary>安全边界、授权与治理</summary>

- [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [RFC 8693 §2.1 与 §4](https://www.rfc-editor.org/rfc/rfc8693.html)
- [PostgreSQL 18 事务隔离](https://www.postgresql.org/docs/18/transaction-iso.html)
- [OWASP Prompt Injection 防护](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [Guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices)

</details>

### 进阶 12 的来源

<details><summary>Agent 优化与参数训练</summary>

- [DAgger 原论文（AISTATS 2011）](https://proceedings.mlr.press/v15/ross11a.html)
- [DPO 原论文](https://arxiv.org/abs/2305.18290)
- [策略梯度原论文](https://proceedings.neurips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html)
- [DeepSeekMath](https://arxiv.org/html/2402.03300v3)
- [TRL 的 Loss Types](https://huggingface.co/docs/trl/grpo_trainer#loss-types)
- [Thomas 与 Brunskill，ICML 2016 §2](https://proceedings.mlr.press/v48/thomasa16.html)
- [PPO 原论文](https://arxiv.org/abs/1707.06347)
- [原始论文](https://arxiv.org/abs/2508.03680)
- [v1.0 论文](https://arxiv.org/abs/2608.17528)
- [Agent Lightning v1.0 技术报告 v1 §3.2](https://arxiv.org/html/2608.17528v1#S3.SS2)
- [官方 README](https://raw.githubusercontent.com/microsoft/agent-lightning/main/README.md)
- [项目仓库](https://github.com/microsoft/agent-lightning)

</details>

### 进阶 13 的来源

<details><summary>模型 API 与输出合同</summary>

- [Claude 工具调用生命周期](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
- [WHATWG SSE 标准](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream)
- [Claude 流式事件](https://platform.claude.com/docs/en/build-with-claude/streaming)

</details>

### 进阶 14 的来源

<details><summary>知识摄取与索引发布</summary>

- [Python os.replace 与 fsync](https://docs.python.org/3/library/os.html#os.replace)
- [LightRAG 源码说明](https://github.com/HKUDS/LightRAG)

</details>

### 进阶 15 的来源

<details><summary>Text-to-SQL 与指标核验</summary>

- [PostgreSQL 17 SELECT 的处理说明](https://www.postgresql.org/docs/17/sql-select.html#SQL-SELECT-DESCRIPTION)
- [SQLite 聚合语义](https://www.sqlite.org/lang_aggfunc.html)
- [SQLite SELECT 的连接与 WHERE 说明](https://www.sqlite.org/lang_select.html#whereclause)
- [SQLite 表达式与 NULL](https://www.sqlite.org/lang_expr.html)
- [SQLite authorizer](https://www.sqlite.org/c3ref/set_authorizer.html)
- [进度回调](https://www.sqlite.org/c3ref/progress_handler.html)
- [SQLite query_only](https://www.sqlite.org/pragma.html#pragma_query_only)
- [Spider 2.0](https://github.com/xlang-ai/Spider2)
- [BIRD-Interact](https://github.com/bird-bench/BIRD-Interact)

</details>

### 进阶 16 的来源

<details><summary>Agent 任务服务与运维</summary>

- [RFC 9110 §15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-202-accepted)
- [http.server 不用于生产部署](https://docs.python.org/3.10/library/http.server.html)
- [SQLite事务文档](https://www.sqlite.org/lang_transaction.html)
- [PostgreSQL 17 SELECT 锁定说明](https://www.postgresql.org/docs/17/sql-select.html#SQL-FOR-UPDATE-SHARE)
- [Python SQLite接口](https://docs.python.org/3/library/sqlite3.html)

</details>

### 进阶 17 的来源

<details><summary>事件驱动与主动任务</summary>

- [SQLite事务](https://www.sqlite.org/lang_transaction.html)
- [Flink 1.20窗口与迟到](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/datastream/operators/windows/#allowed-lateness)
- [Cloudflare调度入口](https://developers.cloudflare.com/agents/api-reference/schedule-tasks/)
- [Transactional Outbox模式](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)

</details>

### 进阶 18 的来源

<details><summary>多模态证据与实时语音</summary>

- [PaddleOCR 3.0.3流水线示例](https://www.paddleocr.ai/v3.0.3/en/quick_start.html)
- [v1流式结果合同](https://docs.cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1#streamingrecognitionresult)
- [Python monotonic合同](https://docs.python.org/3/library/time.html#time.monotonic)
- [W3C Web Audio时间定义](https://www.w3.org/TR/webaudio/#dom-baseaudiocontext-currenttime)
- [WHATWG媒体时间](https://html.spec.whatwg.org/multipage/media.html#dom-media-currenttime)
- [LiveKit事件](https://docs.livekit.io/reference/agents/events/)
- [WHATWG媒体元素](https://html.spec.whatwg.org/multipage/media.html#media-elements)

</details>

[返回工程进阶](README.md) · [GitHub 与博客图谱](../research/advanced-landscape.md) · [来源元数据](../research/advanced-sources.json)
