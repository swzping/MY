---
name: a-share-tail-close-overnight
description: 用于运行、安装、迁移、验证或优化独立 A 股主板尾盘隔夜纸面交易策略工作区，包括每日推荐、次日复盘、滚动报告、排序损失分析和策略规则迭代。
---

# A 股尾盘隔夜策略

## 概览

本技能用于管理一个独立的 A 股主板尾盘隔夜纸面交易策略工作区。技能包内置可复用脚手架，位于 `assets/scaffold/`；不要依赖本机已有的旧项目路径。

本策略仅用于纸面交易观察。绝不进行真实下单，也不要暗示收益保证。

## 初始化或定位工作区

工作区选择必须严格：

- 如果用户指定了目录，或当前就在一个新目录中，使用该目录。
- 不要因为旧工作区已有数据或脚本，就切换到旧工作区。
- 所有初始化、执行、报告生成、测试和脚本修复，都必须发生在选定工作区内。

如果选定工作区为空，或缺少策略文件，用技能包内置脚手架初始化或修复：

```bash
python3 ~/.agents/skills/a-share-tail-close-overnight/scripts/init_tail_strategy.py /path/to/stock-workspace
cd /path/to/stock-workspace
python3 -m venv .venv
.venv/bin/pip install requests pytest
```

初始化至少必须创建一个报告文件：

- `reports/strategy_01/daily_run_YYYY-MM-DD.md`

工作区应包含：

- `scripts/run_strategy_01.py`
- `scripts/report_strategy_01_tail_entry.py`
- `scripts/review_strategy_01_next_open.py`
- `scripts/_archive/` 中可保留回测、排序比较、最佳画像和收盘位置研究脚本。
- `strategies/01_tail_close_overnight.md`
- `tests/`

如果这些文件缺失，先从 `assets/scaffold/` 初始化或修复同一个工作区，再运行报告。

日常目录必须保持清爽：

- 人看的每日总报告只放在 `reports/strategy_01/daily_run_YYYY-MM-DD.md`。
- 候选 CSV、候选明细报告、纸面台账、次日复盘明细、滚动复盘明细统一放在 `reports/strategy_01/_data/`。
- 回测、排序比较、最佳画像、收盘位置研究等研究产物统一放在 `reports/strategy_01/_archive/`。
- 不要把 `*_candidates.csv`、`*_report.md`、`*_next_open_review.*`、`paper_trades.csv`、`tail_entry/` 直接留在 `reports/strategy_01/` 根目录。

## 每日流程

命令必须在策略工作区中运行，不要在技能目录中运行。

如果用户说“执行策略”“执行今日优选”“今日优选”“筛选今日尾盘股”或类似表达，只做当日尾盘候选筛选：拉取能取得的实时/当日行情数据，按策略筛出今日推荐股最多 3 只，并按“可买入评分”排序；不生成滚动收益报告、不执行次日复盘、不拉取历史每日交易数据。使用：

```bash
python3 ~/.agents/skills/a-share-tail-close-overnight/scripts/run_daily_tail_strategy.py . --date YYYY-MM-DD --mode pick
```

该命令会补齐缺失脚手架文件，在 `.` 内执行。日常只需要打开一份总报告：

- `reports/strategy_01/daily_run_YYYY-MM-DD.md`

内部机器数据写入：

- `reports/strategy_01/_data/YYYY-MM-DD_report.md`
- `reports/strategy_01/_data/YYYY-MM-DD_candidates.csv`
- `reports/strategy_01/_data/paper_trades.csv`

`paper_trades.csv` 中当天默认记录为策略推荐 Top1，来源标为 `策略Top1`。如果用户明确说“指定买入/确认买入/实际纸面买入”某只股票，则用用户指定标的作为当天纸面交易记录，来源标为 `用户指定买入`，并保留该来源用于复盘对比。

只有当用户明确要求“完整执行”“重新获取滚动指标”“生成收益报告”“复盘”时，才运行完整模式：

```bash
python3 ~/.agents/skills/a-share-tail-close-overnight/scripts/run_daily_tail_strategy.py . --date YYYY-MM-DD --mode full
```

完整模式会额外写出：

- `reports/strategy_01/_data/tail_entry/START_to_END.md`

但对用户展示仍只以 `reports/strategy_01/daily_run_YYYY-MM-DD.md` 为准。该总报告必须同时包含今日优选、纸面交易记录、历史交易复盘、胜率/收益等关键指标和策略反馈闭环；不要让用户去打开多个过程文件拼信息。

即使行情数据接口很慢或失败，命令也必须在同一工作区留下状态报告。不要为了获得更完整的旧数据或更漂亮的输出而切换到旧项目。

仅在必要时使用手动命令：

```bash
.venv/bin/python scripts/run_strategy_01.py YYYY-MM-DD
.venv/bin/python scripts/review_strategy_01_next_open.py YYYY-MM-DD
.venv/bin/python scripts/report_strategy_01_tail_entry.py START_DATE END_DATE
```

收益报告里的“每日交易”只允许来自本地纸面持仓台账：

- `reports/strategy_01/_data/paper_trades.csv`
- 旧位置 `reports/strategy_01/paper_trades.csv` 只作为兼容读取；执行后应整理回 `_data/`。
- 记录来源只能是策略当日默认推荐买入的 Top1，或用户明确说明买入/持仓的标的。
- 每个交易日最多一笔纸面交易；用户指定买入优先于默认 Top1。
- 生成收益报告时不要重新拉取每日候选池来构造“每日交易”，避免把事后重算候选误当成真实纸面交易。
- 没有纸面持仓台账的日期，不应出现在“每日交易”表中。
- 历史复盘只利用上一交易日或台账中已有的真实纸面记录验证次日开盘/冲高/收盘表现；不能把当天重新筛出的 Top1  retroactively 写成历史交易。

回答用户时使用中文，并包含：

- 今日最优推荐或空仓原因。
- 尾盘买入价，以及买入时间是精确快照还是 `收盘价近似`。
- 如果只是“今日优选”，只回答今日候选、尾盘买入价、买入时间口径、不可买入过滤和风险；不要附带滚动指标或复盘。
- 如果用户明确要求完整报告，再包含前一交易日验证、滚动指标和策略反馈，但仍只展示每日总报告路径。

## 策略规则

- 股票池：仅限 A 股主板；排除 ST 以及明显退市或财务风险标的。
- 今日入选推荐股最多 3 只，并按“可买入评分”排序；原始评分只代表信号强度。
- 可买入评分必须扣除短期乖离、放量偏大、换手偏高、日内振幅偏高、弱封/炸板、不可买入等风险。
- 每天最多记录一个纸面持仓。
- 默认纸面持仓是今日可买入评分 Top1；用户明确指定买入时覆盖默认持仓，并标注来源。
- 弱市场日期可以记录为空仓；不要强行交易。
- 强封涨停股可以有效但可能不可买入；需要与可执行纸面交易分开记录。
- 弱封板或炸板候选必须打风险标签，并降低优先级，尤其是在弱市场中。
- 如果历史分钟数据无法还原 14:45/14:50/14:55，买入时间标为 `收盘价近似`。
- 真实盘中纸面运行时，保存 14:45、14:50 和 14:55 快照，便于后续报告使用真实尾盘买入时间。

## 持续优化

工作区脚本允许持续演进。当证据显示策略存在弱点时，修改工作区内的脚本和测试；除非基础模板本身需要面向未来机器变更，否则不要改技能脚手架。

每次沟通和每次生成收益报告后，都要把新增信息纳入策略自我进化闭环：

- 读取用户本次目标、约束和偏好，识别是否出现新的风险偏好、空仓规则、报告字段或排序关注点。
- 读取当日推荐、次日复盘、滚动收益报告和排序损失，记录哪些因子改善了胜率，哪些因子造成亏损或错过事后最佳候选。
- 将结论拆成“观察、假设、待测规则、验证结果”，写入当前工作区报告或策略备注，避免只在对话中口头保留。
- 优先优化纸面开盘胜率、平均/中位收益和平均排序损失；任何优化都必须继续声明纸面交易性质，不得暗示收益保证。
- 有多日样本支持时，才修改策略脚本、排序权重或风险过滤；只有单日证据时，标记为观察并安排后续验证。
- 反馈闭环只使用 `paper_trades.csv` 的真实纸面交易样本：区分 `策略Top1` 与 `用户指定买入`，分别观察胜率、收益和风险标签表现。

每次验证都应比较：

- 策略选择标的与事后最佳候选。
- 开盘收益与次日最高收益。
- 排序损失及其可能原因。
- 市场环境，以及当日是否本应空仓。

优先采用多日样本支持的改动。单日结论只能标记为观察，不要当作稳定规律。

## 验证

在声称策略脚本改动完成前，运行：

```bash
.venv/bin/python -m pytest tests
.venv/bin/python -m py_compile scripts/*.py
```

在声称技能包本身有效前，运行：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.agents/skills/a-share-tail-close-overnight
```
