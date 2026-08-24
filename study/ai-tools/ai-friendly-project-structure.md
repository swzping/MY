# 利于 AI 协作的项目目录结构

这里记录适合 AI agent、coding agent 和多人协作的项目结构。重点不是追求文件越多越好，而是让 AI 能快速理解项目、遵守边界、执行验证、沉淀经验。

## 文件与目录总览

| 文件/目录 | 常见适用工具 | 主要作用 | 适合放什么 |
| --- | --- | --- | --- |
| `README.md` | 所有人和所有 AI 工具 | 项目入口说明 | 项目目标、启动方式、核心命令、目录导览 |
| `AGENTS.md` | Codex、OpenAI coding agents、通用 agent | Agent 工作规则 | 架构说明、代码规范、测试命令、禁止事项、验收标准 |
| `.codex/config.toml` | Codex | 项目级 Codex 配置 | sandbox、approval、model、MCP、hooks、项目配置覆盖 |
| `.codex/agents/` | Codex | 项目级自定义 subagents | worker、reviewer、researcher 等角色配置 |
| `CLAUDE.md` | Claude Code | Claude 专用项目规则 | Claude 工作偏好、命令、约束、项目记忆 |
| `.cursor/rules/` | Cursor | Cursor 规则库 | 按语言、模块、场景拆分的规则文件 |
| `.github/copilot-instructions.md` | GitHub Copilot | Copilot 仓库指令 | 代码风格、测试要求、PR 习惯、框架约定 |
| `instructions.md` | 通用 | 项目或任务说明 | 临时任务背景、人工说明、AI 执行约束 |
| `docs/` | 所有人和所有 AI 工具 | 长期文档 | 架构、业务规则、接口说明、决策记录 |
| `specs/` | 产品/工程/AI agent | 需求与设计 | 功能规格、验收标准、用户故事、边界条件 |
| `plans/` | 工程执行 | 实施计划 | 分阶段任务、检查点、风险、回滚方案 |
| `tests/` | 工程验证 | 自动化验证 | 单元测试、集成测试、回归测试、测试数据 |
| `scripts/` | 工程自动化 | 固定命令入口 | 初始化、构建、检查、数据处理、发布脚本 |
| `.env.example` | 开发者和 AI 工具 | 环境变量模板 | 变量名、示例值、用途说明，不放真实密钥 |

## 核心原则

- `README.md` 负责让人和 AI 知道“这个项目是什么”。
- `AGENTS.md` 负责让 AI 知道“在这个项目里应该怎么工作”。
- 工具专属文件只放该工具真的需要的差异，不要互相复制一大段。
- 长期稳定的知识放 `docs/`，具体功能设计放 `specs/`，执行步骤放 `plans/`。
- 能用命令验证的内容，尽量写成脚本或测试，而不是只写在说明里。

## 主流智能体差异

不同 AI 编程工具读取的文件不完全一样。最稳妥的做法是：用 `README.md` 和 `AGENTS.md` 放通用项目知识，再为具体工具补少量专属配置。

| 工具 | 首选通用说明 | 工具专属位置 | 适合放什么 | 不适合放什么 |
| --- | --- | --- | --- | --- |
| Codex | `AGENTS.md` | `.codex/config.toml`、`.codex/agents/`、`~/.codex/` | 项目规则、Codex 配置、MCP、hooks、自定义 subagents | 不要把长篇开发规范塞进 `config.toml` |
| Claude Code | `CLAUDE.md` 或 `AGENTS.md` | `~/.claude/`、项目内 `CLAUDE.md` | Claude 项目记忆、常用命令、协作偏好 | 不要和 `AGENTS.md` 写出相反规则 |
| Cursor | `README.md` | `.cursor/rules/` | 按主题拆分的编辑规则、框架规则、测试规则 | 不要把所有规则堆在一个超长文件 |
| GitHub Copilot | `README.md` | `.github/copilot-instructions.md` | 仓库级编码习惯、框架约定、测试要求 | 不要期待它承担完整 agent 流程管理 |
| Windsurf / 其他 IDE Agent | `README.md`、`AGENTS.md` | 工具自己的 rules / memories / workspace settings | 项目约定、命令、上下文提示 | 不要假设所有工具都会读取同一个专属文件 |

### Codex：AGENTS.md 和 .codex 的区别

Codex 里最容易混淆的是 `AGENTS.md` 和 `.codex/`。

`AGENTS.md` 适合写“怎么在这个仓库里工作”：

- 项目结构和架构边界。
- 常用安装、启动、测试、lint 命令。
- 代码风格和验收标准。
- 禁止事项，例如不要改生成文件、不要提交密钥。
- 子目录可以有更具体的 `AGENTS.md`，越靠近当前目录的规则越具体。

`.codex/config.toml` 适合写“Codex 这个工具怎么运行”：

- 默认模型或 provider。
- sandbox 和 approval 策略。
- MCP server 配置。
- hooks。
- 项目级配置覆盖。

`.codex/agents/` 适合写“Codex 的项目级自定义 subagents”：

- 每个 agent 一个 TOML 文件。
- 适合定义 explorer、reviewer、frontend-worker、data-researcher 等角色。
- 每个角色可以有自己的描述、developer instructions 和部分配置覆盖。

可以这样理解：

- `AGENTS.md`：给 agent 读的项目工作说明。
- `.codex/config.toml`：给 Codex 程序读的项目配置。
- `.codex/agents/`：给 Codex 创建项目专用角色。

一个 Codex 友好的项目结构可以是：

```text
project/
  README.md
  AGENTS.md
  .codex/
    config.toml
    agents/
      reviewer.toml
      explorer.toml
  docs/
  specs/
  plans/
  scripts/
  tests/
```

参考来源：

- [Codex: Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex: Config basics](https://developers.openai.com/codex/config-basic)
- [Codex: Subagents](https://developers.openai.com/codex/subagents)
- [Codex: MCP](https://developers.openai.com/codex/mcp)

## AGENTS.md

`AGENTS.md` 可以理解为项目给 AI agent 的工作说明书。它适合放在仓库根目录，让 agent 一进入项目就知道基本规则。

适合包含：

- 项目一句话说明。
- 技术栈和关键目录。
- 常用命令，例如安装、启动、测试、lint、格式化。
- 代码风格和架构边界。
- 哪些文件不能随便改。
- 完成任务前必须跑哪些验证。
- 安全注意事项，例如不要提交密钥、不要执行危险命令。

简单模板：

```markdown
# Agent Instructions

## Project

一句话说明项目目标。

## Commands

- Install: `...`
- Dev: `...`
- Test: `...`
- Lint: `...`

## Architecture

- `src/`: 核心代码
- `tests/`: 测试
- `docs/`: 文档

## Rules

- 优先复用现有组件和工具函数。
- 修改功能时补充或更新测试。
- 不要提交真实密钥或本地配置。
- 完成前运行 `...` 验证。
```

## CLAUDE.md

`CLAUDE.md` 是 Claude Code 常用的项目规则文件。它和 `AGENTS.md` 很像，但更偏 Claude 工具自己的长期项目记忆。

适合包含：

- Claude 在本项目中的工作方式。
- 项目约定和偏好。
- 常用调试命令。
- 易错点和历史经验。

建议：

- 如果项目主要给多种 AI 工具使用，优先维护 `AGENTS.md`，再在 `CLAUDE.md` 中写 Claude 特有差异。
- 避免 `CLAUDE.md` 和 `AGENTS.md` 内容冲突。

## .cursor/rules/

`.cursor/rules/` 是 Cursor 常见的规则目录，适合把规则拆成多个小文件。

适合按场景拆分：

- `frontend.mdc`：前端组件、样式、交互规则。
- `backend.mdc`：接口、数据库、服务层规则。
- `testing.mdc`：测试规范和命令。
- `docs.mdc`：文档写法。

适合这种结构：

```text
.cursor/
  rules/
    frontend.mdc
    backend.mdc
    testing.mdc
    docs.mdc
```

建议：

- 规则要短而具体。
- 每个规则文件只管一个主题。
- 规则里尽量写“应该怎么做”和“如何验证”，少写抽象口号。

## .github/copilot-instructions.md

`.github/copilot-instructions.md` 是 GitHub Copilot 读取的仓库级说明文件，适合放项目的整体编码约定。

适合包含：

- 使用的框架和语言版本。
- 命名规范。
- 测试要求。
- PR 或代码审查习惯。
- 不要使用的库或模式。

它通常比 `AGENTS.md` 更偏“代码补全和编辑建议”，不一定承担完整 agent 工作流。

## instructions.md

`instructions.md` 不是固定标准，但很适合用作临时或局部任务说明。

适合场景：

- 某个实验项目暂时不想建立完整规范。
- 给 AI 一次性说明任务背景。
- 在子目录里补充局部规则。

注意：

- 如果内容会长期使用，应迁移到 `AGENTS.md` 或 `docs/`。
- 如果只是一次性任务，完成后可以归档或删除，避免以后误导 AI。

## specs/ 与 plans/

`specs/` 和 `plans/` 能把“想做什么”和“怎么做”分开。

`specs/` 适合放：

- 需求背景。
- 用户目标。
- 功能范围。
- 非目标。
- 验收标准。
- 边界情况。

`plans/` 适合放：

- 实施步骤。
- 文件修改范围。
- 测试计划。
- 风险和回滚方式。
- 已完成/未完成状态。

建议：

- 复杂功能先写 `specs/`，再写 `plans/`。
- 小任务可以只写简短 plan。
- 不要把执行细节塞进需求文档，也不要让计划缺少验收标准。

## 推荐目录模板

一个利于 AI 协作的项目可以从下面这种结构开始：

```text
project/
  README.md
  AGENTS.md
  .env.example
  docs/
    architecture.md
    decisions.md
  specs/
    2026-06-29-feature-name.md
  plans/
    2026-06-29-feature-name-plan.md
  scripts/
    check.sh
    setup.sh
  src/
  tests/
```

如果同时使用 Cursor、Claude Code 和 Copilot，可以扩展：

```text
project/
  AGENTS.md
  .codex/
    config.toml
  CLAUDE.md
  .cursor/
    rules/
      frontend.mdc
      testing.mdc
  .github/
    copilot-instructions.md
```

## 和 Harness engineering 的关系

这些文件和目录本质上是在给 AI agent 搭建 harness：

- `README.md` 和 `docs/` 提供背景。
- `AGENTS.md`、`CLAUDE.md`、`.cursor/rules/` 提供规则。
- `scripts/` 和 `tests/` 提供验证入口。
- `specs/` 和 `plans/` 提供任务边界和执行路径。
- `.env.example` 和权限说明提供安全边界。

好的项目结构能减少 AI 的猜测，让它更像在一个清晰的工作台里行动。

## 常见错误

- 规则太长，AI 读了也抓不到重点。
- 多个规则文件互相冲突。
- 只写“要高质量”，不写测试命令和验收标准。
- 把真实 API key、账号、密码写进说明文件。
- 文档过期，命令已经不能运行。
- 每个工具都复制一份完整规则，后续维护时不同步。

## 最小可用版本

如果只想做最小配置，优先保留这四个：

```text
README.md
AGENTS.md
.env.example
tests/
```

其中 `AGENTS.md` 至少写清楚：

- 项目是什么。
- 怎么安装和运行。
- 怎么测试。
- 修改代码时遵守什么规则。
- 完成前如何验证。
