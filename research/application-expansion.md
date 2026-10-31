# 应用专题扩充：从协议到可恢复任务

核查日期：2026-10-31。实施基线：`d13e113`。本轮沿用基础10章、系统机制12章与Q001–Q092，新增应用专题13–18和Q093–Q110。原学习链接与复习记录格式继续使用；新增题目从未学习状态开始。

## 扩充补哪一段

原手册已经解释幂等、恢复、审批、文档更新、SQL权限、取消及发布回退。新增内容把这些原则连接到实际协议、词项索引、SQLite分析、HTTP任务、事件账本和媒体状态。只把某个原则再讲一次，不构成本轮的交付。

六组实验围绕虚构差旅政策展开，数据与原政策实验分别保存。新增统计数据、媒体和索引不改变旧任务的期望。各实验的README说明运行命令、故障场景、证据级别及可选依赖。

## 按目标安排顺序

| 路径 | 阅读和实验顺序 | 完成后能做什么 |
| --- | --- | --- |
| 应用主线 | 基础工具循环 → [13模型接入](../advanced/13-model-api-and-output-contracts.md) → [16A最小服务](../advanced/16-service-deployment-and-operations.md) → [14摄取](../advanced/14-ingestion-and-index-lifecycle.md) → 16B受控执行与运维 | 提交、补参、恢复任务，解释结果来自哪份适用证据 |
| 数据分析 | 最小SQL基础 → [15 SQL分析](../advanced/15-text-to-sql-and-data-analysis.md) → 16的任务接口 | 给出指标口径、可执行查询和独立核验的结果 |
| 主动任务 | 14与16 → [17事件订阅](../advanced/17-event-driven-and-proactive-agents.md) | 由有资格的事件启动有界任务，撤销订阅并解释通知条件 |
| 媒体交互 | 13与16 → [18A媒体证据、18B播放与打断](../advanced/18-multimodal-and-realtime-agents.md) | 将图片、转写和当前条件关联，拒用迟到旧结果并同步播放历史 |

编号用于稳定回查，不要求先学SQL或训练才能做任务服务。第16章按最小服务和受控执行两层阅读；第18章先解释媒体证据，再选修实时交互。

## 能力、失败与证据

| 能力 | 必须能发现的失败 | 需要观察的证据 | 实现入口 |
| --- | --- | --- | --- |
| 完整模型往返 | 工具ID缺失、重复、半截参数、拒答与异常停止 | 原始字节、解析事件、回填对应表和终态 | [模型协议](../examples/model_protocol_lab/README.md) |
| 可更新知识 | 同源重复导入、中途失败、旧块残留、撤权 | 原文位置、内容哈希、索引代次、变更前后查询 | [知识摄取](../examples/knowledge_pipeline_lab/README.md) |
| 正确统计 | JOIN放大、错误分母、空结果、非法查询 | 数据快照、SQL、返回表、修复记录和独立期望 | [SQL分析](../examples/sql_agent_lab/README.md) |
| 持久任务服务 | 重复提交、跨用户访问、并发更正、重启与取消 | 接收账本、任务所有者、状态版本、HTTP记录和业务对象 | [任务服务](../examples/service_lab/README.md) |
| 有界事件任务 | 重复、乱序、崩溃后重投、撤销后的迟到事件 | 原始事件、版本归并、派生任务、通知决定和本地Outbox | [事件订阅](../examples/event_agent_lab/README.md) |
| 媒体条件一致 | 临时转写提前执行、用户更正、旧工具结果迟到、打断后历史失真 | 证据区域、媒体时间线、任务版本和实际播放位置 | [媒体与播放](../examples/multimodal_lab/README.md) |

默认实验使用独立期望核验真实运行结果，支持一次正常过程与多种失败变式。规则策略、预制候选和媒体识别替身均需在结果中明确；不能用本地全绿证明真实模型规划、语义检索、OCR、ASR或TTS质量。

## 四类证据分别报告

1. **离线协议与状态证据**：增量解析、ID对应、预算、版本、通知和媒体状态等控制逻辑。
2. **本地真实组件证据**：实际词项索引、SQLite查询、HTTP请求、跨进程恢复或浏览器音频播放。
3. **真实供应商接入证据**：指定模型、API版本、请求与返回成立；需要自己的凭据和费用预算。
4. **模型能力评测证据**：声明任务集、逐题期望、重复次数、预算、终态与失败归因。教材已公开任务属于回归集，不能同时称作未见保留集。

真实模型评测可以沿用 [政策实验的live入口](../examples/policy_agent/README.md)，固定版本、任务与预算后重复运行；比较简单固定流程、观察驱动规则和模型策略时分别报告适用任务与调用开销。默认CI不发起付费调用。播放器的合成提示音只证明播放进度和打断路径，无人声识别或语音合成效果数据。

## 外部项目如何进入教材

以下为一手资料中的机制与课程设计判断。外部项目未因被引用而在本机部署；可变文档以核查日期标记，运行其示例时须固定采用版本。来源记录见 [机器可读台账](application-sources.json)。

| 一手来源 | 可支持的事实 | 本手册采用的判断与边界 |
| --- | --- | --- |
| [Anthropic：Building effective agents](https://www.anthropic.com/research/building-effective-agents) | 建议先使用最简单可行结构，理解模型输入、工具与反馈 | 13先完整往返，再深入流式协议；框架抽象不能代替合同解释 |
| [Anthropic：Long-running harnesses](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents) | 环境、进度工件、增量工作和检查共同支持跨会话任务 | 16验收同一任务跨中断继续完成，HTTP成功仅是一项中间观察 |
| [Anthropic：Agent evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 任务、尝试、轨迹和环境终态要分别观察 | 保留多次运行和独立结果核验，区分能力与回归评测 |
| [LangChain：Deep Agents evals](https://www.langchain.com/blog/how-we-build-evals-for-deep-agents) | SDK测试与模型能力评测承担不同职责 | 110题是内容规模，学习收益仍需迁移练习和真人试读 |
| [LlamaIndex：Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/) | 通过文档ID、内容哈希、缓存与docstore组织增量处理 | 14用实际词项索引讲生命周期；不报告Embedding语义质量 |
| [LangSmith：Agent Server](https://docs.langchain.com/langsmith/agent-server) | API、运行、持久状态、任务队列、取消和流事件组成服务边界 | 16用本地最小服务解释职责，不复制整套云平台 |
| [Spider 2.0](https://spider2-sql.github.io/) | 企业SQL任务包含环境、文档、不同方言及结果核验 | 15使用小型可复算数据库，不能把SQLite示例成绩推广到企业基准 |
| [Cloudflare：Project Think](https://blog.cloudflare.com/project-think/) | 持久会话、执行与事件入口可组合成Agent运行平台 | 17先验证事件合同与本地Outbox；本地通知对象不等于外部消息送达 |
| [LiveKit：Turns](https://docs.livekit.io/agents/logic/turns/) | 轮次、打断和已播放内容影响会话状态 | 18B独立核对生成、播放、打断与历史；离线回放不代表网络时延 |

GitHub热度帮助挑选阅读样本，不决定课程优先级。[OpenViking](https://github.com/volcengine/OpenViking)的分层上下文可回查03/04/06；[Switchyard](https://github.com/NVIDIA-NeMo/Switchyard)的路由与客户端分工可回查10/13。各自实现不能自动保证本手册的权限、恢复或任务质量合同。

## 验收与剩余验证

本轮保留旧Q001–Q092，生成Q093–Q110独立文章；每章三题、正文回链、题源回链、合订页锚点与旧复习记录分别检查。检查器和HTML校验器共享轻量章名配置，题目正文继续单源维护。

六组实验进入仓库CI与站点CI。播放器只发布三份明确列出的HTML/WAV/SVG文件，其他实验源码与夹具使用GitHub源码链接；不会因为允许一个演示而发布整个实验目录。

自动检查覆盖协议、状态、真实本地组件、题目生成、站点链接和构建。真实供应商任务集评测需要凭据与测量条件；外部框架性能、生产认证、高可用、真实OCR/ASR/TTS质量不由这些离线检查证明。真人试读继续采用不同经验的读者完成代表任务，记录卡点、提示次数与条件变化后的迁移表现，不能由阅读量或单元测试数量替代。

## 本次本地验收记录

2026-10-31在Python 3.12环境完成下列验证；Python 3.10已做语法兼容检查，实际3.10运行由仓库CI继续验证。所有实验命令均未调用真实供应商模型。

| 实验 | 场景数 | 本地结果 |
| --- | ---: | --- |
| 模型协议 | 9 | 全部通过，包含第二轮截断/拒答 |
| 知识摄取 | 8 | 全部通过，包含更新、撤权与回退 |
| SQL分析 | 8 | 全部通过，多数据实例核验与访问控制成立 |
| HTTP任务服务 | 6 | 全部通过，另有真实子进程退出与恢复测试 |
| 事件订阅 | 10 | 全部通过，包含接收后派发前恢复与冲突版本隔离 |
| 媒体状态 | 5 | 全部通过，包含更正、取消代次重投与迟到结果 |

全仓244项单元测试通过；原有机制、数值、运行时实验与政策任务22/22通过。110题生成重复执行结果一致，本地文档链接与JSON检查通过。严格站点构建与201个HTML页面检查通过，110篇独立题解及原合订题锚点保留；新六章和18篇新题解均已进入中文搜索索引。

播放器HTML、4秒WAV及SVG确已进入站点，JavaScript语法和媒体文件元数据检查通过。浏览器对本地地址的两次自动授权均超时，故真实播放、中途打断与重置交互尚未实测，不能记录为浏览器验收通过。真实供应商效果评测、外部框架运行及真人试读也未在本轮执行。

[工程进阶](../advanced/README.md) · [应用题目目录](../docs/advanced/README.md) · [项目工作坊](../advanced/project-workshop.md)
