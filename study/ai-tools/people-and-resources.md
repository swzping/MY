# AI 工具人物与资源

这里记录值得关注的开发者、项目作者、资料源和 GitHub 账号，方便后续回看其项目、思路和工具生态。

## 资源总览

| 名称 | 类型 | 关注方向 | 适合学习 |
| --- | --- | --- | --- |
| [Michael Sitarzewski / msitarzewski](https://github.com/msitarzewski) | 开发者 / 创业者 | AI agents、开发者工具、产品原型 | 从个人项目观察 AI 工具产品化和 agent 工作流设计 |
| [agency-agents](https://github.com/msitarzewski/agency-agents) | 开源 agent 角色库 | 多角色 AI agent、跨工具安装、工作流拆分 | 学习如何定义 agent 角色边界、输出标准和协作方式 |

## Michael Sitarzewski / msitarzewski

链接：

- GitHub：[msitarzewski](https://github.com/msitarzewski)
- 个人网站：[msitarzewski.com](https://msitarzewski.com)

一句话简介：Michael Sitarzewski 是一位有 30 多年构建经验的开发者、创业者和 Techstars alum，长期关注把想法做成可运行产品。

公开主页信息：

- GitHub 用户名：`msitarzewski`
- 所在地：Dallas, Texas
- 个人定位：builder、startup founder、lifelong tinkerer
- 关注方向：AI agents、开发者工具、产品原型、开源项目

值得关注的原因：

- 他不是只分享概念，而是偏向把想法落到具体工具和项目里。
- 其项目与 AI agent 工作流、开发协作、工具化生产比较相关，适合观察“AI 编程工具如何产品化”。
- 对学习 AI 工具的人来说，可以从他的仓库里看 prompt/agent 设计、工具命名、工作流拆分和文档组织方式。

代表项目/线索：

- `agency-agents`：一组面向开发、设计、测试、写作、MCP 等任务的专业 AI agent 配置，定位类似“可安装的 AI 专家团队”。
- `glassdb.app`：面向 visionOS 的数据库管理客户端，体现其把 AI agent 工作流用于实际产品构建的方向。

### agency-agents 项目简介

链接：

- GitHub：[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)
- 安装应用：[agencyagents.app](https://agencyagents.app)

一句话解释：`agency-agents` 是一个开源的 AI agent 角色库，把前端、后端、设计、测试、安全、产品、营销、项目管理等工作拆成一批可安装、可复用的专业 agent。

项目定位：

- 它不是一个新的大模型，也不是完整 IDE，而是一套“专业角色提示词 + 工作流规范 + 安装转换脚本”。
- 每个 agent 通常包含身份、性格、核心任务、工作流程、交付物标准和成功指标。
- 目标是把通用 AI 编程助手改造成更像“分工明确的 AI 团队”，让不同任务调用不同专家角色。

支持工具：

- Claude Code
- Cursor
- Codex
- Gemini CLI
- OpenCode
- GitHub Copilot
- Aider
- Windsurf
- Kimi Code
- 其他通过转换脚本适配的 agentic coding 工具

典型用法：

- 做前端页面时调用 `Frontend Developer` 或 `UI Designer`。
- 做系统设计时调用 `Backend Architect`。
- 做上线前检查时调用 `Reality Checker`、`Code Reviewer` 或测试类 agent。
- 做内容、社区、营销时调用 marketing / support / sales 相关 agent。

值得学习的点：

- Agent 不是只写一句“你是专家”，而是要定义角色边界、工作步骤、输出标准和验收指标。
- 多 agent 工作流的关键不是“同时叫很多 AI”，而是把任务拆给合适角色，再用清晰交付物串起来。
- 它展示了一种可迁移思路：把自己常用的学习、开发、复盘、写作流程，也沉淀成可复用 agent。

局限与注意：

- agent 数量多不等于效果一定好，关键仍然是任务描述、上下文质量和验收标准。
- 对简单任务可能显得过重，更适合复杂项目、代码审查、产品化开发和需要多角色视角的工作。
- 使用前最好先挑少数高频 agent 试用，而不是一次性安装和依赖全部角色。

后续观察：

- 关注他如何设计不同角色的 agent，例如 code reviewer、technical writer、MCP builder、accessibility auditor。
- 观察这些 agent 配置是否能迁移到自己的 Codex/Claude/Cursor 工作流里。
- 如果后续研究 AI agent 协作，可以单独拆一篇 `agency-agents` 项目笔记。
