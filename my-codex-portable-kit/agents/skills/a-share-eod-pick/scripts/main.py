"""
A股尾盘隔夜策略 - 主入口

用法：
    python scripts/main.py run_today_report     # T 日选股并生成报告
    python scripts/main.py train_history        # 历史训练，拉取/复用缓存并累积样本
    python scripts/main.py validate_yesterday   # T+1 日验证昨日推荐
    python scripts/main.py optimize_weekly      # 周度参数优化
    python scripts/main.py optimize_regret_zero # 机会损失/次日最优命中优化
    python scripts/main.py simulate_coverage    # 高出手率模拟，不改正式策略
    python scripts/main.py optimize_balance     # 胜率/出手率平衡优化，更新正式单一策略
    python scripts/main.py show_status          # 查看策略状态
    python scripts/main.py history              # 查看优化历史

反馈闭环命令：
    python scripts/main.py record_adjustment --title "..." --content "..." \\
        --scope f1.py,f2.py --goal "..." --category data_source
    python scripts/main.py collect_metrics --label "..." [--adjustment-id ID]
    python scripts/main.py analyze_feedback --adjustment-id ID
    python scripts/main.py feedback_status [--adjustment-id ID]
    python scripts/main.py plan_optimization --action-id ID --solution "..." --priority P1
    python scripts/main.py implement_action --action-id ID --notes "..."
    python scripts/main.py verify_action --action-id ID --result "..." --improved true
    python scripts/main.py reject_action --action-id ID --reason "..."
    python scripts/main.py close_loop --adjustment-id ID --summary "..."
"""

import sys
import os
import json
import datetime as dt
from pathlib import Path

# 确保可导入同目录模块
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _parse_kv_args(argv):
    """解析 --key value 形式的参数，返回 dict。"""
    result = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                result[key] = argv[i + 1]
                i += 2
            else:
                result[key] = ""
                i += 1
        else:
            i += 1
    return result


def _runtime_overrides(args: dict) -> dict:
    """Parse one-off strategy overrides from CLI args without mutating config."""
    overrides = {}
    if args.get("f2-min") not in (None, ""):
        overrides["F2_volume_price_sync_min"] = float(args["f2-min"])
    if args.get("score-min") not in (None, ""):
        overrides["score_threshold"] = float(args["score-min"])
    if args.get("f8-min") not in (None, ""):
        overrides["F8_overnight_risk_control_min"] = float(args["f8-min"])
    if args.get("f9-min") not in (None, ""):
        overrides["F9_overheat_control_min"] = float(args["f9-min"])
    return overrides


def _strategy_mode(args: dict) -> str:
    mode = str(args.get("mode") or "balanced").strip().lower()
    aliases = {
        "tail": "tail-only",
        "tail_only": "tail-only",
        "tail-only": "tail-only",
        "attack": "attack",
        "balanced": "balanced",
    }
    return aliases.get(mode, "balanced")


def cmd_run_today_report():
    """T 日 14:30-15:00 选股并生成报告。"""
    import strategy_engine
    import report_generator
    import validator

    print("=== 执行尾盘选股 ===")
    args = _parse_kv_args(sys.argv[2:])
    overrides = _runtime_overrides(args)
    try:
        sync = validator.sync_previous_live_paper()
        status = sync.get("status")
        if status == "validated":
            print(f"昨日同步: {sync.get('date')} 已验证 {sync.get('validated', 0)} 笔")
        elif status == "empty":
            print(f"昨日同步: {sync.get('date')} 空仓已记录")
        elif status == "unverifiable":
            print(f"昨日同步: {sync.get('date')} 数据不足以验证，已记录原因")
        elif status == "already_synced":
            print(f"昨日同步: {sync.get('date')} 已同步，跳过")
        elif status == "no_pending":
            print("昨日同步: 无待同步记录")
    except Exception as e:
        print(f"昨日同步警告: {e}")

    mode = _strategy_mode(args)
    result = strategy_engine.run_selection(overrides=overrides or None, mode=mode)

    print(f"日期: {result.get('date')}")
    print(f"候选: {result.get('total_candidates', 0)} / 打分: {result.get('total_scored', 0)}")

    recs = result.get("recommendations", [])
    signals = result.get("opportunity_signals", [])
    if signals:
        top_signal = signals[0]
        print(
            "机会判断: "
            f"{top_signal.get('symbol', '')} {top_signal.get('name', '')} "
            f"{top_signal.get('action_label', top_signal.get('action', ''))} "
            f"机会分={top_signal.get('opportunity_score', 0)} "
            f"下次复核={top_signal.get('next_check_at') or '无需等待'}"
        )
    if recs:
        # 保存待验证推荐
        validator.save_pending_recommendations(recs)
        print(f"推荐 {len(recs)} 只:")
        for i, r in enumerate(recs, 1):
            action = r.get("action_label", r.get("action", ""))
            case = r.get("case_label", r.get("strategy_case", ""))
            print(f"  {i}. {r['symbol']} {r.get('name','')} 得分={r['score']} 行业={r.get('sector')} {case} {action}")
    else:
        validator.save_empty_pending(result.get("date"), reason=result.get("empty_reason", "当日空仓"))
        print(f"空仓: {result.get('empty_reason', '无推荐')}")

    # 生成报告
    path = report_generator.generate(result)
    print(f"\n报告已保存: {path}")

    if result.get("errors"):
        print(f"\n执行警告({len(result['errors'])}条):")
        for e in result["errors"][-3:]:
            print(f"  - {e}")


def cmd_train_history():
    """历史训练：拉取/复用缓存，逐日生成 Top1/空仓样本。"""
    import backtest_runner
    import feedback_loop
    import report_generator
    args = _parse_kv_args(sys.argv[2:])
    days = int(args["days"]) if args.get("days") else backtest_runner.DEFAULT_TRAINING_DAYS
    universe = int(args.get("universe", "150"))
    overrides = _runtime_overrides(args)

    print("=== 历史训练 ===")
    result = backtest_runner.run_backtest(
        trading_days=days,
        universe_size=universe,
        overrides=overrides or None,
    )
    sid = feedback_loop.collect_metrics("train_history")
    report_path = report_generator.generate({
        "date": dt.datetime.now().strftime("%Y-%m-%d"),
        "recommendations": [],
        "market_overview": {},
        "empty_reason": "历史训练完成，今日优选保持当前策略实时结果",
        "errors": [],
    })

    samples = result.get("samples", [])
    trades = result.get("trades", [])
    print(f"样本日: {len(samples)}")
    print(f"出手: {len(trades)} / 空仓: {len(samples) - len(trades)}")
    print(f"报告已更新: {report_path}")
    print(f"指标快照: {sid}")


def cmd_validate_yesterday():
    """T+1 日验证昨日推荐。"""
    import validator

    print("=== 验证昨日推荐 ===")
    result = validator.validate_yesterday()
    print(f"验证笔数: {result.get('validated', 0)}")

    for r in result.get("results", []):
        win = "✅" if r.get("return", 0) > 0 else "❌"
        print(f"  {r['symbol']} {r['name']} 买{r['buy_price']:.2f} "
              f"卖{r['sell_price']:.2f} 收益{r['return']:.2%} {win}")

    perf = result.get("performance", {})
    print("\n最新胜率:")
    for period in ["7d", "30d", "total"]:
        p = perf.get(period, {})
        label = {"7d": "近7日", "30d": "近30日", "total": "总计"}[period]
        print(f"  {label}: {p.get('win_rate', 0):.1%} "
              f"(盈亏比 1:{p.get('pl_ratio', 0):.2f}, 样本 {p.get('samples', 0)})")


def cmd_optimize_weekly():
    """周度参数优化。"""
    import optimizer

    print("=== 周度策略优化 ===")
    result = optimizer.optimize_weekly()
    print(f"状态: {result.get('status')}")

    if result.get("status") == "skipped":
        print(f"原因: {result.get('reason')}")
    elif result.get("status") == "rolled_back":
        print(f"原因: {result.get('reason')}")
        print(f"排序损失: {result.get('ranking_loss')}")
        old_bt = result.get("old_candidate_backtest", {})
        new_bt = result.get("new_candidate_backtest", {})
        if old_bt and new_bt:
            print("候选池回测:")
            print(f"  胜率: {old_bt.get('win_rate', 0):.1%} → {new_bt.get('win_rate', 0):.1%}")
            print(f"  平均收益: {old_bt.get('avg_return', 0):.2%} → {new_bt.get('avg_return', 0):.2%}")
            print(f"  最大连亏: {old_bt.get('max_consecutive_loss', 0)} → {new_bt.get('max_consecutive_loss', 0)}")
            print(f"  出手/空仓: {old_bt.get('trade_samples', 0)}/{old_bt.get('empty_days', 0)}"
                  f" → {new_bt.get('trade_samples', 0)}/{new_bt.get('empty_days', 0)}")
        print("因子相关性:")
        for fk, rho in result.get("correlations", {}).items():
            print(f"  {fk}: {rho}")
    elif result.get("status") == "optimized":
        print(f"版本: {result.get('old_version')} → {result.get('new_version')}")
        print(f"排序损失: {result.get('ranking_loss')}")
        print(f"回测胜率: {result.get('old_winrate', 0):.1%} → {result.get('new_winrate', 0):.1%}")
        if result.get("optimization_method"):
            print(f"采用方法: {result.get('optimization_method')}")
        if result.get("acceptance_reason"):
            print(f"接受原因: {result.get('acceptance_reason')}")
        print(f"下次优化: {result.get('next_optimize_date')}")
        print("\n权重变更:")
        before = result.get("weights_before", {})
        after = result.get("weights_after", {})
        for fk in before:
            print(f"  {fk}: {before[fk]:.3f} → {after[fk]:.3f}")
        print("\n因子相关性:")
        for fk, rho in result.get("correlations", {}).items():
            print(f"  {fk}: {rho}")


def cmd_optimize_iterative():
    """多轮迭代优化：训练逆向反馈 + 验证集正向检验。"""
    import optimizer

    args = _parse_kv_args(sys.argv[2:])
    rounds = int(args.get("rounds", "3"))
    walk_ratio = float(args.get("walk_forward_ratio", "0.3"))
    min_val = int(args.get("min_validation_samples", "20"))
    print("=== 迭代策略优化 ===")
    result = optimizer.optimize_iterative(
        rounds=rounds,
        walk_forward_ratio=walk_ratio,
        min_validation_samples=min_val,
    )

    print(f"状态: {result.get('status')}")
    print(f"轮数: {result.get('rounds_executed', 0)} / {result.get('rounds_requested', 0)}")
    if result.get("reason"):
        print(f"原因: {result.get('reason')}")
    if result.get("status") == "optimized":
        print(f"版本: {result.get('old_version')} → {result.get('new_version')}")
        last_round = result.get("last_round", {})
        print(f"最终策略: {last_round.get('method')} ({last_round.get('accepted_reason')})")
        print(f"新胜率: {last_round.get('old_win_rate', 0):.1%} → {last_round.get('new_win_rate', 0):.1%}")
        print(f"新平均收益: {last_round.get('old_avg_return', 0):.2%} → {last_round.get('new_avg_return', 0):.2%}")
        print(f"下次优化: {result.get('next_optimize_date')}")
    if result.get("validation_mode"):
        print(f"验证模式: {result.get('validation_mode')}")
    if result.get("improvement_mode"):
        print(f"优化模式: {result.get('improvement_mode')}")

    if result.get("rounds_result"):
        print("\n--- 逐轮摘要 ---")
        for r in result["rounds_result"]:
            print(
                f"R{r.get('round')} {r.get('method')} | "
                f"accepted={r.get('accepted')} | {r.get('accepted_reason', '')}"
            )
            if r.get("accepted"):
                print(
                    f"  {r.get('old_win_rate', 0):.1%}→{r.get('new_win_rate', 0):.1%}，"
                    f"{r.get('old_avg_return', 0):.2%}→{r.get('new_avg_return', 0):.2%}，"
                    f"损失 {r.get('old_max_loss')}→{r.get('new_max_loss')}"
                )
            else:
                print(f"  stop_reason={r.get('stop_reason')}")


def cmd_show_status():
    """查看策略状态。"""
    import validator
    print(validator.show_status())


def cmd_simulate_coverage():
    """模拟高出手率目标下的历史表现，不修改正式策略。"""
    import coverage_simulator

    args = _parse_kv_args(sys.argv[2:])
    targets_text = args.get("targets", "0.75,0.80,0.85")
    targets = [
        float(x.strip().rstrip("%")) / 100 if x.strip().endswith("%") else float(x.strip())
        for x in targets_text.split(",")
        if x.strip()
    ]
    include_picks = int(args.get("include_picks", "0"))
    result = coverage_simulator.simulate_from_files(targets=targets)
    print(coverage_simulator.format_summary(result, include_picks=include_picks))


def cmd_optimize_balance():
    """胜率与出手率平衡优化：更新正式单一策略。"""
    import optimizer

    args = _parse_kv_args(sys.argv[2:])
    min_part = float(args.get("min-participation", "0.30"))
    max_part = float(args.get("max-participation", "0.45"))
    min_win = float(args.get("min-win-rate", "0.70"))
    max_loss = int(args.get("max-consecutive-loss", "3"))
    min_avg = float(args.get("min-avg-return", "0.0"))
    result = optimizer.optimize_balance(
        min_participation=min_part,
        max_participation=max_part,
        min_win_rate=min_win,
        max_consecutive_loss=max_loss,
        min_avg_return=min_avg,
    )
    print(f"状态: {result.get('status')}")
    if result.get("reason"):
        print(f"原因: {result.get('reason')}")
    if result.get("status") == "optimized":
        print(f"版本: {result.get('old_version')} → {result.get('new_version')}")
        print(f"采用方法: {result.get('optimization_method')}")
        print(f"接受原因: {result.get('acceptance_reason')}")
        old_bt = result.get("old_candidate_backtest", {})
        new_bt = result.get("new_candidate_backtest", {})
        print("候选池回测:")
        print(
            f"  出手率: {old_bt.get('trade_samples', 0)}/{old_bt.get('samples', 0)}"
            f" → {new_bt.get('trade_samples', 0)}/{new_bt.get('samples', 0)}"
        )
        print(f"  胜率: {old_bt.get('win_rate', 0):.1%} → {new_bt.get('win_rate', 0):.1%}")
        print(f"  平均收益: {old_bt.get('avg_return', 0):.2%} → {new_bt.get('avg_return', 0):.2%}")
        print(f"  最大连亏: {old_bt.get('max_consecutive_loss', 0)} → {new_bt.get('max_consecutive_loss', 0)}")
        print(f"下次优化: {result.get('next_optimize_date')}")
    elif result.get("old_candidate_backtest"):
        bt = result.get("old_candidate_backtest", {})
        print(
            f"当前策略: 出手 {bt.get('trade_samples', 0)}/{bt.get('samples', 0)}，"
            f"胜率 {bt.get('win_rate', 0):.1%}，平均收益 {bt.get('avg_return', 0):.2%}，"
            f"最大连亏 {bt.get('max_consecutive_loss', 0)}"
        )


def cmd_optimize_regret_zero():
    """机会损失趋近0优化：优先命中候选池次日实际最优。"""
    import optimizer

    args = _parse_kv_args(sys.argv[2:])
    validation_ratio = float(args.get("validation-ratio", "0.30"))
    min_validation_samples = int(args.get("min-validation-samples", "20"))
    result = optimizer.optimize_regret_zero(
        validation_ratio=validation_ratio,
        min_validation_samples=min_validation_samples,
    )
    print(f"状态: {result.get('status')}")
    if result.get("reason"):
        print(f"原因: {result.get('reason')}")

    old_bt = result.get("old_candidate_backtest", {}) or {}
    new_bt = result.get("new_candidate_backtest", {}) or {}
    if old_bt and new_bt:
        print("机会损失目标:")
        print(f"  平均机会损失: {old_bt.get('avg_regret', 0):.2%} → {new_bt.get('avg_regret', 0):.2%}")
        print(f"  累计机会损失: {old_bt.get('total_regret', 0):.2%} → {new_bt.get('total_regret', 0):.2%}")
        print(f"  命中次日最优: {old_bt.get('exact_best_hit_rate', 0):.2%} → {new_bt.get('exact_best_hit_rate', 0):.2%}")
        print(f"  胜率/平均收益: {old_bt.get('win_rate', 0):.1%}/{old_bt.get('avg_return', 0):.2%}"
              f" → {new_bt.get('win_rate', 0):.1%}/{new_bt.get('avg_return', 0):.2%}")
    if result.get("status") == "optimized":
        print(f"版本: {result.get('old_version')} → {result.get('new_version')}")
        print(f"采用方法: {result.get('optimization_method')}")
        print(f"接受原因: {result.get('acceptance_reason')}")
        print(f"验证模式: {result.get('validation_mode')}")
        print(f"下次优化: {result.get('next_optimize_date')}")


def cmd_history():
    """查看优化历史。"""
    import optimizer
    print(optimizer.show_optimization_history())


# ---------------------------------------------------------------------------
# 反馈闭环命令
# ---------------------------------------------------------------------------

def cmd_record_adjustment():
    """记录重大调整，自动采集 baseline。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("title") or not args.get("content") or not args.get("goal"):
        print("用法: record_adjustment --title \"...\" --content \"...\" "
              "--scope f1.py,f2.py --goal \"...\" --category data_source [--horizon 30]")
        sys.exit(1)
    aid = feedback_loop.record_adjustment(
        title=args["title"],
        content=args["content"],
        scope=args.get("scope", ""),
        goal=args["goal"],
        category=args.get("category", "data_source"),
        expected_horizon_days=int(args.get("horizon", "30")),
    )
    print(f"已记录调整: {aid}")
    print(f"Baseline 快照已采集")
    print()
    print(feedback_loop.show_feedback_status(aid))


def cmd_collect_metrics():
    """采集指标快照。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("label"):
        print("用法: collect_metrics --label \"...\" [--adjustment-id ID]")
        sys.exit(1)
    sid = feedback_loop.collect_metrics(args["label"], args.get("adjustment-id"))
    print(f"已采集快照: {sid}")


def cmd_analyze_feedback():
    """分析反馈生成行动项。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("adjustment-id"):
        print("用法: analyze_feedback --adjustment-id ADJ-YYYY-MM-DD-NNN")
        sys.exit(1)
    result = feedback_loop.analyze_feedback(args["adjustment-id"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    print(feedback_loop.show_feedback_status(args["adjustment-id"]))


def cmd_feedback_status():
    """展示所有调整与质量指标。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    print(feedback_loop.show_feedback_status(args.get("adjustment-id")))


def cmd_plan_optimization():
    """为反馈行动项制定建议方案。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("action-id") or not args.get("solution"):
        print("用法: plan_optimization --action-id FA-... --solution \"...\" [--priority P1]")
        sys.exit(1)
    ok = feedback_loop.plan_optimization(
        args["action-id"],
        args["solution"],
        args.get("priority", "P1"),
    )
    if not ok:
        print(f"未找到 action: {args['action-id']}")
        sys.exit(1)
    print("已更新优化建议")


def cmd_implement_action():
    """标记反馈行动项已实施。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("action-id") or not args.get("notes"):
        print("用法: implement_action --action-id FA-... --notes \"...\"")
        sys.exit(1)
    ok = feedback_loop.implement_action(args["action-id"], args["notes"])
    if not ok:
        print(f"未找到 action: {args['action-id']}")
        sys.exit(1)
    print("已标记为 implemented")


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "y", "是", "改善")


def cmd_verify_action():
    """验证反馈行动项效果。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("action-id") or not args.get("result"):
        print("用法: verify_action --action-id FA-... --result \"...\" [--improved true|false]")
        sys.exit(1)
    ok = feedback_loop.verify_action(
        args["action-id"],
        args["result"],
        _parse_bool(args.get("improved", "false")),
    )
    if not ok:
        print(f"未找到 action: {args['action-id']}")
        sys.exit(1)
    print("已标记为 verified")


def cmd_reject_action():
    """拒绝反馈行动项。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("action-id") or not args.get("reason"):
        print("用法: reject_action --action-id FA-... --reason \"...\"")
        sys.exit(1)
    ok = feedback_loop.reject_action(args["action-id"], args["reason"])
    if not ok:
        print(f"未找到 action: {args['action-id']}")
        sys.exit(1)
    print("已标记为 rejected")


def cmd_close_loop():
    """关闭指定调整闭环。"""
    import feedback_loop
    args = _parse_kv_args(sys.argv[2:])
    if not args.get("adjustment-id") or not args.get("summary"):
        print("用法: close_loop --adjustment-id ADJ-... --summary \"...\"")
        sys.exit(1)
    result = feedback_loop.close_loop(args["adjustment-id"], args["summary"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("error"):
        sys.exit(1)


COMMANDS = {
    "run_today_report": cmd_run_today_report,
    "train_history": cmd_train_history,
    "validate_yesterday": cmd_validate_yesterday,
    "optimize_weekly": cmd_optimize_weekly,
    "optimize_iterative": cmd_optimize_iterative,
    "simulate_coverage": cmd_simulate_coverage,
    "optimize_balance": cmd_optimize_balance,
    "optimize_regret_zero": cmd_optimize_regret_zero,
    "show_status": cmd_show_status,
    "history": cmd_history,
    # 反馈闭环
    "record_adjustment": cmd_record_adjustment,
    "collect_metrics": cmd_collect_metrics,
    "analyze_feedback": cmd_analyze_feedback,
    "feedback_status": cmd_feedback_status,
    "plan_optimization": cmd_plan_optimization,
    "implement_action": cmd_implement_action,
    "verify_action": cmd_verify_action,
    "reject_action": cmd_reject_action,
    "close_loop": cmd_close_loop,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"可用命令: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    cmd = sys.argv[1]
    COMMANDS[cmd]()


if __name__ == "__main__":
    main()
