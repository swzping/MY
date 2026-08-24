# Agent 工程总览

这里整理 LangGraph、MCP、Skill、Agent、Tool、Memory、Workflow 等概念之间的关系。可以把它理解成一张地图：不同技术不是互相替代，而是分别解决 Agent 系统里的不同层次问题。

## 一句话地图

| 概念 | 一句话理解 | 主要解决什么 | 更像哪一层 |
| --- | --- | --- | --- |
| Agent | 能根据目标、上下文和工具调用做事的智能执行单元 | 谁来判断、规划、执行 | 执行主体 |
| Workflow | 预先设计好的步骤、分支和验收流程 | 事情按什么顺序发生 | 流程层 |
| LangGraph | 用图结构编排 Agent / LLM / Tool / State 的框架 | 复杂多步流程、状态管理、循环与分支 | 编排层 |
| MCP | 让 AI 客户端连接外部工具、数据和资源的协议 | 模型如何安全一致地访问外部系统 | 能力接入层 |
| Tool | Agent 可调用的一个具体动作 | 查数据、写文件、调 API、执行命令 | 原子能力 |
| Skill | 给 AI 的可复用工作方法包 | 怎么完成一类任务、遵守哪些流程 | 方法层 |
| Memory | 保存长期偏好、历史事实、任务状态或外部知识 | Agent 如何记住和复用信息 | 上下文层 |
| Eval | 对 Agent 输出和流程结果做验证 | 怎么知道做得对不对 | 质量层 |

## 核心关系

可以这样理解：

```text
用户目标
  -> Skill 选择工作方法
  -> Workflow / LangGraph 组织步骤
  -> Agent 在步骤中推理和决策
  -> MCP 暴露外部工具、资源和数据
  -> Tool 执行具体动作
  -> Memory 提供长期上下文
  -> Eval / Test 验证结果
```

不是每个项目都需要全部组件。很多任务只需要一个普通脚本、一个清楚的 README 和一个好测试。只有当流程变长、状态变多、外部系统变复杂、失败成本变高时，才需要引入更重的 Agent 工程层。

## LangGraph 的位置

LangGraph 适合处理“流程复杂”的问题：

- 有多个步骤、角色、分支或循环。
- 需要显式保存状态，例如用户信息、任务进度、工具结果、审批状态。
- 需要多 Agent 协作，例如 researcher、planner、coder、reviewer。
- 需要可恢复、可观察、可调试的执行路径。

它不主要解决“怎么连接外部系统”。连接外部系统通常交给工具函数、SDK、API client 或 MCP server。

## MCP 的位置

MCP 适合处理“能力接入”的问题：

- AI 客户端需要访问数据库、内部系统、文件、浏览器、设计工具、知识库或 SaaS。
- 同一个能力希望被多个 AI 客户端复用，例如 Codex、Claude、Cursor、ChatGPT。
- 需要把工具、资源、提示词用统一协议暴露出来。
- 需要明确权限边界，而不是让模型随意碰系统。

MCP 不负责替你设计复杂流程。它更像插座和接口规范：把能力稳定地接给 Agent。

## Skill 的位置

Skill 适合处理“方法复用”的问题：

- 某类任务经常重复，例如写日报、做代码审查、分析股票、生成文档。
- 希望 AI 每次都按固定步骤工作。
- 需要附带参考资料、脚本、模板或检查清单。
- 不一定需要新工具，只是需要更好的操作流程。

Skill 常常会调用已有工具、MCP、脚本或浏览器，但它本身更像“操作手册 + 资源包”。

## 三者最常见组合

| 组合 | 适合场景 | 例子 |
| --- | --- | --- |
| Skill + 脚本 | 任务流程固定，工具简单 | 每天生成学习复盘、批量整理 Markdown |
| Skill + MCP | 有固定工作方法，还要访问外部系统 | 用 Skill 规定研究流程，用 MCP 查私有知识库 |
| LangGraph + Tool | 需要复杂流程，但工具只在本项目内部 | 多步骤报告生成、任务规划与复核 |
| LangGraph + MCP | 流程复杂且外部能力多 | 企业研究 Agent、客服 Agent、数据分析 Agent |
| Skill + LangGraph + MCP | 方法、流程、能力都需要复用 | 垂直行业 Agent 平台 |

## Agent 框架案例

这里记录“智能体本体或 agent 框架”，和单个 Skill、MCP server、脚本区分开。它们通常会同时包含记忆、工具调用、技能系统、运行时和多平台入口。

| 框架 | 一句话理解 | 适合观察 | 注意事项 |
| --- | --- | --- | --- |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | 用多智能体模拟金融交易公司投研流程 | LangGraph 多角色编排、Bull/Bear debate、结构化决策、checkpoint 和 decision log | 研究框架，不是实盘交易系统；金融输出必须人工复核 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Nous Research 的 Skill-native 自改进 agent 框架 | 自动创建/改进 skills、长期记忆、MCP、多平台网关 | 自主学习和第三方 skill 需要权限隔离、版本管理和审计 |

### TradingAgents 在 Agent 工程里的位置

详细整理见：[TradingAgents 项目整理](tradingagents-notes.md)。

`TradingAgents` 是一个很好的 LangGraph 多 agent 案例。它把金融投研拆成分析师、看多/看空研究员、交易员、风险/组合管理等角色，用图流程组织报告、辩论、决策和复核。

它适合观察这些工程问题：

- 什么时候需要多个 agent，而不是一个大 prompt。
- 如何让反方观点成为流程的一部分，而不是事后补一句风险提示。
- 如何用 structured output 让决策能被 CLI、日志、回测或下游系统消费。
- 如何用 checkpoint 保护长流程 agent 的中间状态。
- 如何把模型 provider 和数据 vendor 做成可配置 registry。

它和 MCP 的关系也清楚：TradingAgents 自身重点是流程编排和研究角色，数据源目前更多是项目内工具/vendor 抽象；如果要把它接入企业内部数据、交易系统或自建 A 股数据服务，MCP 更适合作为外部能力接入层。

## Hermes、Codex、Claude Code、OpenClaw 的区别

这四个名字都可以叫 agent，但产品重心不同。最简单的区分是：

- `Codex`：面向软件工程的 coding agent。
- `Claude Code`：Anthropic 的 agentic coding 工具，也可以通过 Agent SDK 作为库来构建 agent。
- `OpenClaw`：个人自动化助手，重点是替用户在消息渠道和设备上做事。
- `Hermes Agent`：自改进 agent 框架，重点是长期记忆和从经验中创建/改进 skills。

| 对比项 | Hermes Agent | Codex | Claude Code | OpenClaw |
| --- | --- | --- | --- | --- |
| 主定位 | 自改进通用 agent 框架 | 软件工程 coding agent | 高自主度 coding agent / Agent SDK | 个人 AI 助手和自动化平台 |
| 核心场景 | 长期陪伴、任务学习、skill 演化、多平台 agent | 读代码、改代码、跑测试、修 bug、PR/云端任务 | 代码库探索、编辑、命令执行、调试，也可嵌入自定义 agent | 邮件、日历、消息、网页、设备和个人任务自动化 |
| Skill 角色 | 核心机制，skills 是 procedural memory，可从经验生成和改进 | 可复用工作流扩展，Codex 按需加载 `SKILL.md` | 可通过工具、命令、MCP、项目规则扩展，skill 不是主叙事 | 生态能力模块，适合快速装配自动化能力 |
| 记忆倾向 | 强调跨会话记忆、用户模型和自我改进 | 更偏项目上下文、任务上下文和 repo 指令 | 更偏当前代码任务、CLAUDE.md、会话和 SDK 上下文 | 更偏个人助手上下文、配置、集成和自动化状态 |
| 工具接入 | 内置工具网关、MCP、多消息平台 | Shell、文件、浏览器、MCP、插件、skills、云端环境 | 文件、命令、编辑、web/MCP，Agent SDK 可编程 | 消息平台、设备、网页、邮件、日历、集成和 skills |
| 运行形态 | CLI、桌面端、消息平台、远程后端等 | CLI、IDE、桌面 app、Web/cloud、GitHub/CI 等 | CLI、IDE/终端体验、Agent SDK | 本地/自托管个人助手，WhatsApp/Telegram 等渠道 |
| 开放性 | 开源框架，强调可换模型和自建能力 | OpenAI 产品和开源 CLI 结合 | Anthropic 产品和 SDK | 开源个人 AI 助手生态 |
| 主要风险 | 自主改 skill、长期记忆、第三方 skill 供应链 | 自动改代码、权限、仓库/云环境安全 | 自动改代码和命令执行、成本、权限 | 真实个人账号和设备权限、恶意 skills、平台集成风险 |

### 怎么选择

如果目标是改代码、修 bug、写测试、理解仓库，优先考虑 `Codex` 或 `Claude Code`。两者都是 coding agent，区别更多在模型生态、工作界面、团队习惯和你想用 OpenAI 还是 Anthropic 的工具链。

如果目标是个人生活或业务自动化，例如清邮件、排日程、从聊天软件触发任务、连接多个个人账号，`OpenClaw` 更接近这个方向。它的重点不是写代码，而是“在你的数字生活里执行动作”。

如果目标是研究一个会长期成长的 agent，特别是想观察“agent 如何把经验沉淀成 skills、如何跨会话记忆、如何自我改进”，`Hermes Agent` 更值得看。它不是 Codex/Claude Code 的直接替代品，而更像一个围绕 skills 和 memory 设计的 agent runtime。

### 和 Skill 的关系

`Codex` 把 Skill 当作可复用工作流扩展：Skill 是目录、`SKILL.md`、脚本和参考资料，Codex 在任务匹配时按需加载。

`Hermes Agent` 更进一步，把 Skill 放进 agent 的学习循环里：成功经验可以被提炼成 Skill，使用中还可能继续改进。

`OpenClaw` 的 Skill 更像个人自动化生态里的能力模块，重点是让助手更快接入具体任务。

`Claude Code` 更强调 coding agent 本体和 Agent SDK：它可以用工具、命令、MCP、项目规则扩展能力，但“Skill”不是它最核心的公开定位。

### Hermes Agent

链接：

- GitHub：[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- 文档：[Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- Skills catalog：[Bundled Skills Catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog)

一句话解释：`Hermes Agent` 是 Nous Research 做的自改进 AI agent 框架。它不是单个 Skill，而是一个带记忆、工具网关、MCP、消息平台入口和 skills 系统的 agent 运行时。

项目定位：

- 它更像 `agent runtime + skill system + memory layer + tool gateway` 的组合。
- 它强调 agent 可以从任务经验中学习，创建或改进 skills。
- 它把 skill 视为 agent 的 procedural memory，也就是可复用的做事方法。

适合观察：

- Skill 如何从“人工写的流程文件”升级成 agent 自我改进的一部分。
- 长期记忆、SOUL/personality、context files、MCP、tool gateway、messaging gateway 如何分工。
- bundled skills catalog 如何组织不同领域能力，例如 research、software-development、social-media。
- 自主 agent 如何处理技能演化、工具权限和多平台输入输出。

学习价值：

- 它适合放在 Agent 工程地图里看，而不是只放在 Skill 分类里。
- 它展示了一个方向：Agent 不只调用工具，也会沉淀自己的工作方法。
- 它可以和 Codex Skills、Claude Skills、OpenClaw、LangGraph 类 workflow 框架做对照。

风险与注意：

- 自动创建和更新 skill 意味着 agent 可能改变自己的工作方式，需要版本管理、审查和回滚。
- 第三方 skill 或 skill marketplace 有供应链风险，安装前要看来源、权限、脚本和外部调用。
- 多平台消息网关和 MCP 工具一旦接入真实账户，要分层授权，默认从只读和 sandbox 开始。
- 记忆系统可能保存私人信息、项目上下文和业务数据，需要清理、导出和删除机制。

## 什么时候不要上复杂架构

下面情况通常不需要 LangGraph 或 MCP：

- 只是一次性整理资料。
- 只是调用一个 API 并输出结果。
- 只需要本地脚本就能稳定完成。
- 没有多步骤状态，也没有多人或多客户端复用需求。
- 项目还在验证需求，流程随时会变。

先把任务写成清楚的脚本、README、测试和数据样例，往往比一开始搭完整 Agent 架构更好。

## 学习路径

1. 先理解 Tool：一个可执行动作怎么定义输入、输出、错误和权限。
2. 再理解 Skill：一类任务的方法、模板和检查清单怎么沉淀。
3. 再理解 MCP：如何把工具和资源接给不同 AI 客户端。
4. 最后理解 LangGraph：如何把多个步骤、状态和 Agent 组织成可观察流程。

## 参考入口

- LangGraph 文档：[LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- MCP 官方站点：[Model Context Protocol](https://modelcontextprotocol.io/)
- MCP 规范：[Specification](https://modelcontextprotocol.io/specification)
- Codex AGENTS.md：[Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- Codex MCP：[MCP in Codex](https://developers.openai.com/codex/mcp)
