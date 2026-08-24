# LangGraph 笔记

一句话解释：`LangGraph` 是 LangChain 生态里的 Agent / workflow 编排框架，用图结构把 LLM、工具、状态、分支、循环和多 Agent 协作组织成可执行流程。

## 适合解决的问题

LangGraph 适合需要显式流程控制的 Agent 系统：

- 多步骤任务。
- 步骤之间共享状态。
- 根据中间结果走不同分支。
- 需要循环重试、反思、复核或人工确认。
- 需要多个 Agent 或多个角色协作。
- 需要观察、调试和恢复执行过程。

它不只是“把 prompt 串起来”，而是把 Agent 流程变成一个可以理解、测试和维护的图。

## 核心概念

| 概念 | 一句话理解 | 关注点 |
| --- | --- | --- |
| Graph | 由节点和边组成的执行流程 | 整体流程结构 |
| State | 图运行时共享和更新的数据 | 输入、工具结果、消息、决策、进度 |
| Node | 图里的一个处理步骤 | 调模型、调用工具、处理数据、做判断 |
| Edge | 节点之间的流转关系 | 下一步去哪 |
| Conditional Edge | 根据状态决定下一步 | 分支、路由、循环 |
| Checkpoint | 保存运行状态 | 中断、恢复、长期会话 |
| Human-in-the-loop | 在流程中加入人工确认 | 高风险操作、审批、纠错 |

## 典型结构

```text
start
  -> planner
  -> researcher
  -> analyzer
  -> reviewer
  -> final_writer
  -> end
```

更复杂时会出现条件分支：

```text
reviewer
  -> pass: final_writer
  -> fail: researcher 或 analyzer
```

## 适合场景

### 多 Agent 研究

例如行业研究、股票研究、技术调研：

- planner：拆问题。
- researcher：查资料。
- analyst：做判断。
- critic：找漏洞。
- writer：生成最终报告。

LangGraph 的价值在于把这些角色之间的流转、状态和复核机制显式化。

项目案例：

- [TradingAgents](tradingagents-notes.md)：用 LangGraph 把金融投研拆成分析师、看多/看空研究员、交易员、风险/组合管理等角色，并加入 debate、structured output、checkpoint 和 decision log。

### 复杂客服或业务流程

例如订单客服：

- 判断用户意图。
- 查询订单。
- 判断是否有权限。
- 必要时要求人工确认。
- 执行退款、改地址或升级工单。
- 记录处理结果。

这种流程有分支、有权限、有外部系统调用，很适合图编排。

### 编程 Agent 工作流

例如：

- 需求澄清。
- 计划。
- 实现。
- 测试。
- 代码审查。
- 修复。
- 总结。

如果流程长期稳定，并且希望自动化多个角色，LangGraph 可以把这些阶段组织起来。

## 不适合场景

下面情况通常不需要 LangGraph：

- 一次性脚本。
- 单轮问答。
- 一个工具调用就能完成。
- 没有状态、分支或循环。
- 项目还在探索期，流程每天都变。

过早使用 LangGraph 会增加心智负担。先把流程用普通函数、脚本或文档跑通，再考虑图化。

## 和 MCP 的区别

LangGraph 管“流程怎么走”，MCP 管“外部能力怎么接入”。

| 问题 | 更像 LangGraph | 更像 MCP |
| --- | --- | --- |
| 下一步该做什么？ | 是 | 否 |
| 状态怎么保存和更新？ | 是 | 否 |
| 如何连接数据库或 SaaS？ | 否 | 是 |
| 多个 AI 客户端如何复用同一工具？ | 否 | 是 |
| 某个工具是否允许写操作？ | 间接 | 是 |

实际项目里经常是 LangGraph 节点调用 MCP 工具。

## 和 Skill 的区别

Skill 是“方法说明”，LangGraph 是“可执行编排”。

Skill 可以告诉 Agent：

- 做这类任务先看什么。
- 输出格式是什么。
- 失败时怎么检查。
- 需要调用哪些脚本或工具。

LangGraph 可以把这些步骤变成固定流程，并在代码层控制状态、分支和循环。

## 设计建议

- 先画出业务流程，再决定是否需要图。
- State 不要什么都塞，优先保存真正影响后续决策的数据。
- Node 要小而清楚，一个节点只做一类事。
- 高风险动作前加入人工确认节点。
- 给外部工具调用设计超时、重试和错误分支。
- 为关键节点保留可观察日志，方便复盘。

## 学习重点

学习 LangGraph 时不要只看 API，要重点看：

- 如何定义状态。
- 如何拆节点。
- 如何设计条件边。
- 如何做 checkpoint 和恢复。
- 如何加入人工确认。
- 如何测试图中的单个节点和整体流程。

## 案例观察：TradingAgents

[TradingAgents](tradingagents-notes.md) 值得作为 LangGraph 多 agent 案例来读。它的价值不只是“用 LLM 分析股票”，而是展示一个复杂决策流程怎样被拆成图：

- 分析师节点负责生成不同维度的研究材料。
- 研究员节点负责 Bull/Bear 辩论，让反方观点进入主流程。
- 交易员节点把分析和辩论压缩成交易动作。
- 风险/组合管理节点复核交易动作，并结合历史决策记忆。
- checkpoint 让长流程失败后可以恢复，不必从头烧 token。

从这个案例反推 LangGraph 设计时，可以重点看三个问题：

- State 里哪些内容必须保留，哪些只是中间文本。
- 哪些节点应该结构化输出，方便测试和复用。
- 哪些外部数据必须被验证，避免 agent 在错误数据上做漂亮推理。

## 参考入口

- 官方概览：[LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- LangChain 文档入口：[LangChain Docs](https://docs.langchain.com/)
- LangGraph GitHub：[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
