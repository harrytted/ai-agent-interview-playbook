# A13–A18 内置图片生成提示词

生成方式：OpenAI 内置 `image_gen`，每章独立生成一张 PNG。读者图片采用原始生成文件；SVG只作流程语义草图，不作为PNG的转换来源。下列记录初稿完整提示词，文末列出最终文件与审核结果，重新生成的完整提示词见[流程修订记录](advanced-imagegen-A13-A18-revisions.md)。

## A13 A13-model-protocol

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “模型往返：完整回填，再核验”.
Layout: one spacious clockwise TOOL ROUNDTRIP in the upper two thirds, plus a separate final-answer validation route below. Main stations left to right: a task paper labeled “任务输入”, a model interface station “模型响应”, an inspection gate “宿主校验”, a tool execution machine “工具执行”, and a paired-result tray “按 ID 回填”. Solid teal arrows: task→model; model→gate arrow labeled “工具请求”; gate→tool; tool→result tray. The result tray contains TWO result slips marked “call-1” and “call-2”. A clearly visible return arrow from the tray back to the SAME model station is labeled “再次请求”. Do not draw the tool results bypassing the model or becoming a user answer directly.
Separate lower route: model station emits “最终回答” down to a magnifying validation station “独立核验”, then right to a delivered report “交付结果”. No path can reach delivery without independent validation. Small gate sublabel: “参数 · 权限 · 预算”.
A modest orange branch/banner, clearly separated from success, reads exactly “截断 / 拒答 / 断流 → 停止并记录”. It applies to every model round. Show no green success mark on this failure branch.
Keep the loop arrow, final-answer branch and failure banner visually distinct; use at most the exact labels above.
```

## A14 A14-ingestion-lifecycle

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “知识摄取：校验后发布，按权限查询”.
A clearly legible left-to-right pipeline of SIX physical stations: source documents “原始资料” → a parser/cutter retaining table headings “解析分块” → a staging tray “持久暂存” → a complete candidate index cabinet “完整候选” → an inspection/publication gate “校验后发布” → a query magnifier over a report “查询结果”.
Source documents have the readable short sublabel “身份 · 日期 · 权限”. Parsed strips retain a table header beside its amount; never illustrate a naked detached amount. Under the parser, a small connected provenance slip is labeled “块 ID · 来源位置”. Only a validated complete candidate may cross the publication gate. A solid pointer/selector after the gate visibly selects the active complete index.
Below the pipeline is a separate older index cabinet labeled “旧索引”. An orange interruption marker on the staging route points to a short note “中断时继续可读” beside the old index. Do not imply partial staging is visible to readers.
At the query stage, show TWO independent filter tabs clearly labeled “业务日期” and “当前权限”. A small update route from source changes back to staging is labeled “更新 / 删除”. A permissions card feeds the current-permission filter directly, labeled “撤权”.
Footer exact: “回退索引，不回退当前权限”. No arrow may bypass the date/permission filters. Do not depict embeddings, graph databases or OCR as implemented.
```

## A15 A15-sql-validation

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “SQL 分析：先定口径，再核对结果”.
Use a clear horizontal main flow with SIX stations: a business-question card “口径确认” → a schema/table relationship sheet “结构映射” → a candidate query card “SQL 候选” → a locked SQLite-shaped execution module “只读执行” → a separate magnifying checker “独立核验” → a final report “带依据结论”. Main arrows have one consistent left-to-right direction.
A small orange execution-error feedback loop goes ONLY from the execution module back to the candidate card, labeled “有限修复”. A blocked stub at execution is labeled “越权 / 超限 → 停止”. Do not feed an expected answer to SQL generation.
A separate sealed expected-results tray labeled “独立期望” connects ONLY to “独立核验”, never to schema mapping or candidate generation. Show the database result table going from execution to independent checking.
Bottom third contains an exact hand-calculable JOIN-grain example in two equal areas. Left, orange repeated application slips, label “一对多 JOIN 放大” and equation “650 × 2 + 700 = 2000”. Right, teal unique-application slips, label “按申请粒度” and equation “650 + 700 = 1350”. These numbers are yuan, not cents; do not add any other numbers. Never label the 2000 result correct, and never portray SUM DISTINCT as a general solution.
Use clear arrows and large Chinese text; preserve independent expected-results isolation.
```

## A16 A16-task-service

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “任务服务：先可靠接收，再确认结果”.
Draw one clear main left-to-right lifecycle across the middle using SEVEN compact physical stations with large labels: “提交任务” → “持久接收” (a database ledger) → “Worker” → “写准备” → “派发提交点” (a sharply distinct dispatch gate) → “业务对象” (a separate service/database) → “结果确认” (a checked report).
Below the receiving ledger a receipt reads “202 仅表示接收”; it is connected ONLY to the ledger, never to the final success check. Below Worker a waiting tray “补参 / 批准” has a return arrow to Worker. Do not imply user approval occurs after creating the business object.
A small orange cancellation tag at “写准备” reads “此处仍可取消”. Immediately after “派发提交点” an orange annotation reads “派发后先核对”. No cancellation arrow may delete a business object or automatically mean it never existed.
From the gap between business-object submission and local result confirmation, show a lower orange branch: “结果未知” → a lookup magnifier “原意图对账” → rejoin “结果确认” only when the existing business object is confirmed. Beside the lookup route, exact short label “保留操作 ID”. Do not route unknown outcomes back to a NEW task or create a new operation ID.
Footer: “请求成功，不等于业务成功”. Arrange branches with ample space and avoid crossing unrelated arrows. This is a mechanism diagram, not a full state machine.
```

## A17 A17-event-dispatch

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “事件触发：先判资格，再派发”.
Six primary physical stations in a clean left-to-right pipeline: incoming event slip “事件” → a durable inbox ledger “接收账本” → an object/version sorter “版本归并” → a controlled inspection gate “派发检查” → a durable work folder “持久任务” → a local outbox tray “本地 Outbox”. Above the first ledger use the short sublabel “ID 与指纹”. The arrow from task to Outbox is labeled “通知条件”.
At the dispatch gate, THREE separate visible checks read “有效订阅”, “业务授权”, “剩余预算”; one small timer beside the gate reads “去抖”. No bypass arrow.
From the inbox, a duplicate event loops back to the SAME ledger and stops, label “重复不重派”. From the version sorter an orange side tray reads “旧版忽略 / 冲突隔离”; a closed stop barrier under conflict reads “等待可信更高版”. A small fresh higher-version slip may return from that barrier to the version sorter, never overwrite current state with an older version.
A cancellation tag before dispatch reads “取消订阅 → 停止新派发”. It must not connect backwards to delete accepted tasks or erase audit history.
Footer exact: “本地待发 ≠ 外部送达”. Do not draw external email delivery, social notifications or a guaranteed recipient receipt. Short readable Chinese labels, clean arrow direction.
```

## A18 A18-media-interruption

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished raster process illustration for a Chinese AI Agent engineering handbook, landscape 1536x1024. Match a restrained existing textbook series: white/off-white background, large dark-navy Chinese title and crisp front-facing Chinese labels, teal/blue physical teaching objects (document trays, ledgers, inspection gates, query lenses, small server modules), subtle matte three-dimensional relief and soft contact shadows, generous whitespace, sparing orange for blocked/unknown/error branches. The physical objects support an explicit, technically correct flowchart: unambiguous arrowheads and clearly separated branches are essential. Use short, large labels rather than dense explanatory prose. No robots, brains, ornamental circuits, tiny pseudo-code, invented performance scores, watermarks, decorative clutter, or arrowless concept collage. Main labels must remain readable when the whole 1536px image is displayed at 900px width. Render every supplied Chinese phrase verbatim, never invent explanatory text. Keep 60px outer margins; no clipped objects or text. This is a teaching diagram, not a claim of production deployment.

Exact title: “媒体交互：条件要更新，播放可打断”.
Make TWO clearly separated horizontal teaching lanes with front-facing large labels, no dense paragraphs.
UPPER LANE, business evidence: a receipt image with highlighted region plus a short waveform/transcript card labeled “媒体证据” → confirmed conditions card “确认条件 v2” with city “云洲” → query card “工具请求 v2” → an inspection lens “核对版本” → final report “当前结论”. On the final report exactly “票据 650 / 上限 650” and “不超标”. A small obsolete-result slip labeled “旧 v1 结果” is diverted to a gray archive “仅留日志”, NEVER to the current report. The source transcript card has the short label “人工转写”, so it cannot imply real ASR was measured.
LOWER LANE, output playback: an audio stack labeled “生成 4 秒” and marked “g1” → a speaker/progress station “实际播放 1.25 秒” → a clear orange stop switch “打断停播” → a retained media strip labeled “保留 0–1.25 秒”. Do not draw a time axis or duration-proportional graph; the precise numbers are expressed by labels only. A late g1 audio slip meets a closed barrier labeled “旧代次不复活”; a distinct fresh slip “新输出 g2” may start a new playback, not restart cancelled g1.
Footer exact: “媒体时钟 ≠ 实际听见”. The image explains state and media position, not OCR/ASR/TTS accuracy. No human speaking portrait or fake measured latency. Maintain clear lane separation and unambiguous arrows.
```

## 最终采用与审核 · 2026-11-01

六张发布图均保留内置生成器的原始1536×1024 PNG，未缩放或叠加文字；文件尺寸与SHA-256见[清单](imagegen-manifest.json)。A13、A14采用初稿，A15–A18采用[修订提示词](advanced-imagegen-A13-A18-revisions.md)生成的版本。

| 图 | 仓库发布路径 | 原始生成文件 |
| --- | --- | --- |
| A13 | `website/assets/diagrams/advanced/A13-model-protocol.png` | `exec-7e1bb4d2-ddaa-44e4-b442-2da0ef4280af.png` |
| A14 | `website/assets/diagrams/advanced/A14-ingestion-lifecycle.png` | `exec-68096475-085d-447a-8d29-dcc6bc00587b.png` |
| A15 | `website/assets/diagrams/advanced/A15-sql-validation.png` | `exec-80db7246-b3a6-45de-8d9f-aefb486f3606.png` |
| A16 | `website/assets/diagrams/advanced/A16-task-service.png` | `exec-de2ada1d-6d37-4678-b47a-bf491a2b792d.png` |
| A17 | `website/assets/diagrams/advanced/A17-event-dispatch.png` | `exec-96157986-2d11-45ef-84e6-c65e690d3259.png` |
| A18 | `website/assets/diagrams/advanced/A18-media-interruption.png` | `exec-940ee159-a3c9-4fae-831c-aba31ee9f3a2.png` |

逐图核对中文、流程方向、数值与正文：

- A13：工具结果按调用ID回填模型；正常最终回答再独立核验。截断、拒答和断流进入停止记录。
- A14：保留初稿，旧索引明确经过当前权限过滤；第二站的表格片段表示解析分块，正文图解补全站名。重新生成的 `exec-4a0e6acb-cb5e-4249-86e7-f3984f974f6d.png` 未采用，因为撤权标签落在正向查询路线，容易误读。
- A15：独立期望只进入核验器；一个A申请分成两条明细，2000与1350两种计算方式符合正文。图中没有双650的SUM DISTINCT反例，该反例仍由正文解释。
- A16：202只表示接收，写准备仍可取消。对账分为“查到且一致”和“未查到／仍不确定”，后者保持未知。
- A17：旧版忽略是独立终点；同版冲突才隔离并等待可信更高版。取消只停止新派发，本地Outbox不代表外部送达。
- A18：确认条件是城市和金额，政策上限在工具结果后比较；旧v1结果经版本核对只留日志。播放1.25秒与生成4秒分别表述，旧输出代次不复活。

章节图片入口保留替代文字与正文说明，沿用当前页面点击放大功能。SVG源文件及发布副本仅作静态语义草图，与PNG不要求像素一致。
