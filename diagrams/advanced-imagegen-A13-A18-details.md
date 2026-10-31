# 13–18章补充机制图：内置图片生成记录

2026-11-01：每章在原总览图之外新增两张机制图，共12张，插入相应机制段落。全部面向读者的PNG由OpenAI内置imagegen独立生成，原始文件直接保存；SVG仅作为语义草图。图中的来源、数值和状态边界以本地章节与实验为依据，不把示意图当作模型或生产效果实测。

## A13B · 流式输入：先组装，再决定

目标：网络字节、UTF-8、SSE、内容块与整条消息结束的分层重组。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “流式输入：先组装，再决定”. Use a left-to-right five-stage pipeline with short two-line labels: “网络字节” → “UTF-8 解码” → “SSE 事件” → “内容块拼接” → “完整消息检查”. Byte cards become Chinese text, then event cards, then grouped tool argument slips. Below first stages respectively show short labels “跨读保留”, “空行分隔”, “按块索引”. From 完整消息检查 one teal conditional arrow “正常工具结束” leads to a host inspection gate “参数与权限校验” then “允许调度”. A separate ORANGE arrow from 完整消息检查 leads to terminal “截断 / 拒答 / 断流” then “停止并记录”. These are alternatives, never a serial success path. No earlier stage may have an arrow to execution. Footer “一个网络分块，不等于一个完整响应”. Do not show execution before the whole message termination has been checked.
```

## A13C · 输出验收：格式通过只是第一关

目标：JSON语法、结构合同、证据一致性与目标覆盖的分层验收。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “输出验收：格式通过只是第一关”. Four numbered inspection stations on one clear main route: “JSON 语法” → “字段与类型” → “证据一致” → “目标覆盖” → final checked document “交付结果”. Main arrows are conditional pass, not automatic. Under each of the FOUR gates put a short orange downward branch to its own terminal slip, respectively “无法解析”, “结构不符”, “主张不符”, “缺少回答”. No failure slip reconnects to delivery. Below the third gate a pair of large comparison cards reads “模型主张：7000” and “实际条款：700”, separated by orange “不一致”. Connect this example ONLY to the third gate’s failure slip 主张不符. Do not suggest valid JSON or correct integer types prove a factual claim. Footer “结构合法，仍需核对事实与问题覆盖”. Exact short labels only; reserve the lower half for the numeric counterexample.
```

## A14B · 业务日期决定适用版本

目标：规范业务日期、左闭右开版本区间与650元的不同判断。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “业务日期决定适用版本”. Two independent horizontal lanes, NOT a single chronological execution chain. At top a shared tiny policy reference has TWO readable rows: “v1：2026-01-01 ≤ 日期 < 2026-11-01” and “v2：2026-11-01 起”. Upper lane: calendar “出差 2026-10-31” → document “匹配 v1” → limit card “上限 600 元” → orange comparison “650 > 600” → “超标”. Lower lane: calendar “出差 2026-11-12” → document “匹配 v2” → limit card “上限 700 元” → teal comparison “650 ≤ 700” → “未超标”. The lodging amount is the SAME “住宿 650 元” in both lanes; show a shared amount badge if helpful. Do not connect one lane’s result to the other. Footer “先校验 YYYY-MM-DD，再按出差日期匹配”. No upload-time rule, no claim that newest-uploaded equals applicable, no extra amounts.
```

## A14C · 中断恢复：复用暂存，完整后发布

目标：磁盘暂存跨实例复用、旧索引可读及校验后的发布点。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “中断恢复：复用暂存，完整后发布”. Main diagram has two logical phases separated by a visible orange restart break. Before break: document “解析变化源” → disk tray “持久暂存” → orange “进程中断”. After break: fresh small service “新实例重启” → disk tray “读取暂存” → workspace “只处理剩余资料” → complete cabinet “完整候选” → gate “校验后发布”. Draw a restart arrow from 进程中断 to 新实例重启, not a success arrow into publication. Show a separate blue “旧索引” cabinet BELOW the early steps with a short path to “继续查询”; the query route remains separate from staging and candidate. No line from partial staging or incomplete candidate reaches readers. Only after the publication gate may a short teal pointer say “切换可见索引”. Footer “暂存是恢复进度，不是可见索引”. Keep the count of objects small; no changed monetary amounts or invented stages.
```

## A15B · 超标比例：先筛可比较的申请

目标：未知金额或上限不进入分母，三笔申请仅一笔可比较。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “超标比例：先筛可比较的申请”. The upper half shows exactly THREE equally sized application cards from the missing-values teaching dataset: “a1：金额 650 / 上限 500”, “a4：金额未知 / 上限 700”, “a5：金额 100 / 上限未知”. All amounts are in yuan; do not invent other rows. All three feed a central inspection funnel “金额与上限都已知？”. Only a1 goes through a teal YES path to a tray “可比较 1 笔”. a4 and a5 follow a GRAY NO path to a separate tray “未知 2 笔”, with a clear stop, not treated as compliant. From 可比较1笔 continue to “超标 1 笔” and a large formula “1 ÷ 1 = 100%”. A separate bottom summary badge reads “申请 3 笔 · 已知金额 750 元”. Footer “未知项不按未超标计入分母”. This is a filtering flow, NOT a pie chart. Do not route all three into the denominator or claim 33.3% is this metric.
```

## A15C · SQL 执行：先限定数据，再限定动作

目标：可信身份限定行范围、独立SQLite快照及列操作资源约束。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “SQL 执行：先限定数据，再限定动作”. Layout TWO short connected rows that separate host preparation from candidate execution. Upper host row: “可信身份” → “宿主筛选允许行” → “独立 SQLite 快照”. A separate source cabinet “只读源库” feeds ONLY 宿主筛选允许行, not the candidate. Under the source cabinet an excluded slip reads “薪资不复制”. Lower candidate row starts “候选 SQL” → inspection gate “表列 / 函数 / 操作校验” → timer gate “步数 / 时间 / 行数预算” → “返回结果”. Draw a clear data connection from 独立SQLite快照 into the checked execution region in the lower row. Orange stop branches from BOTH gates terminate at “拒绝 / 停止”. At bottom one short note “去掉 WHERE，也仍只读当前快照”. No candidate-to-source arrow. No user-selectable tenant arrow. No claim that query_only gives tenant isolation, PostgreSQL RLS, or OS sandboxing. Footer “宿主先限定行，执行器再检查动作”.
```

## A16B · 缺少日期时，同一任务怎样继续

目标：接收、持久等待、补日期、重新排队与累计预算延续。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “缺少日期时，同一任务怎样继续”. Main flow “可靠接收” → “已排队” → decision gate “日期齐全？” → YES route “读取制度” → “有证据回答”. Under 可靠接收 hangs a small receipt “202 + 任务 ID”. The decision NO branch goes downward to a durable ledger “等待补日期”, then right to input slip “收到日期回复”, then a clear loop returns to the SAME 已排队 node. Label the loop “沿用原任务”. Keep waiting and reply away from the success branch; no new task is created by the reply. A small storage symbol under 等待补日期 says “重启后仍保留”. Footer “任务 ID 不变，预算持续累计”. Do not reset budget, execute without date, imply 202 means answered, or draw a new task identifier after reply.
```

## A16C · 发布切换新入口，任务保留原版本

目标：固定验收、不可变版本登记、激活与回退只影响新任务。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “发布切换新入口，任务保留原版本”. Two clearly separate horizontal lanes. UPPER existing-task lane, heading “已有任务”: “任务绑定 v1” → locked manifest “原清单 v1” → “继续使用 v1”. NO arrows from a release switch into this lane. LOWER release lane, heading “新任务入口”: “候选 v2” → “固定验收” → “登记 v2” → switch “激活 v2” → “新任务用 v2”. From 固定验收 an orange failure branch “验收失败” stops before registration and activation. Under the switch a separate short rollback route reads “回退 v1” → “后续新任务用 v1”; it does NOT change existing tasks, delete objects, or migrate in-flight state. A small label near registration says “版本不可覆盖”. Footer “固定验收不等于全面质量保证”. No production canary rollout or automatic compensation claim. Clear arrows and no intersecting lanes.
```

## A17B · 去抖：等最新版本的安静窗口

目标：5个逻辑秒去抖、持久合并与显式flush的到期派发。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “去抖：等最新版本的安静窗口”. Main route of three stations: event card “第 0 秒：收到 v2” → update card “第 2 秒：收到 v3” → persistent ledger “最新待办：v3 / 第 7 秒到期”. Use a small clock badge “窗口 5 秒” beside the ledger. Below ledger a query gate “flush 检查”. It has TWO separate conditional outcomes: “第 6 秒” → gray terminal “继续等待”; “第 7 秒” → teal task tray “只接受 v3 的 1 项任务”. Both check arrows originate from the same pending ledger/gate, and the gray waiting terminal cannot enter the accepted-task tray directly. Use logical time labels, not a quantitatively scaled time axis. Footer “持久待办不会自动派发，需显式 flush”. Do not imply the CLI runs a resident scheduler, do not dispatch v2 at second5 after v3 has arrived, do not show 2 tasks.
```

## A17C · 保存后确认丢失，重投怎样处理

目标：任务预算Outbox事务提交后的确认丢失、重开账本与幂等重投。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “保存后确认丢失，重投怎样处理”. Top left a clearly outlined boundary “本地事务已提交” contains exactly THREE short cards: “任务 1 项”, “预算扣 1 次”, “本地待发 1 条”. From this committed boundary an arrow reaches a broken ACK card “确认前中断”. A restart route continues “重启同一数据库” → “重投同一事件” → magnifying ledger “查接收账本” → “补记确认”. Do NOT draw another task-creation branch after 查接收账本. Above or below the replay route a large concise result badge reads “任务仍为 1 · 预算仅扣 1”. A local Outbox card must be labeled “本地待发”, never “已送达”. Footer “输入确认与外部送达是两件事”. This depicts a sequential local SQLite teaching case, not a real broker or distributed exactly-once proof. Avoid extra counts or external delivery icons.
```

## A18B · 先留证据，再核对最终条件

目标：媒体定位、临时转写不落业务事实以及金额冲突的澄清分支。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “先留证据，再核对最终条件”. Main left-to-right flow “原始媒体” → “带定位的证据” → “最终条件” → gate “金额一致且清晰？” → YES “继续查政策”. Show receipt and waveform source objects, and evidence slips labeled only “图像区域” and “音频秒数”. A separate gray branch from 原始媒体 goes to “临时转写” then terminal “仅作候选”; NO arrow from that terminal into business facts or draft. From the amount gate a separate orange NO branch leads to “金额冲突 / 模糊” then terminal “等待澄清”. Do not produce a supported draft from the uncertain branch. Under the gate a tiny numeric counterexample reads “票据 650 ≠ 转写 6500”, colored orange, and belongs only to the conflict branch. Footer “定位合法不等于内容正确；本例使用人工夹具”. Do not claim real OCR or ASR was executed. Keep arrows simple and separate.
```

## A18C · 先核对输出代次，再检查播放位置

目标：旧音频代次先过滤、当前代次时长与单调播放时钟校验。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “先核对输出代次，再检查播放位置”. Four-station main route: “播放事件” → first gate “当前代次且未取消？” → second gate “位置合法且未倒退？” → “更新播放时钟”. Teal YES arrows pass through both gates. From FIRST gate, a GRAY NO branch ends “忽略迟到事件”; this branch must never touch the second position gate. From SECOND gate, an orange NO branch ends “拒绝越界 / 倒退”. Near the first gate place a current-state card “当前 g2：时长 2 秒”. Lower half has TWO short, separate examples: gray “旧 g1：位置 3.8 秒” → “忽略”; teal “当前 g2：位置 0.5 秒” → “位置通过”. The old g1 position 3.8 MUST NOT be compared with g2’s 2 seconds or be called a g2 boundary error. Footer “旧代次先过滤，不污染当前时钟”. No speech recognition claim, no hearing measurement, no restarting cancelled output.
```


## 修订与最终采用 · 2026-11-01

12张发布图均为内置工具生成的原始1536×1024 PNG，无机械导出、缩放或后期文字叠加。文件哈希与尺寸见[清单](imagegen-manifest.json)。A13B和A18B采用下列修订提示词生成的新版本，其余采用初稿。

| 图 | 原始生成文件 | 发布路径 |
| --- | --- | --- |
| A13B | `exec-ba302f44-9429-4079-b9d8-a1d41f28ff19.png` | `website/assets/diagrams/advanced/A13B-stream-assembly.png` |
| A13C | `exec-1c91fd3d-aade-4925-9deb-e59987503545.png` | `website/assets/diagrams/advanced/A13C-output-validation.png` |
| A14B | `exec-539adb34-e96b-42cc-84f4-e03539a6f6b3.png` | `website/assets/diagrams/advanced/A14B-effective-date-selection.png` |
| A14C | `exec-71ae4570-b69e-4413-a435-cd0796e81fa5.png` | `website/assets/diagrams/advanced/A14C-staging-recovery.png` |
| A15B | `exec-d5bd564c-abc9-4e94-bed9-083927744fc1.png` | `website/assets/diagrams/advanced/A15B-comparable-denominator.png` |
| A15C | `exec-10dde974-25da-4eda-9999-e54ac8936fc7.png` | `website/assets/diagrams/advanced/A15C-scoped-sql-execution.png` |
| A16B | `exec-f0dbce5b-4a14-44d9-a936-1a12e5c08d5a.png` | `website/assets/diagrams/advanced/A16B-task-clarification.png` |
| A16C | `exec-cc6cdf6b-3b28-4672-879b-b5738c1e1af4.png` | `website/assets/diagrams/advanced/A16C-release-binding.png` |
| A17B | `exec-3510ae0f-c9d9-495f-a85f-75e9655e0270.png` | `website/assets/diagrams/advanced/A17B-debounce-window.png` |
| A17C | `exec-f848989e-0ba1-4788-852e-d1ceaed04a4e.png` | `website/assets/diagrams/advanced/A17C-ack-replay.png` |
| A18B | `exec-81602733-f850-4af7-a88a-853b718986b7.png` | `website/assets/diagrams/advanced/A18B-evidence-confirmation.png` |
| A18C | `exec-e14e183c-4504-46a8-a302-4dd815b713a0.png` | `website/assets/diagrams/advanced/A18C-generation-routing.png` |

### A13B 修订

初稿自行补出未实现的协议事件示例，并把分层标签放错位置；修订明确禁止任何伪代码与样例事件名。未采用原文件 `exec-c100f675-1706-4018-afa7-24337d274e08.png`。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “流式输入：先组装，再决定”. Render ONLY the Chinese text specified here, plus UTF-8 and SSE. Absolutely NO code, JSON, hex bytes, sample event names, English event labels, tool names, letter tiles, or text inside document props; the inside of every paper prop has only abstract gray strokes. Use six equal main stations in one spacious horizontal row: “网络字节” → “UTF-8 解码” → “SSE 事件” → “内容块拼接” → “完整消息检查” → “宿主校验”. Under UTF-8解码 ONLY put “保留残字节”; under SSE事件 ONLY put “空行分隔”; under 内容块拼接 ONLY put “按块索引”. No subtitle under 网络字节. From 完整消息检查 to 宿主校验 the arrow says “正常工具结束”. Under 宿主校验 put “参数与权限”, then a short downward teal arrow to terminal “允许调度”. From 完整消息检查 draw a separate orange downward branch to a terminal card with exactly two lines “截断 / 拒答 / 断流” and “停止并记录”. Failure never reaches dispatch. No earlier stage has an execution branch. Footer exact “一个网络分块，不等于一个完整响应”. Large short labels and blank document illustrations only; no invented protocol examples.
```

### A18B 修订

初稿把临时转写候选连接到金额冲突与澄清支路，会误导为临时转写即可改变业务判断；修订将其隔离成无出边的灰色终点。未采用原文件 `exec-dbc9c7b4-6e6d-4cb7-95b2-93cbbd791e05.png`。

```text
Use case: scientific-educational, infographic-diagram. Create ONE finished Chinese technical teaching diagram, landscape 1536x1024. White opaque canvas, bold crisp dark-navy Chinese type, matte blue/teal document trays, ledgers, inspection gates and small service modules with restrained 3D relief and soft shadows, matching an established engineering handbook series. Use large front-facing short labels, generous whitespace and clear arrowheads. Orange means blocked, uncertain or requires attention. Relationships and arrow direction matter more than decoration. Render the specified Chinese labels verbatim. No invented extra labels or data, robots, brains, logos, decorative circuits, tiny prose or watermark. Keep all text inside 55px safe margins. This explains a local teaching implementation, not production guarantees.

Title “先留证据，再核对最终条件”. Main UPPER row has five objects connected left to right: “原始媒体” → “带定位的证据” → “最终条件” → decision gate “金额一致且清晰？” → YES “继续查政策”. The evidence station has the short subtitles “图像区域” and “音频秒数”. Only the amount gate has an orange NO arrow down to a small terminal at LOWER RIGHT saying “金额冲突 / 模糊” then “等待澄清”. Inside this ORANGE terminal group the counterexample says “票据 650 ≠ 最终转写 6500”.
LOWER LEFT: create a clearly enclosed GRAY panel, wholly separate from the orange group, with heading “临时转写”. Inside this gray enclosure put only one small downward arrow to a terminal card “仅作候选 / 不改业务条件”. A gray input arrow may descend from 原始媒体 to this enclosed gray panel. CRITICAL: the gray panel is a DEAD END. There is no outgoing line, no outgoing arrow and no connection AT ALL from this gray panel to 最终条件, 金额核对, 金额冲突 or 等待澄清. Leave at least 250px WHITE EMPTY SPACE between the gray panel and the orange terminal group. Do not align these as consecutive stages and do not bridge this empty gap with an arrow. Interim transcription alone never triggers the business-conflict/clarification state. It only waits as a tentative candidate. Main final-conditions path and gray tentative path must be visibly distinct.
Footer “定位合法不等于内容正确；本例使用人工夹具”. No OCR/ASR implementation claim, invented text, code, extra amounts, output draft or actual submission. All labels large, no pseudo-protocol examples.
```

### 逐图审核

- A13B：重生成版本：仅短标签与空白卡片；分层字幕、消息终态和宿主校验方向正确。初稿含未实现协议示例，未采用。
- A13C：四层验收各有失败终点；7000与实际条款700比较不一致，失败不连交付。
- A14B：两次独立查询均住宿650元；10/31匹配v1 600，11/12匹配v2 700，比较与区间正确。
- A14C：中断后读取持久暂存，只处理剩余；旧索引继续查询；完整候选校验后切换。
- A15B：核对missing-values数据：a1 650/500，a4未知/700，a5 100/未知；1/1=100%，申请3，已知金额750。
- A15C：源库先受可信身份控制再筛行与复制快照；候选只对快照，经列操作与资源预算检查。图解明确身份由可信宿主预先提供。
- A16B：日期缺失先持久等待，回复回原排队任务；202仅接收，任务ID与预算不重置。
- A16C：已有v1任务与新入口两行分开；失败不登记，激活/回退只影响新任务；版本不可覆盖。
- A17B：v3携带变化条文，t0/t2和5秒窗口得到t7；t6等待t7一项；正文另限定不变正文只刷新版本不延长窗口。
- A17C：本地事务包含任务1、预算扣1、待发1；确认前中断，重开同一数据库后查接收账本补确认；无外部送达承诺。
- A18B：采用重生成版本：临时转写是封闭灰色终点，不连接金额冲突/澄清；仅最终条件金额冲突进入等待澄清。
- A18C：先过滤旧代次/已取消，再验证位置与时钟单调性；g1 3.8秒被忽略，g2长2秒的0.5秒通过。

图文位置：流式图与输出验收分置第13章两个机制段；第14章分置日期与中断恢复；第15章分置分母与执行边界；第16章分置澄清与发布；第17章分置去抖与确认重投；第18章分置媒体证据与代次过滤。均保留准确替代文字、两句左右图解与点击放大入口。
