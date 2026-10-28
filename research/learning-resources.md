# Agent 系统学习资源：章节实读与采用说明

目标是理解机制、读懂控制流、完成可解释的实验，再衔接面试。建议从本仓库 [系统课程](../learning/README.md) 开始，按具体问题选读外部章节。

下列 7 个资源分别侧重模型基础、工具调用、Agent 循环、框架实践与评估。章节位置、适用条件与许可信息见 [learning-sources.json](learning-sources.json)。


## 教学比较

| 资源与阅读入口 | 前置与范围 | 适合采纳的教学方法 | 需要限定的地方 |
|---|---|---|---|
| [Hello-Agents](https://github.com/datawhalechina/hello-agents)：[第 3 章](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter3/第三章%20大语言模型基础.md)、[第 4 章](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter4/第四章%20智能体经典范式构建.md) | Python 与基本 API 知识；从语言模型过渡到 ReAct、计划与反思 | 先拆开模型调用、工具执行与循环，再组合验证 | 第 4 章为教学实现，文本解析与打印轨迹不能替代生产校验；第 3 章词向量数值例子有手设数据，不能当真实模型测量 |
| [Hugging Face Agents Course](https://github.com/huggingface/agents-course)：[Tools](https://github.com/huggingface/agents-course/blob/main/units/en/unit1/tools.mdx)、[First Agent](https://github.com/huggingface/agents-course/blob/main/units/en/unit1/tutorial.mdx) | 基础 Python、LLM 概念；从工具合同到 smolagents 实作 | 将工具描述、参数、执行函数和返回观察分开解释 | Tools 章的文本输入输出说明是入门简化；CodeAgent 的代码执行及远程工具加载需要单独审视执行权限 |
| [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners)：[入门](https://github.com/microsoft/ai-agents-for-beginners/blob/main/01-intro-to-ai-agents/README.md)、[Tool Use](https://github.com/microsoft/ai-agents-for-beginners/blob/main/04-tool-use/README.md) | 基础 Python 与 LLM 使用经验；以设计模式连接工具、状态与消息 | 每课先说明学习目标，工具章用消息往返连接抽象与代码 | 示例主要依赖微软生态；经典 Agent 分类与现代 LLM Agent 的工程范围应区分，环境与决策系统的边界也应说清 |
| [Anthropic Courses](https://github.com/anthropics/courses)：[工具概览](https://github.com/anthropics/courses/blob/master/tool_use/01_tool_use_overview.ipynb)、[完整工具往返](https://github.com/anthropics/courses/blob/master/tool_use/04_complete_workflow.ipynb) | Python、JSON、API；提示、工具与评测练习 | 用一个请求标识连接调用与结果，逐步补全消息历史 | 页面显示 **2026-09-15 已归档**；旧模型名和“没有服务端工具”的表述不能作为当前 API 结论 |
| [LangChain Agents From Scratch](https://github.com/langchain-ai/agents-from-scratch)：[基础实现](https://github.com/langchain-ai/agents-from-scratch/blob/main/src/email_assistant/email_assistant.py)、[人工介入实现](https://github.com/langchain-ai/agents-from-scratch/blob/main/src/email_assistant/email_assistant_hitl.py) | 能读 Python、状态和条件分支；邮件分类、执行循环与人工介入 | 对照基础版与人工介入版，定位执行前真正增加的控制 | 默认课程工具是模拟邮件／日历；真实 Gmail 接入另有实现，学习代码不能等同已集成真实服务 |
| [深入理解 AI Agent](https://github.com/bojieli/ai-agent-book)：[第 1 章](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter1.md)、[第 7 章](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter7.md) | 能修改 Python，理解 Git、JSON、REST；工程构成与任务评估 | 将模型、运行治理层和环境分开；用终态与轨迹检查学习效果 | 三组件公式是工程视角，不能替代一般 Agent 的形式化定义；案例数字须保留模型、任务与验证器条件 |
| [Neural Networks: Zero to Hero](https://github.com/karpathy/nn-zero-to-hero)：[micrograd](https://github.com/karpathy/nn-zero-to-hero/blob/master/lectures/micrograd/micrograd_lecture_first_half_roughly.ipynb)、[makemore bigram](https://github.com/karpathy/nn-zero-to-hero/blob/master/lectures/makemore/makemore_part1_bigrams.ipynb) | Python、基础导数；计算图、梯度、条件概率与采样 | 用小数据亲算梯度和负对数似然，分清训练与生成 | 是可选的模型基础补课，不是 Agent 构建教程；小型字符模型的结果不代表现代聊天模型表现 |

## 环境与费用

| 资源 | 读正文 | 运行示例的要求 |
|---|---|---|
| Hello-Agents | 可直接阅读 | 第 4 章建议 Python 3.10+，使用模型服务凭据及 SerpAPI 搜索配置；第 3 章本地模型需要下载权重、安装 PyTorch／Transformers并使用本地计算资源 |
| Hugging Face | 可直接阅读 | 首个 Agent 教程需要有推理权限的 `HF_TOKEN`，并复制 Space、安装相应依赖；模型推理与托管按所用服务的额度和计费规则使用 |
| Microsoft | 可直接阅读 | 当前 [Setup](https://github.com/microsoft/ai-agents-for-beginners/blob/main/00-course-setup/README.md) 要求 Python 3.12+；主要路径需 Azure 订阅、Foundry 项目及模型部署，并通过 Azure CLI 认证。API Key 并非所有 notebook 的必需条件 |
| Anthropic | 可直接阅读 | 工具实作含 Anthropic SDK 与 Wikipedia 依赖，会访问模型及外部数据服务；归档教材需要先对照当前官方文档迁移，不能直接沿用旧模型 ID |
| LangChain | 可直接阅读 | README 要求 Python 3.11+、项目安装、模型凭据与 LangSmith 配置；mock 工具不表示模型调用也离线，真实 Gmail 另需授权与配置 |
| bojieli 技术书 | 可直接阅读 | 当前 README 给出 Python 3.11–3.13 与按章依赖；模型实验需凭据，部分实验另需浏览器、CUDA 或其他运行时。运行时按所选实验配置环境 |
| Karpathy | 可直接阅读 | 两个抽读 notebook 使用 NumPy／Matplotlib、PyTorch 或 Graphviz；bigram 例子读取 `names.txt`，要准备对应数据。所读教学单元可在本地计算，不需要模型 API，需先准备相应依赖与数据 |

实际费用由模型、托管、搜索和计算服务的当前计费规则决定。

## 建议阅读顺序

1. **先做一张边界图。**读本仓库系统课程的导读与基础章，再选读微软入门或技术书第 1 章。能把用户、模型、运行时、工具、环境和状态分别标出来即可前进。
2. **补足模型最小常识。**读 Hello-Agents 第 3 章的语言模型、token 与推理部分。若梯度、概率和采样仍难理解，再补 Karpathy 两个小练习；无需先学完完整训练课程。
3. **手工走完工具往返。**先看 HF Tools，随后对照 Anthropic 归档 notebook 的请求／结果关联，同时用当前官方工具文档修正版本差异。
4. **理解循环再使用框架。**读 Hello-Agents 第 4 章，对照 LangChain 基础版的条件边，再定位人工介入版的暂停、接受、修改与忽略分支。
5. **围绕一个任务评测。**读技术书第 7 章，建立小型任务集，分别检查终态、执行轨迹、禁止行为和资源消耗。然后再扩展检索、记忆或多 Agent。
6. **回到面试表达。**用本仓库题库检查能否解释“为什么、如何执行、如何失败、怎样验证”。只有亲自运行的结果才能写入自己的项目证据。

这是建议路径；每个阶段以能解释和验证为准，不以阅读页数或框架数量计进度。

## 10 个容易从简化教材中形成的误解

| 误解 | 更准确的理解与参考资料 |
|---|---|
| Agent 必须有长期记忆库，必须使用某个框架 | 应先看任务是否需要跨会话保持信息。LangChain 基础实现展示工具循环，再在后续模块增加记忆；这不是要求每个 Agent 都有向量库。架构选择应从任务所需的最简单方案开始。[架构依据](https://www.anthropic.com/research/building-effective-agents) |
| token 就是一个字或一个单词 | 切分取决于分词器，子词、字节和特殊标记会改变数量；窗口与费用不能只用字符数精确推算。[官方分词说明](https://huggingface.co/docs/transformers/main/en/tokenizer_summary) |
| 上下文装得下，就一定能充分使用全部信息 | 窗口容量与利用效果应分别评估。2023 年研究在其所测模型和任务上发现信息位置会影响表现；不能把当年的具体降幅直接套用到所有当前模型。[原论文](https://arxiv.org/abs/2307.03172v3) |
| RAG 有检索就不会答错 | RAG 连接检索与生成；仍需检查证据相关性、时效、权限和答案支持程度。检索质量与生成质量应分别评估。[原论文](https://arxiv.org/abs/2005.11401v4) |
| 模型输出了工具调用，就已完成外部操作；所有工具都在客户端运行 | 模型调用意图与真正执行须区分。当前 Claude 文档区分由应用执行的 client tools 和由平台执行的 server tools，归档教材中的客户端示例不是全部部署形态。[当前官方说明](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) |
| MCP 标准接口或参数 schema 会自动保证安全 | 协议与格式不替代身份、授权、同意和最小权限。MCP 官方文档专门讨论混淆代理、会话劫持和本地服务风险。[官方安全说明](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices) |
| Reflection／Reflexion 就是在在线训练模型 | 原始 Reflexion 用反馈与情节记忆中的文字影响后续尝试，并不更新模型权重。若采用参数训练，必须另外明确训练算法、数据和更新步骤。[原论文](https://arxiv.org/abs/2303.11366v4) |
| 多一步反思、多一个 Agent，一定效果更好 | 复杂性需要任务收益支持，同时计入额外延迟、成本与错误传播。工作流和自主 Agent 是架构选择，不是能力等级排名。[官方工程讨论](https://www.anthropic.com/research/building-effective-agents) |
| LLM 给自己打高分，就完成了验证 | 模型评判会有位置、冗长与自我偏好等偏差。用可执行断言核对事实，再用明确量表与人工样本校准开放性评价。[评判器研究](https://arxiv.org/abs/2306.05685v4) |
| 教程运行成功一次，就能证明安全、生产可用或案例性能可泛化 | 课程示例只能提供特定条件下的观察。自己的验证还需报告数据集、版本、失败分母与副作用终态；克隆、安装、模拟工具输出都不等于真实服务验收。[评估章节](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter7.md)、[参考资料](../learning/verification.md) |

## 参考来源与许可

Hello-Agents README 标注 CC BY-NC-SA 4.0；Anthropic 的实际 LICENSE 为 CC BY-NC 4.0；HF 页面标注 Apache-2.0；微软、LangChain、Karpathy 页面标注 MIT；bojieli 仓库标注 Apache-2.0，并说明部分子项目可能有独立声明。具体来源链接在 [learning-sources.json](learning-sources.json) 中。
