# 模型协议实验：从原始字节到完整往返

Python 3.10+ 标准库，默认不联网。作者编写的 SSE 夹具采用 Claude Messages 的 text/client tool_use 事件形状；这不是供应商实测记录或完整协议实现。

```bash
python3 -m examples.model_protocol_lab.lab --scenario all --output .local/model_protocol
python3 -m unittest discover -s tests -p 'test_model_protocol_lab.py' -v
```

| 场景 | 改变什么 | 应观察到什么 |
| --- | --- | --- |
| normal | 每次只读取一个字节 | 中文与两项工具参数完整重组，海岚700/云洲650引用成立 |
| missing-result | 删除第二项工具结果 | 下一轮之前拒绝不完整回填 |
| duplicate-id | 两个工具复用同一调用 ID | 协议错误，不能调度 |
| truncated | 结束原因为 max_tokens | 不派发该响应的调用 |
| refusal | 结束原因为 refusal | 拒答独立记录 |
| disconnect | 删除 message_stop | 未知完整结果，不标成功 |
| semantic-error | 将700写成7000 | JSON仍合法，证据核验拒绝 |
| final-truncated | 工具全部返回后，最终回答max_tokens | 不读取不存在的完整答案，报告截断 |
| final-refusal | 工具全部返回后，最终回答refusal | 保留已有读取证据，任务记录拒答 |

产物在 `<output>/<scenario>/`：`raw.sse`、`answer.sse`、`trace.jsonl`、`result.json`、`grade.json`。故障变式先修改输入字节，再解析与保存；因此可直接重放这两份SSE文件，复现重复ID、截断、拒答或错误金额。正常结果包含 `next_request.messages`，保留完整 assistant 块与按 ID 对应的全部结果。`expected.json` 是评分预期，不传给工具执行器或答案校验器。

工具只支持固定教学日2026-11-12及海岚/云洲。解析器支持UTF-8跨读、CR/LF/CRLF、多行data和注释；不支持thinking、server tools或任意未来事件，遇到不支持内容会停止。它从真实原始字节解析，未将预制终态当作解析结果。

## 可选真实供应商调用

真实模型选做沿用[政策助手的显式 live 入口](../policy_agent/README.md#可选真实模型接口测试与实际效果分开)。先在环境中配置 `ANTHROPIC_API_KEY`，不要把密钥写进源码或命令；可用 `ANTHROPIC_MODEL`显式指定可用模型。适配器当前固定API版本2026-10-21，默认模型claude-haiku-5-5，以[实际源码](../policy_agent/live.py)及运行后的provider.json为准；供应商不支持该配置时报告错误，不静默换模型。

```bash
python3 -m examples.policy_agent run --task 住宿金额核对 --mode live --run-id live-api-13-a
```

上面是实际联网且可能付费的命令，本轮实现与验收未执行它。默认测试不会读取凭据、联网或发起付费请求。该适配器是非流式真实接口入口；不要把本实验离线SSE通过写成真实供应商流式调用通过。

需要小任务集重复采样时，可在明确接受调用费用后运行下面的四次有界流程。两类任务各重复两次，每次使用独立运行目录；调用失败、拒答和预算耗尽仍保留在四次分母中。它先保存原始trace/provider/result，再单独运行独立评分，没有用模型自评代替grade。

```python
import json, os, subprocess, sys, time
from pathlib import Path
from examples.policy_agent.grade import grade

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise SystemExit("先在环境配置凭据，再明确决定是否运行付费采样")
root = Path(".local/live-protocol") / str(time.time_ns())
root.mkdir(parents=True)
report = []
for task in ("T01", "T05"):
    for repeat in range(2):
        run_id = f"sample-{task}-{repeat}"
        try:
            process = subprocess.run(
                [sys.executable, "-m", "examples.policy_agent", "--root", str(root),
                 "run", "--task", task, "--mode", "live", "--run-id", run_id],
                capture_output=True, text=True, timeout=90)
            returncode, output = process.returncode, process.stdout + process.stderr
        except subprocess.TimeoutExpired:
            returncode, output = 124, "Host sampling deadline exceeded; inspect saved run before retry."
        folder = root / run_id
        folder.mkdir(exist_ok=True)
        (folder / "host-output.txt").write_text(output)
        try:
            score = grade(folder)
        except (OSError, ValueError, KeyError) as error:
            score = {"passed": False, "error": type(error).__name__}
        (folder / "grade.json").write_text(json.dumps(score, ensure_ascii=False, indent=2))
        report.append({"run_id": run_id, "returncode": returncode, "passed": score["passed"]})
(root / "sampling-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
```

此流程是可选采样方法，不附带真实模型成绩或成功率承诺。若需比较策略，还应预先固定输入、版本、预算与评分，不把四次示范当作统计充分的生产评测。

[学习章13](../../advanced/13-model-api-and-output-contracts.md) · [题源Q093–Q095](../../docs/advanced/13-model-api-and-output-contracts.md)
