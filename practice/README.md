# 练习与复习

先口述问题，再看答案，用自己的项目举证。看答案时处处眼熟，合上后却只剩“这个我见过”，是很常见的错觉；抽题就是让这个错觉早点露面。

工具会读取全部 [92 道详解题](../docs/question-index.md)，包括 56 道基础与工程题、[36 道进阶题](../docs/advanced/README.md)。每题都有三个已作答追问与实战案例，并链接对应学习内容。学习记录留在本地。

```bash
python3 scripts/study.py list
python3 scripts/study.py draw --count 3 --topic rag
python3 scripts/study.py draw --count 5 --seed 42
python3 scripts/study.py draw --topic docs/advanced/ --count 3
python3 scripts/study.py show Q060
python3 scripts/study.py show Q019
python3 scripts/study.py review Q019 --score 1
python3 scripts/study.py due
python3 scripts/study.py stats
```

`--topic` 匹配题目、文件路径或答案正文。`draw` 用于无提示抽题，未标记前不会改变进度。`show` 展示答案。`due` 分开显示到期和未学习题目。

GitHub 中每题先显示短答，详细解析、追问和案例放在折叠区；命令行 `show` 会完整展开，方便连续阅读。按 `docs/foundations/03-` 筛选可练 RAG，按 `docs/advanced/02-` 可练进阶持久执行。旧题号与已有复习记录继续使用。

## 自评分与日期规则

| 分数 | 自评标准 | 下次复习 |
| --- | --- | --- |
| 0 | 无法解释或核心机制错误 | 今天，阶段重置为 0 |
| 1 | 看提示后能解释 | 明天，阶段重置为 0 |
| 2 | 独立说清机制、失败路径 | 3 天后，阶段至少为 1 |
| 3 | 能答追问，并拿练习/项目举证 | 阶段前进一步，按 1/3/7/14 天安排，最多 14 天 |

日期按 Asia/Shanghai 计算；不需要为了打卡强行给高分。相同题目可随时重评。

默认记录文件 `.local/study-progress.json` 已忽略。若想换位置，把 `--progress /path/to/progress.json` 放在子命令前。不要将私人面试记录、公司机密或客户数据提交到公开仓库。

## 口述评分

每次回答从四项各给 0–2 分：概念准确、机制完整、取舍合理、证据具体。总分 8 分。请同伴拿一个不同场景再追问一次，检查是否只是背下了固定答案。

[模拟面试](mock-interviews.md) · [项目模板](project-story-template.md) · [复盘模板](review-template.md)
