# 92 题索引

先找到问题，再回到机制。短答用于口述，详细答案用于理解，追问与案例用于检查能否迁移。

[基础课程](../learning/README.md) · [进阶课程](../advanced/README.md) · [36 道进阶题与章节对照](advanced/README.md)

## 基础原理：Q001–Q032

| 题号 | 问题 | 学习入口 |
| --- | --- | --- |
| Q001 | [什么是 Agent，和普通 LLM 调用有何区别？](foundations/01-agent-and-llm.md#q001-什么是-agent和普通-llm-调用有何区别) | [基础课程](../learning/README.md) |
| Q002 | [自回归语言模型到底在预测什么？](foundations/01-agent-and-llm.md#q002-自回归语言模型到底在预测什么) | [基础课程](../learning/README.md) |
| Q003 | [Transformer 的 Attention 在做什么？](foundations/01-agent-and-llm.md#q003-transformer-的-attention-在做什么) | [基础课程](../learning/README.md) |
| Q004 | [Prefill、Decode 与 KV Cache 为什么影响延迟？](foundations/01-agent-and-llm.md#q004-prefilldecode-与-kv-cache-为什么影响延迟) | [基础课程](../learning/README.md) |
| Q005 | [预训练、SFT、偏好优化、LoRA 分别是什么？](foundations/01-agent-and-llm.md#q005-预训练sft偏好优化lora-分别是什么) | [基础课程](../learning/README.md) |
| Q006 | [Prompt、RAG 与微调如何选？](foundations/01-agent-and-llm.md#q006-promptrag-与微调如何选) | [基础课程](../learning/README.md) |
| Q007 | [为什么模型会给出流畅但错误的回答？](foundations/01-agent-and-llm.md#q007-为什么模型会给出流畅但错误的回答) | [基础课程](../learning/README.md) |
| Q008 | [如何为 Agent 选择模型而不只看排行榜？](foundations/01-agent-and-llm.md#q008-如何为-agent-选择模型而不只看排行榜) | [基础课程](../learning/README.md) |
| Q009 | [最小 Agent Loop 应包含哪些环节？](foundations/02-planning-and-orchestration.md#q009-最小-agent-loop-应包含哪些环节) | [基础课程](../learning/README.md) |
| Q010 | [ReAct 与先规划后执行有何不同？](foundations/02-planning-and-orchestration.md#q010-react-与先规划后执行有何不同) | [基础课程](../learning/README.md) |
| Q011 | [为什么用状态图组织 Agent？](foundations/02-planning-and-orchestration.md#q011-为什么用状态图组织-agent) | [基础课程](../learning/README.md) |
| Q012 | [如何防止循环、反复重规划与无效重试？](foundations/02-planning-and-orchestration.md#q012-如何防止循环反复重规划与无效重试) | [基础课程](../learning/README.md) |
| Q013 | [多个分支何时可以并发？](foundations/02-planning-and-orchestration.md#q013-多个分支何时可以并发) | [基础课程](../learning/README.md) |
| Q014 | [Checkpoint 能保证恢复后不重复扣款吗？](foundations/02-planning-and-orchestration.md#q014-checkpoint-能保证恢复后不重复扣款吗) | [基础课程](../learning/README.md) |
| Q015 | [什么时候值得使用多个 Agent？](foundations/02-planning-and-orchestration.md#q015-什么时候值得使用多个-agent) | [基础课程](../learning/README.md) |
| Q016 | [多 Agent 如何交接，冲突如何处理？](foundations/02-planning-and-orchestration.md#q016-多-agent-如何交接冲突如何处理) | [基础课程](../learning/README.md) |
| Q017 | [一个 RAG 系统的完整数据流是什么？](foundations/03-rag-and-search.md#q017-一个-rag-系统的完整数据流是什么) | [基础课程](../learning/README.md) |
| Q018 | [Chunk 大小和重叠该怎样选择？](foundations/03-rag-and-search.md#q018-chunk-大小和重叠该怎样选择) | [基础课程](../learning/README.md) |
| Q019 | [为什么向量检索和关键词检索可以互补？](foundations/03-rag-and-search.md#q019-为什么向量检索和关键词检索可以互补) | [基础课程](../learning/README.md) |
| Q020 | [召回和 Rerank 为什么分两阶段？](foundations/03-rag-and-search.md#q020-召回和-rerank-为什么分两阶段) | [基础课程](../learning/README.md) |
| Q021 | [向量索引如何兼顾延迟与检索质量？](foundations/03-rag-and-search.md#q021-向量索引如何兼顾延迟与检索质量) | [基础课程](../learning/README.md) |
| Q022 | [ACL 应放在哪里？文档更新和删除如何传播？](foundations/03-rag-and-search.md#q022-acl-应放在哪里文档更新和删除如何传播) | [基础课程](../learning/README.md) |
| Q023 | [RAG 如何评测，Recall@k、MRR 和答案质量有何区别？](foundations/03-rag-and-search.md#q023-rag-如何评测recallkmrr-和答案质量有何区别) | [基础课程](../learning/README.md) |
| Q024 | [RAG 回答错误应该按什么顺序排查？](foundations/03-rag-and-search.md#q024-rag-回答错误应该按什么顺序排查) | [基础课程](../learning/README.md) |
| Q025 | [Function Calling 的真正执行者是谁？](foundations/04-tools-memory-protocols.md#q025-function-calling-的真正执行者是谁) | [基础课程](../learning/README.md) |
| Q026 | [怎样设计易用且可控的工具接口？](foundations/04-tools-memory-protocols.md#q026-怎样设计易用且可控的工具接口) | [基础课程](../learning/README.md) |
| Q027 | [Schema 合法为什么仍然不够？](foundations/04-tools-memory-protocols.md#q027-schema-合法为什么仍然不够) | [基础课程](../learning/README.md) |
| Q028 | [MCP 的 Host、Client、Server 分别负责什么？](foundations/04-tools-memory-protocols.md#q028-mcp-的-hostclientserver-分别负责什么) | [基础课程](../learning/README.md) |
| Q029 | [MCP 是否自动解决鉴权和 Prompt Injection？](foundations/04-tools-memory-protocols.md#q029-mcp-是否自动解决鉴权和-prompt-injection) | [基础课程](../learning/README.md) |
| Q030 | [Context、短期记忆和长期记忆如何区分？](foundations/04-tools-memory-protocols.md#q030-context短期记忆和长期记忆如何区分) | [基础课程](../learning/README.md) |
| Q031 | [上下文太长时如何压缩而不丢任务？](foundations/04-tools-memory-protocols.md#q031-上下文太长时如何压缩而不丢任务) | [基础课程](../learning/README.md) |
| Q032 | [长期记忆怎样避免污染与跨用户泄漏？](foundations/04-tools-memory-protocols.md#q032-长期记忆怎样避免污染与跨用户泄漏) | [基础课程](../learning/README.md) |

## 工程与项目：Q033–Q056

| 题号 | 问题 | 学习入口 |
| --- | --- | --- |
| Q033 | [怎样判断一个 Agent 真正完成了任务？](engineering/05-evaluation-and-observability.md#q033-怎样判断一个-agent-真正完成了任务) | [工程学习路线](00-roadmap.md) |
| Q034 | [成功率的分母怎么定义，拒答算成功还是失败？](engineering/05-evaluation-and-observability.md#q034-成功率的分母怎么定义拒答算成功还是失败) | [工程学习路线](00-roadmap.md) |
| Q035 | [怎样构建评测集，避免越调越像“背答案”？](engineering/05-evaluation-and-observability.md#q035-怎样构建评测集避免越调越像背答案) | [工程学习路线](00-roadmap.md) |
| Q036 | [LLM-as-a-Judge 有哪些偏差，怎么用才可信？](engineering/05-evaluation-and-observability.md#q036-llm-as-a-judge-有哪些偏差怎么用才可信) | [工程学习路线](00-roadmap.md) |
| Q037 | [一条有用的 Agent trace 应记录什么？](engineering/05-evaluation-and-observability.md#q037-一条有用的-agent-trace-应记录什么) | [工程学习路线](00-roadmap.md) |
| Q038 | [怎样解释 p95 延迟，如何定位慢任务？](engineering/05-evaluation-and-observability.md#q038-怎样解释-p95-延迟如何定位慢任务) | [工程学习路线](00-roadmap.md) |
| Q039 | [怎样算 Agent 的成本，优化时看哪些指标？](engineering/05-evaluation-and-observability.md#q039-怎样算-agent-的成本优化时看哪些指标) | [工程学习路线](00-roadmap.md) |
| Q040 | [离线分数提升，为什么线上还可能变差？](engineering/05-evaluation-and-observability.md#q040-离线分数提升为什么线上还可能变差) | [工程学习路线](00-roadmap.md) |
| Q041 | [工具失败后应该怎样重试？](engineering/06-reliability-and-security.md#q041-工具失败后应该怎样重试) | [工程学习路线](00-roadmap.md) |
| Q042 | [什么是幂等，为什么“工具超时”不等于“工具没执行”？](engineering/06-reliability-and-security.md#q042-什么是幂等为什么工具超时不等于工具没执行) | [工程学习路线](00-roadmap.md) |
| Q043 | [人工审批应该放在哪里，审批后还能改参数吗？](engineering/06-reliability-and-security.md#q043-人工审批应该放在哪里审批后还能改参数吗) | [工程学习路线](00-roadmap.md) |
| Q044 | [怎么应对网页或文档中的 Prompt Injection？](engineering/06-reliability-and-security.md#q044-怎么应对网页或文档中的-prompt-injection) | [工程学习路线](00-roadmap.md) |
| Q045 | [工具沙箱、参数校验和 ACL 分别解决什么？](engineering/06-reliability-and-security.md#q045-工具沙箱参数校验和-acl-分别解决什么) | [工程学习路线](00-roadmap.md) |
| Q046 | [Checkpoint 能保证崩溃恢复后不重复执行工具吗？](engineering/06-reliability-and-security.md#q046-checkpoint-能保证崩溃恢复后不重复执行工具吗) | [工程学习路线](00-roadmap.md) |
| Q047 | [用户点了停止，怎样取消流式 Agent？](engineering/06-reliability-and-security.md#q047-用户点了停止怎样取消流式-agent) | [工程学习路线](00-roadmap.md) |
| Q048 | [如何防止 Agent 死循环与故障扩散？](engineering/06-reliability-and-security.md#q048-如何防止-agent-死循环与故障扩散) | [工程学习路线](00-roadmap.md) |
| Q049 | [设计一个企业知识库客服 Agent，你会怎样开始？](engineering/07-system-design-and-projects.md#q049-设计一个企业知识库客服-agent你会怎样开始) | [工程学习路线](00-roadmap.md) |
| Q050 | [设计一个可以引用来源的研究助手，怎么保证报告可信？](engineering/07-system-design-and-projects.md#q050-设计一个可以引用来源的研究助手怎么保证报告可信) | [工程学习路线](00-roadmap.md) |
| Q051 | [设计一个能创建、分派工单的 Agent，状态如何流转？](engineering/07-system-design-and-projects.md#q051-设计一个能创建分派工单的-agent状态如何流转) | [工程学习路线](00-roadmap.md) |
| Q052 | [面试官问“为什么选这个框架”，怎样回答？](engineering/07-system-design-and-projects.md#q052-面试官问为什么选这个框架怎样回答) | [工程学习路线](00-roadmap.md) |
| Q053 | [怎样向面试官讲清一个真实个人项目？](engineering/07-system-design-and-projects.md#q053-怎样向面试官讲清一个真实个人项目) | [工程学习路线](00-roadmap.md) |
| Q054 | [怎样解释指标提升，避免编造与夸大？](engineering/07-system-design-and-projects.md#q054-怎样解释指标提升避免编造与夸大) | [工程学习路线](00-roadmap.md) |
| Q055 | [Agent 项目怎样做测试，哪些该 mock？](engineering/07-system-design-and-projects.md#q055-agent-项目怎样做测试哪些该-mock) | [工程学习路线](00-roadmap.md) |
| Q056 | [线上突然回答变差，你会如何排查？](engineering/07-system-design-and-projects.md#q056-线上突然回答变差你会如何排查) | [工程学习路线](00-roadmap.md) |

## 进阶系统：Q057–Q092

| 题号 | 问题 | 学习入口 |
| --- | --- | --- |
| Q057 | [Harness 与模型、Agent 框架分别承担什么职责？](advanced/01-harness-and-deep-agents.md#q057-harness-与模型agent-框架分别承担什么职责) | [01 章](../advanced/01-harness-and-deep-agents.md) |
| Q058 | [怎样区分文件 Backend、执行 Sandbox 与持久化状态？](advanced/01-harness-and-deep-agents.md#q058-怎样区分文件-backend执行-sandbox-与持久化状态) | [01 章](../advanced/01-harness-and-deep-agents.md) |
| Q059 | [长任务跨会话交接应该保存什么？](advanced/01-harness-and-deep-agents.md#q059-长任务跨会话交接应该保存什么) | [01 章](../advanced/01-harness-and-deep-agents.md) |
| Q060 | [持久执行为什么仍需要外部幂等？](advanced/02-durable-execution.md#q060-持久执行为什么仍需要外部幂等) | [02 章](../advanced/02-durable-execution.md) |
| Q061 | [怎样让审批与 Outbox 在恢复后仍保持正确含义？](advanced/02-durable-execution.md#q061-怎样让审批与-outbox-在恢复后仍保持正确含义) | [02 章](../advanced/02-durable-execution.md) |
| Q062 | [租约、Fencing 与取消分别保护什么？](advanced/02-durable-execution.md#q062-租约fencing-与取消分别保护什么) | [02 章](../advanced/02-durable-execution.md) |
| Q063 | [上下文选择、外置与摘要应该怎样配合？](advanced/03-context-engineering.md#q063-上下文选择外置与摘要应该怎样配合) | [03 章](../advanced/03-context-engineering.md) |
| Q064 | [怎样区分 KV、前缀、检索与最终答案缓存？](advanced/03-context-engineering.md#q064-怎样区分-kv前缀检索与最终答案缓存) | [03 章](../advanced/03-context-engineering.md) |
| Q065 | [长任务怎样分配上下文预算并传播证据失效？](advanced/03-context-engineering.md#q065-长任务怎样分配上下文预算并传播证据失效) | [03 章](../advanced/03-context-engineering.md) |
| Q066 | [长期事实为什么需要实体解析与两条时间轴？](advanced/04-memory-and-skills.md#q066-长期事实为什么需要实体解析与两条时间轴) | [04 章](../advanced/04-memory-and-skills.md) |
| Q067 | [反思经验怎样写入记忆而不制造新错误？](advanced/04-memory-and-skills.md#q067-反思经验怎样写入记忆而不制造新错误) | [04 章](../advanced/04-memory-and-skills.md) |
| Q068 | [Skills 怎样渐进加载并安全升级？](advanced/04-memory-and-skills.md#q068-skills-怎样渐进加载并安全升级) | [04 章](../advanced/04-memory-and-skills.md) |
| Q069 | [大工具目录怎样做到发现、加载与执行一致？](advanced/05-tool-routing-and-mcp.md#q069-大工具目录怎样做到发现加载与执行一致) | [05 章](../advanced/05-tool-routing-and-mcp.md) |
| Q070 | [程序化工具调用怎样节省上下文并保持调用边界？](advanced/05-tool-routing-and-mcp.md#q070-程序化工具调用怎样节省上下文并保持调用边界) | [05 章](../advanced/05-tool-routing-and-mcp.md) |
| Q071 | [MCP 授权、业务 ACL 与 A2A 任务合同怎样区分？](advanced/05-tool-routing-and-mcp.md#q071-mcp-授权业务-acl-与-a2a-任务合同怎样区分) | [05 章](../advanced/05-tool-routing-and-mcp.md) |
| Q072 | [Agentic RAG 怎样围绕证据依赖选择检索路径？](advanced/06-agentic-rag.md#q072-agentic-rag-怎样围绕证据依赖选择检索路径) | [06 章](../advanced/06-agentic-rag.md) |
| Q073 | [GraphRAG 的局部与全局查询怎样选择和维护？](advanced/06-agentic-rag.md#q073-graphrag-的局部与全局查询怎样选择和维护) | [06 章](../advanced/06-agentic-rag.md) |
| Q074 | [研究助手怎样反向核验证据并决定停止？](advanced/06-agentic-rag.md#q074-研究助手怎样反向核验证据并决定停止) | [06 章](../advanced/06-agentic-rag.md) |
| Q075 | [什么时候采用 Manager，什么时候采用 handoff？](advanced/07-multi-agent-systems.md#q075-什么时候采用-manager什么时候采用-handoff) | [07 章](../advanced/07-multi-agent-systems.md) |
| Q076 | [动态任务图怎样处理共享状态、冲突与迟到结果？](advanced/07-multi-agent-systems.md#q076-动态任务图怎样处理共享状态冲突与迟到结果) | [07 章](../advanced/07-multi-agent-systems.md) |
| Q077 | [多 Agent 怎样在失败、取消和高成本时收敛？](advanced/07-multi-agent-systems.md#q077-多-agent-怎样在失败取消和高成本时收敛) | [07 章](../advanced/07-multi-agent-systems.md) |
| Q078 | [Coding Agent 怎样形成可复现、可验收的修复闭环？](advanced/08-coding-and-computer-use.md#q078-coding-agent-怎样形成可复现可验收的修复闭环) | [08 章](../advanced/08-coding-and-computer-use.md) |
| Q079 | [文件系统 Backend、路径白名单和沙箱分别保护什么？](advanced/08-coding-and-computer-use.md#q079-文件系统-backend路径白名单和沙箱分别保护什么) | [08 章](../advanced/08-coding-and-computer-use.md) |
| Q080 | [Browser / Computer Use 怎样保持观察新鲜并确认任务完成？](advanced/08-coding-and-computer-use.md#q080-browser--computer-use-怎样保持观察新鲜并确认任务完成) | [08 章](../advanced/08-coding-and-computer-use.md) |
| Q081 | [pass@k 提升是否意味着 Agent 更可靠？怎样正确计算？](advanced/09-evaluation-and-feedback.md#q081-passk-提升是否意味着-agent-更可靠怎样正确计算) | [09 章](../advanced/09-evaluation-and-feedback.md) |
| Q082 | [怎样校准 LLM-as-a-Judge，避免总体高分掩盖关键错误？](advanced/09-evaluation-and-feedback.md#q082-怎样校准-llm-as-a-judge避免总体高分掩盖关键错误) | [09 章](../advanced/09-evaluation-and-feedback.md) |
| Q083 | [怎样证明一次 Agent 改进来自策略，而不是任务、预算或数据泄漏？](advanced/09-evaluation-and-feedback.md#q083-怎样证明一次-agent-改进来自策略而不是任务预算或数据泄漏) | [09 章](../advanced/09-evaluation-and-feedback.md) |
| Q084 | [怎样定位 Agent 的延迟瓶颈，为什么加 Worker 未必更快？](advanced/10-performance-and-serving.md#q084-怎样定位-agent-的延迟瓶颈为什么加-worker-未必更快) | [10 章](../advanced/10-performance-and-serving.md) |
| Q085 | [KV / 前缀缓存与检索、工具、答案缓存有什么区别？](advanced/10-performance-and-serving.md#q085-kv--前缀缓存与检索工具答案缓存有什么区别) | [10 章](../advanced/10-performance-and-serving.md) |
| Q086 | [多分支 Agent 怎样控制共享预算，并设计模型升级与降级？](advanced/10-performance-and-serving.md#q086-多分支-agent-怎样控制共享预算并设计模型升级与降级) | [10 章](../advanced/10-performance-and-serving.md) |
| Q087 | [认证、资源授权、动作批准与执行隔离为什么不能合并？](advanced/11-security-and-governance.md#q087-认证资源授权动作批准与执行隔离为什么不能合并) | [11 章](../advanced/11-security-and-governance.md) |
| Q088 | [提示注入怎样穿过检索、记忆与 MCP，应该在哪里阻断？](advanced/11-security-and-governance.md#q088-提示注入怎样穿过检索记忆与-mcp应该在哪里阻断) | [11 章](../advanced/11-security-and-governance.md) |
| Q089 | [人工审批怎样与参数、恢复、撤销和审计绑定？](advanced/11-security-and-governance.md#q089-人工审批怎样与参数恢复撤销和审计绑定) | [11 章](../advanced/11-security-and-governance.md) |
| Q090 | [Agent 出错时，怎样选择改运行时、SFT、DPO 或 Agent RL？](advanced/12-agent-training.md#q090-agent-出错时怎样选择改运行时sftdpo-或-agent-rl) | [12 章](../advanced/12-agent-training.md) |
| Q091 | [GRPO 的组内相对奖励怎样计算，为什么标准化不等于完整训练？](advanced/12-agent-training.md#q091-grpo-的组内相对奖励怎样计算为什么标准化不等于完整训练) | [12 章](../advanced/12-agent-training.md) |
| Q092 | [Harnessed Agent RL 怎样组织训练数据，如何理解 Agent Lightning 的版本？](advanced/12-agent-training.md#q092-harnessed-agent-rl-怎样组织训练数据如何理解-agent-lightning-的版本) | [12 章](../advanced/12-agent-training.md) |


[学习路线](00-roadmap.md) · [复习工具](../practice/README.md) · [仓库首页](../README.md)
