# Bright Path 插件生命周期

这份文档说明 Bright Path 从源码、marketplace、缓存安装到日常维护的完整流程。

## 1. 源码阶段

插件源码位置：

```text
/Users/edy/Documents/MY/plugins/bright-path
```

日常开发只改这里。不要直接修改 Codex 的缓存目录。

核心文件：

```text
.codex-plugin/plugin.json
skills/
references/
assets/
.mcp.json
hooks.json
hooks/
scripts/
README.md
CHANGELOG.md
```

## 2. 注册阶段

个人 marketplace 位置：

```text
/Users/edy/.agents/plugins/marketplace.json
```

Bright Path 的条目指向：

```text
./plugins/bright-path
```

在 personal marketplace 流程里，这个相对路径会解析到兼容入口：

```text
/Users/edy/plugins/bright-path
```

该路径现在是一个符号链接，指向真实源码位置：

```text
/Users/edy/Documents/MY/plugins/bright-path
```

## 3. 安装/缓存阶段

Codex 使用插件时，会从 marketplace 指向的源码位置复制/安装到缓存目录，类似：

```text
/Users/edy/.codex/plugins/cache/...
```

这个 cache 是 Codex 运行读取的副本。它可能被刷新、替换或清理，不建议手动修改。

正确关系是：

```text
编辑源码：
/Users/edy/Documents/MY/plugins/bright-path

Codex 读取缓存：
/Users/edy/.codex/plugins/cache/...
```

## 4. 迭代阶段

每次改完插件源码后，建议做三件事：

1. 更新 cachebuster，让 Codex 知道本地插件有新版本。
2. 运行插件校验。
3. 在 Codex app 里重新查看、安装或刷新插件。

推荐直接运行：

```bash
/Users/edy/Documents/MY/plugins/bright-path/scripts/refresh-local-plugin.sh
```

等价于：

```bash
python3 /Users/edy/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py /Users/edy/Documents/MY/plugins/bright-path
python3 /Users/edy/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/edy/Documents/MY/plugins/bright-path
```

`cachebuster` 的作用是让 Codex 识别“这个本地插件已经变更”。

## 5. 使用阶段

当前技能：

```text
bright-path
ima-copilot
sw-knowledge
creator-workflow
topic-selector
content-drafter
platform-rewriter
creator-review
```

示例：

```text
使用 Bright Path 帮我整理这个想法。
使用 IMA Copilot 查询我的知识库：这个主题有哪些关键资料？
使用 SW 知识库整理这个项目：……
使用创作者工作流，从 SW 里找 5 个适合本周发布的选题。
把这个观点写成小红书和短视频口播两个版本。
复盘这条内容的数据和评论，沉淀下一批选题。
```

## 6. 维护阶段

保持这些习惯：

- 改完跑 `validate_plugin.py`。
- 每次功能变化更新版本号或 cachebuster。
- README 写清楚用途和示例。
- `SKILL.md` 保持聚焦，不要变成“大而全”。
- 不要在 `plugin.json` 里写无效字段。
- 不直接编辑 `~/.codex/plugins/cache/...`。
- MCP 认证信息只放在本机环境变量、`.env` 或 Docker 环境里，不写进插件源码。

## 7. 发布/分享阶段

个人使用时，保留在 personal marketplace 即可。

如果要分享给别人，可以选择：

- 分享 `/Users/edy/Documents/MY/plugins/bright-path` 目录。
- 放入 Git 仓库。
- 建立团队 marketplace。

分享前建议确认：

- `plugin.json` 校验通过。
- README 和 references 没有私人 token、cookie、bkn。
- `.mcp.json` 只包含连接地址，不包含认证信息。
- `CHANGELOG.md` 记录了主要能力变化。
