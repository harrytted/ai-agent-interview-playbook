# 图文复用与机制讲解复核

复核基线：`4977355`，修订分支：`feature/rag-mechanisms-revision`，日期：2026-11-05。本文记录本轮实际发现与处理，不把去掉重复图片等同于知识质量已经通过读者实测。

## 为什么前轮漏掉了G5

前轮主要逐章检查概念与题目递进，没有按canonical图片资产聚合跨栏目的嵌入位置，因此漏报了G5在基础、进阶及多个题源中的重复。提醒“questions是生成副本”本身正确，但即使合并生成副本，G5仍有5个独立源文位置；不能据此将它忽略。

基线的G5位置是：基础06第49行用于入库/查询总览；进阶06第53行用于两类证据缺口案例；题源Q017第23行用于完整链路，Q024第321行用于分层排障，Q072第21行用于检索路径。生成文章Q017第19行、Q024第15行、Q072第17行又展示相同资产。它们合计8次可见嵌入，但属于5个独立内容位置，不是8份独立创作。

## 统计口径与基线规模

- canonical资产按相对链接解析后的仓库路径识别；同一资产的缩略图点击目标不再算一张图片。
- 一个题源中的一个题号/小节与学习章中的一个嵌入点各算一个逻辑源文位置。`questions/Qxxx.md`关联回同号题源，不再算独立作者位置。
- 排除`.site-src`等生成站点目录。本轮初始工作副本中的该目录又映射了109次嵌入，不能当作另一套手写文档。
- 基线共44张资产、109次源Markdown/生成题页嵌入。其中27次位于生成题页，合并后为82个逻辑源文位置；13张资产在多个源文位置重复。
- 资产审查同时解析路径并用SHA-256发现不同文件名下的相同字节；没有用感知哈希识别经过裁剪、重编码的相似画面，也没有以图片数或文本相似率推断读者是否学会。

下表的行号固定在基线提交，用于说明发现位置；修订后行号会变化。“生成映射”列只是题页中的嵌入次数，不能再次累加到逻辑源文数量。

## 每张图的实际位置与用途

所有资产位于`website/assets/diagrams/`。C类在`concepts/`下，A类在`advanced/`下。

| 图资产 | 逻辑源文位置数 | 生成映射 | 基线位置/题号 | 用途与处理边界 |
| --- | ---: | ---: | --- | --- |
| [C1-capability-map.png](../website/assets/diagrams/concepts/C1-capability-map.png) | 3 | 1 | `README.md:28`<br>`docs/foundations/01-agent-and-llm.md:41` Q001<br>`learning/01-system-map.md:42` | 常见能力总览；主图归基础01，首页和题源改链接。 |
| [C2-model-context.png](../website/assets/diagrams/concepts/C2-model-context.png) | 2 | 1 | `docs/foundations/01-agent-and-llm.md:56` Q001<br>`learning/01-system-map.md:59` | 模型当前输入；主图归基础01，Q001保留职责解释。 |
| [C3-tool-interface.png](../website/assets/diagrams/concepts/C3-tool-interface.png) | 4 | 3 | `docs/foundations/01-agent-and-llm.md:66` Q001<br>`docs/foundations/04-tools-memory-protocols.md:21` Q025<br>`docs/foundations/04-tools-memory-protocols.md:65` Q026<br>`learning/01-system-map.md:75` | 声明、请求与执行；Q001/Q025/Q026不再用同图铺陈三次。 |
| [C4-memory-context.png](../website/assets/diagrams/concepts/C4-memory-context.png) | 6 | 5 | `docs/advanced/03-context-engineering.md:30` Q063<br>`docs/foundations/01-agent-and-llm.md:76` Q001<br>`docs/foundations/02-planning-and-orchestration.md:109` Q011<br>`docs/foundations/04-tools-memory-protocols.md:239` Q030<br>`docs/foundations/04-tools-memory-protocols.md:287` Q031<br>`learning/01-system-map.md:91` | 保存与可见范围；状态、记忆、摘要题分别做范围辨析或失效诊断。 |
| [C5-planning-feedback.png](../website/assets/diagrams/concepts/C5-planning-feedback.png) | 4 | 2 | `advanced/07-multi-agent-systems.md:83`<br>`docs/foundations/01-agent-and-llm.md:86` Q001<br>`docs/foundations/02-planning-and-orchestration.md:193` Q013<br>`learning/01-system-map.md:111` | 两地依赖与反馈；主图归基础01，进阶和Q013考控制/并发条件。 |
| [C6-runtime-boundary.png](../website/assets/diagrams/concepts/C6-runtime-boundary.png) | 5 | 4 | `docs/advanced/01-harness-and-deep-agents.md:21` Q057<br>`docs/engineering/07-system-design-and-projects.md:19` Q049<br>`docs/foundations/01-agent-and-llm.md:96` Q001<br>`docs/foundations/02-planning-and-orchestration.md:21` Q009<br>`learning/01-system-map.md:127` | 运行时边界；系统定义、循环、系统设计与Harness题各自用合同推理。 |
| [G1-system-flow.png](../website/assets/diagrams/G1-system-flow.png) | 2 | 0 | `advanced/01-harness-and-deep-agents.md:71`<br>`learning/00-first-agent.md:13` | 首次任务系统总览；主图归learning/00，进阶01改原理图链接。 |
| [G2-model-output.png](../website/assets/diagrams/G2-model-output.png) | 1 | 0 | `learning/02-llm-primer.md:19` | 模型生成机制；主图归基础02，无跨源重复。 |
| [G3-tool-roundtrip.png](../website/assets/diagrams/G3-tool-roundtrip.png) | 5 | 1 | `docs/engineering/05-evaluation-and-observability.md:193` Q037<br>`examples/policy_agent/README.md:26`<br>`learning/00-first-agent.md:42`<br>`learning/04-agent-loop.md:27`<br>`learning/05-tools-and-mcp.md:120` | 工具往返；主图归基础04，入门、工具、实验说明与trace题改链接。 |
| [G4-mcp-connections.png](../website/assets/diagrams/G4-mcp-connections.png) | 4 | 2 | `advanced/05-tool-routing-and-mcp.md:82`<br>`docs/foundations/04-tools-memory-protocols.md:151` Q028<br>`docs/foundations/04-tools-memory-protocols.md:195` Q029<br>`learning/05-tools-and-mcp.md:126` | MCP连接角色；主图归基础05，进阶路由与Q028/Q029保留各自推理。 |
| [G5-rag-pipelines.png](../website/assets/diagrams/G5-rag-pipelines.png) | 5 | 3 | `advanced/06-agentic-rag.md:53`<br>`docs/advanced/06-agentic-rag.md:21` Q072<br>`docs/foundations/03-rag-and-search.md:23` Q017<br>`docs/foundations/03-rag-and-search.md:321` Q024<br>`learning/06-rag-and-retrieval.md:49` | 入库/查询总览；主图归基础06，进阶及Q017/Q024/Q072不再嵌同一总图。 |
| [G6-state-memory.png](../website/assets/diagrams/G6-state-memory.png) | 2 | 0 | `advanced/04-memory-and-skills.md:75`<br>`learning/07-memory-and-state.md:58` | 事实修订与输入；主图归基础07，进阶04用双时间机制展开。 |
| [G7-planning-compare.png](../website/assets/diagrams/G7-planning-compare.png) | 2 | 1 | `docs/foundations/02-planning-and-orchestration.md:65` Q010<br>`learning/08-planning-and-multi-agent.md:52` | 交错与显式计划对照；主图归基础08，Q010转向控制方式比较。 |
| [G8-write-recovery.png](../website/assets/diagrams/G8-write-recovery.png) | 7 | 4 | `advanced/02-durable-execution.md:62`<br>`docs/advanced/02-durable-execution.md:21` Q060<br>`docs/engineering/06-reliability-and-security.md:61` Q042<br>`docs/engineering/06-reliability-and-security.md:111` Q043<br>`docs/foundations/02-planning-and-orchestration.md:241` Q014<br>`examples/policy_agent/README.md:89`<br>`learning/10-reliability-and-security.md:61` | 远端提交/本地确认窗口；主图归基础10；审批题不再借该图代替批准机制。 |
| [A01-harness.png](../website/assets/diagrams/advanced/A01-harness.png) | 1 | 0 | `advanced/01-harness-and-deep-agents.md:65` | 对应进阶章的“一次跨会话交接怎样形成”机制图；只在该主学习章内嵌。 |
| [A02-recovery.png](../website/assets/diagrams/advanced/A02-recovery.png) | 1 | 0 | `advanced/02-durable-execution.md:56` | 对应进阶章的“工单创建与本地记账之间的窗口”机制图；只在该主学习章内嵌。 |
| [A03-context.png](../website/assets/diagrams/advanced/A03-context.png) | 1 | 0 | `advanced/03-context-engineering.md:37` | 对应进阶章的“大工具结果如何清理”机制图；只在该主学习章内嵌。 |
| [A04-memory-time.png](../website/assets/diagrams/advanced/A04-memory-time.png) | 1 | 0 | `advanced/04-memory-and-skills.md:37` | 对应进阶章的“事实何时有效，系统何时得知”机制图；只在该主学习章内嵌。 |
| [A05-tool-routing.png](../website/assets/diagrams/advanced/A05-tool-routing.png) | 1 | 0 | `advanced/05-tool-routing-and-mcp.md:31` | 对应进阶章的“把发现与执行分成两个阶段”机制图；只在该主学习章内嵌。 |
| [A06-evidence-loop.png](../website/assets/diagrams/advanced/A06-evidence-loop.png) | 1 | 0 | `advanced/06-agentic-rag.md:29` | 对应进阶章的“从问题分解走到证据依赖图”机制图；只在该主学习章内嵌。 |
| [A07-control.png](../website/assets/diagrams/advanced/A07-control.png) | 1 | 0 | `advanced/07-multi-agent-systems.md:29` | 对应进阶章的“Manager 与 handoff 的控制权不同”机制图；只在该主学习章内嵌。 |
| [A08-action-feedback.png](../website/assets/diagrams/advanced/A08-action-feedback.png) | 1 | 0 | `advanced/08-coding-and-computer-use.md:13` | 对应进阶章的“从工具循环走到代码与界面操作”机制图；只在该主学习章内嵌。 |
| [A09-evaluation.png](../website/assets/diagrams/advanced/A09-evaluation.png) | 1 | 0 | `advanced/09-evaluation-and-feedback.md:77` | 对应进阶章的“设计一次能解释的改进实验”机制图；只在该主学习章内嵌。 |
| [A10-critical-path.png](../website/assets/diagrams/advanced/A10-critical-path.png) | 1 | 0 | `advanced/10-performance-and-serving.md:36` | 对应进阶章的“用依赖图分析 Agent 延迟”机制图；只在该主学习章内嵌。 |
| [A11-trust-boundaries.png](../website/assets/diagrams/advanced/A11-trust-boundaries.png) | 1 | 0 | `advanced/11-security-and-governance.md:39` | 对应进阶章的“五种控制不要混成一个开关”机制图；只在该主学习章内嵌。 |
| [A12-training.png](../website/assets/diagrams/advanced/A12-training.png) | 1 | 0 | `advanced/12-agent-training.md:37` | 对应进阶章的“先确认你在优化哪一层”机制图；只在该主学习章内嵌。 |
| [A13-model-protocol.png](../website/assets/diagrams/advanced/A13-model-protocol.png) | 1 | 0 | `advanced/13-model-api-and-output-contracts.md:40` | 对应进阶章的“先读完两地住宿查询的完整往返”机制图；只在该主学习章内嵌。 |
| [A13B-stream-assembly.png](../website/assets/diagrams/advanced/A13B-stream-assembly.png) | 1 | 0 | `advanced/13-model-api-and-output-contracts.md:81` | 对应进阶章的“从网络字节逐层重组成工具参数”机制图；只在该主学习章内嵌。 |
| [A13C-output-validation.png](../website/assets/diagrams/advanced/A13C-output-validation.png) | 1 | 0 | `advanced/13-model-api-and-output-contracts.md:60` | 对应进阶章的“JSON、Schema 与业务事实分别保证什么”机制图；只在该主学习章内嵌。 |
| [A14-ingestion-lifecycle.png](../website/assets/diagrams/advanced/A14-ingestion-lifecycle.png) | 1 | 0 | `advanced/14-ingestion-and-index-lifecycle.md:80` | 对应进阶章的“在最后一步才让新索引可见”机制图；只在该主学习章内嵌。 |
| [A14B-effective-date-selection.png](../website/assets/diagrams/advanced/A14B-effective-date-selection.png) | 1 | 0 | `advanced/14-ingestion-and-index-lifecycle.md:48` | 对应进阶章的“生效时间与系统记录时间不能混用”机制图；只在该主学习章内嵌。 |
| [A14C-staging-recovery.png](../website/assets/diagrams/advanced/A14C-staging-recovery.png) | 1 | 0 | `advanced/14-ingestion-and-index-lifecycle.md:88` | 对应进阶章的“在最后一步才让新索引可见”机制图；只在该主学习章内嵌。 |
| [A15-sql-validation.png](../website/assets/diagrams/advanced/A15-sql-validation.png) | 1 | 0 | `advanced/15-text-to-sql-and-data-analysis.md:71` | 对应进阶章的“让数据库执行层约束候选”机制图；只在该主学习章内嵌。 |
| [A15B-comparable-denominator.png](../website/assets/diagrams/advanced/A15B-comparable-denominator.png) | 1 | 0 | `advanced/15-text-to-sql-and-data-analysis.md:63` | 对应进阶章的“空值、撤销和比例怎样共同影响结果”机制图；只在该主学习章内嵌。 |
| [A15C-scoped-sql-execution.png](../website/assets/diagrams/advanced/A15C-scoped-sql-execution.png) | 1 | 0 | `advanced/15-text-to-sql-and-data-analysis.md:88` | 对应进阶章的“让数据库执行层约束候选”机制图；只在该主学习章内嵌。 |
| [A16-task-service.png](../website/assets/diagrams/advanced/A16-task-service.png) | 1 | 0 | `advanced/16-service-deployment-and-operations.md:114` | 对应进阶章的“16B：加入批准、写入与恢复”机制图；只在该主学习章内嵌。 |
| [A16B-task-clarification.png](../website/assets/diagrams/advanced/A16B-task-clarification.png) | 1 | 0 | `advanced/16-service-deployment-and-operations.md:81` | 对应进阶章的“固定内容版本，仍使用当前文档授权”机制图；只在该主学习章内嵌。 |
| [A16C-release-binding.png](../website/assets/diagrams/advanced/A16C-release-binding.png) | 1 | 0 | `advanced/16-service-deployment-and-operations.md:166` | 对应进阶章的“运行版本、发布与回退怎样一起管理”机制图；只在该主学习章内嵌。 |
| [A17-event-dispatch.png](../website/assets/diagrams/advanced/A17-event-dispatch.png) | 1 | 0 | `advanced/17-event-driven-and-proactive-agents.md:15` | 对应进阶章的“从一个事件到一个可解释的任务”机制图；只在该主学习章内嵌。 |
| [A17B-debounce-window.png](../website/assets/diagrams/advanced/A17B-debounce-window.png) | 1 | 0 | `advanced/17-event-driven-and-proactive-agents.md:55` | 对应进阶章的“去抖、合并、循环和预算”机制图；只在该主学习章内嵌。 |
| [A17C-ack-replay.png](../website/assets/diagrams/advanced/A17C-ack-replay.png) | 1 | 0 | `advanced/17-event-driven-and-proactive-agents.md:75` | 对应进阶章的“处理成功但确认丢失”机制图；只在该主学习章内嵌。 |
| [A18-media-interruption.png](../website/assets/diagrams/advanced/A18-media-interruption.png) | 1 | 0 | `advanced/18-multimodal-and-realtime-agents.md:42` | 对应进阶章的“临时转写与最终条件”机制图；只在该主学习章内嵌。 |
| [A18B-evidence-confirmation.png](../website/assets/diagrams/advanced/A18B-evidence-confirmation.png) | 1 | 0 | `advanced/18-multimodal-and-realtime-agents.md:32` | 对应进阶章的“用位置让证据可以回查”机制图；只在该主学习章内嵌。 |
| [A18C-generation-routing.png](../website/assets/diagrams/advanced/A18C-generation-routing.png) | 1 | 0 | `advanced/18-multimodal-and-realtime-agents.md:73` | 对应进阶章的“已生成、待播放、已播放是三个进度”机制图；只在该主学习章内嵌。 |

## 文本与同案例推导的人工复核

图片相同容易机械识别，换一种措辞重复案例则需要检查新增推导。文本候选筛查仅用于定位；同一术语在三个栏目出现，并不自动说明内容冗余。

| 高频主题 | 必要复现与已有差异 | 本轮识别的问题与处理 |
| --- | --- | --- |
| 检索/RAG | 基础解释数据结构与计算；进阶应新增证据状态、查询选择、停止及复杂索引；题目检查读者能否诊断 | G5被多次拿来支持相近的住宿案例，却不能解释BM25、向量表示、候选上限或阶段指标。本轮重写Q017–Q024，用不同认知任务替换总流程复述。基础06/进阶06正文由各负责人补机制，不把同一图改图注当成进阶。 |
| 工具回填 | 基础04需要完整一轮；进阶13需要多ID、流式边界与终态 | Q094原实战案例再次复述两城700/650正常往返。本轮改为倒序、缺失、重复、陌生ID的诊断表，特别说明集合相等仍可能重复，避免把正常案例再讲一遍。 |
| 上下文/记忆 | 当前输入、任务状态与跨会话范围的短定义需复现；摘要失效和双时间属于新增机制 | Q030原长段重讲“长期不等于持久”。本轮用SQLite持久任务状态与内存跨会话store的反向对照，要求从实现条件辨认逻辑范围。Q031保留单轮摘要合同，Q063保留多轮依赖/撤权推理，不重复整幅记忆图。 |
| 恢复窗口 | Q014解释本地/远端两份事实；Q046读日志；Q060处理迟到回包与恢复查询 | 重复G8没有增加这些差异；Q043批准题中该图甚至不展示批准步骤。本轮移除题源图片和空泛读图句，保留故障窗口、日志、并发归并和具体批准的不同任务。 |
| Agent组成 | 基础01需要连续建立全景；Q001应检验控制路径判断 | Q001再次完整复述650与700的正常链。本轮将案例换为正常轨迹相同的两个实现，要求查看控制规则与模型动作请求来判断，不能凭工具次数分类。 |
| 训练定义与来源 | SFT/DPO定义在基础、进阶、题解需要简短回查；具体版本说明要一致 | 长段候选筛查会提示训练路线与Lightning版本说明相近。人工复核将定义和固定来源事实保留为必要复现，未用相似分数要求删掉正确版本边界。 |

基线的长段候选筛查在去链接/空白后的跨栏目段落中定位了训练定义与Lightning版本说明；它没有覆盖上述大量同案例、改写式冗余。因此不能以“没有长段完全一致”宣布没有重复，也不能以候选分数直接判定抄写。

## 本轮题源实际完成的修改

技术写作负责人在题源中移除26次重复整图嵌入，均改为主学习章相应节的短链接；Q072的1次嵌入由进阶RAG负责人处理。主审随后通过生成器同步独立题页，没有手工编辑生成题页。题解仍保留定义、机制、三个已回答追问、实战案例、误区与可验证练习。

Q017–Q024的职责分别为：输入/输出与失败边界；检索单元及阅读上下文；BM25与dense匹配信号；候选覆盖上限与重排；ANN/过滤/预算；内容版本与当前catalog；近邻/任务证据/排序/grounding指标；给定中间产物的分层排障。数值与集合是手工教学设定，不写成真实检索成绩。

本轮作者源文的38处移图已落盘：技术写作负责人处理26处题源，进阶RAG负责人处理进阶06与Q072共2处，其他进阶正文负责人处理5处，主审处理首页与入门/实验入口5处。主审机器审计确认当前44张图对应44个作者内嵌位置，主图所有权违规为0。生成题页已同步去除基线27次影子内嵌；不将它们再次统计成作者冗余。最终站点HTML共有44处正文图示嵌入，G5只出现在基础06。

全部题源落盘后，`check_repo.py --write-index`已刷新110道题，随后只读检查通过；与基线逐一比较，110个题号和题目标题均未改变。RRF分数、候选集合覆盖和RR/MRR算例已独立复算，差异空白检查通过。

全仓306项单元测试通过，其中新增检索实验13项、内容审计11项。检索、基础数学、运行时三个实验CLI运行通过；44组SVG源图/发布图和44张PNG检查通过。MkDocs严格构建通过，站点检查覆盖203个HTML页面、44,866处本地引用及110道独立题页；浏览器抽查了进阶RAG正文的导航与排版。

当前规范化后不少于120字符的长段落完全重复组为0，5-gram Jaccard不小于0.85的候选为0；这些只是指定扫描口径的结果，不能推出语义冗余为0，更不能据此宣布全部知识质量通过。尚未开展陌生读者阅读实测，也没有运行真实嵌入模型、ANN索引或GraphRAG效果基准；教学实验的手工数值不代表生产检索收益。

## 基础06与进阶06的只读交叉复核

复核对象是本轮修订后的正文及其题源衔接，不运行真实检索模型，也不把程序通过当作可读性实测。

- 基础06将文档身份、可独立返回的chunk与查找结构index分开；分别解释词项/向量召回、RRF融合和已有候选的重排，给出各自输入、输出与不能修复的遗漏。另行区分相关、适用、真冲突和缺少必要证据，住宿例子缩为一个最小核对案例。
- 进阶06补充可推演的算法和诊断：BM25词频饱和与长度归一、未归一向量的度量排序反例、HNSW探索队列与IVF列表、后过滤的候选饥饿、重排集合上限、冲突的可信优先关系、带证据状态与预算的停止，以及oracle分层替换。内容已增加机制推导，仍待读者试读验证理解效果。
- 交叉复核发现进阶曾复用基础的RRF手算，现已改为候选窗口截断及重复通道隐式加权的失效对照；扩大候选窗口只说明候选预算变化，不直接声称延迟按比例变化。
- 交叉复核发现候选集合曾混用筛选前后含义，现已明确`D_scope → C_raw → C_valid`；同时修正查询/索引分析器的兼容条件，补充ANN同距近邻的计分边界。

以上意见已由正文负责人和主审修正，并纳入最终生成与构建检查。复核确认机制增量，不宣称初学者必定已经学会。

## 可执行审计的正确边界

主图所有权应配置为：C1–C6归基础01；G1归learning/00；G2–G8分别归基础02、04、05、06、07、08、10；A类归对应进阶章节。非主位置可以链接该章节，不重复内嵌。新增独立机制图应证明它解释的是新的关系，不能只给同一总图换名称。

审计工具应报告canonical资产、作者源文位置、所在题号/小节与生成映射；站点构建产物另列。规范化长段完全相同或高相似候选仅进入人工复核，保留原文与上下文，不自动删除，不把关键词数量或“重复率下降”当作学习效果证据。

基础章负责从概念建立到机制算例，进阶章负责新增约束下的状态、决策或索引机制，题目负责改变条件、辨析边界与定位故障。三者可以共享术语与必要的短定义；若读者只是再次看到相同金额比较或同一条正常工具链，没有获得新的判断任务，就需要压缩或改写。
