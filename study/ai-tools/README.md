# AI 工具学习地图

这里整理 AI 工具、Agent 工程、平台案例、开源项目和项目结构规范。重点不是追热点名词，而是判断：它解决什么问题、适合放在系统哪一层、什么时候值得自己动手用。

## 目录

- [Agent 工程总览](agent-engineering.md)
- [Agent Stack 实战手册](agent-stack-playbook.md)
- [LangGraph 笔记](langgraph-notes.md)
- [TradingAgents 项目整理](tradingagents-notes.md)
- [MCP 笔记](mcp-notes.md)
- [Skills 笔记](skills-notes.md)
- [AI 工具术语表](glossary.md)
- [AI 工具人物与资源](people-and-resources.md)
- [AI 工具平台案例](platforms.md)
- [AI 工具开源项目案例](projects.md)
- [利于 AI 协作的项目目录结构](ai-friendly-project-structure.md)
- [Agent 项目结构模板](templates/agent-project-structure.md)

## 阅读顺序

如果是第一次系统整理 Agent 工程，建议按这个顺序看：

1. 先看 [Agent 工程总览](agent-engineering.md)，建立 LangGraph、MCP、Skill、Tool、Memory 的关系。
2. 再看 [Agent Stack 实战手册](agent-stack-playbook.md)，判断遇到需求时该用哪一层。
3. 需要深入某个技术时，再分别看 LangGraph、MCP、Skills 三篇专题。
4. 真要开项目时，用 [Agent 项目结构模板](templates/agent-project-structure.md) 做目录起点。

## 记录原则

- 先写一句话解释，再写适用场景。
- 先区分边界，再比较优劣。
- 对快速变化的工具，只记录稳定概念和官方入口，不把临时 UI 当长期知识。
- 对接近真实账户、交易、私有数据或外部系统的能力，必须记录权限、审计、回退和人工确认。
