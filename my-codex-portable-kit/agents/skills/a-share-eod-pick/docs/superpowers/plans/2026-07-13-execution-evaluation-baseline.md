# Execution Evaluation Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make historical backtests, live-paper validation, and optimizer acceptance use one auditable, net-of-cost execution contract.

**Architecture:** A new pure `execution_model` module will turn T/T+1 rows and configured assumptions into either a filled trade or an explicit skip. The backtest and validator will persist this shared outcome; feedback, reports, and the optimizer will consume its net-return fields and time-split summaries.

**Tech Stack:** Python 3.13, pandas, JSON persistence, unittest, SQLite K-line cache.

---

## File Structure

- Create: `scripts/execution_model.py` - fill eligibility, prices, slippage, costs, normalized outcome.
- Create: `tests/test_execution_model.py` - execution contract unit tests.
- Modify: `config/strategy_params.json` - execution-cost and validation-gate settings.
- Modify: `scripts/backtest_runner.py` - persist normalized outcomes for historical candidate pools and selections.
- Modify: `scripts/validator.py` - reuse the normalized outcome for live-paper validation.
- Modify: `scripts/feedback_loop.py` - calculate layered net-return, coverage, skips, and drawdown metrics.
- Modify: `scripts/optimizer.py` - require net out-of-sample non-regression before updating the strategy.
- Modify: `scripts/report_generator.py` - disclose execution assumptions and segmented net metrics.
- Modify: `tests/test_training_split.py`, `tests/test_feedback_loop.py`, `tests/test_optimizer_candidate_pool.py`, `tests/test_report_history_regret.py` - integration coverage.

### Task 1: Add The Pure Execution Contract

**Files:**
- Create: `tests/test_execution_model.py`
- Create: `scripts/execution_model.py`

- [ ] **Step 1: Write failing tests for filled and skipped outcomes**

```python
def test_trade_applies_adverse_slippage_and_costs():
    outcome = evaluate_overnight_trade(valid_t(), valid_t1(), cost_model())
    assert outcome["execution_status"] == "filled"
    assert outcome["gross_return"] > outcome["net_return"]
    assert outcome["return"] == outcome["net_return"]

def test_trade_skips_invalid_exit_row():
    assert evaluate_overnight_trade(valid_t(), {"open": 0}, {}) == {
        "execution_status": "skipped", "skip_reason": "invalid_t1_row"
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_execution_model -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'execution_model'`.

- [ ] **Step 3: Implement `scripts/execution_model.py`**

```python
def evaluate_overnight_trade(t_row, t1_row, model, *, entry_price=None, entry_source="T_close"):
    if not is_valid_bar(t_row):
        return skipped("invalid_t_row")
    if not is_valid_bar(t1_row):
        return skipped("invalid_t1_row")
    if is_unfillable_entry(t_row, model):
        return skipped("entry_unfillable_limit")
    if is_unfillable_exit(t1_row, model):
        return skipped("exit_unfillable_limit")
    buy = float(entry_price or t_row["close"]) * (1 + bps(model, "entry_slippage_bps") / 10000)
    sell = float(t1_row["open"]) * (1 - bps(model, "exit_slippage_bps") / 10000)
    gross = sell / buy - 1
    cost = 2 * rate(model, "commission_rate") + rate(model, "stamp_duty_rate")
    return filled(buy, sell, gross, gross - cost, entry_source)
```

Return raw and adjusted prices, source fields, `gross_return`, `net_return`, `return=net_return`, `win`, `execution_status`, and `skip_reason`. The module must not import loaders or write files.

- [ ] **Step 4: Run the unit tests**

Run: `python -m unittest tests.test_execution_model -v`

Expected: PASS.

- [ ] **Step 5: Commit the isolated component**

Run: `git add scripts/execution_model.py tests/test_execution_model.py && git commit -m "feat: add auditable overnight execution model"`

### Task 2: Configure Costs And Preserve Historical Compatibility

**Files:**
- Modify: `config/strategy_params.json`
- Modify: `scripts/execution_model.py`
- Modify: `tests/test_execution_model.py`

- [ ] **Step 1: Write a failing normalization test**

```python
def test_normalize_execution_model_defaults_to_zero_costs():
    assert normalize_execution_model({}) == {
        "entry_slippage_bps": 0, "exit_slippage_bps": 0,
        "commission_rate": 0, "stamp_duty_rate": 0,
        "require_valid_ohlcv": True, "skip_limit_entry": True, "skip_limit_exit": True,
    }
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_execution_model.ExecutionModelTests.test_normalize_execution_model_defaults_to_zero_costs -v`

Expected: FAIL with `NameError`.

- [ ] **Step 3: Add production settings and defaults**

Add this `execution_costs` object to `config/strategy_params.json`:

```json
{"entry_slippage_bps":5,"exit_slippage_bps":5,"commission_rate":0.0003,"stamp_duty_rate":0.0005,"require_valid_ohlcv":true,"skip_limit_entry":true,"skip_limit_exit":true}
```

Implement `normalize_execution_model` by merging supplied settings over the zero-cost defaults. This keeps legacy fixtures deterministic while new runs use explicit assumptions.

- [ ] **Step 4: Run the execution tests**

Run: `python -m unittest tests.test_execution_model -v`

Expected: PASS.

- [ ] **Step 5: Commit the contract configuration**

Run: `git add config/strategy_params.json scripts/execution_model.py tests/test_execution_model.py && git commit -m "feat: configure paper execution costs"`

### Task 3: Use The Contract In Historical Backtests

**Files:**
- Modify: `scripts/backtest_runner.py`
- Modify: `tests/test_training_split.py`

- [ ] **Step 1: Write a failing selected-but-skipped test**

```python
def test_build_daily_sample_keeps_selected_signal_when_execution_is_skipped():
    sample = build_daily_sample("2026-01-05", "2026-01-06", [eligible_stock()], config_with_costs(), candidate_validations={"000001": {"execution_status": "skipped", "skip_reason": "exit_unfillable_limit"}})
    assert sample["selected"] is True
    assert sample["execution_status"] == "skipped"
    assert sample["return"] is None
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_training_split.TrainingSplitTests.test_build_daily_sample_keeps_selected_signal_when_execution_is_skipped -v`

Expected: FAIL because skipped validation is currently converted to an empty day.

- [ ] **Step 3: Implement the integration**

Keep `validate_close_to_next_open` minute-price selection, but pass the chosen entry price and T/T+1 rows to `evaluate_overnight_trade`. Copy all execution fields into candidate pools and samples. Preserve `selected=True` when a valid strategy choice cannot fill; only selection-rule failures are strategy empty days. In `recompute_performance_full`, calculate returns only from `execution_status="filled"` and emit `selected_days`, `executable_trades`, `skipped_executions`, and `execution_coverage`.

- [ ] **Step 4: Run the focused tests**

Run: `python -m unittest tests.test_training_split tests.test_execution_model -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add scripts/backtest_runner.py tests/test_training_split.py && git commit -m "feat: persist backtest execution outcomes"`

### Task 4: Use The Contract In Live-Paper Validation

**Files:**
- Modify: `scripts/validator.py`
- Modify: `tests/test_training_split.py`

- [ ] **Step 1: Write a failing live-parity test**

```python
def test_live_validation_persists_net_execution_fields():
    trade = validator.validate_close_to_next_open("000001", "测试", "2026-01-05", pending_snapshot())
    assert trade["execution_status"] == "filled"
    assert trade["net_return"] == trade["return"]
    assert trade["gross_return"] > trade["net_return"]
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_training_split.TrainingSplitTests.test_live_validation_persists_net_execution_fields -v`

Expected: FAIL because live validation calculates a separate return.

- [ ] **Step 3: Implement live reuse and persistence**

Load `execution_costs`, call `evaluate_overnight_trade`, and merge it with the pending snapshot metadata. Extend `_save_live_samples` to preserve `execution_status`, `skip_reason`, gross/net returns, adjusted prices, and cost fields. A skipped trade must never be stored as a zero-return fill.

- [ ] **Step 4: Run parity tests**

Run: `python -m unittest tests.test_training_split tests.test_execution_model -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add scripts/validator.py tests/test_training_split.py && git commit -m "feat: unify live paper execution accounting"`

### Task 5: Calculate Layered Net Metrics

**Files:**
- Modify: `scripts/feedback_loop.py`
- Modify: `tests/test_feedback_loop.py`

- [ ] **Step 1: Write a failing metric-separation test**

```python
def test_metrics_separate_empty_days_from_skips_and_use_net_return(self):
    layer = self.feedback_loop.compute_sample_metrics([
        {"sample_type":"historical_training","selected":True,"execution_status":"filled","net_return":0.01},
        {"sample_type":"historical_training","selected":True,"execution_status":"skipped"},
        {"sample_type":"historical_training","selected":False,"empty_reason":"score_below_threshold"},
    ])["historical_training"]
    assert (layer["selected_days"], layer["executable_trades"], layer["skipped_executions"], layer["empty_days"]) == (2, 1, 1, 1)
    assert layer["net_avg_return"] == 0.01
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_feedback_loop.FeedbackLoopTests.test_metrics_separate_empty_days_from_skips_and_use_net_return -v`

Expected: FAIL because only `trade_samples` and `empty_days` exist.

- [ ] **Step 3: Implement additive layered metrics**

Treat legacy numeric `return` records without an execution status as filled but count them as `legacy_filled_trades`. For each existing layer, calculate selected days, executable trades, skipped executions, empty days, coverage, gross/net mean and cumulative return, profit/loss ratio, maximum drawdown, and maximum consecutive loss from filled net returns.

- [ ] **Step 4: Run feedback tests**

Run: `python -m unittest tests.test_feedback_loop -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add scripts/feedback_loop.py tests/test_feedback_loop.py && git commit -m "feat: report execution coverage and net metrics"`

### Task 6: Require Net Out-Of-Sample Improvement

**Files:**
- Modify: `scripts/optimizer.py`
- Modify: `tests/test_optimizer_candidate_pool.py`

- [ ] **Step 1: Write a failing validation-gate test**

```python
def test_walk_forward_rejects_lower_net_validation_return():
    accepted, reason = optimizer.evaluate_walk_forward_candidate(
        {"net_avg_return": .01, "max_drawdown": .02, "execution_coverage": .8, "trade_samples": 10},
        {"net_avg_return": .005, "max_drawdown": .01, "execution_coverage": .8, "trade_samples": 10},
        {"net_avg_return": .01, "max_drawdown": .02, "execution_coverage": .8, "trade_samples": 10},
        {"net_avg_return": .005, "max_drawdown": .01, "execution_coverage": .8, "trade_samples": 10}, min_validation_trades=5)
    assert not accepted
    assert "净平均收益" in reason
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_optimizer_candidate_pool.OptimizerCandidatePoolTests.test_walk_forward_rejects_lower_net_validation_return -v`

Expected: FAIL because acceptance does not require net-return non-regression.

- [ ] **Step 3: Implement strict chronological gates**

Extend `backtest_candidate_pool` to exclude skipped trades from executable performance but retain selected/skipped counts. Add `net_avg_return`, `net_total_return`, `max_drawdown`, and `execution_coverage`. Keep `split_walk_forward_samples` chronological. Reject a new candidate when validation trades are insufficient, net average return declines, drawdown/consecutive loss breach tolerance, or coverage leaves its configured range. Persist both train and validation net summaries in version history.

- [ ] **Step 4: Run optimizer tests**

Run: `python -m unittest tests.test_optimizer_candidate_pool -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add scripts/optimizer.py tests/test_optimizer_candidate_pool.py && git commit -m "feat: gate optimizer on net walk-forward metrics"`

### Task 7: Report Assumptions And Run Verification

**Files:**
- Modify: `scripts/report_generator.py`
- Modify: `tests/test_report_history_regret.py`
- Modify: `SKILL.md`

- [ ] **Step 1: Write a failing report test**

```python
def test_html_report_discloses_execution_costs_and_net_metrics(self):
    html = self.report_generator.render_html_report(payload_with_execution_metrics())
    assert "执行覆盖率" in html
    assert "净平均收益" in html
    assert "单边滑点" in html
```

- [ ] **Step 2: Verify it fails**

Run: `python -m unittest tests.test_report_history_regret.ReportHistoryRegretTests.test_html_report_discloses_execution_costs_and_net_metrics -v`

Expected: FAIL because the report omits execution configuration and net metrics.

- [ ] **Step 3: Add Markdown/HTML disclosures**

Render entry/exit slippage, commission, stamp duty, buy/exit convention, and each layer's selected days, executable trades, skips, empty days, coverage, gross/net returns, drawdown, and consecutive losses. Mark records without execution metadata as legacy. Update `SKILL.md` so training and validation explicitly state net-of-cost and skipped-execution treatment.

- [ ] **Step 4: Run all tests**

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`

Expected: PASS.

- [ ] **Step 5: Run a bounded integration backtest**

Run: `python scripts/backtest_runner.py --days 10 --universe 20`

Expected: exits successfully; newly generated samples contain `execution_status`, `gross_return`, and `net_return`; performance and report artifacts show coverage and net metrics.

- [ ] **Step 6: Commit**

Run: `git add scripts/report_generator.py tests/test_report_history_regret.py SKILL.md && git commit -m "docs: disclose execution evaluation assumptions"`

## Plan Self-Review

- Tasks 1-4 cover one T/T+1 execution contract, costs, sources, skips, historical and live persistence.
- Task 5 provides the required training/live/combined net metrics, coverage, skips, drawdown, and legacy compatibility.
- Task 6 makes temporal out-of-sample net results the sole optimizer acceptance baseline.
- Task 7 supplies user-visible auditability and unit plus bounded integration verification.
- Factor definitions, thresholds, stock universe, and real trading remain out of scope.
