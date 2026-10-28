# 08 · Coding 与 Computer Use：让执行环境提供真实反馈

[上一章：多 Agent 系统](07-multi-agent-systems.md) · [进阶目录](README.md) · [下一章：评测与反馈](09-evaluation-and-feedback.md)

Coding Agent 改代码，Browser Agent 操作网页，Computer Use 操作桌面。它们共享一个核心难题：模型提出动作时看到的世界，可能已经与实际环境不同。可靠运行依赖一套 harness，负责组织输入、执行工具、收集观察、保存状态、控制预算并验证终态，而不是只靠一句“完成后自行检查”。

## Coding Agent 的闭环围绕仓库证据展开

企业政策助手需要修复“跨时区日期让旧政策被错误选中”。首先确定目标行为与工作目录，读取仓库规则和依赖配置，再定位日期解析、版本选择及相应测试。仓库索引可以提供文件、符号和调用关系线索；它若落后于当前 commit，仍要回到真实源码确认，不能直接按索引摘要修改不存在的函数。

一个紧凑闭环是“定位证据→复现问题→提出最小补丁→运行相关测试→分析输出→决定继续或结束”。SWE-agent 1.0 的架构将 Agent 与环境分离：运行环境管理 shell，历史处理器压缩交互记录，动作解析后再交给环境执行，说明这些能力属于系统运行时。[SWE-agent 架构](https://swe-agent.com/latest/background/architecture/)

模型生成的 diff 只是候选补丁。应用前检查路径范围、基线版本与补丁是否匹配；应用后读取实际差异，防止误删其他修改。测试输出也是待解释的观察：命令退出码、运行数量、失败内容和环境错误共同决定结论，不能仅因日志出现“passed”就宣布需求完成。

## 一次修复怎样留下可重现证据

第一步，用确定的时间与政策版本构造失败样例，保存修复前的失败结果；如果测试本来就无法启动，先区分环境故障与业务缺陷。第二步，检查日期比较究竟使用当地日期、UTC 时间还是业务生效时区，明确合同后修改对应模块，而不是在所有调用处随意加一天。

第三步，补充刚好跨日、生效瞬间及无时区输入的案例，运行针对性测试。第四步，按影响范围检查关联功能与实际 diff；若发现新失败，回到具体断言定位原因，不自动删除测试。第五步，交付补丁、复现命令、测试结果和剩余问题，区分“命令已运行”“测试已通过”“用户目标已验收”。

固定仓库版本、依赖锁文件、环境镜像、必要配置和数据快照，有助于重建相同实验。外部服务响应、系统时间与随机性也要控制或记录。重建环境不只是保存一个对话 transcript；没有依赖和数据，重放命令仍可能得到不同结果。

## 文件系统抽象不等于执行沙箱

Agent 看到的 `/workspace` 可能是状态中的虚拟文件、真实本地目录或远程沙箱。Deep Agents 的 backend 决定文件工具映射到哪里，执行隔离是另一项能力；本地 shell 与受隔离环境的权限边界不同。[Deep Agents Backends](https://docs.langchain.com/oss/python/deepagents/backends)

为修复任务挂载必要仓库与临时目录，限制可写路径、出站域名和运行资源。路径检查要考虑规范化、符号链接以及检查后文件变化；只验证字符串以 `/workspace` 开头，不能证明最终写入仍在该目录。依赖安装脚本和仓库测试会执行代码，它们应受同样的环境权限约束。

凭据不应成为仓库索引、模型上下文或一般测试输出的一部分。需要访问服务时，让受控执行器注入最小范围、有限期限的凭据，并对日志脱敏；禁用真实生产密钥后，测试必须明确使用替身还是测试服务。容器是否隔离网络、宿主挂载和特权能力，要由实际配置验证。

## Browser 与 Computer Use 的观察方式不同

网页任务可以利用 DOM、可访问性树和语义定位器，必要时结合截图。桌面任务更多依赖截图、窗口状态与坐标。当前 Claude 文档也区分 page-aware 的 browser use 与完整桌面的 computer use；两者工具集的执行合同不能互换。[Browser use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)、[Computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)

对“打开政策后台、更新一份草稿的生效日期”，先确认当前系统、对象 ID、草稿状态和目标字段，再执行单个或短批动作，随后重新读取。导航、弹窗、筛选和虚拟列表都可能使旧观察失效。Playwright locator 会在动作时重新定位匹配元素；这改善重渲染适应性，但仍要确保定位语义对应正确对象。[Playwright Locators](https://playwright.dev/docs/locators)

有些浏览器执行器返回临时元素引用。引用只对对应标签页和有效页面状态成立，页面发生实质变化后需要重读；遇到 stale reference 应返回具体错误并停止依赖它的后续动作，不能继续把键盘输入打到未知焦点。[Browser use 引用与错误处理](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool#handle-errors)

## 视觉定位也要保持观察新鲜

截图坐标依赖窗口位置、缩放、滚动和视口。若刚发生滚动，不能沿用旧图里的按钮坐标；应重新截图，识别目标与遮挡，再行动。表格中每行都有“编辑”时，先确认行标题或对象标识；仅看按钮样式无法区分对象。Canvas 或远程桌面缺少可靠文本结构时，视觉可以补足定位，但不能省略对象核对。

一次“保存”点击返回成功，只说明输入动作完成。还要确认页面显示新日期、目标对象仍正确、保存状态或版本已变化；若支持独立读取，可核对持久结果。出现响应超时后，应先重新读取当前状态，避免重复点击造成重复提交。截图、页面文本、工具返回和外部对象状态各有覆盖范围，组合起来才能支持任务结论。

## 多模态证据与人工介入

页面文字、图片、注释与仓库文件都属于输入资料，不能自行赋予发送、删除或读取其他数据的权限。工具环境应限制高影响动作，遇到需要用户决策的具体操作时暂停，展示目标对象、字段变化、证据与后果；恢复时重验页面和参数，防止审批等待期间对象被修改。Computer use 文档将低权限隔离环境、网络限制和必要的人类确认列为实施要点。[Computer use 安全考虑](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool#security-considerations)

运行记录保留足以关联动作的证据：仓库 commit、补丁摘要、测试输出，或标签页 URL、对象 ID、动作前后状态与对应截图。截图未显示的隐藏字段不能据此宣称已检查；图片中的文字识别不确定时，应放大或通过另一条可用信息渠道确认。无法稳定定位、出现权限变化或关键结果不确定时，交给人工带着状态继续。

## 设计练习

设计一个流程，先修复日期选择逻辑，再在测试后台更新草稿。注入三个故障：索引指向旧文件、点击前页面重排、保存后响应丢失。验收要求：代码定位回到当前源码；新观察定位正确对象；保存超时先读状态；补丁有可复现测试；任何一步都不把工具动作成功直接当成业务目标完成。

## 自检与答案

<details><summary>1. 仓库索引给出的函数名能否直接当作修改依据？</summary>

需要回到当前源码确认版本、定义与调用关系，索引可能过期。
</details>
<details><summary>2. 用了语义 locator 是否无需重读页面？</summary>

仍需重读关键状态。定位器重解析元素，不保证业务对象、权限与页面含义没有变化。
</details>
<details><summary>3. 保存按钮点击成功后为什么还要验证？</summary>

点击是动作结果；持久化内容、目标对象和任务约束才决定是否完成目标。
</details>

## 参考资料

- [SWE-agent Architecture](https://swe-agent.com/latest/background/architecture/)：环境、模型历史、动作解析与执行闭环。
- [Deep Agents Backends](https://docs.langchain.com/oss/python/deepagents/backends)：虚拟文件、本地文件与执行环境的区别。
- [Claude Browser use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)、[Computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)：观察、动作、错误与环境配置。
- [Playwright Locators](https://playwright.dev/docs/locators)：基于页面语义的重新定位。
