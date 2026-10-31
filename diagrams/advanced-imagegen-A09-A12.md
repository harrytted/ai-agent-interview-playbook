# A09–A12 图片生成提示词

使用内置 `image_gen` 图片工具生成全新图片；不使用 SVG 转换、截图或外部 API。以下为实际发送的完整提示词，最终 PNG 原样复制到 `website/assets/diagrams/advanced/`。

最终采用输出（均为内置工具原始 PNG，1536×1024）：

- A09：`exec-7bc4e2cb-d9de-457e-aca5-9952106fae8c.png` → `website/assets/diagrams/advanced/A09-evaluation.png`
- A10：`exec-30d96c16-83ad-417c-9559-10ad372a5ad4.png` → `website/assets/diagrams/advanced/A10-critical-path.png`
- A11：`exec-7d1aec1d-754b-4dc5-95fb-481e9c8afb93.png` → `website/assets/diagrams/advanced/A11-trust-boundaries.png`
- A12：`exec-cf7d6bb2-1546-4e0c-be9a-8bd1b0dd43ba.png` → `website/assets/diagrams/advanced/A12-training.png`

逐张检查了中文与方向关系。A10 原时轴图和一次编辑未通过比例检查，最终重新生成无量尺的依赖图；两路独立读取在汇合点等齐，再综合，公式保留准确数值。A09 未填虚构效果分数；A11 的必要批准和其他职责分开；A12 三种训练路线并列，资料修复绕过参数更新直接进入验收。

## A09 evaluation

```text
Use case: scientific-educational. Create a polished Chinese textbook information illustration for an Agent engineering handbook, a fresh raster illustration, landscape approximately 3:2. White/off-white background, deep navy very large clear Chinese typography, teal and blue physical parts, sparing orange accents. Tangible teaching objects with subtle three-dimensional depth, matte surfaces and soft contact shadows, generous whitespace, restrained professional composition. Directional relationships must be immediately legible. No robots, brains, circuits, dashboards, mechanical rounded-box flowcharts, dense paragraphs, watermarks, or decorative clutter. All exact supplied Chinese text must be rendered correctly.
Subject: a comparative experiment desk. On the left, two side-by-side matched exam papers mounted together and clearly labeled “基线” and “候选”; both use the same task cards and the same budget ruler, summarized by a small overhead label “固定任务与预算”. Their corresponding rows are connected by subtle pairing lines, not score numbers. Center: a large magnifying lens inspecting paired evidence slips, with one teal tag “修复” and one orange tag “退步”. Right: a robust neatly organized regression-test folder labeled “回归验证”. A strong left-to-right arrow connects the matched paper pair to the lens, then to the folder. The concept is comparing identical tasks, finding both repaired and regressed behavior, then regression validation. Do not invent performance scores or imply an actual measured improvement.
Exact main title: “评测：同题对照，追查差异”.
The only other text: “固定任务与预算”, “基线”, “候选”, “逐题配对”, “修复”, “退步”, “回归验证”. Place “逐题配对” directly below the joined paper pair. Make illustration and typography balanced, with large legible labels.
```

## A10 critical-path

```text
Use case: scientific-educational. Create a polished Chinese textbook information illustration for an Agent engineering handbook, a fresh raster illustration, landscape approximately 3:2. White/off-white background, deep navy very large clear Chinese typography, teal and blue physical parts, sparing orange accents. Tangible teaching objects with subtle three-dimensional depth, matte surfaces and soft contact shadows, generous whitespace, restrained professional composition. Directional relationships must be immediately legible. No robots, brains, circuits, dashboards, mechanical rounded-box flowcharts, dense paragraphs, watermarks, or decorative clutter. All exact supplied Chinese text must be rendered correctly.
Primary request: an exceptionally clear, handsome, mathematically rigorous time-track educational illustration. Do not sacrifice the timeline for ornament. Use a front-facing flat horizontal time axis with subtle solid 3D time blocks and small physical document-reading stations entirely to the left of the time plot. Four separate horizontal lanes, top to bottom planning, read A, read B, synthesis. All blocks on the same proportional time scale.
Exact title: “关键路径：要等最慢的一路”.
Axis tick labels 0, 200, 500, 700, 1100 and unit ms. Precisely aligned block intervals: planning starts at 0 and ends at 200; read A starts at 200 and ends at 500; read B starts at 200 and ends at 700; synthesis starts at 700 and ends at 1100. Let 0→1100 cover the entire available plotting width: planning width is 200/1100, A width 300/1100, B width 500/1100, synthesis width 400/1100. Planning, B and synthesis are dark teal, forming the critical path; A is pale blue with dark navy text. Draw a thin dashed horizontal waiting segment in the A lane from 500 to 700, labeled “等待”. Synthesis must start aligned at 700, after both reads. Dashed vertical guides at 200 and 700 explain simultaneous starts and the join; no causal arrow through a block.
Lane labels exactly: “规划”, “读取 A”, “读取 B”, “综合”. Duration text inside the correct blocks: “200”, “300”, “500”, “400”. A restrained dark-teal route annotation: “关键路径：规划 → B → 综合”.
At the bottom place large correct equations on two separate lines:
“并行：200 + max(300, 500) + 400 = 1100 ms”
“串行：200 + 300 + 500 + 400 = 1400 ms”
Small but readable footer: “教学理想耗时，非实测”.
No second time scale, no distorted perspective on the axis, no duplicated blocks, no extra model/server drawings.
```

### A10 定点修订：统一时轴比例与终点

```text
Use case: precise-object-edit. Correct ONLY the proportional timeline geometry of this attached Chinese critical-path textbook illustration. Preserve the polished white/teal physical-block style, document icons, title, all Chinese lettering, both formulas, footer and overall 1536-by-1024 composition exactly. The four time blocks must share ONE consistent linear scale. In this 1536px-wide image, use x=321 for time 0, x=521 for 200, x=821 for 500, x=1021 for 700, x=1421 for 1100. Correct each axis tick and its number to these x coordinates. Planning block from x321 to521. Read A from x521 to821. Read B from x521 to1021. Synthesis from x1021 to1421, so its right edge is EXACTLY above the 1100 tick, with no overhang. Vertical dashed guides at x521 andx1021. Read A's dashed waiting segment fromx821 tox1021. These x positions represent the FRONT FACE boundaries; any subtle depth must not change the perceived measured start or end. Keep each block at its existing y lane and retain duration labels200/300/500/400 centered. Do not alter the text or add content. There must be no mathematical or spelling changes.
```

### A10 最终重绘：用依赖关系说明并行与等待

前述原稿与定点编辑的刻度比例未达到要求，均未采用。最终改用无量尺的依赖图；准确数值由公式表达。

```text
Use case: scientific-educational. Create a NEW Chinese textbook information illustration for an Agent engineering handbook, landscape about3:2. White background, very large deep navy Chinese lettering, teal and blue tangible desk objects with subtle 3D relief, matte finish, soft shadows and generous whitespace. This is a simple DEPENDENCY DIAGRAM, with no rulers, axes, tick marks, duration-proportional bars, timelines or charts. No robots, brains, circuits or generic box flowchart.
Exact title: “两路一起查，等齐再汇总”.
At the left a physical planning clipboard on a small desk station labeled “规划 200 ms”. From this clipboard clearly split into TWO independent arrows: upper arrow to an upper-middle document reading station labeled “读取 A 300 ms”; lower arrow to a lower-middle document reading station labeled “读取 B 500 ms”. The two stations should look like actual document stands, one pale blue, one teal, not software cards. Their routes are parallel independent work, no arrow between A and B. From the outputs of BOTH reading stations, draw TWO forward arrows joining before a right-hand synthesis/report tray station labeled “综合 400 ms”. A clear short note above the join: “等待两路完成”. All arrows flow left to right; no output may skip the join, no arrow loops backwards. Keep the labels large and obvious. Visual arrangement left planning → middle two stacked independent reads → right combined report. Equal clear hierarchy, not an exaggerated perspective drawing.
Bottom exact formulas, rendered correctly and prominently on separate lines:
“并行：200 + max(300, 500) + 400 = 1100 ms”
“串行：200 + 300 + 500 + 400 = 1400 ms”
Footer: “教学理想耗时，非实测”.
The upper A route finishing earlier must still wait at the merge. Use the layout and merge to teach dependencies; absolutely no numeric time axis or scaled rectangular bars. Premium restrained educational illustration, strong legibility, no additional text.
```

## A11 trust-boundaries

```text
Use case: scientific-educational. Create a polished Chinese textbook information illustration for an Agent engineering handbook, a fresh raster illustration, landscape approximately 3:2. White/off-white background, deep navy very large clear Chinese typography, teal and blue physical parts, sparing orange accents. Tangible teaching objects with subtle three-dimensional depth, matte surfaces and soft contact shadows, generous whitespace, restrained professional composition. Directional relationships must be immediately legible. No robots, brains, circuits, dashboards, mechanical rounded-box flowcharts, dense paragraphs, watermarks, or decorative clutter. All exact supplied Chinese text must be rendered correctly.
Subject: trust boundaries explained as a physical controlled passage, not a generic software box diagram. On the far left, a standing external PDF/document sheet with an orange quoted instruction slip; label it “外部资料” and add the firm readable note “文字不能授予权限”. The sheet enters a navy/teal reading station which proposes a small action token labeled “动作请求”. It then meets a sequence of four visibly separate physical inspection gates, with the gate functions clearly labeled in order: “身份确认”, “资源授权”, “必要批准”, “执行隔离”. The approval gate has a small orange seal, the others teal/blue. The route ends at a physical delivery tray/check station labeled “结果与出口核对”. One clear forward route; no bypass arrow, no arrow granting permission directly from the document. Gate signs must be large, not on distant tiny parts. Four gates plus the final station represent different responsibilities, not interchangeable authorization.
Exact title: “信任边界：每道关卡各管一件事”.
Only the labels supplied above. Compose as an elegant shallow isometric inspection corridor in generous white space, with all signs front-facing and readable. No people or robots; physical metaphor should help distinguish the controls.
```

## A12 training

```text
Use case: scientific-educational. Create a polished Chinese textbook information illustration for an Agent engineering handbook, a fresh raster illustration, landscape approximately 3:2. White/off-white background, deep navy very large clear Chinese typography, teal and blue physical parts, sparing orange accents. Tangible teaching objects with subtle three-dimensional depth, matte surfaces and soft contact shadows, generous whitespace, restrained professional composition. Directional relationships must be immediately legible. No robots, brains, circuits, dashboards, mechanical rounded-box flowcharts, dense paragraphs, watermarks, or decorative clutter. All exact supplied Chinese text must be rendered correctly.
Subject: a diagnosis workbench that splits into two routes and rejoins at independent validation. At upper center a magnifying lens and a short trajectory strip labeled “先定位原因”. Left route has a document stack and a tool wrench on a repair tray labeled “先修资料、工具、运行时”. This route bypasses the parameter training machine and goes directly to the final validation station. Right route has an evidence folder with a small check seal and a note “证据充分仍反复选错”, then branches into THREE PARALLEL choices arranged on an equal footing, never chained: a paired demonstration-card module labeled “SFT”, two side-by-side preference cards labeled “偏好优化”, and a tiny environment interaction loop labeled “Agent RL”. These three alternative modules feed a single parameter chip labeled “参数更新”. Both the left repair route and the parameter-update route go to a final independent test tray labeled “独立验收”. All arrows clear, no backwards arrows, no implication every task needs training.
Exact title: “先诊断，再决定是否训练”.
Include a modest but clearly readable footer: “读记忆与技能，不更新参数”.
Teaching design, not a claim that a training pipeline has been built. Avoid extra pseudo-code, scores, model names or equations. Chinese lettering clear and large; the chip, cards, lens and repair objects are precise premium editorial illustrations.
```
