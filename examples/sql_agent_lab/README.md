# Text-to-SQL 与统计核验实验

配套 [第 15 章](../../advanced/15-text-to-sql-and-data-analysis.md) · [Q099–Q101](../../docs/advanced/15-text-to-sql-and-data-analysis.md)。需要 Python 3.10+ 的标准库 `sqlite3`，无需外部数据库、账号或模型密钥。全部员工、租户和业务数据为虚构 fixture。

这里**真实执行 SQLite SQL**。默认候选为预制 SQL，修复轨迹也使用预制下一候选；它验证执行控制、统计反例和评分器，不能报告自然语言转 SQL 模型准确率。

## 运行

```bash
python3 -m examples.sql_agent_lab --scenario all --output .local/sql_agent_lab
python3 -m examples.sql_agent_lab --scenario join-amplification --output .local/sql_join_lab
python3 -m unittest discover -s tests -p 'test_sql_agent_lab.py' -v
```

各场景有 `result.json`、`trace.jsonl`、`grade.json` 和真实 `.sqlite` 数据文件，根目录另外生成汇总三件套。`semantic-error` 的整体 passed 表示评分器**识别出了错误口径**，不表示那条 SQL 业务正确；必须查看具体 checks 和返回表。返回码 0 表示本次所选验收断言成立。

| 场景 | 验证问题 |
| --- | --- |
| `normal` | 同一统计合同在普通、同金额、日期/空值三份实例上执行 |
| `join-amplification` | 650+700 正确合计 1350，连接明细后错误合计 2000；两个 650 证明 SUM DISTINCT 不是通用修复 |
| `schema-repair` | 编造列名失败后按反馈换下一候选，最多两次 |
| `bounded-repair` | 连续无效候选在两次后停止 |
| `semantic-error` | 错用审批日期的 SQL 可执行，但独立业务预期不通过 |
| `access-control` | 写入、WITH 后写入、ATTACH、内部表、禁用列、扩展函数和多语句被拒；去掉 WHERE 也只看到当前租户 |
| `resource-limit` | 递归查询步数、返回行数及 SQL 文本预算；取消后连接仍可执行正常查询 |
| `clarification` | 日期口径、单位、状态和分母未确认时不执行统计 |

## 数据字典与口径

`employees.id` 唯一标识员工，`applications.employee_id` 指向员工，`expenses.application_id` 指向申请。一笔申请可有多条费用明细，申请表的金额属于申请粒度，不能随连接结果重复累计。源员工表含 `salary_cents`，它从不复制进候选查询快照；示例并不需要薪资信息。

所有金额用整数分。日期须为规范的业务日期字符串 `YYYY-MM-DD`，口径卡会拒绝紧凑日期、ISO周日期及非字符串，保证它们能与数据库日期按相同格式比较。它不是UTC时间戳，本实验没有实现时区转换。统计区间为 `[2026-10-01, 2026-11-01)`，按 `submitted_at`，状态只含 `submitted`、`approved`。`cancelled` 不进入本次金额及分母。

| 返回字段 | 含义 |
| --- | --- |
| `total_cents` | 合同范围内已知申请金额之和；SUM 忽略 NULL |
| `application_count` | 合同范围内全部申请数，包含金额或上限未知的申请 |
| `comparable_count` | 金额和适用上限均已知的申请数 |
| `over_count` | 金额大于上限的申请数 |
| `over_rate` | over_count / comparable_count；无可比较申请时为 NULL |

“上限未知”不能按未超标塞进分母。fixture 的 `limit_cents` 是已给定的适用上限；本实验不重新推断政策，也不假称已经连接第 14 章。金额与日期选择属于公开的任务合同，模型或候选 SQL 不应取得 `expected.json` 中的隐藏预期。

## SQLite 实际控制边界

可信宿主按测试用户 alice/bob 映射 tenant-a/tenant-b，通过固定参数化查询从只读源文件复制允许行，创建每个调用者独立的内存数据库。候选只能取得这个连接上的执行入口，不能决定租户、源连接和源路径。因此 `WHERE 1=1` 仍无法读到其他租户。真实服务必须用认证身份替换本地测试映射，不能让用户自由传入 `user='bob'`。

执行层限制 SQL 文本大小、一个语句、允许表列/函数及只读操作。`set_authorizer` 在 SQLite 编译时拒绝受限访问；带 `WITH` 的 DELETE 也会被拒绝。`PRAGMA query_only=ON` 是另外一道写入限制，本身不提供租户隔离。SQLite 的 `COUNT(*)` 可能触发表读取且列名为空，本实现只允许已知快照表的这种读取。[SQLite authorizer](https://www.sqlite.org/c3ref/set_authorizer.html)

进度回调每约 100 个虚拟机指令检查累计步骤和期限，回调非零时中断；返回结果取 `max_rows+1` 检测超限，超限结果不按成功返回。支持 `Connection.setlimit` 的 Python 运行时额外降低字符串长度、列数和表达式深度。该组合不是精确 CPU/内存硬限额或操作系统沙箱；生产运行不可信 SQL 还需进程、数据库资源和基础设施层隔离。[进度回调](https://www.sqlite.org/c3ref/progress_handler.html)

## 外部模型候选入口

让你选定的真实模型根据 `complete_card()` 和公开 Schema 产生一份 JSON 文件，例如：

```json
{"sql":"SELECT ...","provenance":{"model":"填入实际模型与版本","prompt_version":"填入自己的版本"}}
```

然后执行：

```bash
python3 -m examples.sql_agent_lab --scenario candidate --candidate-file .local/my_candidate.json --output .local/sql_candidate
```

这个命令在三份固定实例上执行同一 SQL，使用固定 `:start`/`:end` 参数，并独立评分；不会再次调用模型，也不会核验 provenance 是否真实。示例 `SELECT ...` 是文件格式说明，需换成完整候选。先用 `lab.py` 的 `CORRECT_SQL` 验证接入，再换模型生成 SQL；准确率、成本和稳定性需要另建未泄题任务集、固定模型/提示版本并记录真实请求。

## 语义评测与参考

`data/expected.json` 独立列出三组统计结果，执行器与预制修复函数不读取它。评分比较结果字段，允许等价 SQL，不要求字符串相同；单元测试额外验证去掉权限过滤、同金额、空值和错误日期。有限数据集仍不能证明任意 SQL 等价。[Distilled Test Suites](https://arxiv.org/abs/2010.02840) 说明多数据实例语义评测的思路。

[Spider 2.0](https://github.com/xlang-ai/Spider2) 和 [BIRD-Interact](https://github.com/bird-bench/BIRD-Interact) 可用于理解更复杂的企业工作流与交互评测，核查日 2026-10-31。本实验没有安装或复现它们，不搬用其模型排行榜，也不把三个教学数据库称作完整基准。扩展时固定数据集版本/提交、适用方言和执行预算，先验证数据库确实成功载入。
