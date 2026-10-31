# 基础原理参考资料

<div id="基础课程参考资料"></div>

按知识主题整理的原论文、官方文档和阅读要点，可与各章正文对照学习。

| 编号 | 知识主题 | 参考来源 | 阅读要点 |
| --- | --- | --- | --- |
| K01 | 可以按主要控制路径区分 workflow 与 agent | [Anthropic 架构讨论](https://www.anthropic.com/research/building-effective-agents) | 按控制路径理解工作流与 Agent；规划、记忆和协作按任务选择。 |
| K02 | Token 切分取决于编码规则与词表 | [HF Tokenization](https://huggingface.co/docs/transformers/tokenizer_summary) | 使用目标模型的分词器统计 token。 |
| K03 | 典型自回归生成依赖已有前缀 | [HF LLM tutorial](https://huggingface.co/docs/transformers/llm_tutorial) | 关注前缀信息、条件概率与解码策略。 |
| K04 | 标准缩放点积注意力对 Value 做加权 | [Attention 原论文](https://arxiv.org/abs/1706.03762) | 缩放点积、因果 mask 与 Value 加权和；配套一维和二维算例。 |
| K05 | KV Cache 复用过去 Key/Value 中间表示 | [HF cache explanation](https://huggingface.co/docs/transformers/cache_explanation) | 缓存中间表示与长期记忆分属不同机制；跨请求复用取决于实现。 |
| K06 | SFT、偏好优化与 LoRA 分属不同描述维度 | [TRL SFT](https://huggingface.co/docs/trl/sft_trainer)、[DPO](https://huggingface.co/docs/trl/dpo_trainer)、[LoRA 原论文](https://arxiv.org/abs/2106.09685) | 区分训练目标、训练信号与参数适配方式。 |
| K07 | 上下文需选择；压缩可能丢失重要信息 | [Anthropic context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 选择证据、管理上下文预算，并在摘要中保留关键条件。 |
| K08 | 工具参数合同、真正执行和业务权限是不同边界 | [MCP Tools 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)、[当前客户端/服务端工具](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | 分别检查输入结构、业务权限与执行结果；执行器可在应用侧或平台侧。 |
| K09 | MCP 的 Host/Client/Server 是逻辑职责 | [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture)、[传输规范 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | 理解逻辑角色、会话连接与能力协商；stdio指标准输入/输出传输。 |
| K10 | MCP HTTP 授权机制不能替代资源级业务授权 | [MCP authorization 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | 区分 HTTP 与 stdio 的授权流程，以及连接权限与业务对象权限。 |
| K11 | MCP 与 A2A 可在同一应用里组合 | [A2A 官方对照](https://a2a-protocol.org/latest/topics/a2a-and-mcp/) | 根据工具连接与 Agent 任务协作的需求组合协议。 |
| K12 | RAG 使用外部检索材料，工程实践可比原论文更广 | [RAG](https://arxiv.org/abs/2005.11401)、[检索与生成的关系](https://docs.langchain.com/oss/python/deepagents/retrieval)、[DPR](https://arxiv.org/abs/2004.04906) | 先理解检索增强生成的用途与过程，再分别设计资料入库、检索与生成链路。 |
| K13 | 余弦为归一化点积；RRF 可以融合排名 | [cosine 官方定义](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)、[Elastic RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) | 关注同语义空间、零向量处理与排名融合；算例常数为 60。 |
| K14 | 重排只处理已召回的候选 | [Sentence Transformers retrieve/rerank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) | 检查候选集合覆盖范围和最终 top-k 的证据完整性。 |
| K15 | 存储记忆、检索和读入当前上下文是不同步骤 | [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、[上下文与窗口外笔记](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 区分应用状态、窗口外存储与模型参数。 |
| K16 | ReAct 是推理与行动的交替；文本反思未必更新权重 | [ReAct](https://arxiv.org/abs/2210.03629)、[Reflexion](https://arxiv.org/abs/2303.11366) | 理解反馈、情节记忆与参数更新的机制区别。 |
| K17 | Agent 评测要区分任务、尝试、轨迹与环境终态 | [Anthropic agent evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 用后端终态和执行轨迹共同判断任务结果。 |
| K18 | 二值 gain 的 nDCG 用相应理想排序归一化 | [scikit-learn nDCG](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html) | 声明 gain、截断位置、空相关集合与汇总口径；算例约为 0.530721。 |
| K19 | Judge 存在任务相关偏差，需人工校准 | [MT-Bench 原研究](https://arxiv.org/abs/2306.05685) | 检查位置、冗长与自我偏好，并用人工样本校准。 |
| K20 | 超时不等于没有副作用；幂等约束操作效果而非响应字节 | [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)、[AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | 先区分幂等定义与创建接口的实现，再围绕稳定意图 ID、参数、作用域、期限和一致性设计恢复。 |
| K21 | 多层重试可能放大负载；次数上限不同于总耗时上限 | [AWS retry/backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | 协调重试层和总期限；每层含首次最多尝试 3 次时，3 层最坏为 27 次。 |
| K22 | 恢复执行可能重放外部副作用 | [LangGraph re-execution and idempotency](https://docs.langchain.com/oss/python/langgraph/graph-api#re-execution-and-idempotency) | 恢复节点时结合外部事务、幂等合同与查询对账。 |
| K23 | 访问控制须由可信系统落实；不可信资料不能自行授权 | [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)、[injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | 在可信执行边界落实权限、参数与资源限制。 |
| K24 | 多 Agent、缓存、阈值和具体框架选型需任务内验证 | [本手册第 08 章](08-planning-and-multi-agent.md)、[第 09 章](09-evaluation.md) | 以目标任务的质量、延迟和成本比较架构与参数。 |

## 新案例的证据边界

[独立题目文章](../questions/README.md)、概念图及运行机制图使用本仓库自己的教学案例与布局。住宿标准、咨询要求和办公通知等制度均为虚构教学资料，金额和日期不是外部事实；它们检验同一案例的适用性与运行合同。概念依上表K01、K07–K10、K15–K23核对，不把源博客的类比当定义条件。

正文中“协议样本”“设计样本”“教学耗时”是可手工核对的示范，不表示供应商实测。已保存的运行记录来自政策实验；模型路径只有实际调用并保留证据后才能标为已验证。手册的学习效果需要试读记录，程序测试通过不能替代。

## 配套实验

- [政策实验](../examples/policy_agent/README.md)：同案例查询、补参、证据变式、持久恢复与独立评分；默认有限规则策略。
- [基础数学实验](../examples/foundations/README.md)：Attention、余弦、RRF 与检索指标。
- [工具循环实验](../examples/agent_lab/README.md)：工具校验、重试、审批、幂等和循环终止。

```bash
python3 -m examples.policy_agent eval --suite pilot --mode offline --output .local/policy_agent/pilot-report.json
python3 examples/foundations/math_lab.py --section all
python3 examples/agent_lab/lab.py --scenario all
```

[阅读目录](README.md) · [资源深度调研](../research/learning-resources.md) · [来源数据](../research/learning-sources.json) · [面试知识参考资料](../docs/claim-ledger.md)
