# My Codex Portable Kit

这是一个个人 Codex 迁移包，用来把常用经验、技能、规则和可复用配置带到新电脑。

目标是：新电脑安装 Codex 后，把这个目录复制过去，然后让 Codex 或终端执行一次安装脚本，就能恢复大部分常用工作流。

快速了解本包能力：见 `CAPABILITIES.md`。

## 包含什么

- `skills/`：个人和第三方 Codex skills 快照，目前包含 Superpowers 系列技能、个人记忆/复盘技能、家装全景/VR 技能、本地微信解析与微信分析 Agent 生成技能；不包含 Codex `.system` 系统技能。
- `agents/skills/`：全局 Agent skills 快照，目前包含 A 股数据、股票分析、尾盘策略、前端设计和技能发现相关技能。
- `agents/plugins/marketplace.json`：全局 Agent personal marketplace 记录，目前登记 `bright-path` 本地插件来源。
- `plugins/cache/`：可迁移插件缓存，目前包含 `obra/superpowers`、`openai-api-curated/github`、`openai-api-curated/hyperframes` 和 `personal/bright-path`。
- `automations/`：从 `~/.codex/automations` 整理出的自动任务模板和说明；只迁移 prompt/调度思路，不迁移运行状态。
- `rules/default.rules`：常用命令审批规则。
- `instructions.md`：Codex 全局说明文件；当前可以为空，后续可持续沉淀个人偏好和工作习惯。
- `templates/config-portable.toml`：从当前机器提取的可迁移配置模板，已经去掉项目路径和机器相关的 node runtime 配置。
- `resources/agents-skill-lock.json`：从 `~/.agents/.skill-lock.json` 复制的来源清单，只用于记录全局 Agent skills 的安装来源和哈希，不作为安装状态恢复。
- `install.sh`：安装脚本，会备份新机器已有配置，并安装 skills、第三方插件缓存、rules 和 instructions。
- `scripts/setup-windows-codex.ps1`：Windows Codex 环境初始化脚本，只创建 `%USERPROFILE%\.codex\config.toml` 和 `auth.json`，具体内容手动填写。

## 不包含什么

出于安全和可迁移性考虑，不打包这些内容：

- `auth.json`：登录凭据和 token。
- `*.sqlite`：记忆、日志、状态数据库。
- `history.jsonl`、`sessions/`、`archived_sessions/`：聊天历史和会话记录。
- `automations/*/memory.md`、`.run-jitter-salt`、自动任务运行记忆、线程绑定状态和运行时间戳。
- `.tmp/`、`shell_snapshots/`、`logs`：临时文件和机器状态。
- 旧电脑上的具体项目路径 trust 配置。
- `plugins/cache/openai-bundled`、`plugins/cache/openai-primary-runtime`：OpenAI 官方内置/运行时插件缓存，通常跟 Codex 版本绑定，应由新电脑上的 Codex 自己安装或刷新。
- `skills/.system/`：Codex 官方系统技能，例如 `imagegen`、`openai-docs`、`plugin-creator`、`review-agent`、`skill-creator`、`skill-installer`；这些随 Codex 运行时分发，不作为个人资产迁移。
- 股票数据 MCP 服务、API 凭据和本机数据目录；股票分析 skills 只迁移通用说明、脚本和指标参考。
- `~/.agents` 的包管理状态、临时文件和系统垃圾文件；本包只把可复用 Agent skill 内容、Agent personal marketplace 和来源清单沉淀到 kit。
- Agent skill 的运行数据和本机状态，例如 `.git/`、`.mootdx/`、`data/` 中的交易样本/收益记录、`reports/` 日报、`__pycache__/`、`.pyc` 和临时调试文件。

## 在新电脑上安装

把整个 `my-codex-portable-kit` 目录复制到新电脑，然后执行：

```bash
cd /path/to/my-codex-portable-kit
bash ./install.sh
```

安装完成后重启 Codex。

脚本会：

- 备份新电脑已有的 `~/.codex/skills`、`~/.codex/rules`、`~/.codex/config.toml`。
- 覆盖安装本包里的 Codex skills 到 `~/.codex/skills`。
- 覆盖安装本包里的 Agent skills 到 `~/.agents/skills`。
- 覆盖安装本包里的 Agent plugin marketplace 到 `~/.agents/plugins`。
- 覆盖安装本包里的第三方插件缓存到 `~/.codex/plugins/cache`。
- 覆盖安装 `rules/default.rules`。
- 安装 `instructions.md` 到 `~/.codex/instructions.md`。
- 把配置模板复制到 `~/.codex/config.portable-kit.toml`，但不会自动覆盖 `~/.codex/config.toml`。
- 自动任务模板只保留在 `automations/` 中供人工参考，安装脚本不会自动启用或复制到 `~/.codex/automations`。

## 配置模板怎么用

安装后检查：

```bash
cat ~/.codex/config.portable-kit.toml
```

然后把你确认需要的段落合并到：

```bash
~/.codex/config.toml
```

建议优先检查这些项：

- `model` / `model_provider` / `review_model`
- `[model_providers.*]`
- `[mcp_servers.figma]`
- `[desktop]`
- `[plugins.*]`
- GitHub / Bright Path 等插件在新机器上的登录、MCP 服务和本地依赖

不要直接复制旧电脑的 `auth.json`。新电脑应该重新登录或重新配置 API key。

## Windows 上配置 Codex

在 Windows PowerShell 中进入本目录，然后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-codex.ps1
```

脚本会：

- 创建 `%USERPROFILE%\.codex\` 目录。
- 创建 `%USERPROFILE%\.codex\config.toml`，里面只有注释模板。
- 创建 `%USERPROFILE%\.codex\auth.json`，里面只有空 key 占位。
- 默认不覆盖已有文件。

如果你想重建文件，可以加 `-Force`；脚本会先备份旧文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-codex.ps1 -Force
```

创建后手动打开 `config.toml` 和 `auth.json`，填入你的 `key`、`base_url`、`model_provider` 等内容。

Windows 上文件位置是：

```text
%USERPROFILE%\.codex\config.toml
%USERPROFILE%\.codex\auth.json
```

通常等于：

```text
C:\Users\你的用户名\.codex\config.toml
C:\Users\你的用户名\.codex\auth.json
```

要直接打开这两个文件，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\open-windows-codex-config.ps1
```

## 更新这个包

在旧电脑上重新生成或手动同步这些目录即可：

```bash
rsync -a --delete --exclude='.system/' ~/.codex/skills/ ./skills/
cp ~/.codex/rules/default.rules ./rules/default.rules
cp ~/.codex/instructions.md ./instructions.md
mkdir -p ./plugins/cache/obra
cp -R ~/.codex/plugins/cache/obra/* ./plugins/cache/obra/
mkdir -p ./plugins/cache/openai-api-curated ./plugins/cache/personal
rsync -a --delete --exclude='.DS_Store' ~/.codex/plugins/cache/openai-api-curated/github ./plugins/cache/openai-api-curated/
rsync -a --delete --exclude='.DS_Store' ~/.codex/plugins/cache/openai-api-curated/hyperframes ./plugins/cache/openai-api-curated/
rsync -a --delete --exclude='.DS_Store' ~/.codex/plugins/cache/personal/bright-path ./plugins/cache/personal/
```

自动任务建议只同步模板，不同步运行状态：

```bash
mkdir -p ./automations/templates
# 只复制 automation.toml，之后删除 created_at/updated_at、模板化路径和 target_thread_id。
find ~/.codex/automations -maxdepth 2 -name automation.toml
```

同步后建议删除系统垃圾文件：

```bash
find . -name '.DS_Store' -delete
```

## 验证

安装后可以运行：

```bash
find ~/.codex/skills -maxdepth 2 -type f -name SKILL.md | sort
```

如果能看到 `brainstorming`、`writing-plans`、`test-driven-development`、`systematic-debugging`、`using-superpowers` 等，说明 Codex Superpowers 技能已经安装。

如果能看到 `conversation-memory`、`daily-self-review`、`home-panorama-tour`、`shouwang-wechat-agent-builder`、`yichen-wechat-local-vault`，说明个人 Codex skills 也已经安装。

Agent skills 可以运行：

```bash
find ~/.agents/skills -maxdepth 2 -type f -name SKILL.md | sort
```

如果能看到 `a-share-eod-pick`、`a-share-tail-close-overnight`、`a-stock-data`、`stock-analyst`、`technical-analysis`、`frontend-design`、`ui-ux-pro-max`、`find-skills`，说明全局 Agent skills 已完整同步。

Agent plugin marketplace 可以运行：

```bash
cat ~/.agents/plugins/marketplace.json
```

如果能看到 `personal` marketplace 和 `bright-path` 插件记录，说明 Agent 插件登记信息已同步。

## 股票分析技能前置条件

本包包含两个股票相关 skills：

- `a-share-eod-pick`：A 股主板尾盘隔夜纸面交易策略，支持今日选股、历史训练、次日验证和周度优化。
- `a-share-tail-close-overnight`：独立尾盘隔夜策略工作区管理技能，支持初始化脚手架、执行日内推荐、复盘及回测。
- `a-stock-data`：A 股全栈数据工具包，覆盖行情、研报、信号、资金面、新闻、基础数据和公告等多层数据源。
- `stock-analyst`：面向对话式股票技术分析，声明依赖 `stock-sdk` MCP 服务。
- `technical-analysis`：读取 `output/<股票代码>/<日期>/data.json`，运行 `scripts/analyze.py` 生成 `analysis.json`。
- `frontend-design`：前端 UI/UX 设计与实现指导技能，覆盖页面/组件级交付。
- `ui-ux-pro-max`：UI/UX 规则库与推荐检索技能，支持色彩/字体/交互/可用性决策。
- `bright-path`：个人规划和内容工作流插件，提供想法整理、内容草稿、平台改写、内容复盘、SW 知识库检索和 IMA Copilot 辅助技能。

迁移后需要在新机器上单独配置 Python 依赖、股票数据来源、MCP 服务或数据采集流程。本包不会迁移任何股票 API key、token、sqlite 数据库或历史输出。

`a-share-eod-pick`、`a-share-tail-close-overnight`、`frontend-design`、`ui-ux-pro-max` 来源记录也见 `resources/agents-skill-lock.json`。
`a-stock-data` 来源当前为 `simonlin1212/a-stock-data`。

## 关于官方系统技能和内置插件

当前机器可能会看到这些 Codex 官方内容：

- `~/.codex/skills/.system/imagegen`
- `~/.codex/skills/.system/openai-docs`
- `~/.codex/skills/.system/plugin-creator`
- `~/.codex/skills/.system/review-agent`
- `~/.codex/skills/.system/skill-creator`
- `~/.codex/skills/.system/skill-installer`
- `~/.codex/plugins/cache/openai-bundled/browser*`
- `~/.codex/plugins/cache/openai-bundled/computer-use`
- `~/.codex/plugins/cache/openai-bundled/record-and-replay`
- `~/.codex/plugins/cache/openai-bundled/visualize`
- `~/.codex/plugins/cache/openai-primary-runtime/documents`
- `~/.codex/plugins/cache/openai-primary-runtime/pdf`
- `~/.codex/plugins/cache/openai-primary-runtime/presentations`
- `~/.codex/plugins/cache/openai-primary-runtime/spreadsheets`
- `~/.codex/plugins/cache/openai-primary-runtime/template-creator`

这些属于 Codex 官方系统技能、内置浏览器插件或官方运行时插件缓存。本 kit 只在文档和配置模板中记录它们的用途，不复制缓存文件。迁移到新机器后，让 Codex 自己安装或刷新这些内容，避免把旧机器的运行时版本、临时文件或机器绑定状态带过去。

最近检查结果（2026-08-20）：

- `~/.codex/skills` 发现并已沉淀新增可迁移个人 Codex skills：`shouwang-wechat-agent-builder`、`yichen-wechat-local-vault`。差异中 `.system` 官方系统技能、`.DS_Store` 和 `__pycache__` 继续排除。本机官方系统技能当前包含 `imagegen`、`openai-docs`、`plugin-creator`、`review-agent`、`skill-creator`、`skill-installer`。
- `~/.codex/plugins/cache` 未发现新的可迁移第三方插件缺口；kit 已包含 `obra/superpowers@5.1.0`、`openai-api-curated/github@0.1.6`、`openai-api-curated/hyperframes@0.1.2`、`personal/bright-path@0.1.1+codex.20260715092747`。
- `~/.agents/skills` 当前检测到 `a-share-eod-pick`、`a-stock-data`、`find-skills`、`frontend-design`、`stock-analyst`、`technical-analysis`、`ui-ux-pro-max`；已按目录同步可复用文件到 `agents/skills/`，排除 `.git/`、`.mootdx/`、运行 `data/`、`reports/`、缓存和临时文件；kit 继续保留此前已沉淀的 `a-share-tail-close-overnight`，本次不删除历史资产。
- `~/.agents/plugins/marketplace.json` 已同步到 `agents/plugins/marketplace.json`；当前登记 `personal` marketplace 下的 `bright-path` 本地插件来源，不包含凭据。
- OpenAI 官方内置/运行时插件缓存当前为 `browser-use@0.1.0-alpha2`、`browser@26.803.41515`、`computer-use@1.0.1000633`、`record-and-replay@1.0.1000633`、`visualize@1.0.20` 和 `openai-primary-runtime/*@26.819.11345`，只更新文档记录和可选启用项，不复制到 kit。
- 本机 `~/.codex/automations/codex/automation.toml` 当前为 `ACTIVE`，`rrule = "FREQ=DAILY;BYHOUR=18;BYMINUTE=0;BYSECOND=0"`；kit 内模板仍保持 `PAUSED`，供新机器人工启用。
- `~/.codex/automations` 已整理为 `automations/templates/*.toml`：9 个任务均改为 `PAUSED`，移除运行时间戳，线程 ID 和本机路径均占位符化；`codex` 自动任务模板确认是每天 18:00。
- 本包继续排除 `auth.json`、API key、token、sqlite、history、sessions、日志、临时文件和机器专属路径。

## 关于插件页面

Codex 的插件页面显示的是 marketplace/插件注册状态，不一定显示直接安装到 `~/.codex/skills` 的技能。

所以：

- 技能已安装：看 `~/.codex/skills/<skill-name>/SKILL.md`。
- 插件缓存已安装：看 `~/.codex/plugins/cache/<vendor>/<plugin>/<version>/.codex-plugin/plugin.json`。
- 插件页可见：还需要 marketplace 注册和 `config.toml` 插件启用项。

这个 portable kit 优先保证技能可用，而不是强行改插件 UI 注册。
