# 进阶机制实验

使用 Python 3.10+ 标准库，运行三组独立实验：

```bash
python3 examples/advanced/runtime_lab.py --scenario all
```

| 场景 | 机制 | 预期重点 |
| --- | --- | --- |
| `evaluation` | pass@k、逐任务重复可靠性、组内奖励标准化 | 5 次中成功 1 次的 pass@2 估计为 0.4；两题 p=0.9/0.1 的至少一次成功均值为 0.59，全部成功均值为 0.41 |
| `budget` | 共享预算台账、任务依赖与关键路径 | 600+500 超过预算 1000 时拒绝第二笔；改为 400 后总预留 1000；理想并行下界 1100ms、串行 1400ms |
| `replay` | 跨连接恢复、外部成功后本地进度丢失 | 中断时本地 pending；恢复后 done；两次恢复返回同一工单，后端对象数为 1 |

## 评测算例

`pass_at_k(n, successes, k)` 计算 `1-C(n-successes,k)/C(n,k)`，相当于从 n 个已评分样本中等概率选 k 个，至少一个成功的比例。它要求 `1 <= k <= n`。

`iid_reliability` 对每题分别假设 k 次尝试独立、成功概率固定：至少一次成功为 `1-(1-p)^k`，全部成功为 `p^k`，最后再按题平均。实际尝试之间的相关性需要用重复实验检查。

`relative_advantages` 使用组均值和总体标准差，奖励 `[0,0,1,1]` 对应 `[-1,-1,1,1]`；同分组返回全 0。这里展示奖励的相对化步骤，完整 GRPO 还包括策略概率、裁剪、正则项与参数更新。

## 配对改进与不确定性

```bash
python3 examples/advanced/evaluation_lab.py
python3 -m unittest discover -s tests -p 'test_evaluation_lab.py' -v
```

默认12对标签由作者手工编写，基线成功6题、候选8题，其中修复3题、退步1题。脚本实际复算约16.7个百分点的配对差、McNemar双侧精确p值0.625，以及按整对任务重采样的百分位区间。默认2000次、种子7时区间约为[-16.7,50.0]个百分点；这是教学结果，不是模型实测提升。

结果包含修复/退步ID及采样配置。可用`--input .local/paired-outcomes.json`读取自己已判定的任务对，每项须有唯一`task_id`与布尔字段`baseline`、`candidate`。缺失或未判定不能隐式变成False；任务独立性、近重复分组及多次尝试协议需要由评测者先明确。小样本百分位区间不保证稳定覆盖；全同分的退化区间也不证明总体等价。完整手算与解释见[评测章](../../advanced/09-evaluation-and-feedback.md#成功率提高后还要看配对差异与不确定性)。

## 训练目标与一次参数更新

```bash
python3 examples/advanced/training_objectives.py --section all
python3 -m unittest discover -s tests -p 'test_training_objectives.py' -v
```

新的[训练目标实验](training-objectives.md)把两轮模型动作与工具观察分开，计算带掩码的SFT损失，再检查正/负优势、概率比裁剪与明确方向的KL正则。独立二值状态上的解析梯度与有限差分对照，随后做一次小步参数更新。它验证教学目标的计算，不是完整GRPO或语言模型训练；输入概率、标签与优势均为教学设定。

## 检索评分、候选与冲突

检索专题的[独立机制实验](retrieval-mechanisms.md)可用 `python3 examples/advanced/retrieval_lab.py --section all` 运行，复算BM25、给定向量、RRF、候选损失与冲突偏序；输入由作者编写，不报告真实语义检索或ANN性能。

## 预算与调度算例

台账中的单位是预留额度，不是自动读取的模型 token 或账单；同一个预留 ID 重放不重复扣额，更换预留量会拒绝。台账顺序执行；多 Worker 服务应使用具备并发一致性的共享存储。

关键路径按给定耗时、无限 Worker、零调度开销求最早完成时间。它是依赖图的理想下界；脚本不通过真实并发或等待来模拟 1100ms，实际服务还要测排队、限流和重试。

## 恢复算例

本地意图与模拟远端工单分别存在两个 SQLite 文件中。流程先提交本地 pending，再单独提交远端写入，然后注入中断，使本地没有记录完成。恢复时使用原操作 ID；远端凭唯一键和内容 hash 返回已有对象，随后本地改为 done。

两个数据库没有共同事务。示例的顺序恢复依赖远端的原子幂等合同；已有对象与键在实验期间持续保留。多租户键空间、幂等记录过期、实际网络错误和并发恢复可作为扩展练习。SQLite 文件在一次命令期间使用临时目录保存，命令退出后清理。

```bash
python3 -m unittest discover -s tests -p 'test_advanced_runtime.py' -v
```

[工程进阶](../../advanced/README.md) · [恢复执行](../../advanced/02-durable-execution.md) · [评测闭环](../../advanced/09-evaluation-and-feedback.md) · [性能与预算](../../advanced/10-performance-and-serving.md)
