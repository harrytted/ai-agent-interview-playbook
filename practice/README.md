# 练习与复习

先口述问题，再看答案，用自己的项目举证。题目按文档自动读取，学习记录留在本地。

```bash
python3 scripts/study.py list
python3 scripts/study.py draw --count 3 --topic rag
python3 scripts/study.py draw --count 5 --seed 42
python3 scripts/study.py show Q019
python3 scripts/study.py review Q019 --score 1
python3 scripts/study.py due
python3 scripts/study.py stats
```

`--topic` 匹配题目、文件路径或答案正文。`draw` 用于无提示抽题，未标记前不会改变进度。`show` 展示答案。`due` 分开显示到期和未学习题目。

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
