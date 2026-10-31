# 去除图中示例代号 · 2026-10-31

使用内置 imagegen 编辑已有 PNG，原始输出直接复制到发布路径，未进行程序绘制或转码。逐图检查中文标签和箭头关系。

## G3

引用原图：`website/assets/diagrams/G3-tool-roundtrip.png`。

实际完整编辑提示词：

```text
Use case: text-localization. Edit the referenced existing Chinese technical textbook illustration in place, preserve its 1536x1024 white canvas, title, two round-trip lanes, exactly two blue model chips, document trays, request ticket, executor, tool result, answer bubble, all arrow directions, colors, shadows and layout. Make only three text substitutions: both occurrences of 'call_id: c1' must become the identical clear Chinese label '同一调用'. Replace the bottom footer '请求与结果按 call_id 对应，执行结果进入下一轮输入' with '请求与结果一一对应，执行结果进入下一轮输入'. Keep all other text verbatim, especially the title '应用侧工具调用：执行结果怎样回到模型', labels '第 1 轮','第 2 轮','当前上下文','模型','调用请求','宿主执行','工具结果','包含工具结果的新上下文','基于结果回答'. Large correctly spelled Chinese. No raw call_id or c1 anywhere after edit. Preserve the sequence: proposed request -> host execution -> result -> next input -> model -> answer. Do not add labels, new diagrams, or new arrows; no watermarks.
```

## G8

引用原图：`website/assets/diagrams/G8-write-recovery.png`。

实际完整编辑提示词：

```text
Use case: text-localization. Edit the referenced existing Chinese textbook recovery illustration. Preserve the original 1536x1024 canvas, white background, title, all six numbered steps and their objects, arrows, blue/teal/orange visual style, composition, document/record identity and correctness. Only simplify these textual labels: replace BOTH occurrences of 'operation_id: op1' with the identical clear Chinese label '原操作标识'. Replace the step 5 heading '按原 ID 查询' with '沿原操作查询'. Replace the bottom banner '恢复使用原 ID；重放仍需服务端幂等约束' with '沿原操作恢复；重放仍需服务端幂等约束'. Keep every other label exactly unchanged, especially '写入后崩溃，怎样恢复','记录本地意图','远端已提交','本地确认前崩溃','远端成功，本地未知','重启后恢复','核对并确认原对象','本地记录','远端服务'. No operation_id, op1 or arbitrary sample codes anywhere. Do not change the semantic mechanism: remote already committed before local confirmation crashes; recovery checks the same original operation, still requiring the server idempotency contract. No new objects, no raw JSON, no watermark.
```
