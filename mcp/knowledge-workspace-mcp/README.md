# Knowledge Workspace MCP

本地 MCP server，用于让 Codex 安全读取和整理 `/Users/edy/Documents/SW` 知识库。

## Tools

- `read_workbench`：读取 `00-入口/今日工作台.md`。
- `read_suggestions`：读取 `00-入口/今日整理建议.md`。
- `create_atomic_note`：在用户确认后创建 `20-原子知识/` 笔记。

## 安全边界

- 默认知识库根目录：`/Users/edy/Documents/SW`。
- 可以通过 `KNOWLEDGE_BASE_ROOT` 覆盖根目录。
- 所有路径都会限制在知识库根目录内。
- 写入原子知识必须传入 `confirmed: true`。
- 已存在的笔记不会被覆盖。

## 本地开发

```bash
npm install
npm test
npm run build
```

## Codex 配置

构建后添加 MCP server：

```bash
codex mcp add knowledge-workspace \
  --env KNOWLEDGE_BASE_ROOT=/Users/edy/Documents/SW \
  -- node /Users/edy/Documents/SW/mcp/knowledge-workspace-mcp/dist/server.js
```

也可以写入 `~/.codex/config.toml`：

```toml
[mcp_servers.knowledge-workspace]
command = "node"
args = ["/Users/edy/Documents/SW/mcp/knowledge-workspace-mcp/dist/server.js"]

[mcp_servers.knowledge-workspace.env]
KNOWLEDGE_BASE_ROOT = "/Users/edy/Documents/SW"
```

