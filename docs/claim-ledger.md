# 事实与教学核验台账

核验日期：2026-10-28（Asia/Shanghai）。范围：基础 Q001–Q032、工程 Q033–Q056、7 天实验安排与 GitHub 调研的主要主张。此台账检查关键事实和表达边界，不代表对外部仓库全部答案、代码或生产安全性完成审计。

状态约定：`verified` 为一手资料支持该有限主张；`design-advice` 为本仓库建议；`teaching-simplification` 为有明确假设的教学模型；`unresolved` 为证据尚不足。设计建议的来源是依据，不是建议收益的实测证明。

| Claim | 一手来源或核验依据 | Status | 边界 |
|---|---|---|---|
| Agent 没有跨所有社区统一的唯一架构定义 | [Anthropic 架构讨论](https://www.anthropic.com/research/building-effective-agents) | verified | Q001 声明本仓库采用的控制闭环定义；记忆、多 Agent 不是统一必要条件 |
| 工具调用意图与工具实际执行是不同阶段 | [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | verified | Q025–Q027；结构有效不等于获授权、业务正确或执行成功 |
| ReAct 交替组织推理与环境动作 | [ReAct 原论文](https://arxiv.org/abs/2210.03629) | verified | Q010；原文任务效果不外推，调试不以公开隐藏思维为前提 |
| RAG 使用外部检索材料辅助生成 | [RAG 原论文](https://arxiv.org/abs/2005.11401) | verified | Q006、Q017；这是机制说明，不提供“必然正确”的保证 |
| 两阶段检索先召回再对候选重排 | [Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) | verified | Q020；候选之外的证据不会由重排自动补回 |
| 特定 ANN 实现中，过滤可能减少返回结果与召回 | [pgvector Filtering](https://github.com/pgvector/pgvector#filtering) | verified | Q021；这里核验的是 pgvector 行为，不推广为所有向量库实现 |
| MCP 标准化能力交换，授权规范需按传输与版本适用 | [MCP 架构](https://modelcontextprotocol.io/docs/learn/architecture)、[2025-11-25 授权规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | verified | Q028–Q029；HTTP 授权机制不能替代具体资源权限校验 |
| Checkpoint 可恢复状态，节点重执行仍可能重复副作用 | [LangGraph 重执行与幂等](https://docs.langchain.com/oss/python/langgraph/graph-api#re-execution-and-idempotency) | verified | Q014、Q046；外部服务与本地状态不天然共享事务 |
| 超时不表示副作用未发生；重试会增加负载 | [AWS 重试经验](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | verified | Q041；必须声明“重试数”是否包含首次尝试，策略依错误类别选择 |
| 稳定业务意图 ID 可支持安全去重 | [AWS 幂等 API](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | verified | Q042；依赖服务端合同、参数核对和一致性设计，单靠本地标记不够 |
| LLM Judge 可能出现位置、冗长与自我偏好等偏差 | [MT-Bench 原研究](https://arxiv.org/abs/2306.05685) | verified | Q036；分数不是经校准的正确概率，需任务内人工校准 |
| 指标需预先声明样本集合、分母和拒答口径 | [本仓库指标练习](engineering/05-evaluation-and-observability.md)、[任务评测依据](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | design-advice | Q023、Q034、Q054；“未错误作答”不自动等于“正确拒答”，可能还有超时等终态 |
| Trace 用 span 与关联信息组织执行观测 | [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/) | verified | Q037；自定义字段不是协议标准，日志不应无差别保存敏感正文 |
| 权限检查与工具执行边界应由可信程序落实 | [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)、[Prompt Injection 防御](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | design-advice | Q022、Q044–Q045；不是承诺可以完全消除注入风险 |
| 应区分当前上下文、会话状态与跨会话记忆 | [LangChain 短期记忆](https://docs.langchain.com/oss/python/langchain/short-term-memory)、[长期记忆](https://docs.langchain.com/oss/python/langchain/long-term-memory) | verified | Q030–Q032；存储中的内容需要被读取，应用记忆不等于模型参数更新 |
| 固定策略的离线循环只能演示其实际控制逻辑 | [本仓库实验边界](engineering/08-project-lab.md)、[项目表达与测试](engineering/07-system-design-and-projects.md) | teaching-simplification | 不证明真实 LLM 的规划、工具选择、检索或理解能力；任务清单不等于已实现代码 |
| 状态机、容量、期限、优先级和学习天数是学习设计 | [基础编排练习](foundations/02-planning-and-orchestration.md)、[系统设计练习](engineering/07-system-design-and-projects.md)、[7 天实验](engineering/08-project-lab.md) | teaching-simplification | 所有目标值应通过本人实验验证，不能写成公司履历或行业标准 |
| 外部项目实时热度、不可变版本与完整正确性未全部确认 | [调研口径](../research/github-survey.md)、[机器可读来源快照](../research/sources.json) | unresolved | Star 为页面快照；未取得全部 SHA，也未运行外部完整项目，不能比较实时增长或认证成熟度 |

## 检查结论

- 56 个问题 ID 连续且唯一；基础及工程题包含回答、追问、误区与主动回忆练习。
- 发现的比例与成本算例可按给定分母复算；教学容量及性能目标已有假设标识。
- 未发现把他人案例写成本人经历，或把教学指标写成已发生的生产成绩。
- 没有验证真实模型能力、外部项目运行兼容性与线上效果；这些结论需要后续实际实验。

复习入口：[仓库首页](../README.md) · [GitHub 调研](../research/github-survey.md)
