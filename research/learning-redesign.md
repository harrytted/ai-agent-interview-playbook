# 本轮学习内容改版与验证边界

核对日期2026-10-30。改版以同一虚构政策案例串联概念、机制图、输入、实际观察和条件变化；保留原10章基础、12章进阶和92道题的ID与路径。首个入口为 [走完一次任务](../learning/00-first-agent.md)，代码与记录为 [政策实验](../examples/policy_agent/README.md)。

## 从调研采用了什么

| 来源 | 采用的组织方法 | 本仓库的具体落点 |
| --- | --- | --- |
| [Microsoft工具课](https://github.com/microsoft/ai-agents-for-beginners/blob/main/04-tool-use/README.md) | 先暴露完整协议，再解释框架隐藏部分 | schema、call_id、实际回包、第二轮输入 |
| [Hello-Agents第一章](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter1/第一章%20初识智能体.md) | 概念与逐轮例题相邻 | 系统图与三条可复现路径 |
| [Hugging Face Dummy Agent](https://huggingface.co/learn/agents-course/en/unit1/dummy-agent-library) | 用错误观察暴露执行边界 | 工具声明与执行分开，旧证据触发核对 |
| [LangChain Academy](https://github.com/langchain-ai/langchain-academy) | 同一案例逐步增加机制 | 查询、澄清、纠正、批准、恢复共享数据 |
| [Lilian Weng综述](https://lilianweng.github.io/posts/2023-06-23-agent/) | 组件地图与后续机制关联 | 八图各回答一个问题，2023年实现作历史来源 |
| [Anthropic架构文章](https://www.anthropic.com/research/building-effective-agents) | 按任务选择工作流与动态决策 | 不将独立规划器或长期记忆列为必要组件 |
| [上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 当前输入由候选材料选取 | 实际PolicyView、来源与取舍说明 |
| [Agent评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 区分过程、评分与环境结果 | 独立期望、实际对象数及内容、故障变式 |
| [小林组件讲解](https://xiaolinnote.com/ai/agent/2_components.html)及同栏目抽样 | 简短概念入口、围绕误解逐步解释 | 基础工作定义、输入样本、纠错状态与练习 |

调研比较的是所抽取章节的方法与边界，不是学习效果排名。小林栏目共抽读12篇，未审计全站。外部文字与图片不直接迁入；图采用自己的案例和布局，机制来源在相邻课程列出。记忆保存、固定组件必要性、规划成本排序与未经同任务实测的性能比例均不当作标准结论。

## 已交付与未实现的范围

已交付的离线实验包含12个主任务及10个额外评测项，默认不联网。状态、工具、批准和故障是受控教学实现；T12使用两个Python进程和两个SQLite数据库验证特定提交窗口。所有声明须与 [实验边界](../examples/policy_agent/README.md)及实际测试一致。

进阶中的交接包、压缩、技能、规划比较、缓存、浏览器对象和训练样本分别标明设计推演或模拟。没有把这些文档样本宣称为生产多Agent团队、真实浏览器控制、GPU部署或完整训练管线。

真实模型接入有离线HTTP夹具测试；本分支未执行真实付费请求，因此没有模型成功率、真实调用费用或live_verified记录。离线确定性通过不代表模型能力。

## 本地技术验收记录

本分支在2026-10-30完成以下本地检查：全仓134项unittest、新实验22/22项离线任务、八图合同、原有三组实验、严格站点构建和HTML链接检查。构建输出70个HTML页面，92题均保持原ID和锚点。自动检查不覆盖所有外部URL的当前可达性。

真实Chromium对首页、首次任务、工具/MCP三页分别检查360/768/1280px，共九组；页面没有横向溢出，SVG加载和折叠交互正常。另用受控反例修复了矛盾回答显示、伪引用、完成态撤权、工具枚举合同和合法主张顺序被误判的问题。上述为本地技术证据，未代替外部读者试读。

## 试读怎样判断

目前没有招募或完成外部读者试验，也没有留存或面试成功率数据。自动检查通过只能报告技术验收结果。

后续试读可选5名会Python但未做Agent的读者、3名有RAG经验的读者。使用正文未完整解答的新条件，记录能否解释机制、预测下一步、修改输入并引用证据，另记提示次数。同一个阻塞在两个独立读者处出现就修复并复测；小样本用于发现问题，不代表总体收益。

建议先检查 [首次任务](../learning/00-first-agent.md)：是否能独立运行；图中箭头是否对应事件；日期删掉后是否知道为什么等待；旧资料出现后是否能解释为何追加查询。再选一个进阶完成物检查迁移能力。不要仅以“页面更长、图片更多”判定改进。

[返回资料目录](README.md) · [基础课程](../learning/README.md) · [进阶课程](../advanced/README.md)
