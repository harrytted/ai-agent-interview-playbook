# 知识摄取与索引生命周期实验

配套 [第 14 章](../../advanced/14-ingestion-and-index-lifecycle.md) · [Q096–Q098](../../docs/advanced/14-ingestion-and-index-lifecycle.md)。Python 3.10+，仅标准库，全部人物、地区和金额为虚构教学数据。

这里实际读取 Markdown、解析表格、建立词项倒排索引、查询与持久化发布。没有调用 Embedding、OCR 或语言模型；词项命中和版本控制通过不代表语义检索质量通过。

## 运行与证据

在仓库根目录运行：

```bash
python3 -m examples.knowledge_pipeline_lab --scenario all --output .local/knowledge_pipeline_lab
python3 -m examples.knowledge_pipeline_lab --scenario interruption --output .local/knowledge_pipeline_retry
python3 -m unittest discover -s tests -p 'test_knowledge_pipeline_lab.py' -v
```

返回码 0 表示所选场景的验收断言全部成立。根输出包含汇总 `result.json`、`grade.json`、`trace.jsonl`；每个场景包含详细三件套、源文档副本、`store/state.json`、不可变内容的 generation 文件和 staging 日志。根轨迹只汇总场景，具体 `document_staged`、`published`、`query`、`access_revoked` 事件在场景轨迹。

| 场景 | 实际操作 | 应观察到的结果 |
| --- | --- | --- |
| `normal` | 以两个业务日期检索同一政策 | 10 月 31 日 600 元，11 月 1 日起 700 元，均有表头和源位置 |
| `duplicate` | 重复提交同一完整清单 | 仍是三份版本记录，三份复用，块数量不增加 |
| `update` | 将新版金额改为 720 元 | 只重新解析一份，块 ID 保持、内容哈希变化，旧 700 不再命中当前索引 |
| `interruption` | 修改两份资料，暂存一份后中断，再创建新实例 | 中断期间仍读旧 generation；重跑复用已暂存对象，最终金额 730 |
| `delete` | 从完整源清单中删除 v2 | 当前与指定旧 generation 均不返回 v2；保留的 v1 仍支持历史日期 |
| `revoke` | 撤回 employee 读取资格，再回退索引 | 当前、旧快照和回退后都拒绝 employee，admin 仍能读取 |
| `switch` | 新索引发布后切回旧 generation | 一次查询只使用一份完整索引；当前授权与删除状态保留 |
| `invalid-source` | 删除必要的有效日期 | 拒绝发布，旧索引继续可读 |

## 源数据和身份合同

`data/manifest.json` 是**完整清单**，不是追加事件。每条包含 `doc_id`、`version`、源 URI、生效起止和教学身份标签；`path` 在载入时由 `file` 转为本地路径。遗漏的版本在新发布后不可见。增量指仅重处理指纹变化的源文件；本版仍重建完整倒排表，不能称为数据库级增量 posting 更新。

稳定文档身份为 `doc_id@version`。每段正文要有 `<!-- block: key -->`；简单表格第一列必须为 `条款ID`，块身份由文档版本、marker 和行 ID 派生。修改金额不会改块 ID，删除后也不会与下一行碰撞。没有通用 Markdown 解析器：不支持合并格、转义竖线、多行单元格、代码围栏或扫描件，遇到不支持的输入拒绝处理。

业务时间采用 `valid_from <= 查询日期 < valid_to`；无截止日期表示开放区间。同一文档的版本区间重叠会被拒绝。这不是“系统当时知道什么”的双时间模型，旧 generation 只是可检查的索引快照。源 URI 为 `fixture://` 定位符，示例行号指向仓库中的对应 Markdown，不能当作可访问的公网引用。

检索将 ASCII 连续字母数字作为一个词项、汉字拆成单字，对非空查询词项做 AND 求交；排序按命中词频和块 ID。此规则便于复算，不具备中文分词、同义词理解或 BM25 保证。标题会进入块文本，查询“海岚 住宿 上限”比只查“海岚”更能定位金额条款。

## 发布、恢复与权限

`publish` 校验全部元数据 → 复用旧对象或读取 staging → 解析变化源 → 建倒排索引 → 写完整 generation → 最后原子替换 `state.json`。一个读者先读一次 state，再读其指定 generation，因此不会看到半个新索引。已解析对象保存在 staging，可由新的 `Pipeline` 实例重用。

这里只支持同一本地文件系统、单写者；没有分布式锁、并发发布冲突解决或断电后的端到端持久性承诺。文件写入执行 flush/fsync，指针采用 `os.replace`；若需要跨机器一致性、对象存储或硬件故障保证，应重新设计存储事务。

state 中当前 catalog 决定可访问版本及 principal。检索即使指定旧 generation，也要经过**当前 catalog**，因此删除、撤权不会随索引回退失效。`activate` 不回退 catalog。重新 `publish` 的完整清单是可信权限来源，若管理员再次提交允许 employee 的清单，就会重新授权；本例没有外部身份服务或独立审批工作流。旧文件仍留在实验目录，撤权不等于磁盘安全擦除；需要清理的旧模型上下文和外部缓存也不在本实验中。

## 使用自己的简单 Markdown

下面直接调用实际摄取接口，不使用场景脚本中的初始化与故障注入：

```python
import json
from pathlib import Path
from examples.knowledge_pipeline_lab.lab import Pipeline

directory = Path("examples/knowledge_pipeline_lab/data")
manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
sources = [{**entry, "path": str(directory / entry["file"])} for entry in manifest]
pipeline = Pipeline(".local/my_knowledge_index")
pipeline.publish(sources)
rows = pipeline.query("海岚 住宿 上限", "2026-11-12", "employee")
print(rows[0]["text"], rows[0]["source_location"])
```

要改变源数据，复制数据目录、调整清单和 Markdown 后传给 `publish`。场景 CLI 每次从仓库 fixture 建立新工作区，会重置自己拥有的教学输入，不用于保存手工修改。

## 独立评分与选做

摄取和查询代码不读取 `data/expected.json`；场景执行完成后，`grade` 才读取独立预期。单元测试另外改变金额、日期区间、条款 ID、权限和实例进程，核验对象及实际查询结果。该设计避免把“解析函数返回了 success”直接当作任务成功，仍不代表覆盖所有真实文档。

可选对照 [LlamaIndex Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/) 的处理链、缓存和文档管理，以及 [LightRAG](https://github.com/HKUDS/LightRAG) 的图派生更新与删除。外部入口核查日为 2026-10-31，实验未安装这些依赖，也未声明某个未运行版本的兼容性；选做时固定包版本和源码提交，并沿用相同变更集与独立查询预期。
