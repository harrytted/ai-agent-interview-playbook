# 事件接收、合并与主动任务实验

对应[学习章17](../../advanced/17-event-driven-and-proactive-agents.md)与[Q105–Q107](../../docs/advanced/17-event-driven-and-proactive-agents.md)。仅用Python标准库，真实写入SQLite接收账本、对象版本、派生任务和本地通知箱，不调用模型，不连接消息中间件或外部通知服务。

```bash
python3 examples/event_agent_lab/lab.py --scenario all --output .local/event_agent_lab/all-report.json
python3 examples/event_agent_lab/lab.py --scenario crash_recovery
python3 -m unittest discover -s tests -p 'test_event_agent_lab.py' -v
```

`--scenario`支持`normal`、`duplicate`、`out_of_order`、`crash_recovery`、`receive_recovery`、`cancelled`、`debounce`、`conflict_resolution`、`budget_and_loop`、`authorization`。每个场景使用新的临时数据库，结束前将真实数据库快照写入报告；崩溃场景在同一场景内关闭连接并重新打开同一文件。报告目录另有`trace.jsonl`、`result.json`和`grade.json`。逻辑秒由调用者传入，不等待真实时钟。

`expected.json`是独立期望；评分器对比任务数、通知数、对象版本和持久预算，测试另用不同事件ID、金额、版本与取消时序检验迁移。预算是每订阅允许接受的任务总数，不是模型token计费。

接收器先在事务中保存事件处理决定、对象和待派发项；到期派发时在同一事务中接受任务、扣预算和写Outbox，最后记录输入确认。`receive_recovery`在接收提交后、派发前中断，重投会先恢复到期派发再确认；`crash_recovery`在派发完成后、确认前中断，重投不重复接受任务。未到去抖期限的待处理项由显式定时入口`flush(now)`派发；本实验不运行常驻调度器。SQLite事务与唯一键是此实验的实际机制，单进程顺序调用不证明多实例竞争、外部消息恰好一次送达或生产认证。

与[服务章16](../../advanced/16-service-deployment-and-operations.md)的接口对应：`intent_id`作为任务接受幂等键，`owner`来自可信订阅，`run_id`对应接受后的执行标识，`version/content`是固定任务输入。这里的`tasks.state=accepted`只代表本地登记成功，尚未调用16的HTTP服务或运行复核工作；对接时应在服务端按同一意图键查重，并保留请求丢失后的查询路径。

同版不同正文会持久标记`conflicted=1`，清除该版本未派发项；同版重投不能解除隔离。只有可信更高版本才能解决冲突，即使它正文与最早保存的正文相同，也重新建立复核候选并引用新版本。冲突不会在本实验中追溯撤回已接受任务或既有Outbox；消费端停止/补偿需另接服务合同。

触发资格由有效订阅和对象匹配决定；`review_allowed`决定能否接受复核任务；`notify`和内容变化决定是否建立本地通知。任意一项允许都不授予另外两项权限。取消订阅会删除尚未派发项；已接受任务不会在本实验中自动撤回，生产对接需另定义取消范围和竞争顺序。

`outbox.state=local_pending`表示本地通知对象存在，正文包含版本与条文；它不表示邮件、飞书消息已送达。事件来源由本地夹具提供，真实接收Webhook前还需验证来源与签名，不能信任外部载荷自行声明的`origin`。

参考：[Cloudflare Agents调度](https://developers.cloudflare.com/agents/api-reference/schedule-tasks/) · [SQLite事务](https://www.sqlite.org/lang_transaction.html) · [AWS Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)。
