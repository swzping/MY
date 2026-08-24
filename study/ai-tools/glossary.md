# AI 工具术语表

## 术语总览

| 术语 | 类型 | 一句话理解 | 重点关注 |
| --- | --- | --- | --- |
| HyperFrames / Hypeframes | AI 视频生成框架 | 用 HTML/CSS/JS 生成、预览和渲染视频 | AI agent 视频制作、程序化视频、代码化内容生产 |
| Harness engineering | AI agent 工程方法 | 设计模型周围的工具、规则、上下文、验证和反馈环境 | 让 coding agent 更可靠、可控、可复用 |
| Headroom | 通用能力/资源概念 | 剩余空间、余量或继续提升的空间 | 性能余量、能力提升、上下文/token 预算 |
| RTK | 命令/缩写易混词 | 在截图中像是包在测试命令前的运行器或包装工具 | 区分 CLI runner、Redux Toolkit、RTK 定位等不同语境 |

## HyperFrames / Hypeframes

一句话解释：`HyperFrames` 是 HeyGen 开源的 HTML/CSS/JavaScript 转视频框架，让 AI 编程代理可以通过写网页式代码来生成、预览和渲染 MP4 视频。

常见中文说法：

- HyperFrames：规范拼写。
- Hypeframes：社交媒体和口语里容易出现的误拼或混写，可以当作检索入口，但正式记录时建议写 `HyperFrames`。
- HTML 转视频、AI Agent 视频生成框架、代码化视频制作。

常见语境：

- AI 编程代理视频制作：让 Codex、Claude Code、Cursor、Gemini CLI 等代理根据自然语言生成视频项目。
- 程序化视频：用 HTML、CSS、JS、动画时间线、图片、视频、音频等素材组合成可渲染的视频。
- 产品宣传/社媒短视频/解释视频：适合做产品介绍、网站转视频、动态图表、字幕叠加、动效片头等。
- 开源视频工作流：本地预览和渲染，核心依赖 Node.js、FFmpeg、CLI 和素材管理。

为什么值得关注：

- 它把 AI 擅长生成的网页代码，变成视频生产入口，降低了“从想法到视频初稿”的门槛。
- 它更像面向 AI agent 的视频制作基础设施，而不只是一个普通在线视频编辑器。
- 对个人学习来说，值得把它和 `Remotion`、`FFmpeg`、`GSAP`、`Lottie`、`Three.js`、字幕与音频工作流放在一起看。

例子：

- “用 HyperFrames 做一个 10 秒产品介绍视频”，可以理解为：让 AI agent 写 HTML/CSS/JS 组合画面、动效和素材，然后渲染成 MP4。
- “安装 HyperFrames skills”，通常是指给 AI 编程工具添加相关工作流，让它知道如何规划、预览、检查和渲染视频。

待确认：

- 实际项目中是否稳定好用，要看本地环境、素材质量、渲染速度、动画复杂度和代理执行能力。
- 如果只是想做无代码口播视频，HeyGen 主产品可能更合适；如果想用代码和 AI agent 自动化视频生产，HyperFrames 更值得试。

## Harness engineering

一句话解释：`Harness engineering` 是围绕 AI agent 设计“工作环境”的工程方法，包括上下文、工具、权限、验证、反馈循环和流程约束，让模型不只是会回答，而是能更稳定地完成任务。

中文理解：

- 可以译作：AI 驾驭工程、Agent 驾驭工程、AI 工作环境工程。
- `harness` 直译有“马具、系带、线束、约束装置”的意思，在 AI agent 语境里更接近“把模型接入可靠工作系统的一整套装置”。
- 注意不要和传统电气/机械里的 wire harness engineering 混淆，后者是线束设计工程。

常见语境：

- Coding agent：给 Codex、Claude Code、Cursor、Gemini CLI 等工具准备仓库说明、测试命令、代码规范、审查流程和权限边界。
- Agent harness：模型之外的执行层，包括 tools、memory、guardrails、workflow control、validation gates。
- Context engineering：harness engineering 可以看作 context engineering 的一个具体应用，但它不只管上下文，也管工具、流程、验证和治理。
- 多 agent 工作流：为不同 agent 设计角色、输入输出、交接方式、检查点和失败回退。

核心组成：

- Guides：让 agent 知道怎么做，例如 README、AGENTS.md、架构说明、代码规范、任务模板。
- Sensors：让 agent 知道做得对不对，例如测试、lint、类型检查、截图检查、日志、指标、人工评审。
- Tools：agent 可以调用的工具，例如 shell、浏览器、数据库、MCP、内部 API。
- Guardrails：权限、审批、沙箱、密钥隔离、危险操作限制。
- Feedback loops：失败后把经验沉淀回规范、测试、脚本或模板，减少同类错误复发。

为什么重要：

- 模型能力越强，越需要一个清晰的执行环境，否则它会在错误上下文里高效地产生错误结果。
- 好的 harness 能把“会用 AI”升级成“能让 AI 稳定交付”。
- 未来 AI 编程的竞争点不只是 prompt，而是仓库可读性、测试体系、工具接口、权限设计和流程验收。

例子：

- 给项目写清楚 `npm test`、`npm run lint`、截图验收流程、代码风格和禁止修改的目录，就是在做一部分 harness engineering。
- 为股票分析 agent 规定只能读取数据、不能直接下单，并要求输出来源、置信度和风险提示，也是在设计 harness。
- `agency-agents` 的角色定义、`QuantDinger` 的 paper-only token 和 audit log，都可以从 harness engineering 角度观察。

待确认：

- 这个词还在发展中，不同作者会强调不同部分：有人偏上下文，有人偏工具，有人偏安全治理，有人偏反馈闭环。
- 记录时最好结合具体场景问：这个 harness 约束了什么、暴露了什么工具、怎么验证结果、失败经验如何沉淀。

## Headroom

一句话解释：`headroom` 通常指“剩余空间”或“余量”，在 AI 工具语境里常用来描述系统、模型或用户体验还能继续提升的空间。

常见语境：

- 性能余量：模型、工具链或基础设施距离瓶颈还有多少空间。
- 能力提升空间：当前效果还没有达到上限，仍有优化潜力。
- 上下文余量：在上下文窗口或 token 预算中还剩多少可用空间。

例子：

- “这个模型在复杂推理任务上还有 headroom。”表示它仍有改进空间。
- “当前 prompt 已经接近上下文上限，headroom 不多。”表示可继续追加的信息空间很少。

待确认：

- 具体文章或产品文档里使用 `headroom` 时，需要结合上下文判断它指性能、能力、预算还是体验余量。

## RTK

一句话解释：在截图里的命令 `rtk venv/bin/python -m pytest ...` 中，`rtk` 看起来是放在实际命令前面的命令行运行器或包装工具，用来启动、托管或记录后续的 Python 测试命令。

截图语境：

- 形式：`rtk venv/bin/python -m pytest -q tests/...`
- 真正要跑的命令：`venv/bin/python -m pytest ...`
- `rtk` 的位置：在 Python 命令前面，说明它更像一个 CLI runner、task wrapper 或环境包装层，而不是 Python、pytest 或测试文件本身的一部分。
- 中文理解：可以先记成“用 rtk 包一层来运行测试命令”。

可能作用：

- 统一命令运行方式，例如设置环境变量、工作目录或虚拟环境。
- 捕获运行过程，例如日志、状态、输出、耗时或失败信息。
- 给 AI 编程工具提供任务执行上下文，例如知道当前正在跑测试、关联后续修复步骤。

仍需区分的其他常见含义：

- Redux Toolkit：前端状态管理库 Redux 的官方工具集，常简称 RTK。
- Real-Time Kinematic：实时动态差分定位技术，常见于测绘、无人机和自动驾驶定位场景。
- AI 工具语境中的内部指标或产品缩写：如果出现在某个产品、论文或团队文档里，可能是特定名词，需要查来源。

例子：

- 截图里的 “正在运行 `rtk venv/bin/python -m pytest ...`” 可以理解为“通过 rtk 这个运行器执行 pytest 测试”。
- 前端开发里说 “RTK Query”，通常指 Redux Toolkit Query。
- 定位系统里说 “RTK 精度”，通常指 Real-Time Kinematic 定位。

待确认：

- 当前机器的 shell 中没有找到 `rtk` 命令，因此还不能确认它的完整名称、来源和全部功能。
- 如果后续能看到 `rtk --help`、安装来源、项目 README 或工具文档，可以把这里更新成确定解释。

## 术语模板

复制下面模板新增条目：

```markdown
## 术语名

一句话解释：

常见语境：

- 

例子：

- 

待确认：

- 
```
