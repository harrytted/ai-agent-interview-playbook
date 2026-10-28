# 56 题索引

由 `python3 scripts/check_repo.py --write-index` 生成。题号保持稳定，按模块阅读全文可看到来源核验记录。

| 题号 | 问题 | 模块 |
| --- | --- | --- |
| Q001 | [什么是 Agent，和普通 LLM 调用有何区别？](foundations/01-agent-and-llm.md#q001-什么是-agent和普通-llm-调用有何区别) | foundations |
| Q002 | [自回归语言模型到底在预测什么？](foundations/01-agent-and-llm.md#q002-自回归语言模型到底在预测什么) | foundations |
| Q003 | [Transformer 的 Attention 在做什么？](foundations/01-agent-and-llm.md#q003-transformer-的-attention-在做什么) | foundations |
| Q004 | [Prefill、Decode 与 KV Cache 为什么影响延迟？](foundations/01-agent-and-llm.md#q004-prefilldecode-与-kv-cache-为什么影响延迟) | foundations |
| Q005 | [预训练、SFT、偏好优化、LoRA 分别是什么？](foundations/01-agent-and-llm.md#q005-预训练sft偏好优化lora-分别是什么) | foundations |
| Q006 | [Prompt、RAG 与微调如何选？](foundations/01-agent-and-llm.md#q006-promptrag-与微调如何选) | foundations |
| Q007 | [为什么模型会给出流畅但错误的回答？](foundations/01-agent-and-llm.md#q007-为什么模型会给出流畅但错误的回答) | foundations |
| Q008 | [如何为 Agent 选择模型而不只看排行榜？](foundations/01-agent-and-llm.md#q008-如何为-agent-选择模型而不只看排行榜) | foundations |
| Q009 | [最小 Agent Loop 应包含哪些环节？](foundations/02-planning-and-orchestration.md#q009-最小-agent-loop-应包含哪些环节) | foundations |
| Q010 | [ReAct 与先规划后执行有何不同？](foundations/02-planning-and-orchestration.md#q010-react-与先规划后执行有何不同) | foundations |
| Q011 | [为什么用状态图组织 Agent？](foundations/02-planning-and-orchestration.md#q011-为什么用状态图组织-agent) | foundations |
| Q012 | [如何防止循环、反复重规划与无效重试？](foundations/02-planning-and-orchestration.md#q012-如何防止循环反复重规划与无效重试) | foundations |
| Q013 | [多个分支何时可以并发？](foundations/02-planning-and-orchestration.md#q013-多个分支何时可以并发) | foundations |
| Q014 | [Checkpoint 能保证恢复后不重复扣款吗？](foundations/02-planning-and-orchestration.md#q014-checkpoint-能保证恢复后不重复扣款吗) | foundations |
| Q015 | [什么时候值得使用多个 Agent？](foundations/02-planning-and-orchestration.md#q015-什么时候值得使用多个-agent) | foundations |
| Q016 | [多 Agent 如何交接，冲突如何处理？](foundations/02-planning-and-orchestration.md#q016-多-agent-如何交接冲突如何处理) | foundations |
| Q017 | [一个 RAG 系统的完整数据流是什么？](foundations/03-rag-and-search.md#q017-一个-rag-系统的完整数据流是什么) | foundations |
| Q018 | [Chunk 大小和重叠该怎样选择？](foundations/03-rag-and-search.md#q018-chunk-大小和重叠该怎样选择) | foundations |
| Q019 | [为什么向量检索和关键词检索可以互补？](foundations/03-rag-and-search.md#q019-为什么向量检索和关键词检索可以互补) | foundations |
| Q020 | [召回和 Rerank 为什么分两阶段？](foundations/03-rag-and-search.md#q020-召回和-rerank-为什么分两阶段) | foundations |
| Q021 | [向量索引如何兼顾延迟与检索质量？](foundations/03-rag-and-search.md#q021-向量索引如何兼顾延迟与检索质量) | foundations |
| Q022 | [ACL 应放在哪里？文档更新和删除如何传播？](foundations/03-rag-and-search.md#q022-acl-应放在哪里文档更新和删除如何传播) | foundations |
| Q023 | [RAG 如何评测，Recall@k、MRR 和答案质量有何区别？](foundations/03-rag-and-search.md#q023-rag-如何评测recallkmrr-和答案质量有何区别) | foundations |
| Q024 | [RAG 回答错误应该按什么顺序排查？](foundations/03-rag-and-search.md#q024-rag-回答错误应该按什么顺序排查) | foundations |
| Q025 | [Function Calling 的真正执行者是谁？](foundations/04-tools-memory-protocols.md#q025-function-calling-的真正执行者是谁) | foundations |
| Q026 | [怎样设计易用且可控的工具接口？](foundations/04-tools-memory-protocols.md#q026-怎样设计易用且可控的工具接口) | foundations |
| Q027 | [Schema 合法为什么仍然不够？](foundations/04-tools-memory-protocols.md#q027-schema-合法为什么仍然不够) | foundations |
| Q028 | [MCP 的 Host、Client、Server 分别负责什么？](foundations/04-tools-memory-protocols.md#q028-mcp-的-hostclientserver-分别负责什么) | foundations |
| Q029 | [MCP 是否自动解决鉴权和 Prompt Injection？](foundations/04-tools-memory-protocols.md#q029-mcp-是否自动解决鉴权和-prompt-injection) | foundations |
| Q030 | [Context、短期记忆和长期记忆如何区分？](foundations/04-tools-memory-protocols.md#q030-context短期记忆和长期记忆如何区分) | foundations |
| Q031 | [上下文太长时如何压缩而不丢任务？](foundations/04-tools-memory-protocols.md#q031-上下文太长时如何压缩而不丢任务) | foundations |
| Q032 | [长期记忆怎样避免污染与跨用户泄漏？](foundations/04-tools-memory-protocols.md#q032-长期记忆怎样避免污染与跨用户泄漏) | foundations |
| Q033 | [怎样判断一个 Agent 真正完成了任务？](engineering/05-evaluation-and-observability.md#q033-怎样判断一个-agent-真正完成了任务) | engineering |
| Q034 | [成功率的分母怎么定义，拒答算成功还是失败？](engineering/05-evaluation-and-observability.md#q034-成功率的分母怎么定义拒答算成功还是失败) | engineering |
| Q035 | [怎样构建评测集，避免越调越像“背答案”？](engineering/05-evaluation-and-observability.md#q035-怎样构建评测集避免越调越像背答案) | engineering |
| Q036 | [LLM-as-a-Judge 有哪些偏差，怎么用才可信？](engineering/05-evaluation-and-observability.md#q036-llm-as-a-judge-有哪些偏差怎么用才可信) | engineering |
| Q037 | [一条有用的 Agent trace 应记录什么？](engineering/05-evaluation-and-observability.md#q037-一条有用的-agent-trace-应记录什么) | engineering |
| Q038 | [怎样解释 p95 延迟，如何定位慢任务？](engineering/05-evaluation-and-observability.md#q038-怎样解释-p95-延迟如何定位慢任务) | engineering |
| Q039 | [怎样算 Agent 的成本，优化时看哪些指标？](engineering/05-evaluation-and-observability.md#q039-怎样算-agent-的成本优化时看哪些指标) | engineering |
| Q040 | [离线分数提升，为什么线上还可能变差？](engineering/05-evaluation-and-observability.md#q040-离线分数提升为什么线上还可能变差) | engineering |
| Q041 | [工具失败后应该怎样重试？](engineering/06-reliability-and-security.md#q041-工具失败后应该怎样重试) | engineering |
| Q042 | [什么是幂等，为什么“工具超时”不等于“工具没执行”？](engineering/06-reliability-and-security.md#q042-什么是幂等为什么工具超时不等于工具没执行) | engineering |
| Q043 | [人工审批应该放在哪里，审批后还能改参数吗？](engineering/06-reliability-and-security.md#q043-人工审批应该放在哪里审批后还能改参数吗) | engineering |
| Q044 | [怎么应对网页或文档中的 Prompt Injection？](engineering/06-reliability-and-security.md#q044-怎么应对网页或文档中的-prompt-injection) | engineering |
| Q045 | [工具沙箱、参数校验和 ACL 分别解决什么？](engineering/06-reliability-and-security.md#q045-工具沙箱参数校验和-acl-分别解决什么) | engineering |
| Q046 | [Checkpoint 能保证崩溃恢复后不重复执行工具吗？](engineering/06-reliability-and-security.md#q046-checkpoint-能保证崩溃恢复后不重复执行工具吗) | engineering |
| Q047 | [用户点了停止，怎样取消流式 Agent？](engineering/06-reliability-and-security.md#q047-用户点了停止怎样取消流式-agent) | engineering |
| Q048 | [如何防止 Agent 死循环与故障扩散？](engineering/06-reliability-and-security.md#q048-如何防止-agent-死循环与故障扩散) | engineering |
| Q049 | [设计一个企业知识库客服 Agent，你会怎样开始？](engineering/07-system-design-and-projects.md#q049-设计一个企业知识库客服-agent你会怎样开始) | engineering |
| Q050 | [设计一个可以引用来源的研究助手，怎么保证报告可信？](engineering/07-system-design-and-projects.md#q050-设计一个可以引用来源的研究助手怎么保证报告可信) | engineering |
| Q051 | [设计一个能创建、分派工单的 Agent，状态如何流转？](engineering/07-system-design-and-projects.md#q051-设计一个能创建分派工单的-agent状态如何流转) | engineering |
| Q052 | [面试官问“为什么选这个框架”，怎样回答？](engineering/07-system-design-and-projects.md#q052-面试官问为什么选这个框架怎样回答) | engineering |
| Q053 | [怎样向面试官讲清一个真实个人项目？](engineering/07-system-design-and-projects.md#q053-怎样向面试官讲清一个真实个人项目) | engineering |
| Q054 | [怎样解释指标提升，避免编造与夸大？](engineering/07-system-design-and-projects.md#q054-怎样解释指标提升避免编造与夸大) | engineering |
| Q055 | [Agent 项目怎样做测试，哪些该 mock？](engineering/07-system-design-and-projects.md#q055-agent-项目怎样做测试哪些该-mock) | engineering |
| Q056 | [线上突然回答变差，你会如何排查？](engineering/07-system-design-and-projects.md#q056-线上突然回答变差你会如何排查) | engineering |

[学习路线](00-roadmap.md) · [复习工具](../practice/README.md) · [仓库首页](../README.md)
