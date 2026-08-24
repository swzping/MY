# 守望智能体

Electron + React + Vite 桌面工作台。目前重点模块是“微信群历史分析”：导入指定群聊数据后，用问答方式分析群成员、话题、活跃度和最近聊天内容。

## 安装运行

环境要求：

- Node.js 18+，建议 20+
- npm
- macOS 桌面端建议用 Electron 启动，因为读取本机 vault 和 Python CLI 需要桌面后端能力

安装依赖：

```bash
cd /Users/edy/Documents/MY/shouwang
npm install
```

开发模式：

```bash
npm run dev
```

`npm run dev` 和 `npm run dev:electron` 都会同时启动 Vite 前端和 Electron 桌面端。

如果只想单独启动网页预览：

```bash
npm run dev:renderer
```

常用验证：

```bash
npm run build
node --test test/*.mjs
```

打包：

```bash
npm run pack
npm run dist
```

## 模型配置

默认模型配置集中在：

```text
shared/defaultSettings.ts
```

本机运行时设置保存到 Electron userData：

```text
/Users/edy/Library/Application Support/shouwang/settings.json
```

微信问答使用 OpenAI 兼容的 Responses API。当前实现会把 `apiBaseUrl` 规范成：

```text
{base_url}/responses
```

例如：

```text
https://ap1.upit.top/51Token/v1/responses
```

请求体使用：

```json
{
  "model": "gpt-5.5",
  "input": "群聊上下文和用户问题"
}
```

模型调用代码在：

```text
shared/wechatModelClient.ts
electron/modelClient.ts
```

## 群聊分析模块

入口在：

```text
src/App.tsx
electron/main.ts
electron/wechatAnalysis.ts
electron/wechatAgentTool.ts
src/wechatBrowserAnalysis.ts
```

界面目标保持简单：

- 数据名称：填写群名，例如“天沐锦江老板群”
- 开始时间、结束时间：限制导入时间范围
- 导入数据：桌面端从本机 vault 导入；网页预览端导入 md/txt/json/csv 文件
- 对话分析：导入后向模型提问

### 数据来源

桌面端不直接读取微信原始缓存目录，也不在 App 里抓 key 或解密数据库。

当前链路是：

1. Electron 调用项目内脚本：

```text
wechat-agent-tool/wechat_agent_cli.py
```

2. `wechat_agent_cli.py` 调用已安装的微信本地保险箱 skill：

```text
~/.codex/skills/yichen-wechat-local-vault/scripts/vault_cli.py
```

3. `vault_cli.py` 只读已经解密好的 vault：

```text
/Users/edy/Library/Application Support/wechat-local-vault/decrypted/current
```

常见可用库包括：

```text
contact/contact.db
message/message_0.db
message/message_fts.db
message/message_resource.db
session/session.db
```

### 微信本地保险箱 skill

这个项目依赖“安装微信本地保险箱 skill”那次对话建立的本地能力。它的职责是把微信数据整理成一个本机可查询 vault，并提供 `vault_cli.py` 统一入口。

本项目只使用只读查询能力，例如：

```bash
python3 ~/.codex/skills/yichen-wechat-local-vault/scripts/vault_cli.py status --format json
python3 ~/.codex/skills/yichen-wechat-local-vault/scripts/vault_cli.py history "天沐锦江老板群" --start-time "2026-04-01" --end-time "2026-08-19" --format json
```

项目内封装脚本提供 agent 友好的命令：

```bash
python3 wechat-agent-tool/wechat_agent_cli.py status
python3 wechat-agent-tool/wechat_agent_cli.py messages --chat "天沐锦江老板群" --start "2026-04-01" --end "2026-08-19" --limit 1000
```

桌面端点击“导入数据”时，会先触发微信本地保险箱的日常增量刷新，再读取群聊数据：

```bash
python3 ~/.codex/skills/yichen-wechat-local-vault/scripts/decrypt_all_dbs.py --mode incremental
```

这样导入时会尽量拿到最新微信数据，而不是只读取上一次已经解密好的缓存。如果增量刷新失败，导入会直接提示失败原因，避免静默使用旧数据造成误判。

如果选择了时间范围，Electron 会按 `offset` 分页读取，避免只拿到最近 1000 条：

```text
offset=0, limit=1000
offset=1000, limit=1000
offset=2000, limit=1000
...
```

读取后会按时间戳升序排序，再计算导入后的时间范围。

### 数据处理流程

导入流程：

```text
用户点击导入数据
-> src/App.tsx
-> window.shouwang.importWechatAgentChat
-> electron/preload.cjs
-> electron/main.ts: wechat:importAgentChat
-> yichen-wechat-local-vault/scripts/decrypt_all_dbs.py --mode incremental
-> electron/wechatAgentTool.ts
-> wechat-agent-tool/wechat_agent_cli.py
-> yichen-wechat-local-vault/scripts/vault_cli.py
-> decrypted/current 中的 SQLite 明文 vault
```

分析流程：

```text
WechatMessage[]
-> analyzeWechatMessages
-> WechatAnalysis
-> 本地保存到 /Users/edy/Library/Application Support/shouwang/wechat-groups/{群名}.json
-> 问答时把统计摘要 + 最近聊天记录组装成模型 input
-> Responses API
```

`WechatAnalysis` 包含：

- 总消息数
- 成员数
- 时间范围
- 发言排行
- 关键词
- 活跃时间
- 代表消息
- 最近消息上下文

### 网页预览和桌面端区别

网页预览 `http://127.0.0.1:5173/` 不能直接调用本机 Python CLI，也不能读本机 vault。因此网页预览只支持导入用户选择的文本文件：

```text
md / txt / json / csv
```

Electron 桌面端可以通过 preload 暴露的 IPC 调用本机脚本，因此支持：

- 按群名读取本机 vault
- 导入前自动执行 vault 增量刷新
- 按时间范围分页导入
- 本地保存导入结果
- 调用模型做问答

### 安全边界

当前实现遵循这些边界：

- App 不直接抓取微信 key
- App 不直接解密微信原始数据库
- App 不扫描微信缓存目录
- App 导入前通过微信本地保险箱 skill 刷新本机 vault，然后读取已解密 vault
- 聊天原文默认只在本机处理和保存
- 回答里只做基于聊天文本的行为观察，不做人格、健康、家庭、身份属性推断

如果增量刷新提示 key、权限或数据库状态异常，需要先在微信本地保险箱 skill 的流程里处理全量解密或 key 复用，再回到本项目导入分析。

## 重要文件

```text
src/App.tsx                         主界面和微信分析页面
src/styles.css                      页面样式
src/main.tsx                        浏览器预览 mock
electron/main.ts                    Electron 主进程和 IPC
electron/preload.ts                 preload 类型版
electron/preload.cjs                实际注入 preload
electron/wechatAgentTool.ts         调用项目内 wechat-agent-tool
electron/wechatAnalysis.ts          聊天记录解析和本地统计
shared/defaultSettings.ts           默认模型配置
shared/wechatModelClient.ts         Responses API 模型客户端
wechat-agent-tool/wechat_agent_cli.py  项目内只读微信 vault CLI
test/*.mjs                          回归测试
```

## 后续方向

- 装修智能体：上传户型图，写需求，生成 3D 效果图
- 群聊日报：基于时间范围生成群聊摘要
- 群成员画像：按群友聚合发言、关键词和跟进事项
- 导出报告：把模型问答结果保存为 Markdown
