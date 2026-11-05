# 面试知识参考资料

按基础概念和工程主题整理的一手资料。

| 知识主题 | 参考来源 | 阅读要点 |
| --- | --- | --- |
| Agent 没有跨所有社区统一的唯一架构定义 | [Anthropic 架构讨论](https://www.anthropic.com/research/building-effective-agents) | Q001 声明本仓库采用的控制闭环定义；记忆、多 Agent 不是统一必要条件 |
| 工具调用意图与工具实际执行是不同阶段 | [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Q025–Q027；结构有效不等于获授权、业务正确或执行成功 |
| ReAct 交替组织推理与环境动作 | [ReAct 原论文](https://arxiv.org/abs/2210.03629) | Q010；结合环境反馈组织推理与动作。 |
| RAG 使用外部检索材料辅助生成 | [RAG 原论文](https://arxiv.org/abs/2005.11401) | Q006、Q017；对照检索增强生成的机制与证据使用。 |
| 两阶段检索先召回再对候选重排 | [Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) | Q020；候选之外的证据不会由重排自动补回 |
| 特定 ANN 实现中，过滤可能减少返回结果与召回 | [pgvector Filtering](https://github.com/pgvector/pgvector#filtering) | Q021；关注 pgvector 索引扫描与过滤行为。 |
| MCP 标准化能力交换，授权规范需按传输与版本适用 | [MCP 架构](https://modelcontextprotocol.io/docs/learn/architecture)、[2025-11-25 授权规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | Q028–Q029；HTTP 授权机制不能替代具体资源权限校验 |
| Checkpoint 可恢复状态，节点重执行仍可能重复副作用 | [LangGraph 重执行与幂等](https://docs.langchain.com/oss/python/langgraph/graph-api#re-execution-and-idempotency) | Q014、Q046；外部服务与本地状态不天然共享事务 |
| 超时不表示副作用未发生；重试会增加负载 | [AWS 重试经验](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Q041；必须声明“重试数”是否包含首次尝试，策略依错误类别选择 |
| 稳定业务意图 ID 可支持安全去重 | [AWS 幂等 API](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | Q042；依赖服务端合同、参数核对和一致性设计，单靠本地标记不够 |
| LLM Judge 可能出现位置、冗长与自我偏好等偏差 | [MT-Bench 原研究](https://arxiv.org/abs/2306.05685) | Q036；分数不是经校准的正确概率，需任务内人工校准 |
| 指标需预先声明样本集合、分母和拒答口径 | [本仓库指标练习](engineering/05-evaluation-and-observability.md)、[任务评测依据](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Q023、Q034、Q054；“未错误作答”不自动等于“正确拒答”，可能还有超时等终态 |
| Trace 用 span 与关联信息组织执行观测 | [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/) | Q037；自定义字段不是协议标准，日志不应无差别保存敏感正文 |
| 权限检查与工具执行边界应由可信程序落实 | [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)、[Prompt Injection 防御](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | Q022、Q044–Q045；权限、参数校验与注入防御。 |
| 应区分当前上下文、会话状态与跨会话记忆 | [LangChain 短期记忆](https://docs.langchain.com/oss/python/langchain/short-term-memory)、[长期记忆](https://docs.langchain.com/oss/python/langchain/long-term-memory) | Q030–Q032；存储中的内容需要被读取，应用记忆不等于模型参数更新 |
| 固定策略的离线循环只能演示其实际控制逻辑 | [本仓库实验边界](engineering/08-project-lab.md)、[项目表达与测试](engineering/07-system-design-and-projects.md) | 脚本策略、关键词检索、执行器合同与可扩展实现。 |
| 系统设计与项目实验 | [基础编排练习](foundations/02-planning-and-orchestration.md)、[系统设计练习](engineering/07-system-design-and-projects.md)、[7 天实验](engineering/08-project-lab.md) | 结合任务约束设计状态、容量、期限和验收条件。 |
| GitHub 项目统计与版本信息 | [调研口径](../research/github-survey.md)、[机器可读来源快照](../research/sources.json) | 页面 Star 快照、分支和来源元数据见调研报告。 |
| SFT 动作目标需与环境观察区分 | [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer)、[本手册小实验](../examples/advanced/training-objectives.md) | Q090；目标 mask 与标签预测位置对齐，观察仍作条件输入；assistant-only loss 需要模板支持，不把本例合同当成所有 SFT 默认行为。 |
| 概率比与正负优势共同决定裁剪，完整目标还需声明正则和均值单位 | [DeepSeekMath v3 §4.1](https://arxiv.org/html/2402.03300v3#S4.SS1)、[TRL Loss Types](https://huggingface.co/docs/trl/grpo_trainer#loss-types) | Q091；小策略使用已给定优势、一动作状态等权与精确二元 KL；一次目标下降不等于复现完整 GRPO，更不能证明真实 LLM 变好。 |
| Agent Lightning v1 的样本选择与一般保留建议是不同来源 | [技术报告 v1 §3.2](https://arxiv.org/html/2608.17528v1#S3.SS2)、[官方 README](https://raw.githubusercontent.com/microsoft/agent-lightning/main/README.md) | Q092；报告对同 rollout 相同 prompt 只留最后一个 `model_request`；本手册另提审计保留建议。旧版（legacy）的实际分支名是 `v0.x`。 |
| 配对版本比较需检查不一致对、区间与独立样本单位 | [statsmodels McNemar](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html)、[SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) | 评测进阶；exact 条件二项检验与相同索引配对重采样。教学手写夹具不是模型实测，percentile 不是优于 BCa 的结论。 |
| BM25、双编码检索与ANN分别有不同的误差来源 | [Lucene BM25](https://lucene.apache.org/core/10_5_2/core/org/apache/lucene/search/similarities/BM25Similarity.html)、[DPR](https://arxiv.org/abs/2004.04906)、[Faiss索引](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes) | Q019–Q021、Q072–Q074；表示、近似搜索、资格过滤和排序误差分开评价。 |
| 重排上限由固定候选中的相关证据数量约束 | [检索—重排](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)、[本手册实验](../examples/advanced/retrieval-mechanisms.md) | 没有新增读取或展开时，排序不能产生缺失候选；RR改善不代表必要证据齐全。 |
| 冲突裁决不能由相关性分数或转载数量推导 | [本手册冲突合同](../advanced/06-agentic-rag.md#知识冲突先确定身份与适用域再检查权威关系)、[可复算实现](../examples/advanced/retrieval_lab.py) | 先统一事实键、适用域和有效时间，再应用可信偏序；无裁决依据时保留分歧，属于明确的业务设计。 |
| Outbox原子保存发送意图，不保证外部消费者只见一次 | [Transactional outbox模式原作者说明](https://microservices.io/patterns/data/transactional-outbox.html) | 02、17；转发器在发送后、记确认前退出可能重发，消费端仍需幂等。不能把本地事务扩张成远端恰好一次执行。 |
| SQL的逻辑处理顺序和多重集语义决定统计含义 | [PostgreSQL 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) | 15；FROM/JOIN、WHERE、分组/聚合、HAVING与投影等有语义区别；默认保留重复，物理优化可改执行计划但不能任意改结果。 |
| 吞吐保护需要观察资源需求，重试也会增加负载 | [Google SRE过载处理](https://sre.google/sre-book/handling-overload/) | 10、16；请求成本不同，固定QPS不等于固定资源占用；容量模型要声明假设，排队和接收策略另按实际负载验证。 |
| DPO在固定参考策略下比较偏好响应的相对log概率 | [DPO原论文§4](https://arxiv.org/html/2305.18290v2#S4) | 12；原始目标对响应动作token的log概率求和，参考策略与采样旧策略职责不同；手算二元策略不代表真实语言模型训练。 |
| 原始LLaVA以视觉编码器和投影连接语言模型 | [Visual Instruction Tuning v2 §4.1](https://arxiv.org/html/2304.08485v2#S4.SS1) | 18；矩阵形状按特征行约定解释，连接后的视觉表示不是已核实事实，也不能推广为所有VLM的架构。 |
| HTTP 202不自带持久接收或最终执行保证 | [RFC 9110 §15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-202-accepted)、[本地服务接收实现](../examples/service_lab/service.py) | 16；本服务先提交接收账本再返回202，这是实现合同；状态码本身不证明执行已完成或必然发生。 |
| 单调时钟计量本机经过时间，原始读数不构成可移植截止时刻 | [Python monotonic](https://docs.python.org/3/library/time.html#time.monotonic)、[asyncio loop.time](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.time) | 基础10、进阶10、Q048；日期时间与耗时分开，重试沿用余额。跨机器/系统重启的截止或累计耗时恢复需另定持久合同，不从本机计时接口推导全局期限保证。 |

新增训练与配对统计条目的实现文档、README 于 2026-11-05 核对，仍是可变入口；方法论文分别固定为 DeepSeekMath v3 与 Agent Lightning v1.0 技术报告 v1。规范支持版本行为，原论文支持方法，代码实验支持本例计算；这些证据不替代真实任务效果或读者学习效果的验证。

[仓库首页](../README.md) · [GitHub 调研](../research/github-survey.md)
