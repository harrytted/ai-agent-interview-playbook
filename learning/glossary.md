# 术语回查

这些是本课程采用的简明工作定义；完整机制、边界和一手来源见对应章节。术语在不同框架中可能另有细分，不据此推断某个 SDK 的接口行为。

想查中英术语，或看看概念之间怎样连接，可以打开作者的 [AI 编程字典](https://agent.harrylab.cn/dictionary/)。查完一个词，再回到下表对应的学习章，把它放进实际执行过程里理解。

| 术语 | 在本课程里指什么 | 关键边界 | 阅读 |
| --- | --- | --- | --- |
| LLM（大语言模型） | 处理上下文、生成输出的语言模型 | 生成文字不等于外部动作已执行 | [01](01-system-map.md) |
| Runtime / Harness | 驱动模型、状态与工具执行的程序 | 必须自己落实控制边界 | [01](01-system-map.md) |
| Agent（智能体） | 按声明的定义，能依观察动态选择动作的系统 | 没有跨社区统一的唯一组件清单 | [01](01-system-map.md) |
| Workflow（工作流） | 主要控制路径预先定义的执行流程 | 可以包含模型调用与条件分支 | [01](01-system-map.md) |
| API（应用程序接口） | 程序向另一个程序提供的调用入口与约定 | 接口存在不代表当前用户有权调用 | [01](01-system-map.md) |
| JSON | 用文本表达对象、列表等结构化数据的格式 | 解析成功不证明字段内容真实 | [01](01-system-map.md) |
| HTTP（超文本传输协议） | 客户端与服务端交换请求、响应的协议 | 没收到响应不能推出服务端没有执行 | [01](01-system-map.md) |
| Token（词元） | 由相应编码规则处理的模型输入/输出单位 | 不是固定一个字或单词 | [02](02-llm-primer.md) |
| 自回归 | 依前缀逐步生成后续 token | 概率高不等于事实真 | [02](02-llm-primer.md) |
| Attention（注意力） | 用查询与键的匹配权重混合值表示 | 权重不是事实可信度 | [02](02-llm-primer.md) |
| Prefill / Decode（输入预填充 / 解码生成） | 处理已有输入 / 逐步生成输出的阶段 | 性能还受服务实现与排队等影响 | [02](02-llm-primer.md) |
| KV Cache（键值缓存） | 可复用的历史 Key/Value 中间表示 | 不等于持久记忆或参数学习 | [02](02-llm-primer.md) |
| Embedding（嵌入表示） | 将内容映射为数值表示 | 维度相同不保证语义空间兼容 | [06](06-rag-and-retrieval.md) |
| SFT（监督微调） | 以示范数据调整模型行为的微调 | 数据质量与泛化仍需验证 | [02](02-llm-primer.md) |
| LoRA（低秩适配） | 用低秩增量进行参数高效适配的一种方法 | 与 SFT 不在同一分类维度 | [02](02-llm-primer.md) |
| Prompt（提示） | 本课程中狭指指令与示例 | 广义用法可能包含完整模型输入 | [03](03-context-and-prompts.md) |
| Context（上下文） | 一次调用中实际可见的信息 | 存在数据库中不等于已进入输入 | [03](03-context-and-prompts.md) |
| Tool Call（工具调用） | 调用工具的意图与参数 | Schema 合格不等于获授权 | [05](05-tools-and-mcp.md) |
| Function Calling（函数调用） | 模型以结构化形式提出调用工具的请求 | 实际动作仍由执行器完成 | [05](05-tools-and-mcp.md) |
| Schema（结构约束） | 数据结构、字段与类型等合同 | 不证明字段内容真实或合规 | [05](05-tools-and-mcp.md) |
| MCP（模型上下文协议） | 连接应用与能力提供方的标准协议 | 不自动实现业务资源授权 | [05](05-tools-and-mcp.md) |
| A2A | Agent 之间协作的协议体系 | 与 MCP 有不同侧重，可组合 | [05](05-tools-and-mcp.md) |
| RAG（检索增强生成） | 生成时使用检索到的外部证据 | 不保证正确，也不强制使用向量库 | [06](06-rag-and-retrieval.md) |
| Chunk（分块） | 按一定策略切分出的检索单位 | 要保留来源、版本与上下文关系 | [06](06-rag-and-retrieval.md) |
| Sparse / Dense Retrieval | 稀疏词项表示 / 稠密向量表示的检索 | 对精确编号与语义改写的表现需实测 | [06](06-rag-and-retrieval.md) |
| RRF | 按多份排名的倒数位置融合候选 | 不直接把不同检索器分数相加 | [06](06-rag-and-retrieval.md) |
| Rerank（重排） | 对已经召回的候选重新排序 | 不能凭空补回候选外的证据 | [06](06-rag-and-retrieval.md) |
| State（状态） | 当前任务的可维护进度与观察 | 未持久化的状态可能随进程丢失 | [07](07-memory-and-state.md) |
| Memory（记忆） | 保留后续可取用信息的应用机制 | 保存、检索、读入是不同步骤 | [07](07-memory-and-state.md) |
| TTL（生存时间） | 记录的保存或再确认期限 | 期限内也可能过时或被新事实更正 | [07](07-memory-and-state.md) |
| Checkpoint（检查点） | 为恢复而保存的某个执行状态 | 不自动与外部写入共享事务 | [07](07-memory-and-state.md) |
| 决策策略（policy） | 模型或规则如何选择下一步动作 | 不要与案例中的报销制度文件混淆 | [04](04-agent-loop.md) |
| 不变量（invariant） | 无论走到哪一步都应保持成立的规则 | 一次正常路径通过不足以证明始终成立 | [04](04-agent-loop.md) |
| ReAct | 交替组织推理与行动的一种范式 | 不要求公开模型隐藏思维 | [08](08-planning-and-multi-agent.md) |
| Reflection（反思） | 对先前过程或结果进行反馈与调整 | 只写反思文本不等于更新权重 | [08](08-planning-and-multi-agent.md) |
| Multi-agent（多智能体） | 多个有各自职责的 Agent 协作 | 会增加通信、汇总与冲突成本 | [08](08-planning-and-multi-agent.md) |
| Reducer（归并规则） | 一个状态字段怎样合并多份更新 | 合并数据不等于解决事实冲突 | [08](08-planning-and-multi-agent.md) |
| Trial / Outcome | 一次任务尝试 / 运行后的环境终态 | 文字“完成”不替代后端核验 | [09](09-evaluation.md) |
| LLM-as-a-Judge（模型评审） | 让模型按评分细则辅助评价 | 评分器仍需对照人工与客观证据校准 | [09](09-evaluation.md) |
| Recall@k | 前 k 个结果命中的相关项占全部标注相关项的比例 | 标注集合不完整会影响解释 | [09](09-evaluation.md) |
| MRR@k | 在声明查询集合上对首个命中的倒数排名取平均 | 单题是 RR，不是均值 MRR | [09](09-evaluation.md) |
| nDCG@k | 折扣累积收益相对于理想排名的归一化值 | 必须声明 gain 与无相关项口径 | [09](09-evaluation.md) |
| p95 | 一批观测的第95百分位耗时 | 不是平均数，也不是单次期限保证 | [09](09-evaluation.md) |
| SLO（服务水平目标） | 服务希望达到的质量或性能水平 | 需说明指标与统计窗口并实际验证 | [09](09-evaluation.md) |
| 身份认证 / 授权 / 批准 | 确认是谁 / 能做什么 / 是否同意本次具体动作 | 三者不能相互替代 | [10](10-reliability-and-security.md) |
| Idempotency（幂等） | 同一操作重复执行的约定效果与执行一次相同 | 不要求响应相同；创建接口仍需规定作用域、期限与一致性 | [10](10-reliability-and-security.md) |
| Prompt Injection（提示注入） | 不可信内容试图改变系统指令或行动的攻击 | 仅靠提示不形成完整执行边界 | [10](10-reliability-and-security.md) |

[课程目录](README.md) · [参考资料](verification.md)
