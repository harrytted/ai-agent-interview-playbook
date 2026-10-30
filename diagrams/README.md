# 课程插图维护

课程、题解与首页展示 `website/assets/diagrams/` 下的 PNG 插图。这批图片使用 OpenAI 内置 imagegen 生成；完整提示词保存在 [imagegen-prompts.md](imagegen-prompts.md)，图片、主题和对应语义草图列在 [imagegen-manifest.json](imagegen-manifest.json)。

每张正文插图下提供“查看原图”链接，手机读者可以打开原始分辨率图片并通过浏览器放大细节。重要知识仍由正文与替代文字说明，不要求读者辨认图片中的小字才能继续学习。

`source/` 下的 SVG 和 `website/assets/diagrams/` 下对应的 SVG 保留为语义草图，便于复查原有概念、箭头和例子。PNG 是重新生成的插图，并非 SVG 的机械导出；两种格式不要求像素一致。

更新时先核对正文和语义草图，再用内置 imagegen 生成新图，人工检查图中的中文、箭头方向、条件和例子。图片应保留清晰的短标签；详细解释和替代文字写在 Markdown 中。重新生成可能得到不同画面，提示词记录用于追溯设计意图，不能保证逐像素复现。

保存选定的 PNG 后运行：

```bash
python3 scripts/check_diagrams.py --suite all
python3 scripts/check_repo.py --write-index
python3 scripts/prepare_site.py --source-ref codex/agent-handbook-learning
.venv-docs/bin/python -m mkdocs build --strict
python3 scripts/check_site.py
```

校验脚本检查 14 组 SVG 源文件与发布副本、14 张 PNG 的固定发布路径、文件结构、校验和及尺寸。它不判断中文内容与技术关系是否正确；这些需要结合正文逐图审核，并在课程页面中检查实际阅读效果。
