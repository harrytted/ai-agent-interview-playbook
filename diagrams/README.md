# 手册插图维护

<div id="课程插图维护"></div>

章节正文、题解与首页展示 `website/assets/diagrams/` 下的 PNG 插图，均使用 OpenAI 内置 imagegen 生成。基础部分有 14 张，工程进阶有 18 张。完整提示词从 [imagegen-prompts.md](imagegen-prompts.md) 进入，图片、主题和对应语义草图列在 [imagegen-manifest.json](imagegen-manifest.json)。

在线手册中点击正文图片即可在当前页面放大，按 Esc 或点击关闭控件收起，不再额外显示“查看原图”入口。图片使用原始分辨率，手机读者仍可通过浏览器缩放查看细节。重要知识同时由正文与替代文字说明。

`source/` 下的 SVG 和 `website/assets/diagrams/` 下对应的 SVG 保持字节一致，仅用作语义草图，便于复查概念、箭头和例子。PNG 是内置工具重新生成的插图，并非 SVG 的机械导出；两种格式不要求像素一致。进阶的 A01–A18 也直接展示 PNG。

更新时先核对正文和语义草图，再用内置 imagegen 生成新图，人工检查图中的中文、箭头方向、条件和例子。图片应保留清晰的短标签；详细解释和替代文字写在 Markdown 中。重新生成可能得到不同画面，提示词记录用于追溯设计意图，不能保证逐像素复现。

保存选定的 PNG 后运行：

```bash
python3 scripts/check_diagrams.py --suite all
python3 scripts/check_repo.py --write-index
python3 scripts/prepare_site.py
.venv-docs/bin/python -m mkdocs build --strict
python3 scripts/check_site.py
```

校验脚本检查 32 组 SVG 源文件与发布副本、32 张 PNG 的固定发布路径、文件结构、校验和及尺寸。它不判断中文内容与技术关系是否正确；这些需要结合正文逐图审核，并在相关页面中检查实际阅读效果。进阶图沿用正文中的机制与示例，设计图不能当作实验已经实现对应功能的证明。

上面的准备命令默认把源码链接指向 `main`。审阅其他已发布版本时，可用 `--source-ref` 指定 GitHub 上已存在的分支、标签或提交 SHA；该参数只改变源码链接，不改变本地构建内容。详见[网站维护说明](../website/README.md#本地预览)。
