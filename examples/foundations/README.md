# 基础知识算例

Python 3.10+、标准库、无需联网或密钥。在仓库根目录执行：

```bash
python3 examples/foundations/math_lab.py --section all
```

实验使用手工数值，展示 Attention、向量相似度、排名融合与检索指标的计算过程。

| 实验 | 输入 | 预期重点 |
| --- | --- | --- |
| `--section attention` | 一个 Query、两个 Key/Value，维度为 2 | 权重约 `[0.669762, 0.330238]`；屏蔽第二位置后输出 `[2, 0]` |
| `--section retrieval` | 手工向量；两份排名 `[A,B,C]` 与 `[C,B,D]` | 余弦平行为 1、正交为 0；RRF 常数 60 时顺序为 `C,B,A,D` |
| `--section metrics` | 排名 `[B,A,C]`，相关集合 `{A,C,D}`，k=3 | Precision=2/3、Recall=2/3、单题 RR=1/2、二值 nDCG≈0.530721 |

实现与口径：

- Attention 计算一个 head 的一个 query；Q/K/V 直接给出，mask 由调用者提供。完整 Transformer 中的可训练投影、多头、残差和 MLP 可作为后续扩展。
- Softmax 先减最大值再求指数，数学分布不变，避免大正数输入的指数溢出。
- 本脚本对余弦要求两个非零、同维向量；零向量使数学定义的分母为零，因此拒绝计算。库可能另约定其结果为 0，比较时须核对。同维不代表可比较的语义空间，实际检索须匹配模型及处理配置；相似度不是概率。
- RRF 使用一基排名，分数为各列表的 `1/(constant+rank)` 之和。60 是这个教学实验的参数，不是所有任务的最优值。列表内不得重复同一文档。
- 检索指标只针对一个查询；MRR 还需对预先声明的查询集合取平均。Precision@k 分母是 k；列表不足 k 的位置视为未命中。
- nDCG 使用二值相关性、gain=0/1、折扣 `log2(rank+1)`。实际有分级相关性时，必须声明 gain 形式，不能直接混用结果。
- 无相关文档时 Recall 与 nDCG 在这里返回 JSON `null`；Precision 与 RR 返回 0。真实任务应另测正确拒答，并说明宏平均如何处理这类查询。

测试覆盖手算已知值、边界输入与序列化输出：

```bash
python3 -m unittest discover -s tests -p 'test_foundations_math.py' -v
```

[基础课程](../../learning/README.md) · [评测章](../../learning/09-evaluation.md)
