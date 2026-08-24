#!/usr/bin/env python3
"""Initialize a standalone A-share tail-close overnight strategy workspace."""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCAFFOLD_DIR = SKILL_DIR / "assets" / "scaffold"


def copy_tree(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        target = dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        shutil.copy2(item, target)


def write_readme(root: Path) -> None:
    path = root / "README.md"
    if path.exists():
        return
    path.write_text(
        "\n".join(
            [
                "# A股主板尾盘隔夜纸面策略",
                "",
                "此目录由 `a-share-tail-close-overnight` skill 初始化。",
                "",
                "## 常用命令",
                "",
                "```bash",
                "python3 -m venv .venv",
                ".venv/bin/pip install requests pytest",
                "python3 ~/.agents/skills/a-share-tail-close-overnight/scripts/run_daily_tail_strategy.py . --date YYYY-MM-DD",
                ".venv/bin/python -m pytest tests",
                "```",
                "",
                "日常只看 `reports/strategy_01/daily_run_YYYY-MM-DD.md`。候选、台账、复盘明细等机器数据位于 `reports/strategy_01/_data/`，研究归档位于 `_archive/`。",
                "",
                "策略只做纸面验证，不进行真实下单。后续优化应在本目录脚本和测试中持续迭代。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_initial_report(root: Path) -> Path:
    report_dir = root / "reports" / "strategy_01"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"daily_run_{date.today().isoformat()}.md"
    if report_path.exists():
        return report_path
    report_path.write_text(
        "\n".join(
            [
                f"# 尾盘隔夜策略初始化报告：{date.today().isoformat()}",
                "",
                "## 状态",
                "",
                "- 已创建独立策略工作区。",
                "- 尚未执行行情筛选；请在本目录运行每日执行命令生成当天唯一总报告。",
                "- 本策略只做纸面验证，不进行真实下单。",
                "",
                "## 下一步",
                "",
                "```bash",
                "python3 ~/.agents/skills/a-share-tail-close-overnight/scripts/run_daily_tail_strategy.py .",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Target workspace directory")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    copy_tree(SCAFFOLD_DIR, target)
    for rel in [
        "data/cache/kline",
        "data/cache/hot_reason",
        "reports/strategy_01",
    ]:
        (target / rel).mkdir(parents=True, exist_ok=True)
    write_readme(target)
    report_path = write_initial_report(target)
    print(f"Initialized standalone tail strategy workspace: {target}")
    print(f"Initial report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
