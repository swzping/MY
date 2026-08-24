# Agent 项目结构模板

这个模板适合创建 AI Agent、MCP server、Skill、LangGraph workflow 或混合型项目。实际使用时不必全部创建，按项目复杂度逐步增加。

## 最小结构

适合刚开始验证想法：

```text
project/
  README.md
  AGENTS.md
  .env.example
  scripts/
  tests/
  docs/
```

每个文件的作用：

| 文件/目录 | 作用 |
| --- | --- |
| `README.md` | 给人和 AI 看的项目入口 |
| `AGENTS.md` | 给 coding agent 的工作规则 |
| `.env.example` | 环境变量模板，不放真实密钥 |
| `scripts/` | 可重复运行的脚本 |
| `tests/` | 自动化验证 |
| `docs/` | 长期文档 |

## 完整 Agent 工程结构

适合需要 Skill、MCP、LangGraph、工具、记忆和评估的项目：

```text
project/
  README.md
  AGENTS.md
  .env.example

  docs/
    architecture.md
    decisions/
    runbooks/

  specs/
    2026-06-29-feature-name.md

  plans/
    2026-06-29-feature-name-plan.md

  skills/
    domain-research/
      SKILL.md
      references/
      templates/
      scripts/

  mcp-servers/
    domain-data/
      README.md
      src/
        server.ts
        tools/
        resources/
        auth/
      tests/
      .env.example

  graphs/
    research-workflow/
      README.md
      src/
        graph.py
        state.py
        nodes/
        edges/
      tests/

  tools/
    clients/
    parsers/
    validators/

  prompts/
    system/
    tasks/
    eval/

  memory/
    schemas/
    examples/
    exports/

  evals/
    datasets/
    rubrics/
    runners/
    reports/

  scripts/
    setup.sh
    check.sh
    dev.sh

  tests/
    fixtures/
    integration/
    unit/
```

## 目录职责

| 目录 | 主要放什么 | 不适合放什么 |
| --- | --- | --- |
| `docs/` | 架构、运行手册、长期决策 | 临时草稿 |
| `specs/` | 需求、边界、验收标准 | 具体执行流水账 |
| `plans/` | 分阶段实施计划 | 长期架构真相 |
| `skills/` | 可复用 AI 工作方法包 | 单纯业务代码 |
| `mcp-servers/` | MCP server 代码和工具定义 | 无边界的万能脚本 |
| `graphs/` | LangGraph 或其他 workflow 编排 | 外部系统认证逻辑 |
| `tools/` | 普通工具函数、SDK client、解析器 | Agent 流程说明 |
| `prompts/` | 稳定提示词模板 | 密钥、生产数据 |
| `memory/` | 记忆 schema、样例和导出 | 不受控的敏感数据 |
| `evals/` | 评估数据、rubric、运行器和报告 | 没有标准的主观评价 |
| `scripts/` | 可重复运行的命令入口 | 只能在一个人电脑上跑的隐式操作 |
| `tests/` | 自动化测试和 fixtures | 生产密钥和真实敏感数据 |

## README.md 模板

~~~markdown
# Project Name

一句话说明项目目标。

## What It Does

- 

## Architecture

- `skills/`: 
- `mcp-servers/`: 
- `graphs/`: 
- `tools/`: 
- `evals/`: 

## Setup

```bash
...
```

## Development

```bash
...
```

## Verification

```bash
...
```

## Safety

- 默认只读或 sandbox。
- 写操作需要人工确认。
- 不提交真实密钥。
~~~

## AGENTS.md 模板

~~~markdown
# Agent Instructions

## Project

一句话说明项目是什么，以及 Agent 在这里主要帮什么忙。

## Commands

- Install: `...`
- Dev: `...`
- Test: `...`
- Lint: `...`

## Architecture

- `skills/`: 可复用工作流。
- `mcp-servers/`: 外部能力接入。
- `graphs/`: 多步骤 Agent 编排。
- `tools/`: 普通工具函数和客户端。
- `evals/`: 质量评估。

## Rules

- 优先复用现有工具和脚本。
- 修改行为时补充或更新测试。
- 涉及外部系统时先确认权限边界。
- 不提交真实密钥、token 或隐私数据。
- 完成前运行验证命令。
~~~

## MCP server README 模板

~~~markdown
# MCP Server: Name

## Purpose

这个 server 给 AI 客户端暴露什么能力。

## Tools

| Tool | 输入 | 输出 | 权限 |
| --- | --- | --- | --- |
| `tool_name` |  |  | read-only |

## Resources

| Resource | URI | 内容 |
| --- | --- | --- |
|  |  |  |

## Environment

- `API_KEY`: 
- `BASE_URL`: 

## Safety

- 默认只读。
- 写操作需要人工确认。
- 记录调用日志。

## Test

```bash
...
```
~~~

## Skill SKILL.md 模板

~~~markdown
---
name: skill-name
description: 什么时候使用这个 skill
---

# Skill Name

## When To Use

- 

## Workflow

1. 
2. 
3. 

## Inputs

- 

## Output

- 

## Verification

- 

## Safety

- 
~~~

## LangGraph workflow README 模板

~~~markdown
# Graph: Workflow Name

## Purpose

这个图负责什么流程。

## State

| Field | Type | Meaning |
| --- | --- | --- |
|  |  |  |

## Nodes

| Node | Responsibility |
| --- | --- |
| `planner` |  |
| `executor` |  |
| `reviewer` |  |

## Edges

- `start -> planner`
- `planner -> executor`
- `executor -> reviewer`
- `reviewer pass -> end`
- `reviewer fail -> executor`

## Human Approval

- 哪些节点前需要人工确认。

## Test

```bash
...
```
~~~

## 采用建议

新项目不要一次性铺满完整结构。建议从最小结构开始：

1. 先有 `README.md`、`AGENTS.md`、`scripts/`、`tests/`。
2. 重复任务稳定后，加 `skills/`。
3. 外部能力需要复用时，加 `mcp-servers/`。
4. 流程复杂后，加 `graphs/`。
5. 结果质量需要长期追踪时，加 `evals/`。
