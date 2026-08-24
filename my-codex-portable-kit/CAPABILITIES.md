# Codex 能力清单

这份清单用于快速了解当前 `my-codex-portable-kit` 已经沉淀了哪些插件、技能、MCP、规则和配置。

## 总览

| 类型 | 名称 | 作用 |
| --- | --- | --- |
| 第三方插件 | Superpowers `5.1.0` | 给 coding agent 增加规划、TDD、调试、代码审查、分支收尾等工程工作流。 |
| Curated 插件 | GitHub `0.1.6` | 检查仓库、PR、Issue、CI，处理 review comments，并辅助提交 PR。 |
| Curated 插件 | HyperFrames `0.1.2` | 用 HTML/CSS/GSAP 构建视频合成、字幕、TTS、转场和网站转视频流程。 |
| 个人插件 | Bright Path `0.1.1+codex.20260715092747` | 整理想法、行动计划、内容创作、多平台改写、知识库检索和复盘。 |
| Codex 技能集合 | Superpowers skills | 14 个工程流程技能，安装到 `~/.codex/skills` 后由 Codex 按任务触发。 |
| 个人 Codex 技能 | `conversation-memory` / `daily-self-review` / `home-panorama-tour` / `shouwang-wechat-agent-builder` / `yichen-wechat-local-vault` | 用于整理历史会话记忆、每日自我复盘、家装 360 全景/VR 看房、本地微信解析和微信分析 Agent 生成。 |
| 官方系统技能 | `imagegen` / `openai-docs` / `plugin-creator` / `review-agent` / `skill-creator` / `skill-installer` | 当前 Codex 运行时提供的 `.system` skills；本包只记录能力，不迁移文件。 |
| Agent 技能发现 | `find-skills` | 安装到 `~/.agents/skills`，帮助搜索、评估和安装 open agent skills 生态里的技能。 |
| Agent 插件市场 | `agents/plugins/marketplace.json` | 恢复 `~/.agents/plugins` 的 personal marketplace，目前登记 Bright Path 本地插件来源。 |
| Agent A 股数据技能 | `a-stock-data` | 安装到 `~/.agents/skills`，A 股全栈数据工具包，覆盖行情、研报、资金、新闻、公告等数据源。 |
| Agent 股票分析技能 | `stock-analyst` / `technical-analysis` | 安装到 `~/.agents/skills`，用于股票 K 线、技术指标、资金流和交易信号分析；需要另行配置数据源。 |
| Agent 交易策略技能 | `a-share-eod-pick` / `a-share-tail-close-overnight` | 安装到 `~/.agents/skills`，用于尾盘隔夜纸面交易筛选、历史训练、次日验证与策略优化。 |
| UI 设计技能 | `frontend-design` / `ui-ux-pro-max` | 安装到 `~/.agents/skills`，用于界面风格、可用性与交互设计方法与查询。 |
| MCP | Figma MCP | 让 Codex 连接 Figma，读取设计、截图、变量、组件信息，并可写入 Figma。 |
| 内置插件启用项 | Documents / PDF / Spreadsheets / Presentations / Template Creator / Browser / Visualize | 在配置模板中保留启用项；实际插件由 Codex 官方运行时提供。 |
| 自动任务模板 | `automations/templates/*.toml` | 保存本机 Codex 自动任务的脱敏参考模板；默认暂停，路径和线程 ID 需要在新机器上替换。 |
| 命令规则 | `rules/default.rules` | 预先允许常用开发命令，减少重复授权。 |
| 全局说明 | `instructions.md` | 放个人长期偏好、工程习惯和交互规则；当前文件为空，可继续补充。 |

## 插件

### Superpowers

- 来源：`obra/superpowers`
- 版本：`5.1.0`
- 本包位置：`plugins/cache/obra/superpowers/5.1.0`
- 主要作用：把需求澄清、计划、TDD、系统化调试、子代理开发、代码审查和收尾流程固化为 Codex skills。
- 注意：插件缓存存在不等于 Codex 插件页一定显示；插件页可见还取决于 marketplace 注册和 `config.toml` 启用项。

### GitHub

- 来源：`openai-api-curated/github`
- 版本：`0.1.6`
- 本包位置：`plugins/cache/openai-api-curated/github/11c74d6b`
- 主要作用：仓库/PR/Issue 研判、PR review comments 处理、GitHub Actions CI 排查、提交和打开 PR。
- 注意：`.mcp.json` 只包含 `GITHUB_PAT_TOKEN` 环境变量名，不包含 token；新机器需要自行登录或配置 GitHub 授权。

### HyperFrames

- 来源：`openai-api-curated/hyperframes`
- 版本：`0.1.2`
- 本包位置：`plugins/cache/openai-api-curated/hyperframes/11c74d6b`
- 主要作用：HTML 视频合成、GSAP 动画、字幕/转场/TTS、音频响应视觉和网站转视频工作流。

### Bright Path

- 来源：`personal/bright-path`
- 版本：`0.1.1+codex.20260715092747`
- 本包位置：`plugins/cache/personal/bright-path/0.1.1+codex.20260715092747`
- 主要作用：整理想法、制定下一步、内容草稿、多平台改写、发布复盘、SW 知识库查询和 IMA Copilot 辅助。
- 注意：`.mcp.json` 只记录本机 IMA Copilot MCP 地址 `http://127.0.0.1:8081/mcp`，不包含密钥；新机器需要另行启动对应服务。

## Skills

### Superpowers 工作流技能

| 技能 | 什么时候用 | 能力摘要 |
| --- | --- | --- |
| `using-superpowers` | 会话开始或判断是否需要技能时 | 强制先识别并使用适用技能，建立“技能优先”的工作方式。 |
| `brainstorming` | 做新功能、组件、行为变更等创意/产品工作前 | 先探索上下文、澄清目标、提出方案、形成设计，再进入实现。 |
| `writing-plans` | 已有需求或设计，需要拆成实施计划时 | 写可执行的工程计划，明确文件、步骤、测试和验收。 |
| `executing-plans` | 已有实施计划，需要按计划执行时 | 读取并审查计划，逐项执行，最后进入分支收尾。 |
| `subagent-driven-development` | 有计划且任务相对独立，适合多代理执行时 | 每个任务派发独立 subagent，并做规格审查和代码质量审查。 |
| `dispatching-parallel-agents` | 有多个相互独立的问题或任务时 | 并行派发代理处理独立问题，降低上下文污染和等待时间。 |
| `test-driven-development` | 实现功能、修 bug、改行为前 | 强制先写失败测试，再写最小实现，再重构。 |
| `systematic-debugging` | 遇到 bug、测试失败、构建失败、异常行为时 | 先找根因，再修复，避免拍脑袋补丁。 |
| `verification-before-completion` | 准备说“完成/修好/测试通过”前 | 先运行新鲜验证命令，用证据支撑完成声明。 |
| `requesting-code-review` | 完成主要功能、任务或准备合并前 | 派发代码审查，基于 diff 和需求检查问题。 |
| `receiving-code-review` | 收到代码审查反馈后 | 先理解和验证反馈，再决定接受、追问或技术性反驳。 |
| `finishing-a-development-branch` | 实现完成且测试通过，准备合并/PR/清理时 | 检查测试、判断环境、提供合并/PR/清理选项。 |
| `using-git-worktrees` | 需要隔离工作区或执行计划前 | 优先使用平台原生 worktree，必要时退回 git worktree。 |
| `writing-skills` | 创建、修改或验证技能时 | 用类似 TDD 的方法编写和验证技能文档。 |

### 个人 Codex 技能

| 技能 | 什么时候用 | 能力摘要 |
| --- | --- | --- |
| `conversation-memory` | 需要从 Codex 历史对话中恢复上下文、整理备忘录、压缩历史讨论或创建可迁移提示词时 | 读取本机 Codex 会话记录并整理成结构化记忆；附带 memo schema 与线程提取脚本，但不迁移原始历史、sessions 或 sqlite。 |
| `daily-self-review` | 要复盘当天问题、对话、工作笔记、学习轨迹或总结个人优化方向时 | 基于日常问答和使用痕迹生成个人成长复盘，识别可沉淀资产、改进点和下一步行动。 |
| `home-panorama-tour` | 做家装 360 全景、VR 看房、房间漫游、类似 JustEasy 的页面时 | 帮助选择 Photo Sphere Viewer、Pannellum、Marzipano、A-Frame/WebXR、Three.js 等方案，并覆盖热点、场景切换、户型图、移动端陀螺仪、全屏/VR 等功能。 |
| `shouwang-wechat-agent-builder` | 需要在另一台 macOS 上生成或修复本地微信群聊分析桌面 Agent 时 | 用 Electron + React + Vite 生成便携桌面应用，接入本机 `yichen-wechat-local-vault`，支持群聊导入、日期过滤和 OpenAI-compatible 问答配置。 |
| `yichen-wechat-local-vault` | 需要解析本机微信 Mac 4.x 聊天记录、联系人、群聊、朋友圈、收藏夹、语音或附件索引时 | 提供本地 key 匹配、全量/增量解密、会话导出、搜索、统计和群聊摘要素材包流程；只迁移脚本和说明，不迁移密钥、明文库、聊天内容或机器状态。 |

### 插件随附技能

这些技能随插件缓存一起沉淀到 `plugins/cache/`，由 Codex 插件系统按插件命名空间加载，不作为裸 `~/.codex/skills` 复制。

| 插件 | 技能 | 能力摘要 |
| --- | --- | --- |
| GitHub | `github` / `gh-address-comments` / `gh-fix-ci` / `yeet` | GitHub 仓库与 PR 研判、review comments 处理、CI 日志排查，以及本地变更提交/推送/开 draft PR。 |
| HyperFrames | `hyperframes` / `hyperframes-cli` / `hyperframes-registry` / `gsap` / `website-to-hyperframes` | 视频合成项目创建、CLI 预览/渲染、registry 组件安装、GSAP 动画参考，以及网站捕获到视频的工作流。 |
| Bright Path | `bright-path` / `content-drafter` / `creator-workflow` / `creator-review` / `platform-rewriter` / `topic-selector` / `sw-knowledge` / `ima-copilot` | 想法整理、内容创作与多平台改写、发布复盘、选题筛选、本地 SW 知识库和 IMA Copilot 查询。 |

### 全局 Agent skills

这些技能从 `~/.agents/skills` 整理到 `agents/skills/`，安装脚本会恢复到新机器的 `~/.agents/skills`，不会混入 `~/.codex/skills`。

| 技能 | 什么时候用 | 能力摘要 |
| --- | --- | --- |
| `find-skills` | 用户问“有没有某类 skill”“怎么扩展能力”“找一个技能做 X”时 | 使用 `npx skills find/add/check/update` 搜索和安装 open agent skills 生态里的技能。 |
| `a-stock-data` | 用户要查 A 股行情、估值、研报、题材、资金流、龙虎榜、解禁、两融、新闻或公告时 | 自包含 A 股数据工具包，内嵌直连 HTTP API 与 mootdx 示例代码；来源 `simonlin1212/a-stock-data`，依赖 `mootdx requests pandas stockstats`，iwencai 语义搜索需单独配置 API key。 |
| `stock-analyst` | 用户要求分析某只股票走势、支撑压力、MACD/KDJ/RSI、资金流或是否值得买入时 | 通过 `stock-sdk` MCP 的 `analyze_stock` 等能力获取行情、K 线指标、资金流、北向持仓和分红数据，并输出结构化技术分析报告。 |
| `technical-analysis` | 已有 `output/<股票代码>/<日期>/data.json`，需要离线计算 MA/MACD/RSI、趋势和买卖信号时 | 使用 `scripts/analyze.py` 读取采集数据并生成 `analysis.json`，附带 `references/indicators.md` 指标说明。 |
| `a-share-eod-pick` | 用户要求执行“今日选股”/“训练历史”/“复盘验证”/“策略优化”时 | 触发 `run_today_report`、`train_history`、`validate_yesterday`、`optimize_weekly` 和 `show_status`，支持 Top1/空仓策略与反馈闭环。 |
| `a-share-tail-close-overnight` | 用户要求搭建/修复尾盘隔夜策略工作区或产出策略执行与收益报告时 | 管理 `reports/strategy_01` 工作流、脚手架初始化、策略日报与复盘输出。 |
| `frontend-design` | 用户要做前端页面/组件/应用并要求更有辨识度的设计实现时 | 提供设计方向、样式系统、交互建议与前端实现策略。 |
| `ui-ux-pro-max` | 用户要做 UI/UX 调研、可用性优化或设计规范检索时 | 基于规则库输出颜色、字体、布局、组件、动画与可访问性建议。 |

股票相关 Agent skills 只提供通用数据流程、分析流程、脚本和参考说明，不迁移任何 API key、token、sqlite 数据、历史输出或机器路径。迁移到新机器后，需要单独配置 Python 依赖、`stock-sdk` MCP、数据采集流程或 `data-collect` 能力。全局 `.agents` skills 的来源清单保存在 `resources/agents-skill-lock.json`，只作追溯参考。

### 全局 Agent plugins

`agents/plugins/marketplace.json` 从 `~/.agents/plugins/marketplace.json` 整理而来，安装脚本会恢复到新机器的 `~/.agents/plugins/marketplace.json`。

当前 marketplace：

| Marketplace | 插件 | 来源 | 说明 |
| --- | --- | --- | --- |
| `personal` | `bright-path` | `local`, `./plugins/bright-path` | 让 Agent 插件系统知道 personal Bright Path 插件来源；不包含凭据、token、sqlite 或运行状态。 |

## MCP

### Figma MCP

配置模板中包含：

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
enabled = true
```

启用后可用能力包括：

- 读取 Figma 文件、节点、页面结构和设计上下文。
- 获取节点截图、变量、组件元数据、Code Connect 映射。
- 搜索设计系统组件、样式、变量。
- 通过 Figma Plugin API 创建或修改设计。
- 上传/下载设计资产。
- 生成 FigJam 图表或把网页导入 Figma。

使用前提：新机器上的 Codex/Figma 账号需要有对应文件权限。

## 内置/官方插件启用项

当前机器存在 OpenAI 官方插件缓存：

- `openai-bundled/browser-use@0.1.0-alpha2`
- `openai-bundled/browser@26.803.41515`
- `openai-bundled/computer-use@1.0.1000633`
- `openai-bundled/record-and-replay@1.0.1000633`
- `openai-bundled/visualize@1.0.20`
- `openai-primary-runtime/documents@26.819.11345`
- `openai-primary-runtime/pdf@26.819.11345`
- `openai-primary-runtime/presentations@26.819.11345`
- `openai-primary-runtime/spreadsheets@26.819.11345`
- `openai-primary-runtime/template-creator@26.819.11345`

这些缓存不打包进 portable kit。配置模板中只保留这些插件启用项和使用说明：

| 插件 | 作用 |
| --- | --- |
| `documents@openai-primary-runtime` | 创建、编辑、渲染和验证 Word/文档类文件。 |
| `pdf@openai-primary-runtime` | 读取、生成、渲染和检查 PDF。 |
| `spreadsheets@openai-primary-runtime` | 创建、编辑、分析和可视化表格。 |
| `presentations@openai-primary-runtime` | 创建、编辑、渲染和导出 PPTX/演示文稿。 |
| `template-creator@openai-primary-runtime` | 从 DOCX/PPTX/XLSX 参考文件创建或更新个人 artifact template skills。 |
| `browser@openai-bundled` | 控制 Codex 内置浏览器，测试本地网页、截图、点击、输入等。 |
| `browser-use@openai-bundled` | 旧版/别名浏览器插件缓存，当前只记录版本，不在模板中启用。 |
| `computer-use@openai-bundled` | 控制本机应用 UI；属于官方内置插件缓存，不打包。 |
| `record-and-replay@openai-bundled` | 录制/回放相关官方缓存；不打包。 |
| `visualize@openai-bundled` | 在对话中创建交互式图表、地图、模拟器、3D 模型和数据探索器；不打包。 |

注意：本迁移包不打包 OpenAI 官方插件缓存。新机器应通过 Codex 自己的插件系统安装或刷新这些插件。

## 官方系统 skills

当前 Codex 运行时还提供以下 `.system` skills：

| 技能 | 作用 | 迁移策略 |
| --- | --- | --- |
| `imagegen` | 生成或编辑位图视觉资产。 | 不打包，随 Codex 官方运行时提供。 |
| `openai-docs` | 查询 OpenAI/Codex 官方文档、模型和升级指南。 | 不打包，随 Codex 官方运行时提供。 |
| `plugin-creator` | 创建和维护 Codex 插件。 | 不打包，随 Codex 官方运行时提供。 |
| `review-agent` | 作为代码审查子代理检查变更风险。 | 不打包，随 Codex 官方运行时提供。 |
| `skill-creator` | 创建和维护 Codex skills。 | 不打包，随 Codex 官方运行时提供。 |
| `skill-installer` | 安装 curated 或 GitHub 来源的 skills。 | 不打包，随 Codex 官方运行时提供。 |

判断规则：`~/.codex/skills/.system/` 下的内容视为官方系统能力，只记录用途，不复制到 `skills/`。个人或第三方可迁移 skills 应位于 `~/.codex/skills/<skill-name>/`。

## 命令审批规则

`rules/default.rules` 当前预先允许：

| 命令前缀 | 用途 |
| --- | --- |
| `npm start` | 启动 Node 项目。 |
| `npm run dev` | 启动前端/全栈开发服务器。 |
| `npm run deploy` | 执行项目部署脚本。 |
| `curl` | 下载、请求 API、安装脚本辅助。 |
| `git ls-remote` | 检查远端 Git 分支/版本。 |
| `open` | 在 macOS 打开文件、URL 或应用。 |
| `xcodebuild` | 构建或测试 Xcode 项目。 |
| `xcrun simctl` | 操作 iOS 模拟器。 |

## 自动任务模板

`automations/` 中保存了 9 个从 `~/.codex/automations` 整理出的模板：

| 模板 | 类型 | 用途 |
| --- | --- | --- |
| `codex.toml` | cron | 每天 18:00 检查并整理 Codex skills/plugins portable kit。 |
| `9-ai.toml` | cron | 每天扫描 AI/Agent/LLM 情报并写入知识库输入流。 |
| `automation-4.toml` | heartbeat | 晚上从工作台和输入流候选里推进知识整理确认。 |
| `16-30-ai.toml` | cron | 更新 Obsidian AI 自生长知识库。 |
| `9-30.toml` | cron | 更新学习记录中的今日新闻与趋势判断。 |
| `automation-2.toml` | cron | 生成每日晨报。 |
| `automation.toml` | heartbeat | 每小时工作待办提醒。 |
| `automation-3.toml` | heartbeat | 验证尾盘买入收益报告。 |
| `15-t-1.toml` | heartbeat | 每 15 分钟 T+1 股票筛选提醒。 |

迁移策略：只保留任务定义参考，不自动安装。模板全部设置为 `PAUSED`，移除了 `created_at`、`updated_at`，把 `target_thread_id` 和本机路径替换为占位符。`memory.md`、jitter salt、日志和运行状态不进入 portable kit。

## 配置模板

`templates/config-portable.toml` 记录了可迁移偏好：

| 配置 | 当前值/用途 |
| --- | --- |
| `model` | `gpt-5.5` |
| `model_reasoning_effort` | `medium` |
| `review_model` | `gpt-5.4` |
| `web_search` | `live` |
| `model_provider` | `51token` |
| `[model_providers.51token]` | 自定义模型提供商模板，需要新机器自行确认凭据/可用性。 |
| `[desktop] localeOverride` | `zh-CN`，Codex 桌面界面中文。 |
| `[features] js_repl` | `false` |
| `[plugins."documents@openai-primary-runtime"]` | 官方文档插件启用项，仅作模板记录。 |
| `[plugins."spreadsheets@openai-primary-runtime"]` | 官方表格插件启用项，仅作模板记录。 |
| `[plugins."presentations@openai-primary-runtime"]` | 官方演示文稿插件启用项，仅作模板记录。 |
| `[plugins."pdf@openai-primary-runtime"]` | 官方 PDF 插件启用项，仅作模板记录。 |
| `[plugins."browser@openai-bundled"]` | 官方内置浏览器插件启用项，仅作模板记录。 |
| `[plugins."template-creator@openai-primary-runtime"]` | 官方模板创建插件启用项，仅作模板记录。 |
| `[plugins."visualize@openai-bundled"]` | 官方可视化插件启用项，仅作模板记录。 |
| `[plugins."github@openai-api-curated"]` | GitHub curated 插件启用项，不含 GitHub token。 |
| `[plugins."hyperframes@openai-api-curated"]` | HyperFrames curated 插件启用项。 |
| `[plugins."bright-path@personal"]` | Bright Path 个人插件启用项；IMA Copilot 服务需新机器另行启动。 |

模板不会自动覆盖新机器的 `~/.codex/config.toml`。安装脚本只会复制到 `~/.codex/config.portable-kit.toml`，需要人工审阅后合并。

## 建议后续沉淀

- 把你长期有效的工作偏好写入 `instructions.md`。
- 把常用项目类型的经验做成独立 skill，而不是只写在聊天记录里。
- 对每个第三方插件保留来源、版本和为什么安装，避免半年后看不懂。
- 不要把登录凭据、API key、sqlite 状态库、会话历史放进迁移包。
