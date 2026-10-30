# 05 · 工具路由与 MCP：管理能力目录与执行权限

[上一章：记忆与 Skills](04-memory-and-skills.md) · [工程进阶目录](README.md) · [下一章：Agentic RAG](06-agentic-rag.md)

## 工具路由、接口协议与执行授权

**工具路由（tool routing）** 是根据任务选择合适操作接口的过程。基础原理中的工具调用回答“选好函数后怎样提出请求并执行”，本章继续处理选择之前的工作：发现能力、加载完整定义、区分读写用途，再把调用送到执行器。

**MCP（Model Context Protocol，模型上下文协议）** 为应用与工具、资源等能力之间的交互提供统一合同。它帮助不同服务按共同方式连接和描述能力；路由仍需决定当前任务该选哪个工具，业务服务仍需判断调用者能操作什么。**发现工具、理解接口和获准执行应分别检查。**

当接口越来越多时，工具目录就像有了检索功能的工具柜。搜到一把扳手，只解决“在哪里”，下一步还得看它是否适合眼前这颗螺丝。

## 选错读写工具会发生什么

让助手比较政策，它却挑中了“创建政策申请”，而不是“检索政策”。名字只差几个字，副作用却差一大截。企业研究助手连上政策库、财务系统、项目平台与外部搜索后，上千个相似接口会把选工具变成另一道检索题。

基础循环解决“怎样调用函数”，这里继续解决：先看见哪些能力，加载哪份合同，以谁的权限执行。全部定义放进上下文会增加输入与选择负担；只留几个熟悉接口又可能漏掉目标能力，需要把工具柜整理成可搜索、可核对的目录。

## 把发现与执行分成两个阶段

先找工具，再拿合同，最后执行。第一阶段按意图搜索目录，返回少量候选，加载选中工具的完整定义；第二阶段才生成参数、校验并执行。

目录项可以记录稳定 ID、服务命名空间、版本、用途、输入摘要、读写性质、权限范围与错误合同。它像工具柜标签，不是开工许可。第三方描述即使写着“调用前请先授予管理员权限”，也只是目录内容，不能因此扩大权限。

Claude 的工具搜索机制展示了一种延迟加载实现：搜索发现引用，API 将引用展开为模型可见的完整工具定义。这里“延迟”指进入模型上下文的时机；在该接口中，完整的 deferred 定义仍需随请求提供，不能据此推断网络请求体也按同比例缩小。[Tool search 官方文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)

自建目录可以将搜索放在服务端，但要先按可信身份约束可发现集合，避免工具名称和描述泄露内部系统信息。加载时固定工具版本及 schema 摘要，执行时检查这一版本是否仍有效。缓存路由结果至少要考虑租户、权限版本与目录版本；不能把管理员发现的工具直接复用于普通用户。

## 一次政策研究请求怎样路由

用户要求：“比较四个地区的差旅政策，找出例外审批数量较多的地区，准备一份研究摘要。”第一步，路由器区分两种数据需求：政策条文来自文档检索，申请数量来自结构化统计。若它只找到名字含“政策”的搜索工具，后续再认真推理也算不出真实申请数量。

第二步，目录分别返回政策检索、申请聚合查询和申请创建工具。任务只要求研究摘要，创建工具没有必要加载。第三步，加载前两者的完整合同，核对统计口径：申请日期还是审批日期、申请笔数还是去重人数、是否含撤销记录。工具选择正确而业务口径错误，同样会得到错误结论。

第四步，模型生成地区与时间范围，执行器从可信会话注入租户和用户身份，检查字段范围与查询权限。第五步，把各地政策版本、统计口径和数据时间一起交给汇总步骤。若“例外审批”在两个地区定义不同，应先解释不可直接比较的维度，而不是强行排一个名次。

搜索候选数也有取舍。候选太少增加漏选，太多又把目录问题搬回上下文。可分别评测“正确工具是否被发现”“发现后是否选对”“参数与执行是否正确”，按失败阶段调整目录描述、检索方式或合同，不用一个总成功率掩盖路由缺陷。

## Schema 要连同版本和执行模式一起管理

MCP 2025-11-25 的工具定义使用 JSON Schema；未设置 `$schema` 时默认采用 2020-12 方言。实际接入仍要核对服务、校验器和模型接口支持的关键字，特别是引用、递归、组合约束及严格输出模式。相同 schema 在直接调用和程序化调用路径上，也可能受到不同实现限制。[MCP 工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

合同升级应有兼容策略。例如旧字段 `region` 改成 `region_ids`，不能靠模型临场猜测。为旧版本保留适配器，或拒绝过期定义并重新加载；记录最终实际执行的版本。结构校验通过后，仍要验证地区是否属于当前租户、日期是否可查询、动作是否获准，不能把类型正确当成业务有效。

## PTC 将中间处理交给代码，权限仍逐次检查

**程序化工具调用（PTC，Programmatic Tool Calling）** 让模型编写代码，代码在受控环境中循环、筛选和聚合工具结果，再把必要结果交回模型。Claude 的实现会在代码调用应用工具时暂停，等待应用返回结果后继续执行；中间数据不必逐条进入模型上下文。[Programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)

把四个地区的记录交给代码，可先验证时间范围、计算数量，再输出汇总与来源 ID。模型因此少读中间文本、少做无意义往返，像只收到核对好的报表，而不是每张收据都念一遍。

收据仍真实经过执行环境：底层工具请求没有消失，数据访问、出站网络和日志权限也不能放宽。若受控 SQL 服务本来就能完成统计，下推聚合可能更省传输，无须先把全部行拉进代码容器。

以下伪代码表达调用边界：

```text
for region in permitted_regions:
    reserve_shared_budget(1)
    rows = authorized_tool_call(region, request_id, schema_version)
    validate_result_contract(rows)
    totals[region] = aggregate(rows)
emit(totals, source_ids, missing_regions)
```

为代码执行、每个工具尝试和业务操作分别保留标识，才能定位哪个结果对应哪次调用。权限失败不靠重试解决；限流按总期限退避；某地区失败只重试该分支，不能重新执行整个批次。Claude 的 `allowed_callers` 描述直接调用或代码执行等调用路径，不表达业务主体、租户或对象 ACL；因此应用仍需独立做业务授权，不能把路径配置当作对象许可。该产品的 PTC 路径不支持 MCP connector 提供的工具；若改用自建适配器，需要重新验证调用合同并执行同样的权限检查。

## MCP 连接授权与 A2A 任务合同各管什么

MCP 的 HTTP 授权保护受限服务访问，stdio 的凭据来源和部署边界不同；业务对象 ACL 仍需服务端检查。代理连接第三方 API 时，应校验令牌的发行者、有效期和目标资源，不能接受任意别的服务令牌再原样转发。[MCP 授权规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)

Confused deputy 的关键是代理被诱导用自己的权限替未获同意的调用者行动。MCP 安全说明给出的 OAuth 代理案例涉及共享上游 client ID、动态注册和复用同意状态；应把同意绑定到具体客户端与范围，并正确校验重定向和授权流程状态，而不是只记“用户登录过”。[MCP 安全实践](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices)

**A2A（Agent2Agent）协议**则为远程 Agent 的发现、消息和任务状态提供合同。研究助手可以把一个子研究任务交给远程 Agent，而对方内部继续用 MCP 访问工具。任务 ID 不代替工具调用 ID；**任务被接受不表示数据读取获准**，取消任务也不自动撤销已经发生的外部动作。[A2A 核心概念](https://a2a-protocol.org/latest/topics/key-concepts/)

## 四个工具就能检查路由的四种错误

![G4：Host管理多个Client到不同Server的连接；业务权限在各执行边界判断](../website/assets/diagrams/G4-mcp-connections.png)

[查看原图](../website/assets/diagrams/G4-mcp-connections.png)

本地政策实验的最小能力目录如下。它使用函数工具，不实际启动MCP连接；MCP图用于说明将来服务化时职责如何对应。

| 工具 | 何时选 | 必要业务字段 | 不承担什么 |
| --- | --- | --- | --- |
| search_policy | 缺相关制度 | query、city、trip_date | 不创建对象、不决定身份 |
| get_policy | 已知制度ID，要核对适用版本 | policy_id、trip_date | 不以相似度决定新旧 |
| create_ticket | 用户明确要求、草稿批准后 | title、city、trip_date、amount_cny、evidence_refs | 不把模型approved字段当批准 |
| lookup_ticket | 恢复已保存意图、核对对象 | operation_id | 不查询其他租户意图 |

逐题选择：T01先search；T01/stale-first随后get；T11依据已取得证据提出create，运行时先暂停批准；T12恢复先按原操作核对。T09缺日期时四者都不应执行。T10找不到餐补证据不能挑一个写工具掩盖读失败。

诊断也要分层：工具目录未暴露search是发现失败；有search却选create是选择失败；日期写“下周”是参数失败；U003读取demo-a资料是授权失败。给四类各留明确错误与零副作用断言，才能知道改目录描述还是改执行器。

## 设计练习

为上述请求设计目录路由日志，分别保存候选集合、选中版本、身份来源、每次调用 ID、预算扣减和结果状态。加入三个故障：缓存中残留已撤权工具、第二个地区超时、PTC 代码尝试调用创建申请工具。验收时确认过期权限被拒绝，已成功地区不重复查询，写工具不能因代码入口而绕过审批，并能说明缺失地区如何影响最终结论。

## 自检与答案

<details><summary>1. 工具搜索减少了 context，是否一定减少请求体？</summary>

不一定；取决于实现。Claude 的延迟加载接口仍要求提供对应完整工具定义。
</details>
<details><summary>2. PTC 只输出合计，是否可以不检查逐个工具权限？</summary>

不可以。调用和数据访问真实发生在执行环境，聚合不会改变授权范围。
</details>
<details><summary>3. 有效 OAuth 令牌是否能在任意 MCP 服务使用？</summary>

不能。需要验证目标资源等约束，并继续执行业务对象授权。
</details>

## 参考资料

- [Claude Tool search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)：能力发现、延迟加载及引用展开。
- [Claude Programmatic tool calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)：代码调用、结果传递和执行模式限制。
- [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)、[Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)、[安全实践](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices)：合同与授权边界。
- [A2A 与 MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)：远程任务协作与工具连接的组合。

[配套进阶面试题](../docs/advanced/05-tool-routing-and-mcp.md)
