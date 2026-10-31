# 工程进阶插图 A05–A08：内置图片生成提示词

## A05 定向编辑：检查通过后再执行（最终采用版本）

### 完整编辑提示词

```text
Use case: precise-object-edit. Edit the supplied A05 textbook illustration, retaining its 1536×1024 landscape composition, white background, exact Chinese typography, all four object stations, lighting, palette and illustration style. Make ONLY these three targeted changes so the main path unambiguously means checks have passed before execution:
1. On the execution checkpoint, the indicator below “必要批准” must become a green circle with a white check mark, matching the already green indicators below “参数” and “权限”. Preserve all three existing headings exactly.
2. Change the closed red-and-white barrier into a visibly OPEN barrier, with its striped arm lifted diagonally upward. Remove the closed “no entry” sign from the passage or lift it with the arm so no closed barrier or blocking sign remains. Keep the checkpoint body, support posts and three green check indicators recognizable and unobscured.
3. Above the teal arrow between the execution checkpoint and the right-hand service, add a small but clearly legible dark navy Chinese label, exactly “通过后”. It should not overlap objects, other labels or the arrow.

Everything else must remain unchanged: the title “找到工具，再核对执行条件”, the labels “工具目录”“加载说明”“执行检查”“调用工具”, the bottom takeaway “发现工具，不等于获准执行”, the tool drawer, open manual, right-hand service and finished output, spacing, camera angle and dimensions. This depicts a valid approved action after required checks; “必要批准” remains as a conditional check heading, not a claim every tool always requires approval. Do not introduce extra text, additional arrows, watermarks or any new decorative objects.
```

- 编辑方式：内置 `image_gen.imagegen`，使用已查看的 A05 PNG 作为编辑目标；未使用程序修改图像。
- 输入文件：`website/assets/diagrams/advanced/A05-tool-routing.png`（首次生成版本）。
- 内置工具原始输出：`website/assets/diagrams/advanced/A05-tool-routing.png`（生成标识：`exec-4a388bec-1366-42a2-9a66-22e935c6a7e5.png`）。
- 最终文件：`website/assets/diagrams/advanced/A05-tool-routing.png`。
- 尺寸：1536 × 1024，直接复制工具原始 PNG。
- SHA-256：`7ffb8ee2aebf4a9551fe8b4f5883c0f30a3439806e78d9fe640d2cfc9708b66d`。
- 图面复核：三项检查均为绿勾，栏杆抬起，前往调用工具的箭头标注“通过后”；原有标题、四个阶段、底部结论与其他物体保持。A06–A08 未修改。


生成方式：内置 `image_gen.imagegen`，每张独立生成；未使用 CLI、API 或 SVG 转 PNG。

## A05 · A05-tool-routing.png

目标路径：`website/assets/diagrams/advanced/A05-tool-routing.png`

### 完整提示词

```text
Use case: scientific-educational. Create one finished landscape 3:2 Chinese textbook information illustration for an Agent engineering handbook. White background, refined editorial 3D objects with very slight isometric depth, soft shadows, deep navy large Chinese lettering, blue-green objects and a little orange for a caution. It must look like a crafted educational illustration, not a mechanical SVG flowchart or a collection of text boxes.

Explain one relationship: finding a tool does not grant permission to execute. On a spacious tabletop, from left to right show a searchable tool-directory drawer with a few tool cards, an open instruction manual for the selected tool, an execution checkpoint with three small clearly distinct check indicators, and a connected service carrying out one tool request. Connect them using clear single-direction teal arrows in that order. The checkpoint must precede execution. A small orange stopped token at the checkpoint visually explains that failed checks cannot bypass the gate. Do not depict tool discovery as authorization. The third check means approval only when the action requires it.

Render ONLY this exact Chinese text, with a large readable visual hierarchy and no extra microtext:
Title: “找到工具，再核对执行条件”
Stage labels: “工具目录” “加载说明” “执行检查” “调用工具”
The checkpoint's three short indicators: “参数” “权限” “必要批准”
Bottom takeaway: “发现工具，不等于获准执行”

Keep lots of whitespace. Objects should carry the explanation; use few short labels, not paragraphs. No robots, brains, circuits, code fields, policy IDs, watermarks, logos or generic decorative panels. Labels must be spelled correctly. Arrows must be unambiguous, avoid all text and never cross an unrelated object.
```

## A06 · A06-evidence-loop.png

目标路径：`website/assets/diagrams/advanced/A06-evidence-loop.png`

### 完整提示词

```text
Use case: scientific-educational. Create one finished landscape 3:2 Chinese textbook information illustration for an Agent engineering handbook. White background, refined blue-green evidence cards, document folders, a checklist and a small report, slight isometric object depth and soft shadows, large deep navy Chinese lettering, restrained orange branches. The illustration should be warm and precise, not a vector flowchart made of boxes.

Teach evidence-driven retrieval with a finite stopping condition. Lay out three main physical objects left-to-right: a clipboard representing the evidence needed for a question, a document library/search tray, and a magnifying glass checking collected evidence cards against the checklist. A teal arrow carries the needed evidence list to document search, then search results to evidence checking. From checking: an orange loop labelled “有缺口且有预算” returns to the search tray; a teal path to a small finished report is labelled “证据齐全：回答”; a distinct orange path to a visibly incomplete report is labelled “预算用尽或无新信息：说明不足”. Do not connect the incomplete report back into search. The loop must be motivated by a specific evidence gap and remaining budget, not an endless retry.

Render ONLY these exact Chinese labels:
Title: “每次检索，补一个证据缺口”
“证据清单”
“查资料”
“核对缺口”
“有缺口且有预算”
“证据齐全：回答”
“预算用尽或无新信息：说明不足”

No other text, no policy IDs, numbers, implementation fields, robots, logos or watermarks. Use short large labels and generous whitespace. All arrow directions must be unmistakable, never passing through text or an unrelated object. The two finished/incomplete outcomes must be visually different without implying that missing evidence is a complete answer.
```

## A07 · A07-control.png

目标路径：`website/assets/diagrams/advanced/A07-control.png`

### 完整提示词

```text
Use case: scientific-educational. Create one finished landscape 3:2 Chinese textbook information illustration for an Agent engineering handbook. Explain delegation versus handoff using two clean side-by-side workspace scenes, white background, crafted blue-green workstations and task cards with slight isometric depth, soft shadows, deep navy large Chinese labels, orange only for control transfer. Avoid generic boxes, robots and a row of human characters.

LEFT scene: a primary coordinating workstation labelled “主管” sends a task card down to a smaller research workbench labelled “子任务”. A clear teal outward arrow denotes delegation. A separate curved teal arrow labelled “结果返回” goes from the subtask workbench BACK to the same supervisor workstation. A small completed report beside the supervisor makes clear that the supervisor continues and summarizes. Keep the return arrow distinct and avoid crossed routes.

RIGHT scene: a general-purpose workstation labelled “通用角色” hands a task card through one orange arrow labelled “交出控制权” to a specialist workspace labelled “专员继续对话”. Give this specialist an active conversation bubble containing only simple dot marks, indicating that the specialist continues the user interaction. Do not draw an automatic return arrow to the general role; handoff changes the active handler. A very light central divider may separate the scenes. Do not imply either mode grants new resource access.

Render ONLY this exact text:
Title: “委派与交接：谁继续处理？”
“主管”
“子任务”
“结果返回”
“通用角色”
“交出控制权”
“专员继续对话”
Bottom takeaway: “角色变化，不会增加权限”

Keep the typography large, consistent and correctly spelled. Spacious editorial composition, a clear relation in each scene, minimal labels, no policy IDs, code fields, logos, watermark, circuits or decorative cards. Arrows must point into the correct corresponding workstation.
```

## A08 · A08-action-feedback.png

目标路径：`website/assets/diagrams/advanced/A08-action-feedback.png`

### 完整提示词

```text
Use case: scientific-educational. Create one finished landscape 3:2 Chinese textbook information illustration for an Agent engineering handbook. White background, refined editorial objects with slight isometric depth and soft shadows, deep navy large Chinese text, blue-green objects, a single orange feedback path. Explain that issuing an action is not the same as verifying the task result.

Arrange four recognizable object stations in one readable left-to-right main sequence, connected by clear teal arrows:
1 a magnifying glass over the current file/page object, labelled “观察当前状态”;
2 a small code patch and a cursor performing one action, labelled “小步操作”;
3 a freshly read page/file object with a refreshed view, labelled “重新观察”;
4 a checklist comparing the SAME target object before and after, labelled “核对对象结果”.
Use the same distinct blue document tab or small target symbol at stages 1, 3 and 4 to show object identity. The checkpoint should show real object state, not just a green button saying success. A single clean orange return path from the result check runs below the stations back to stage 1, labelled “未通过，回到观察”. It must not share a confusing double arrow or intersect any label.
At the bottom, show two tiny paired result props (an applied code patch plus a test check; a saved page object plus a field check), reinforcing the short takeaway without adding text.

Render ONLY this exact Chinese text:
Title: “动作之后，还要核对结果”
“观察当前状态”
“小步操作”
“重新观察”
“核对对象结果”
“未通过，回到观察”
Bottom takeaway: “补丁与点击，都需要验收”

Labels large, short, highly legible and spelled exactly. Generous whitespace; no long paragraphs, numbers, IDs, code fields, robots, brains, circuits, logos or watermark. The image must be a polished explanatory illustration, not a reproduction of a plain vector box flowchart.
```


## 生成与验收记录

以下四张均为内置工具原始 PNG，已逐张查看中文和箭头关系，未通过截图、转换或重画替换。

### A05 首次生成（历史版本，已由下方修订替代）

- 内置工具原始文件标识：`exec-6455ad00-e015-4d3d-91dd-05f1cb2200f6.png`

- 仓库路径：`website/assets/diagrams/advanced/A05-tool-routing.png`

- 尺寸：1536 × 1024

- SHA-256：`00f051ae59beae2b6117cfd36aa912a7088768c62c4f74efc20f7e35817bb968`

- 复核发现：必要批准为灰灯、栏杆关闭，与右侧执行结果含义不一致；已使用内置工具定向编辑，见下方最终版本。

### A06

- 内置工具原始输出：`website/assets/diagrams/advanced/A06-evidence-loop.png`（生成标识：`exec-9a955618-9789-431d-bbed-0ce6e9bcf01a.png`）

- 仓库路径：`website/assets/diagrams/advanced/A06-evidence-loop.png`

- 尺寸：1536 × 1024

- SHA-256：`22a7cbdf7ecde358199c67cd76b94529a14ab67b2a225bb233155b58858ec81b`

- 人工图面核对：中文可读，标签含义与方向正确，无明显错字或知识错误。

### A07

- 内置工具原始输出：`website/assets/diagrams/advanced/A07-control.png`（生成标识：`exec-542d5bd9-e861-4336-bef3-0113c2a1c8c2.png`）

- 仓库路径：`website/assets/diagrams/advanced/A07-control.png`

- 尺寸：1536 × 1024

- SHA-256：`e726e777c0bb94034180fe832f6a0d75c0b61d7b083938cfb3a9a0dd19ce9915`

- 人工图面核对：中文可读，标签含义与方向正确，无明显错字或知识错误。

### A08

- 内置工具原始输出：`website/assets/diagrams/advanced/A08-action-feedback.png`（生成标识：`exec-9d49cf34-c99b-4538-9749-ea010c9bedc9.png`）

- 仓库路径：`website/assets/diagrams/advanced/A08-action-feedback.png`

- 尺寸：1536 × 1024

- SHA-256：`f76f5a1c34e347325593808bad3cc7bec67a29072eed4624fe67b679b3556b29`

- 人工图面核对：中文可读，标签含义与方向正确，无明显错字或知识错误。
