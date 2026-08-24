# Codex Automations Templates

这个目录保存从本机 `~/.codex/automations` 整理出的自动任务参考模板。

这些文件用于迁移思路和任务 prompt，不用于直接覆盖新机器的自动任务运行状态。自动任务通常绑定本机路径、目标线程、运行时间戳和执行环境，直接复制到另一台电脑容易误跑或指向不存在的目录。

## 当前模板

| 模板 | 类型 | 原任务名 | 迁移说明 |
| --- | --- | --- | --- |
| `templates/codex.toml` | cron | 整理新增 Codex 插件和技能 改成每天18:00运行 | 已保留每天 18:00 运行规则；工作区路径替换为 `<CODEX_SUPERPOWERS_WORKSPACE>`。 |
| `templates/9-ai.toml` | cron | AI情报扫描与输入流筛选 | 知识库路径替换为 `<SW_KNOWLEDGE_VAULT>`。 |
| `templates/automation-4.toml` | heartbeat | 每日知识推进确认 | 目标线程替换为 `<replace-with-target-thread-id>`，知识库路径模板化。 |
| `templates/16-30-ai.toml` | cron | 每日9:30 AI自生长知识库更新 | Obsidian vault 路径替换为 `<OBSIDIAN_VAULT>`。 |
| `templates/9-30.toml` | cron | 每日9:30更新今日新闻 | 工作区路径替换为 `<MY_WORKSPACE>`。 |
| `templates/automation-2.toml` | cron | 每日晨报 | 工作区路径替换为 `<MY_WORKSPACE>`。 |
| `templates/automation.toml` | heartbeat | 每小时工作待办提醒 | 目标线程和工作区路径都已模板化。 |
| `templates/automation-3.toml` | heartbeat | 验证尾盘买入收益报告 | 目标线程和股票工作区路径都已模板化。 |
| `templates/15-t-1.toml` | heartbeat | 15分钟T+1股票筛选 | 目标线程已模板化。 |

## 已脱敏/模板化内容

- 所有模板的 `status` 都改为 `PAUSED`。
- 删除了 `created_at` 和 `updated_at`。
- `target_thread_id` 替换为 `<replace-with-target-thread-id>`。
- 本机绝对路径替换为 `<CODEX_SUPERPOWERS_WORKSPACE>`、`<SW_KNOWLEDGE_VAULT>`、`<OBSIDIAN_VAULT>`、`<MY_WORKSPACE>`、`<MY_STOCK_WORKSPACE>` 等占位符。
- 没有复制 `memory.md`、`.run-jitter-salt`、日志、sqlite、history、sessions、token 或 auth 文件。

## 在新机器上使用

建议优先通过 Codex 桌面端的自动化管理功能重新创建或导入任务，再把这些模板里的 prompt、rrule、model、reasoning effort 和工作区设置迁过去。

启用前逐项检查：

- 占位符路径已经替换成新机器真实路径。
- heartbeat 任务已经绑定到正确的新线程。
- cron 任务的 `cwds` 指向存在的工作区。
- `status` 是否仍应保持 `PAUSED`。
- 涉及联网、股票、知识库写入的任务是否有对应权限和依赖。

当前本机 `codex` 自动任务已经配置为：

```toml
rrule = "FREQ=DAILY;BYHOUR=18;BYMINUTE=0;BYSECOND=0"
```
