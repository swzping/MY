---
name: "a-share-eod-pick"
description: "A股主板尾盘隔夜纸面交易策略：执行选股时只做当日 Top1/空仓报告；执行训练时独立拉取并缓存历史数据，按 T 日收盘买入、T+1 开盘卖出累积样本并反馈验证策略。Invoke when user asks for 尾盘选股/隔夜策略/历史训练/次日验证/策略优化/胜率复盘，或运行 run_today_report / train_history / validate_yesterday / optimize_weekly 命令。"
---

# A股尾盘隔夜纸面交易策略

## 1. 策略定位

- **交易时段**：按用户请求时间执行当日选股；历史训练按 T 日收盘信号 → T+1 日开盘验证
- **交易品种**：沪深主板（600/601/603/605/000/001/002），剔除 ST/*ST/退市/停牌/涨停/跌停
- **持仓周期**：纸面单次，T 日收盘价买入 → T+1 日开盘价卖出
- **目标**：初始胜率 ≥ 55%，盈亏比 ≥ 1:1.5，最大连续亏损 ≤ 3 次

## 2. 工作目录约定

所有脚本均相对于技能根目录运行：

```
.trae/skills/a-share-eod-pick/
├── SKILL.md                      # 本文件
├── config/
│   └── strategy_params.json      # 可调参数（优化器会覆写此文件）
├── scripts/
│   ├── data_loader.py            # 数据采集（mootdx + 腾讯 + 东财）
│   ├── strategy_engine.py        # 多因子打分与排序
│   ├── report_generator.py      # 日报生成
│   ├── validator.py             # 次日开盘验证
│   └── optimizer.py             # 周度参数优化
├── data/
│   ├── trades.json              # 历史交易明细（最近10+笔）
│   ├── performance.json         # 胜率统计（7d/30d/total）
│   └── strategy_version.json    # 策略版本与变更日志
└── reports/
    └── YYYY-MM-DD.md            # 每日策略报告
```

## 3. 执行入口（命令）

| 命令 | 触发时机 | 动作 |
|------|----------|------|
| `run_today_report` | 用户请求时 | 先轻量同步昨日行为 → 当日快速 Top1/空仓选股 → 覆盖输出当日报告 `reports/YYYY-MM-DD.md` |
| `train_history` | 用户明确训练时 | 从已缓存/已样本最早交易日继续向前扩展历史 → 写入统一样本池 `data/strategy_samples.json` |
| `validate_yesterday` | T+1 日开盘后 | 验证昨日推荐 → 写入 live_paper 样本 + trades/performance |
| `optimize_weekly` | 每周五收盘后或周日 | 基于近 30 笔排序损失分析 → 调整 strategy_params.json → 追加 version 日志 |
| `show_status` | 任意 | 打印当前胜率、版本、最近交易、参数快照 |

收到上述任一命令或同义中文意图（如"跑一下今天选股"、"复盘昨天"、"优化一下参数"、"看看策略状态"）时，必须按下列流程执行。

## 4. 多因子选股模型

### 4.1 因子定义与默认权重

详见 `config/strategy_params.json`。七因子结构：

| 因子 | 默认权重 | 计算口径 | 评分区间 |
|------|----------|----------|----------|
| F1 尾盘资金净流入 | 0.20 | 14:30-15:00 主力净额 / 流通市值 | 0-100 |
| F2 量价协同 | 0.15 | 尾盘量比 / 涨跌幅一致性 | 0-100 |
| F3 技术形态 | 0.20 | MACD 金叉/零轴 + RSI(14)∈[40,60] + 价>MA5&MA10 | 0-100 |
| F4 尾盘拉升强度 | 0.15 | (15:00价-14:30价)/14:30价 × 尾盘成交占比 | 0-100 |
| F5 板块热度 | 0.10 | 所属行业当日涨幅排名 + 龙头股联动 | 0-100 |
| F6 消息面催化 | 0.10 | 当日利好公告/政策/研报评级上调 | 0-100（无=50） |
| F7 流通市值适配 | 0.10 | ln(流通市值) 越接近中位偏好区得分越高 | 0-100 |

综合得分 `Score = Σ(wi × Fi)`，归一化到 [0,100]。

### 4.2 预过滤条件（硬约束）

全部满足方可入池，否则直接剔除：

1. 交易日实时可交易（非停牌/一字涨跌停）
2. 收盘价 ∈ [3, 100] 元
3. 当日成交额 ≥ 5000 万元
4. 流通市值 ∈ [5亿, 50亿]
5. 上市满 60 个交易日
6. 非 ST/*ST/退市整理期
7. 最近 20 日无重大违规公告

### 4.3 排序与选取

1. 预过滤后剩余股票按 `Score` 降序
2. 同分按 F1（资金流入）> F4（拉升强度）> F7（市值适配）二级排序
3. 单一行业最多入选 1 只，避免集中风险
4. 只取 Top 1 写入报告（得分需 ≥ 60 分阈值，否则当日空仓）

## 5. 数据处理流程

### 5.1 数据源优先级

| 用途 | 首选 | 备选 | 降级 |
|------|------|------|------|
| 实时行情/分钟K | mootdx TdxQuota | 腾讯 qt.gtimg.cn | 新浪 hq.sinajs.cn |
| 日K/复权 | mootdx TdxK_data | 腾讯 K线 | 百度 finance |
| 资金流向 | 东财 push2 fund flow | 同花顺 | mootdx 推算 |
| F10/财务 | mootdx TdxFin | 东财 datacenter | - |
| 公告/研报 | 巨潮 cninfo | 东财研报 | iwencai |
| 行业/板块 | 东财板块 | 同花顺热点 | - |

### 5.2 run_today_report 流程（T 日 14:30-15:00 执行）

```
1. 轻量同步最近一个可验证交易日：
   - 有昨日推荐：使用昨日实际执行选股时保存的 Top1 快照与执行时间，只拉推荐标的必要 T/T+1 日K，按 T 收盘 → T+1 开盘验证
   - 昨日空仓：写入 live_paper 空仓样本，并保留当日选股执行时间/空仓原因
   - 已同步则跳过；数据不足则记录原因但继续今日选股
2. 获取当日主板股票清单（剔除 ST/停牌/涨跌停）
3. 并行拉取：实时行情 + 尾盘分钟数据 + 资金流向 + 行业涨幅
4. 预过滤（4.2 节硬约束）
5. 逐只计算 F1-F7 因子分（scripts/strategy_engine.py）
6. 加权汇总 → 排序 → 行业去重 → 取 Top 1
7. 渲染报告模板 → 写入 reports/YYYY-MM-DD.md
8. 保存今日待明日验证的 Top1 或空仓
9. 不触发历史训练或参数优化，保证选股任务不被重任务拖慢

### 5.2.1 train_history 流程（用户明确执行训练时）

```
1. 构建历史训练股票池
2. 读取 SQLite 日K缓存，从已缓存/已样本的最早交易日继续向前补充缺口
3. 每个历史交易日仅使用当日及以前数据计算策略得分
4. 每日严格生成 1 条样本：
   - 有达标股票：记录 Top1
   - 无达标股票：记录空仓
5. 验证口径：T 日收盘价买入 → T+1 日开盘价卖出
6. 写入 data/strategy_samples.json，sample_type=historical_training；历史训练没有真实执行时间，只记录训练复原出的当日策略行为
7. 更新 performance、backtest_meta，并采集反馈指标快照
```
```

### 5.3 validate_yesterday 流程（T+1 日开盘后执行）

```
1. 读取 data/pending_recommendations.json 取出最近一个可验证交易日的实际选股快照
2. 按 T 日收盘 → T+1 日开盘口径记录实际执行样本，sample_type=live_paper，并保留 selected_at/score/factor_scores
3. 追加到 data/trades.json，并同步写入 data/strategy_samples.json
4. 重算 data/performance.json（7d/30d/total 胜率 + 盈亏比 + 最大连亏）
5. 若触发最大连亏≥3 或 7 日胜率<50%，在当日唯一报告中打"策略告警"标记
```

### 5.4 optimize_weekly 流程（每周五收盘后）

```
1. 读取 data/trades.json 最近 30 笔已验证交易
2. 排序损失分析（pairwise）：
   - 对每笔交易，记录其 T 日的 F1-F7 各因子分与最终收益率
   - 计算各因子分与收益率的 Spearman 秩相关系数 ρ_i
   - 损失 = 理想排序(按收益率) 与 实际排序(按 Score) 的 Kendall τ 距离
3. 参数调整规则：
   - ρ_i 排名前 2 的因子权重 +0.03
   - ρ_i 排名后 2 的因子权重 -0.03
   - 权重总和归一化
   - 单次调整幅度上限 ±0.05，避免剧烈震荡
4. 写回 config/strategy_params.json
5. 追加 data/strategy_version.json（版本号 +1，记录调整原因 + ρ_i 表）
6. 输出优化摘要
```

## 6. 报告模板

`reports/YYYY-MM-DD.md` 必须包含以下章节（见 report_generator.py 的 render 函数）：

```markdown
# A股尾盘隔夜策略报告 - YYYY-MM-DD

## 一、当日市场概览
- 上证/深证/创业板涨跌幅
- 涨停/跌停家数
- 主力净流入 TOP3 行业

## 二、策略历史胜率
| 周期 | 胜率 | 盈亏比 | 最大连亏 | 样本数 |
|------|------|--------|----------|--------|
| 近7日 | xx% | 1:x | n | n |
| 近30日 | xx% | 1:x | n | n |
| 总计 | xx% | 1:x | n | n |

当前策略版本：vX.Y  | 下次优化日：YYYY-MM-DD

## 三、当日唯一推荐（T 收盘 → T+1 开盘验证）
### 推荐1：股票代码 股票名称
- 综合得分：xx/100
- 推荐理由（必须列出 3 条以上具体依据）：
  1. F1 资金：尾盘主力净流入 xx 万元
  2. F3 技术：MACD 金叉，RSI=xx
  3. F4 拉升：尾盘 30 分钟涨幅 xx%
  ...
- 风险提示：xxx

> 无满足阈值推荐时，必须写明空仓及原因。

## 四、昨日推荐验证结果
| 代码 | 名称 | 买入价 | 卖出价 | 收益率 | 胜负 |
|------|------|--------|--------|--------|------|
| xxx | xxx | xx | xx | xx% | ✅/❌ |

昨日策略命中：x/x

## 五、完整历史训练记录
| 日期 | 行为 | 代码 | 名称 | 买入价 | 卖出价 | 收益率 | 结果/原因 |
|------|------|------|------|--------|--------|--------|-----------|
| ... | 出手/空仓 | ... | ... | ... | ... | ... | 胜/负/空仓原因 |

## 六、策略告警（如有）
- 若最大连亏≥3 或 7日胜率<50% 或 30日胜率<55%，输出红色告警
```

## 7. 性能指标与风控

| 指标 | 目标 | 触发动作 |
|------|------|----------|
| 总胜率 | ≥ 55% | <55% 且样本≥20 → 触发 optimize_weekly |
| 盈亏比 | ≥ 1:1.5 | <1.2 → 下调 F4 权重（降低追涨敞口） |
| 最大连亏 | ≤ 3 | =3 → 次日空仓观察 1 天 |
| 7日胜率 | ≥ 50% | <50% → 报告打告警标记 |
| 30日胜率 | ≥ 55% | <55% → 强制 optimize_weekly |

## 8. 策略迭代与版本管理

- `data/strategy_version.json` 记录每次参数变更：
  - version（语义化，如 v1.3）
  - change_date
  - reason（如"周度排序损失优化"）
  - factor_rho（各因子 ρ_i 快照）
  - weights_before / weights_after
- 优化器只调整权重，不增删因子，保证可回溯
- 每次优化后回测最近 30 笔验证是否改善，恶化则回滚版本

## 9. 执行约束

1. **每日仅一份报告**：`reports/YYYY-MM-DD.md` 唯一，重跑覆盖
2. **数据时效**：必须用当日实时数据，禁止用缓存日K冒充
3. **完成时限**：选股 30 分钟内、验证 15 分钟内
4. **纸面交易**：不涉及真实下单，仅记录价格与收益率
5. **失败降级**：东财封禁 → 切腾讯 → 切新浪，记录降级路径
6. **空仓机制**：无股票得分≥阈值或市场大跌（上证<-2%）→ 当日空仓，报告注明

## 10. 依赖与安装

```bash
pip install mootdx akshare pandas numpy scipy requests
```

首次执行前确认 mootdx 可连通：
```python
from mootdx.quotes import Quotes
client = Quotes.factory(market='std')
client.index(frequency=9, market=0, start=0, offset=10)
```

## 11. 快速验证（首次部署）

1. 运行 `show_status` 应返回空 trades 与 v1.0 版本
2. 运行 `run_today_report` 生成首份报告
3. 次日运行 `validate_yesterday` 写入首笔交易
4. 累计 ≥20 笔后运行 `optimize_weekly` 验证优化闭环

## 12. 反馈闭环机制

针对策略重大调整（数据源替换、因子口径变更、预过滤范围调整、风控阈值修改等），建立系统性的逆向反馈流程，确保调整可追踪、可衡量、可回滚。

### 12.1 五步流程

| 步骤 | 命令 | 触发时机 |
|------|------|---------|
| ① 调整记录 | `record_adjustment` | 调整实施当日 |
| ② 指标采集 | `collect_metrics` | Baseline 自动采集；后续按需 |
| ③ 影响分析 | `analyze_feedback` | 调整后 7 个交易日 |
| ④ 优化方案 | `plan_optimization` → `implement_action` | 识别问题后 24h 内（P0） |
| ⑤ 闭环验证 | `verify_action` → `close_loop` | 调整后 30 个交易日 |

数据存储：`data/feedback/{adjustments,metrics_snapshots,feedback_actions}.json`
实现：`scripts/feedback_loop.py`

### 12.2 时效性标准

| 阶段 | 时效要求 | 触发动作 |
|------|---------|---------|
| 调整记录 | 调整实施当日 | `record_adjustment` |
| Baseline 采集 | 调整记录后 1 个交易日内 | 自动（record_adjustment 内置） |
| 首次反馈分析 | 调整后 7 个交易日 | `analyze_feedback` |
| 闭环验证 | 调整后 `expected_horizon_days`（默认 30） | `close_loop` |
| 异常告警响应 | 发现即触发，24h 内响应 | `plan_optimization priority=P0` |

### 12.3 质量评估指标

| 指标 | 计算口径 | 目标 |
|------|---------|------|
| 数据完整度 | 必填字段填写率 | ≥ 95% |
| 时效达成率 | 按时完成阶段数 / 应完成阶段数 | ≥ 90% |
| 反馈转化率 | (verified + implemented) / 总 findings | ≥ 70% |
| 闭环完成率 | closed / opened（按月） | ≥ 80% |
| 优化有效率 | verified 为改善 / closed | ≥ 60% |

`feedback_status` 命令末尾输出本月质量仪表板。

### 12.4 影响分析触发规则

| 触发条件 | feedback_type | priority |
|---------|--------------|----------|
| 30 日胜率 Δ ≤ -5% | negative | P0 |
| 30 日胜率 Δ ≥ +5% | positive | P2 |
| 排序损失 Δ ≥ +0.10 | negative | P1 |
| 排序损失 Δ ≤ -0.10 | positive | P2 |
| 数据源从 ok → blocked（tencent/mootdx） | negative | P0 |
| 数据源从 ok → blocked（其他） | negative | P1 |
| 数据源从 blocked → ok | positive | P2 |
| 触发风控告警阈值（7d/30d 胜率低于阈值） | negative | P0 |

### 12.5 闭环关闭条件

`close_loop` 要求该 adjustment 关联的所有 action 状态 ∈ `{verified, rejected}`，否则拒绝关闭并返回 pending_ids。

### 12.6 跨项目复用

本技能的反馈闭环机制已抽取为**独立全局技能 `feedback-loop`**（`~/.agents/skills/feedback-loop/`）。其他策略技能（a-stock-data、stock-analyst 等）若需建立反馈闭环：

```bash
# 复制脚本与空模板到目标项目
cp ~/.agents/skills/feedback-loop/scripts/feedback_loop.py <目标项目>/scripts/
mkdir -p <目标项目>/data/feedback
cp ~/.agents/skills/feedback-loop/data/feedback/*.json <目标项目>/data/feedback/
```

详见 [feedback-loop SKILL.md](file:///Users/edy/.agents/skills/feedback-loop/SKILL.md)。

---

**设计原则**：因子可解释、参数可回溯、告警可观测、降级可兜底。任何执行步骤失败须在报告中显式记录失败原因与降级路径，禁止静默吞错。
