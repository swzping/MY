# Study 标签云前端设计

## 目标

为 `study/` 学习笔记设计一个前端页面，把 Markdown 内容转成可浏览的知识标签云。页面重点不是营销展示，而是帮助快速看见学习体系里的名词、概念、技术分类、Agent 工具、收藏资源和项目案例。

## 页面定位

首页采用“知识星图 + 分类标签云”的结构：

- 顶部展示 `study` 的学习主题和分类筛选。
- 主视觉展示标签云，按分类和重要度组织标签。
- 标签下方或侧边展示当前选中分类的笔记摘要、来源文件和相关标签。
- 保留阅读路径入口，例如 Agent 工程总览、Agent Stack 实战手册、新闻趋势判断。

## 标签分类

标签按知识对象类型分类：

| 分类 | 示例 | 用途 |
| --- | --- | --- |
| 概念 / 名词 / 术语 | MCP、Skill、LangGraph、Workflow、Tool、Memory、Eval、Context | 建立基础概念地图 |
| Agent / 工具 / 平台 | Codex、Claude Code、Hermes Agent、OpenClaw、Cursor、AI Model Hub | 对比工具定位和适用场景 |
| 收藏地址 / 人物 / 资源 | 官方文档、GitHub、Skills Catalog、Michael Sitarzewski、API Docs | 汇总可追踪资源 |
| 项目 / 案例 / 模板 | TradingAgents、TradingAgents-CN、a-stock-data、QuantDinger、AI-Trader、Agent 项目结构模板 | 沉淀可研究案例 |
| 新闻趋势 | AI 圈新闻、技术更新、社会热点、行业热点、经济热点 | 承接每日新闻与趋势判断 |
| 学习行动 | 观察、立即试用、深入学习、记录案例、暂不跟进 | 把信息转成行动 |

## 数据同步

标签云数据不能手工写死在 React 组件里。实现时增加一个生成脚本，从 `study/` 下的 Markdown 文件提取数据并生成前端可读的 JSON。

数据来源包括：

- Markdown 一级标题作为文档标题。
- 二级和三级标题作为候选标签或章节。
- README 里的目录链接作为文档入口。
- 特定文件名和路径用于推断分类，例如 `ai-tools/`、`news-trends/`、`projects.md`、`people-and-resources.md`。
- 对关键术语保留一份轻量规则表，用来修正分类、权重和简介。

更新方式：

- 开发时运行 `npm run generate:study` 重新生成标签数据。
- 页面运行时读取生成后的 JSON。
- 后续新增或修改 `study/*.md` 后，只需要重新跑生成命令即可同步页面。

## 悬停简介

每个标签悬停时显示一个简介浮层，至少包含：

- 标签名称。
- 分类。
- 一句话简介。
- 来源笔记。
- 相关标签。

浮层在桌面端用 hover/focus 显示；移动端用点击显示，确保可访问性。

示例：

- `MCP`：能力接入协议，让 AI 客户端以统一方式访问工具、资源和外部系统。来源：`study/ai-tools/mcp-notes.md`。
- `Skill`：可复用工作方法包，沉淀流程、模板、脚本和检查清单。来源：`study/ai-tools/skills-notes.md`。
- `Codex`：面向软件工程的 coding agent。来源：`study/ai-tools/agent-engineering.md`。

## 视觉方向

采用深色知识图谱风格，但保持信息清楚：

- 主背景使用深色。
- 标签按分类使用不同强调色。
- 大标签表示更核心或出现频次更高的概念。
- 卡片边框和分隔线轻量化，避免普通卡片墙。
- 首页第一屏能看到“标签云 + 分类筛选 + 当前摘要”，不做营销 landing page。

## 组件结构

- `StudyPage`：页面容器，负责布局和状态。
- `TagCloud`：渲染标签云和分类簇。
- `TagTooltip`：标签悬停/点击简介。
- `CategoryFilter`：分类筛选。
- `StudyHighlights`：展示阅读路径、最近笔记和选中标签详情。
- `studyData`：由脚本生成的 JSON 数据。

## 验证

- 运行数据生成脚本，确认能从 `study/` 生成标签数据。
- 运行前端类型检查或构建。
- 启动本地页面，用浏览器检查桌面和移动端布局。
- 验证标签 hover/focus/click 都能显示简介。
