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

[仓库首页](../README.md) · [GitHub 调研](../research/github-survey.md)
