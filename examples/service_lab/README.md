# Agent任务服务实验

Python 3.10+ 标准库、POSIX环境（macOS/Linux）。真实运行本地HTTP、任务SQLite账本、单Worker和独立业务SQLite库。政策判断使用原政策助手的资料与适用函数，没有调用真实模型；公开 `demo-*` token只是受控测试身份。

```bash
python3 -m examples.service_lab.lab --scenario all --output .local/service_lab/checks
python3 -m unittest discover -s tests -p 'test_service_lab.py' -v
```

自检用临时端口并清理进程，不能以永不退出的服务器命令替代验收。每批生成新目录，各场景有 `http.jsonl`、`result.json`、`grade.json`；`data/runs/<run-id>/`另有manifest、任务事件与结果，数据库是恢复依据。默认不联网，不需要凭据。

| 场景 | 验证内容 |
| --- | --- |
| normal | 接收后后台读取，业务成功与HTTP接收分开 |
| duplicate-isolation | 同键同内容同任务、异内容409、owner隔离 |
| clarification-restart | 等待保存、重启后补日期、累计预算不归零 |
| approval-correction | 获批后改城市，旧批准失效、旧证据清除、取消不创建对象 |
| crash-recovery | 独立业务库已提交，本地未确认；重启按原意图只确认一个对象 |
| release-rollback | 坏候选不激活、已发任务绑定版本、新入口切换/回退 |

服务演示：

```bash
python3 -m examples.service_lab.lab serve --root .local/service_lab/server --port 8765
```

打印 `{"ready":true,"url":...}` 后可使用[学习章16的curl步骤](../../advanced/16-service-deployment-and-operations.md)。Ctrl-C/SIGTERM会停止接收并等待本地Worker退出，文件锁防止同root启动第二进程。`/health`无认证且不返回任务内容；其他任务入口需 `Authorization: Bearer demo-alice` 或 `demo-bob`。

`POST /tasks`需 `Idempotency-Key`，JSON字段仅 `city`（海岚/云洲）、可选 `trip_date`、`amount_cny`、`reason`、`mode`（query/ticket）。服务拒绝客户端自填身份。`GET /tasks/{id}` 与 `/events`仅本人可读；`/metrics`仅本人聚合。POST后不保证Worker已经完成。

后续动作：`reply`只补缺日期；`correct`改city/trip_date/amount_cny/reason，递增revision并重新取证；`approve`提交当前草稿的request_id和payload_hash；`cancel`、`resume`提交空JSON对象。批准核对后先进入 `write_prepared`，此时取消/更正能阻止派发；Worker下一事务提交 `dispatch_committed`并进入writing后才接管派发，这次事务提交是本地线性化边界。在途写不允许直接更正；结果未知必须用原操作ID核对。取消后只查询已有对象，查无结果仍未知、不新建；未取消的恢复可按原操作ID幂等重试。取消不等于对象被删除。

`POST /releases`只允许 `demo-operator`，body为 `{version:"v2",policies:[...],activate:false}`（实际发送合法JSON）。所有条目的必要结构和三个固定Alice政策查询通过后方可登记，查询使用实际授权与适用逻辑，空权限或异租户也会阻断；`{version:"v2"}`激活，`{version:"v1"}`回退。合法撤权应另有预期拒绝的发布验收，不能静默改掉本固定成功集。门槛是固定smoke，不证明全部政策语义、Embedding或模型质量。Operator不能读取用户任务。

故障注入必须显式 `--allow-faults` 后，提交 `fault:"after_remote_commit"`；默认Worker记录故障并停止。仅在临时实验目录显式加 `--crash-once` 时，服务会在该窗口真实退出73。保留root，用相同root重新启动，查询得到 `write_outcome_unknown`；`resume`确认原对象。自动测试已覆盖这条真实跨进程路径。

容量与边界：一Worker、每任务最多8次决策/12次工具派发；固定日期和城市政策读取，等待人工不占Worker。数据库事务串行化API/Worker状态更新；业务库与任务库没有共同事务。没有生产认证、HTTP TLS、完整浏览器UI、外部消息通知、远程上下文删除、多实例调度、自动补偿或真实模型质量证明。

[学习章16](../../advanced/16-service-deployment-and-operations.md) · [题源Q102–Q104](../../docs/advanced/16-service-deployment-and-operations.md) · [原政策助手](../policy_agent/README.md)
