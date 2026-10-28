# AI Agent 面试准备手册

把 Agent 的机制讲清楚，把工程取舍讲具体，把自己的项目做扎实。

面向 **AI Agent / 大模型应用工程师**，以 Python 实践为主。这里是一份可自学、可复习、可贡献的中文学习仓库：56 道原创问答、30 天路线、工程场景、模拟面试，以及不需要 API Key 的离线教学实验。

> 内容核验日期：2026-10-28。题目优先级是本仓库的学习建议，不代表企业面试频率。示例、演练和项目目标均不代表作者的真实工作经历。

## 从这里开始

| 你的状态 | 建议入口 | 本次产出 |
| --- | --- | --- |
| 刚开始准备 | [学习路线](docs/00-roadmap.md) | 确定 30 天安排与验收标准 |
| 已经做过 LLM 应用 | [56 题索引](docs/question-index.md) | 找出解释不清的机制与失败路径 |
| 面试前一周 | [7 天冲刺](docs/00-roadmap.md#7-天冲刺) | 两轮模拟面试和一个可验证的项目演示 |
| 想动手补工程能力 | [离线实验](examples/agent_lab/README.md) | 运行工具循环，观察重试、审批、幂等和步数上限 |
| 想挑外部学习资料 | [GitHub 项目调研](research/github-survey.md) | 按用途组合资料，避免只收藏不练习 |

## 知识地图

| 模块 | 题号 | 你应当能够解释 |
| --- | --- | --- |
| [Agent 与 LLM 基础](docs/foundations/01-agent-and-llm.md) | Q001–Q008 | Agent 边界、Transformer、训练与推理、模型适配 |
| [规划与编排](docs/foundations/02-planning-and-orchestration.md) | Q009–Q016 | 循环、ReAct、状态、恢复、并发与多 Agent 取舍 |
| [RAG 与检索](docs/foundations/03-rag-and-search.md) | Q017–Q024 | 分块、检索、重排、权限、归因与评测 |
| [工具、记忆与协议](docs/foundations/04-tools-memory-protocols.md) | Q025–Q032 | Schema、执行边界、MCP、上下文和持久记忆 |
| [评测与可观测性](docs/engineering/05-evaluation-and-observability.md) | Q033–Q040 | 数据集、失败归因、Judge 偏差、成本与延迟 |
| [可靠性与安全](docs/engineering/06-reliability-and-security.md) | Q041–Q048 | 重试、幂等、人审、注入、隔离与故障恢复 |
| [系统设计与项目表达](docs/engineering/07-system-design-and-projects.md) | Q049–Q056 | 需求、架构、验收、真实贡献与可复现证据 |

## 每天怎么学

每天 45–60 分钟：闭卷回答 3–5 题，读对应解析，做一个微练习，最后记下解释失败的原因。优先练“为什么、怎么失败、怎么验证”，再补框架名词。

只阅读文档无需安装。运行工具需要 **Python 3.10+**，仅使用标准库，无需联网、安装依赖或配置密钥。在仓库根目录运行：

```bash
# 抽 5 题，只显示问题，先口述再看答案
python3 scripts/study.py draw --count 5

# 查看单题回答、追问和练习
python3 scripts/study.py show Q001

# 自评分：0 不会；1 提示后会；2 独立说清；3 能追问并举证
python3 scripts/study.py review Q001 --score 2

# 查看到期题目、尚未学习的题目和进度
python3 scripts/study.py due
python3 scripts/study.py stats

# 运行离线教学实验
python3 examples/agent_lab/lab.py --scenario all
```

复习记录保存在 `.local/study-progress.json`，默认不进入 Git。使用简单的日期间隔规则，详见 [复习说明](practice/README.md)；没有使用算法预测你的掌握程度。

## 用项目支撑面试回答

[7 天项目实验](docs/engineering/08-project-lab.md)提供从教学循环到真实模型接入的验收步骤。当前代码的决策器是固定脚本，检索是关键词匹配；它能验证执行器边界，**不能衡量真实 LLM 能力、语义检索质量或生产性能**。接入模型、持久化、多租户和部署属于后续练习。

准备面试时使用 [模拟面试](practice/mock-interviews.md)、[项目表达模板](practice/project-story-template.md) 和 [错题复盘模板](practice/review-template.md)。所有业务数据、项目职责和指标请用自己的真实材料填写。

## 资料和维护

- [项目调研及热度口径](research/github-survey.md)：面试题库、教程和框架分别比较；统计有来源和采集说明。
- [关键事实核验台账](docs/claim-ledger.md)：区分事实、工程建议和教学简化。
- [贡献指南](CONTRIBUTING.md)：补充问题、修正事实、增加可复现实验。
- [变更记录](CHANGELOG.md)：跟踪内容与工具更新。

提交前运行：

```bash
python3 scripts/check_repo.py
python3 -m unittest discover -s tests -v
```

本文档与代码为本仓库原创整理，采用 [MIT License](LICENSE)。引用的资料、外部项目和商标归各自权利人所有；其内容适用原项目许可。这里只链接外部资料，不搬运其题库、插图或模板。欢迎 Fork 后加入你自己的笔记与实验，并通过 Issue / PR 分享能核验的改进。
