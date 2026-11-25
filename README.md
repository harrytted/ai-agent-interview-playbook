# AI Agent 系统学习与面试手册

一份中文 Agent 工程手册。沿着一次任务，理解模型读到了什么、程序执行了什么、结果怎么核对。可以从头学，也可以在做项目时按问题回查。

**[10 章基础目录](learning/README.md) · [19 章进阶目录](advanced/README.md) · [110 道题索引](docs/question-index.md)**

[在线阅读](https://harrytted.github.io/ai-agent-interview-playbook/learning/) · [知识主线](learning/knowledge-map.md)

<div class="learning-paths" markdown="1">

- **[系统入门](learning/01-system-map.md)**<br>
  从 Agent 的组成开始，顺着工具、检索和任务状态读完基础十章。

- **[工程回查](#工程进阶)**<br>
  按任务找资料。长任务恢复、检索、评测、性能和上线维护都可以单独阅读。

- **[面试复习](#面试复习)**<br>
  先做 [三道试读题](practice/three-question-preview.md)，也可以按主题查题，从解析回到对应章节。

</div>

## 正文试读

- **[基础 · RAG 与检索](learning/06-rag-and-retrieval.md)**  顺着入库、召回、重排和模型输入定位证据丢失。
- **[进阶 · Agent 故障排查与发布验证](advanced/19-incident-review-and-release.md)**  从执行轨迹找偏差，把修复变成回归检查，再决定能否扩大上线范围。

<div id="从组成看懂协作"></div>
<div id="基础课程"></div>

## 基础原理

从模型与上下文读起，再看工具怎样执行、证据怎样进入回答、任务状态怎样保存。最后用评测与可靠性章节串起整条链路。

[基础十章目录](learning/README.md) · [模型、工具、记忆与规划的关系图](learning/01-system-map.md#模型工具记忆与规划) · [术语表](learning/glossary.md)

<div id="进阶课程"></div>

## 工程进阶

进阶章节讲运行机制、设计取舍和失效条件。做项目遇到具体问题时，可以直接从对应小节读起。

| 查阅主题 | 用于 |
| --- | --- |
| [RAG 证据排查](advanced/06-agentic-rag.md#分层测量与对照实验) | 区分召回遗漏、排序变化和模型输入里的证据丢失。 |
| [写入超时与恢复](advanced/02-durable-execution.md#外部写入与故障窗口) | 沿原操作编号核对外部结果，判断何时能重试。 |
| [Agent 技能验证](advanced/04-memory-and-skills.md#技能选择与效果验证) | 分别判断技能是否选对、启用后结果是否变好。 |
| [评测改动](advanced/09-evaluation-and-feedback.md#配对差异与不确定性) | 用同一批任务比较版本，分清修复与退步。 |
| [上线与回退](advanced/19-incident-review-and-release.md#回退与在途任务) | 回退版本时核对任务状态，处理已经派发的动作。 |

项目主线：[模型 API](advanced/13-model-api-and-output-contracts.md) → [最小任务服务](advanced/16-service-deployment-and-operations.md#16a--持久接收与只读任务) → [知识摄取](advanced/14-ingestion-and-index-lifecycle.md) → [批准写入与恢复](advanced/16-service-deployment-and-operations.md#16b--批准写入与恢复)。

[进阶十九章目录](advanced/README.md) · [项目工作坊](advanced/project-workshop.md) · [进阶参考资料](advanced/official-learning-map.md)

<div id="知识地图"></div>
<div id="每天怎么学"></div>

## 面试复习

可以先做 [三道试读题](practice/three-question-preview.md)，也可以直接看 [110 题索引](docs/question-index.md)。基础和通用工程题为 Q001–Q056。Q057–Q110 对应进阶第 01–18 章。

[分主题题解](questions/README.md) · [模拟面试](practice/mock-interviews.md) · [复习工具](practice/README.md)

<div id="理解以后再用实验和项目加深"></div>

## 离线实验与项目

文档可直接阅读。下面两条命令需要 Python 3.10+，在仓库根目录执行。第一条抽三道题，第二条验证外部提交后中断怎么恢复。

```bash
python3 scripts/study.py draw --count 3
python3 examples/advanced/runtime_lab.py --scenario replay
```

[走完一次任务](learning/00-first-agent.md) · [基础数学实验](examples/foundations/README.md) · [进阶机制实验](examples/advanced/README.md) · [七天项目路线](docs/engineering/08-project-lab.md)

## 参与完善

发现内容或运行问题，可以通过 [Issue](https://github.com/harrytted/ai-agent-interview-playbook/issues/new) 提交章节位置、预期结果和实际结果。补充内容可按 [贡献指南](CONTRIBUTING.md) 提交 Pull Request。

## 参考资料与延伸阅读

[基础参考资料](learning/verification.md) · [学习资源索引](research/README.md) · [AI 编程字典](https://agent.harrylab.cn/dictionary/) · [Agent 技术博客](https://agent.harrylab.cn/articles/)

仓库内容采用 [MIT 许可](LICENSE)。引用资料和外部项目适用各自的许可。
