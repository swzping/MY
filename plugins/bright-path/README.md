# Bright Path

Bright Path 是一个小而完整的个人 Codex 插件，用来把零散想法整理成清晰、具体、带有希望感的前进路径。

它目前提供八个技能：

- `bright-path` - 整理想法、辅助决策、复盘成长、拆解计划，并输出简洁摘要与实际下一步。
- `ima-copilot` - 在需要外部知识库支持时，通过本地 IMA Copilot MCP 服务查询知识库。
- `sw-knowledge` - 检索本地 `/Users/edy/Documents/SW` 知识库，整理股票、项目、主题研究资料。
- `creator-workflow` - 网络博主工作流总入口，覆盖选题、草稿、平台改写、发布检查和复盘。
- `topic-selector` - 从 SW 知识库和输入流中筛选适合发布的选题。
- `content-drafter` - 把观点或资料写成短视频、小红书、公众号、推文等草稿。
- `platform-rewriter` - 将同一个核心观点改写成不同平台版本。
- `creator-review` - 复盘内容表现、评论反馈和后续选题沉淀。

## 示例提示词

```text
使用 Bright Path 帮我整理这个想法。
使用 Bright Path 帮我制定下一步计划。
使用 Bright Path 帮我复盘今天学到的东西。
使用 Bright Path 帮我在这些选项里做选择。
使用 IMA Copilot 查询我的知识库：这个主题有哪些关键资料？
使用 SW 知识库整理这个项目：……
使用创作者工作流，从 SW 里找 5 个适合本周发布的选题。
把这个观点写成小红书和短视频口播两个版本。
复盘这条内容的数据和评论，沉淀下一批选题。
```

## 它会做什么

Bright Path 会先把请求判断为五种模式之一：

- 想法成形
- 行动计划
- 复盘反思
- 决策辅助
- 总结提炼

然后输出一个紧凑结构，包括核心判断、限制条件、下一步行动；只有在缺少关键信息会明显影响建议时，才追问一个问题。

## IMA Copilot MCP

Bright Path 可以连接本机运行的 IMA Copilot MCP 服务：

```text
http://127.0.0.1:8081/mcp
```

插件只声明连接方式，不保存 IMA 登录信息。你需要在本机单独启动 IMA MCP server，并通过环境变量提供认证信息。

详细设置见：

```text
references/ima-copilot-setup.md
```

## Hooks

Bright Path 包含一个轻量 `SessionStart` hook：

```text
hooks/session-start
```

它会在新会话开始时注入一段简短上下文，提醒 Codex：当用户提到整理想法、计划、复盘、决策或查询 IMA 知识库时，可以使用 Bright Path 的相关技能。为了方便确认 hook 已触发，它还会要求新会话第一条回复显示 `Bright Path 已启用`，并写入一条本地日志：

```text
~/.codex/bright-path-session-start.log
```

这个 hook 不会修改文件，也不会自动调用 IMA。

## SW 本地知识库

Bright Path 可以直接读取本机 SW 知识库：

```text
/Users/edy/Documents/SW
```

当你说“查 SW”“用 SW 知识库”“基于 SW 资料”时，`sw-knowledge` 技能会优先使用本地文件检索，按证据来源整理结论。

详细规则见：

```text
references/sw-knowledge-guide.md
```

## 网络博主工作流

Bright Path 可以支持混合型个人 IP 内容生产：AI 工具、Agent/MCP、知识系统、研究方法、投资/项目观察。

工作流：

```text
资料输入 -> 选题判断 -> 内容结构 -> 多平台改写 -> 发布检查 -> 数据复盘 -> 选题沉淀
```

详细规则见：

```text
references/creator-workflow-guide.md
references/platform-style-guide.md
references/content-formats.md
references/creator-review-metrics.md
```

## 生命周期与维护

插件源码、安装缓存、迭代命令和维护习惯已经整理在：

```text
references/plugin-lifecycle.md
```

日常改完插件后，可以直接运行：

```bash
/Users/edy/Documents/MY/plugins/bright-path/scripts/refresh-local-plugin.sh
```

它会更新本地版本标记并运行插件校验。

## 本地安装位置

这个插件已经注册到个人 Codex marketplace：

```text
/Users/edy/.agents/plugins/marketplace.json
```

源码位置：

```text
/Users/edy/Documents/MY/plugins/bright-path
```

兼容入口：

```text
/Users/edy/plugins/bright-path
```

这个旧路径现在是指向源码位置的符号链接，用来保持 personal marketplace 的 `./plugins/bright-path` 入口可用。
