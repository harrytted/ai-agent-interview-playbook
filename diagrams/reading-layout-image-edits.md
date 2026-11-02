# 阅读排版修复：流程图图片编辑记录

2026-11-02：使用 OpenAI 内置 imagegen 编辑三张现有 PNG，保留系列风格。选定结果替换原发布路径，源 SVG 与正文共同核验。以下提示词记录设计约束，不代表像素级可重复生成。

## A16

```text
Edit the supplied Chinese technical diagram in place. Preserve its 1536x1024 opaque white canvas, the exact title, navy typography, teal matte 3D objects, and all seven stations and arrows in the top main row. Correct ONLY the lower uncertainty/reconciliation section so it agrees with the handbook. From “原意图对账” clearly distinguish THREE conditional routes: (1) “查到且一致” goes to the existing “结果确认”; (2) “未取消且未查到” goes to a separate teal box “原 ID 幂等恢复”, with a clearly routed arrow back to “业务对象”, explicitly reusing the SAME operation ID, never a new intent; (3) “已取消且未查到” goes to orange terminal “保持未知”, and stops. Keep “结果未知” feeding “原意图对账” and “保留操作 ID”. You may rearrange the lower half to fit these routes cleanly, with large readable labels and noncrossing arrows; do not overcrowd or obscure main row. Existing upper annotations “此处仍可取消” and “派发后先核对” remain. Footer remains “请求成功，不等于业务成功”. Do not imply cancelled requests can create a new object, absence guarantees no side effect, or automatically undo anything. All exact Chinese labels must render accurately. No extra states or decorative elements.
```

## A16B

```text
Edit the supplied 1536x1024 Chinese flowchart. Preserve the exact title, all text, all objects, white background, navy text, blue/teal 3D style, and existing flow except the orange return arrow. The existing orange line from “收到日期回复” to “已排队” crosses the vertical orange NO line from the diamond “日期齐全？” down into “等待补日期”. Remove that ambiguity: reroute the orange return arrow in a dedicated OUTER lane that never crosses the NO branch or any other edge. Route it from the reply object below the lower nodes to the left outer side and then UP into the queue, or another clean nonintersecting route with an obvious arrowhead into “已排队”. You may move lower objects slightly to create whitespace, keeping the original overall hierarchy. Keep “沿用原任务” next to this return route. Retain the distinct storage arrow from “等待补日期” to “重启后仍保留”. Only one return arrow. Do not connect the reply route to the NO junction. Preserve the footer “任务 ID 不变，预算接着累计” and the “202 + 任务 ID” receipt. Large crisp Chinese labels, no clipping, no added content.
```

## A13B

```text
Edit the supplied technical teaching image with the smallest possible change. Preserve the exact 1536x1024 canvas, all objects, arrows, white background, palette, title, footer, and labels EXCEPT the text above the teal/blue arrow between “完整消息检查” and the host validation object. Replace the ambiguous label “正常工具结束” with two clear short lines: first line “完整工具请求”, second line “tool_use”. This label means a complete provider tool-use REQUEST, before host validation and actual execution. Do not move stages, add arrows, or change “宿主校验”, “参数与权限”, “允许调度”, the error branch, or any other wording. The replacement typography must match the existing navy label style and remain large enough to read. No spurious characters or extra content.
```

## A16 · 派发边界复核修订

首轮结果将结果未知箭头错误放在写准备下方，未选用该版本；选定图必须从派发提交点之后进入结果未知。

```text
Make ONE precise correction to this image, preserving absolutely everything else, including all three reconciliation routes and labels. The ORANGE arrow into the orange “结果未知” card currently starts below “写准备 / 此处仍可取消”, which is technically wrong. ERASE that existing orange downward arrow entirely. Replace it with a clean orange elbow arrow that STARTS at the DISPATCH boundary column “派发提交点”, immediately BELOW its annotation “派发后先核对” (around x=950, y=520), travels a short distance DOWN, then LEFT through empty whitespace, and finally DOWN into the top of the existing “结果未知” card (around x=765,y=625). It must originate ONLY from “派发提交点”, never “写准备”. Avoid the blue Worker input arrow, the “查到且一致” teal route, every label, and every other edge; route the elbow above the lower teal route if necessary. Do not change any text, objects, the top row, or the three corrected conditional routes. Keep the same opaque 1536x1024 image and exact typography.
```

