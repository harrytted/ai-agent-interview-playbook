# AI Agent 系统学习与面试手册

Agent 能把答案说得很像已经办成了。学这份手册，要再往前走一步：看清它读了什么、做了什么，失败后还能不能收拾现场。

面向 **AI Agent / 大模型应用工程师**，以 Python 实践为主。仓库包含 **10 章基础、12 章进阶、92 道原创详解题**，配有数值算例、执行器与恢复实验、项目工作坊、学习路线和模拟面试。

全部题目都有口述短答、详细答案、3 个带回答的追问、实战案例、误区与验收练习，共 **276 组追问、92 个案例**。每题直接链接对应学习内容，章节末尾也能找到相关题目。

可以从一个具体问题开始：为什么引用存在却不支持结论？为什么超时之后反而创建了两张工单？章节沿着案例解释机制，题库再用追问和故障检查理解。术语会逐步出现，不需要入场先背一袋缩写。

## 配套在线阅读

读到陌生词，可以先查字典；学完一章，还可以到博客看图解和工程文章。两个网站都由本仓库作者维护：

- [AI 编程字典：查术语、看关系图](https://agent.harrylab.cn/dictionary/)：查询中英术语，沿概念关系理解 Token、Context、Harness、MCP 等知识怎样连接。
- [Agent 技术博客：读图解与工程实践](https://agent.harrylab.cn/articles/)：阅读 Agent 工程实践、原理图解和技术笔记，把课程里的机制放回具体问题中理解。

可以把仓库当作学习与练习主线，把字典放在手边查词，再按问题选读博客文章。

## 从这里开始

| 你的状态 | 建议入口 | 本次产出 |
| --- | --- | --- |
| 想从原理开始学 | [基础课程](learning/README.md) | 理解从 LLM 到 Agent 系统的完整链路 |
| 已经掌握基础 | [进阶课程](advanced/README.md) | 系统学习长任务、Agentic RAG、协作、质量优化与训练 |
| 开始准备面试 | [学习路线](docs/00-roadmap.md) | 确定 30 天安排与验收标准 |
| 已经做过 LLM 应用 | [92 题索引](docs/question-index.md) | 找出解释不清的机制与失败路径 |
| 要准备进阶追问 | [36 道进阶题](docs/advanced/README.md) | 用详细解析、追问和案例连接 12 章知识 |
| 面试前一周 | [7 天冲刺](docs/00-roadmap.md#7-天冲刺) | 两轮模拟面试和一个可验证的项目演示 |
| 想动手补工程能力 | [离线实验](examples/agent_lab/README.md) | 运行工具循环，观察重试、审批、幂等和步数上限 |
| 想挑外部学习资料 | [GitHub 项目调研](research/github-survey.md) | 按用途组合资料，避免只收藏不练习 |
| 想跟进进阶方向 | [进阶项目与技术博客](research/advanced-landscape.md) | 判断新能力的用途、工程取舍及对应学习章节 |

## 基础课程

先沿连续教程理解机制，再用题目闭卷检验。每章有具体案例、逐步算例、验收练习、自检答案及来源。贯穿案例为虚构的内部政策助手。

| 学习阶段 | 课程 | 核心产出 |
| --- | --- | --- |
| 模型和输入 | [01 系统地图](learning/01-system-map.md) · [02 LLM 原理](learning/02-llm-primer.md) · [03 上下文](learning/03-context-and-prompts.md) | 画清职责，复算注意力，组织有效证据 |
| 行动与知识 | [04 工具循环](learning/04-agent-loop.md) · [05 工具/MCP](learning/05-tools-and-mcp.md) · [06 RAG](learning/06-rag-and-retrieval.md) | 读执行轨迹，定义工具合同，检查检索链路 |
| 状态与协作 | [07 记忆](learning/07-memory-and-state.md) · [08 规划与多 Agent](learning/08-planning-and-multi-agent.md) | 管理状态与版本，解释协作和恢复的边界 |
| 质量与交付 | [09 评测](learning/09-evaluation.md) · [10 可靠性与安全](learning/10-reliability-and-security.md) | 定义指标与终态，处理失败和越权 |

[完整课程与节奏](learning/README.md) · [术语回查](learning/glossary.md) · [课程参考资料](learning/verification.md) · [GitHub 学习资源深度调研](research/learning-resources.md)

## 进阶课程

进阶课程将 GitHub 项目、作者技术博客、官方文档、协议和论文整理成可连续学习的知识。沿同一个政策研究助手案例，从运行机制走到设计练习，再用轨迹、故障和评测判断改进。

| 学&#8288;习&#8288;阶&#8288;段 | 课程 | 核心产出 |
| --- | --- | --- |
| 运&#8288;行&#8288;基&#8288;础 | [01 Harness](advanced/01-harness-and-deep-agents.md) · [02 持久执行](advanced/02-durable-execution.md) · [03 上下文工程](advanced/03-context-engineering.md) · [04 记忆与技能](advanced/04-memory-and-skills.md) | 长任务交接、恢复状态图、上下文与记忆合同 |
| 能&#8288;力&#8288;组&#8288;织 | [05 工具路由/MCP](advanced/05-tool-routing-and-mcp.md) · [06 Agentic RAG](advanced/06-agentic-rag.md) · [07 多 Agent](advanced/07-multi-agent-systems.md) · [08 编码与计算机操作](advanced/08-coding-and-computer-use.md) | 工具选择、证据策略、协作图和操作环境 |
| 质&#8288;量&#8288;优&#8288;化 | [09 评测反馈](advanced/09-evaluation-and-feedback.md) · [10 性能与推理](advanced/10-performance-and-serving.md) · [11 安全治理](advanced/11-security-and-governance.md) · [12 Agent 训练](advanced/12-agent-training.md) | 回归集合、共享预算、授权边界与训练决策 |

[完整进阶路线](advanced/README.md) · [贯穿项目工作坊](advanced/project-workshop.md) · [官方知识体系](advanced/official-learning-map.md) · [机制实验](examples/advanced/README.md)

每章都有对应的 [3 道进阶面试题](docs/advanced/README.md)。先读场景和机制，再闭卷说短答，最后展开详细答案与案例。遇到不会的追问，可以直接回到学习章节补上那一步。

## 知识地图

Q001–Q056 覆盖基础与通用工程，Q057–Q092 对应 12 章进阶系统知识，采用相同的详解与案例标准。想先理解机制，就从学习章进入；想闭卷练回答，就从题目进入。

| 模块 | 题号 | 你应当能够解释 |
| --- | --- | --- |
| [Agent 与 LLM 基础](docs/foundations/01-agent-and-llm.md) | Q001–Q008 | Agent 边界、Transformer、训练与推理、模型适配 |
| [规划与编排](docs/foundations/02-planning-and-orchestration.md) | Q009–Q016 | 循环、ReAct、状态、恢复、并发与多 Agent 取舍 |
| [RAG 与检索](docs/foundations/03-rag-and-search.md) | Q017–Q024 | 分块、检索、重排、权限、归因与评测 |
| [工具、记忆与协议](docs/foundations/04-tools-memory-protocols.md) | Q025–Q032 | Schema、执行边界、MCP、上下文和持久记忆 |
| [评测与可观测性](docs/engineering/05-evaluation-and-observability.md) | Q033–Q040 | 数据集、失败归因、Judge 偏差、成本与延迟 |
| [可靠性与安全](docs/engineering/06-reliability-and-security.md) | Q041–Q048 | 重试、幂等、人审、注入、隔离与故障恢复 |
| [系统设计与项目表达](docs/engineering/07-system-design-and-projects.md) | Q049–Q056 | 需求、架构、验收、真实贡献与可复现证据 |
| [12 章进阶面试](docs/advanced/README.md) | Q057–Q092 | 长任务、上下文、检索协作、运行质量与训练取舍 |

## 每天怎么学

每天可以只解决一个能说清的问题：读案例，预测下一步，运行或手算一次，再口述关联题。面试复习时，每天闭卷回答 3–5 题，读解析、答追问，最后留一个微练习结果。

别急着把每页都涂成已读。对同一个例子加一句“这时网络断了呢”，往往比多背三个框架名更能发现缺口。

只阅读文档无需安装。运行工具需要 **Python 3.10+**，仅使用标准库，无需联网、安装依赖或配置密钥。在仓库根目录运行：

```bash
# 抽 5 题，只显示问题，先口述再看答案
python3 scripts/study.py draw --count 5

# 只练新增的 36 道进阶题
python3 scripts/study.py draw --topic docs/advanced/ --count 3

# 查看单题回答、追问和练习
python3 scripts/study.py show Q001
python3 scripts/study.py show Q060

# 自评分：0 不会；1 提示后会；2 独立说清；3 能追问并举证
python3 scripts/study.py review Q001 --score 2

# 查看到期题目、尚未学习的题目和进度
python3 scripts/study.py due
python3 scripts/study.py stats

# 运行离线教学实验
python3 examples/agent_lab/lab.py --scenario all

# 复算 Attention、余弦、RRF 与检索指标
python3 examples/foundations/math_lab.py --section all

# 验证多次尝试指标、共享预算、关键路径与崩溃恢复
python3 examples/advanced/runtime_lab.py --scenario all
```

复习记录保存在 `.local/study-progress.json`，默认不进入 Git。日期间隔规则详见 [复习说明](practice/README.md)。

## 用项目支撑面试回答

[7 天项目实验](docs/engineering/08-project-lab.md)提供从工具循环到真实模型接入的验收步骤。当前代码使用脚本决策器和关键词检索，实验重点是执行器边界。接入模型、持久化、多租户和部署见后续练习。

准备面试时使用 [模拟面试](practice/mock-interviews.md)、[项目表达模板](practice/project-story-template.md) 和 [错题复盘模板](practice/review-template.md)。所有业务数据、项目职责和指标请用自己的真实材料填写。

## 参与完善

读到不准确的解释、遇到跑不通的示例，欢迎反馈；有值得分享的面试经验或实战做法，也欢迎一起补充。

- **纠错与补充**：通过 [Issue](https://github.com/harrytted/ai-agent-interview-playbook/issues/new) 注明题号或章节位置，写下修改建议，尽量附上参考来源。
- **分享经验与案例**：欢迎通过 [Pull Request](https://github.com/harrytted/ai-agent-interview-playbook/compare) 补充面试追问、答题思路或实战案例，让下一位读者少绕一点弯。
- **反馈代码问题**：提交 [Issue](https://github.com/harrytted/ai-agent-interview-playbook/issues/new) 时，请说明运行环境、复现步骤，以及预期结果和实际表现，方便定位与修复。

内容格式、引用要求和提交前检查见 [贡献指南](CONTRIBUTING.md)。

## 资料和维护

- [项目调研及热度口径](research/github-survey.md)：面试题库、教程和框架分别比较；统计有来源和采集说明。
- [基础学习资源调研](research/learning-resources.md)：实读课程章节，说明建议的阅读基础、示例环境、归档与版本限制。
- [进阶项目与技术博客](research/advanced-landscape.md)：从 Harness、协议、记忆、检索与训练梳理能力变化。
- [官方知识体系与选读地图](advanced/official-learning-map.md)：将官方教程、协议与论文接到 12 章进阶课程。
- [课程参考资料](learning/verification.md)：按课程主题整理原论文和官方文档。
- [面试知识参考资料](docs/claim-ledger.md)：按基础概念和工程主题整理一手资料。
- [贡献指南](CONTRIBUTING.md)：补充问题、修正事实、增加可复现实验。
- [变更记录](CHANGELOG.md)：跟踪内容与工具更新。

提交前运行：

```bash
python3 scripts/check_repo.py
python3 -m unittest discover -s tests -v
```

本文档与代码为本仓库原创整理，采用 [MIT License](LICENSE)。引用的资料、外部项目和商标归各自权利人所有；其内容适用原项目许可。这里只链接外部资料，不搬运其题库、插图或模板。
