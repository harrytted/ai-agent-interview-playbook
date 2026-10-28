# 基础课程的知识核验记录

核验日期：**2026-10-28（Asia/Shanghai）**。本页记录课程采用的有限主张、证据和验证边界。GitHub 课程用于组织学习范围；技术事实优先回查协议、原论文和实现方官方文档。没有对外部课程全部正文或所有代码给出正确性认证。

`supported` 表示已读取的一手资料支持这里限定的主张；`calculated` 表示定义和本仓库教学数字可独立复算；`design-advice` 是有约束的工程建议；`unverified` 表示本仓库没有实际验证该能力。任何状态都不是“所有场景百分之百正确”的承诺。

## 核心主张与证据

| ID | 有限主张 | 一手依据 | 状态与适用边界 |
| --- | --- | --- | --- |
| K01 | 可以按主要控制路径区分 workflow 与 agent | [Anthropic 架构讨论](https://www.anthropic.com/research/building-effective-agents) | supported；采用一种工作定义，不宣布唯一标准；不强制长期记忆或多 Agent |
| K02 | Token 切分取决于编码规则与词表 | [HF Tokenization](https://huggingface.co/docs/transformers/tokenizer_summary) | supported；不能承诺固定中文字符比例，服务计费另查合同 |
| K03 | 典型自回归生成依赖已有前缀 | [HF LLM tutorial](https://huggingface.co/docs/transformers/llm_tutorial) | supported；不把一种生成机制扩大为所有模型架构 |
| K04 | 标准缩放点积注意力对 Value 做加权 | [Attention 原论文](https://arxiv.org/abs/1706.03762) | supported + calculated；一维输出 7→1、二维权重与 mask 已运行；省略完整网络 |
| K05 | KV Cache 复用过去 Key/Value 中间表示 | [HF cache explanation](https://huggingface.co/docs/transformers/cache_explanation) | supported；不等于长期记忆或更新参数，跨请求复用依实现 |
| K06 | SFT、偏好优化与 LoRA 分属不同描述维度 | [TRL SFT](https://huggingface.co/docs/trl/sft_trainer)、[DPO](https://huggingface.co/docs/trl/dpo_trainer)、[LoRA 原论文](https://arxiv.org/abs/2106.09685) | supported；不承诺少参数就无需高质量数据 |
| K07 | 上下文需选择；压缩可能丢失重要信息 | [Anthropic context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | supported；8192 预算为自建算例，不把经验性退化描述写成普遍定律 |
| K08 | 工具参数合同、真正执行和业务权限是不同边界 | [MCP Tools 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)、[当前客户端/服务端工具](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | supported；形状合格不证明语义真实、授权或执行成功；托管工具可由平台运行时执行 |
| K09 | MCP 的 Host/Client/Server 是逻辑职责 | [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture) | supported；不要求各自独占一台机器，不把动态页面当固定 SDK 版本 |
| K10 | MCP HTTP 授权机制不能替代资源级业务授权 | [MCP authorization 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | supported；协议版本有范围，stdio 不照搬 HTTP 流程 |
| K11 | MCP 与 A2A 可在同一应用里组合 | [A2A 官方对照](https://a2a-protocol.org/latest/topics/a2a-and-mcp/) | supported；侧重不同，不能简单视为等同或互斥 |
| K12 | RAG 使用外部检索材料，工程实践可比原论文更广 | [RAG](https://arxiv.org/abs/2005.11401)、[DPR](https://arxiv.org/abs/2004.04906) | supported；不保证消除错误，不强制使用某种数据库 |
| K13 | 余弦为归一化点积；RRF 可以融合排名 | [cosine 官方定义](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)、[Elastic RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) | supported + calculated；本脚本拒绝数学分母为零的向量，库可能另约定为 0；60 是教学参数；同维不等于同语义空间 |
| K14 | 重排只处理已召回的候选 | [Sentence Transformers retrieve/rerank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) | supported；无法凭空补回未进入候选的材料 |
| K15 | 存储记忆、检索和读入当前上下文是不同步骤 | [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、[上下文与窗口外笔记](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | supported；应用层记忆不是自动参数训练 |
| K16 | ReAct 是推理与行动的交替；文本反思未必更新权重 | [ReAct](https://arxiv.org/abs/2210.03629)、[Reflexion](https://arxiv.org/abs/2303.11366) | supported；不索取隐藏思维，不把任务内反馈当训练效果 |
| K17 | Agent 评测要区分任务、尝试、轨迹与环境终态 | [Anthropic agent evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | supported；写成功文字不能证明后端对象存在 |
| K18 | 二值 gain 的 nDCG 用相应理想排序归一化 | [scikit-learn nDCG](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html) | supported + calculated；样例约 0.530721，明确空相关集合与短排名口径 |
| K19 | Judge 存在任务相关偏差，需人工校准 | [MT-Bench 原研究](https://arxiv.org/abs/2306.05685) | supported；偏差观察不外推为所有 Judge 同样程度，分数不直接当正确概率 |
| K20 | 超时不等于没有副作用；幂等需服务端合同 | [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | supported；需考虑意图、参数、作用域、期限和一致性 |
| K21 | 多层重试可能放大负载；次数上限不同于总耗时上限 | [AWS retry/backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | supported + calculated；每层 3 次尝试含首次，3 层最坏 27；代码仅演示次数预算 |
| K22 | 恢复执行可能重放外部副作用 | [LangGraph re-execution and idempotency](https://docs.langchain.com/oss/python/langgraph/graph-api#re-execution-and-idempotency) | supported；checkpoint 不替代外部事务与幂等 |
| K23 | 访问控制须由可信系统落实；不可信资料不能自行授权 | [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)、[injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | design-advice；多层控制降低风险，不承诺彻底消除注入 |
| K24 | 多 Agent、缓存、阈值和具体框架选型需任务内验证 | [本课程第 08 章](08-planning-and-multi-agent.md)、[第 09 章](09-evaluation.md) | design-advice；不从案例结果推出普遍收益 |

## 复核与实际运行

作者写作后进行了另一次审阅：一组审阅跨查工具/检索/记忆/规划概念，另一组独立复算评测与数学实验，并核对执行器代码。审阅会发现和修正问题，不把模型之间意见一致当作事实证明。

- JSON 示例及第 02 章一维注意力算例已实际运行。
- 二维 Attention/mask、余弦、RRF、P@k、Recall@k、RR@k、二值 nDCG 已按教学输入运行，并与独立手算比对。
- 极大有限向量会使直接求模溢出，复核发现后已改为先缩放再归一化，并增加几何已知值测试。
- 正常读取、有限读重试、精确批准、拒绝写入、重复意图、参数冲突、写响应丢失与循环停止已对照脚本行为检查。
- 内部文档链接、题号与 JSON 结构由仓库检查器验证；它不判断外部论断的真伪。

```bash
python3 scripts/check_repo.py
python3 -m unittest discover -s tests -v
python3 examples/foundations/math_lab.py --section all
python3 examples/agent_lab/lab.py --scenario all
```

本轮部分网络工具连接异常，改用浏览器直接读取官方正文。少数一手来源复用了本会话同日已经读取的内容；没有把重新请求失败当成重新核验成功。学习资源的具体实读页面与未取得的 commit SHA 见 [来源快照](../research/learning-sources.json)。

## 未验证的能力

| 内容 | 当前状态 |
| --- | --- |
| 本课程对任意真实模型的准确率、工具选择和规划能力 | unverified；未调用真实模型 |
| 真实语义向量质量、向量数据库和真实数据 ACL | unverified；数学脚本使用手工数值，执行器使用合成关键词资料 |
| 并发原子幂等、跨进程恢复、真实执行超时与取消 | unverified；现有 Runtime 只作内存顺序实验 |
| 所有引用仓库在当前环境的完整运行兼容性 | unverified；实读章节不等于执行完整课程 |
| 仓库之外的全部知识不存在错误、未来接口永不变化 | 不作此承诺；按证据与版本持续修正 |

[课程目录](README.md) · [资源深度调研](../research/learning-resources.md) · [原面试题核验台账](../docs/claim-ledger.md)
