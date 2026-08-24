# MCP 笔记

一句话解释：`MCP`，Model Context Protocol，是一种让 AI 应用以统一方式连接外部工具、数据源、资源和提示词的开放协议。

## 为什么需要 MCP

没有 MCP 时，每个 AI 客户端都可能用自己的方式接工具：

- 一个工具只能给一个客户端用。
- 认证、权限、错误处理和日志散落各处。
- 工具说明可能写在 prompt 里，难以维护。
- 外部系统能力没有统一边界。

MCP 的目标是把这些能力变成标准接口，让 AI 客户端像连接插件一样连接外部上下文和动作。

## 核心角色

| 角色 | 一句话理解 | 例子 |
| --- | --- | --- |
| MCP Host / Client | 发起连接和调用的 AI 应用 | Codex、Claude Desktop、Cursor、ChatGPT app |
| MCP Server | 暴露工具、资源、提示词的服务 | GitHub server、Figma server、数据库 server |
| Tool | 可被模型调用的动作 | 查询订单、创建 issue、读取行情 |
| Resource | 可读取的上下文资源 | 文件、文档、数据库记录、项目元数据 |
| Prompt | 可复用提示词模板 | 代码审查模板、报告生成模板 |

不同客户端支持的 MCP 能力细节可能不同，实际使用前要看对应客户端文档。

## Tools、Resources、Prompts 的区别

| 能力 | 适合放什么 | 关注点 |
| --- | --- | --- |
| Tools | 有输入、有执行、有返回的动作 | 参数 schema、权限、错误、幂等 |
| Resources | 可读取的资料或上下文 | URI、内容类型、更新频率、访问范围 |
| Prompts | 可复用的提示词或任务模板 | 变量、适用场景、输出格式 |

一个 server 可以同时提供三类能力，但最常见、最实用的是 Tools。

## 什么时候写 MCP server

适合写 MCP server 的信号：

- 有外部系统要给 AI 用。
- 这个能力会被多个 AI 客户端或多个项目复用。
- 需要比网页搜索更稳定的数据。
- 需要统一认证、权限和日志。
- 想把业务动作封装成明确的输入输出。
- 想避免把密钥、业务逻辑和 API 细节暴露在 prompt 里。

例子：

- 内部知识库查询。
- 数据库只读查询。
- Figma 设计读取和生成。
- GitHub issue / PR 操作。
- 股票行情、研报、公告数据接口。
- 本地文件索引和检索。

## 什么时候不要写 MCP

下面情况可以先不用 MCP：

- 只是一次性调用 API。
- 一个本地脚本已经够用。
- 只有一个项目内部用，不需要跨客户端复用。
- 需求还没稳定，接口设计每天会变。
- 没有清楚的权限边界。

先写脚本或普通服务，跑通后再封装成 MCP，会更稳。

## 工具设计建议

一个 MCP tool 应该像一个小 API：

- 名字清楚，表达动作。
- 参数少而明确。
- 返回结构化数据。
- 错误信息可读。
- 默认只读，写操作单独拆开。
- 高风险操作需要确认机制。
- 不把真实密钥、内部栈信息或敏感数据返回给模型。

不建议设计成：

- 一个 `run_anything` 工具。
- 一个万能 SQL 执行器直接暴露生产库。
- 参数全是自由文本，server 内部再猜。
- 写操作和读操作混在一个工具里。

## 权限边界

MCP 不是安全魔法。它提供接口形态，但真正的安全要在 server 和宿主系统里设计：

- 认证：谁能连 server。
- 授权：能调用哪些工具。
- 范围：能访问哪些账户、项目、文件或数据表。
- 审计：记录每次调用的输入、输出、时间和身份。
- 确认：高风险写操作是否需要人工确认。
- 环境：开发、测试、生产是否隔离。

对生产系统，建议从只读工具开始，再逐步开放写操作。

## 和 LangGraph 的区别

MCP 管能力接入，LangGraph 管流程编排。

一个常见组合：

```text
LangGraph node
  -> 调用 MCP tool 获取数据
  -> 更新 State
  -> 根据结果决定下一步
```

比如股票分析：

- MCP 提供 `get_daily_kline`、`get_announcements`、`get_research_reports`。
- LangGraph 决定先查什么、怎么组合、什么时候复核、如何输出报告。

## 和 Skill 的区别

MCP 是工具接口，Skill 是工作方法。

例子：

- MCP tool：`search_company_announcements(stock_code, start_date, end_date)`。
- Skill：规定“先查公告，再查研报，再做风险总结，最后输出来源和置信度”。

Skill 可以调用 MCP，但 Skill 本身不是协议，也不负责权限。

## MCP server 目录建议

```text
mcp-servers/
  market-data/
    README.md
    package.json
    src/
      server.ts
      tools/
      resources/
      auth/
    tests/
    .env.example
```

最重要的是把工具列表、权限模型、环境变量和测试方式写清楚。

## 参考入口

- 官方站点：[Model Context Protocol](https://modelcontextprotocol.io/)
- 官方规范：[MCP Specification](https://modelcontextprotocol.io/specification)
- 官方示例与 SDK：[MCP GitHub](https://github.com/modelcontextprotocol)
- Codex MCP 文档：[MCP in Codex](https://developers.openai.com/codex/mcp)
