#!/usr/bin/env python3
"""
Tiny example agent that calls wechat_agent_cli.py with subprocess.

It does not use an LLM by itself. It shows the data access pattern your own
agent can reuse before handing selected messages to a model.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CLI = Path(__file__).with_name("wechat_agent_cli.py")


def call_wechat_agent(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout.strip() or completed.stderr.strip())
    return json.loads(completed.stdout)


def main() -> int:
    keyword = sys.argv[1] if len(sys.argv) > 1 else "公司"
    data = call_wechat_agent("search", "--keyword", keyword, "--limit", "20")

    items = data.get("messages") or data.get("items") or data.get("results") or []
    print(f"Keyword: {keyword}")
    print(f"Fetched messages: {len(items)}")
    print()
    print("Analysis scaffold:")
    print("- Main topics: fill with your LLM or rules")
    print("- People to follow up: fill with your LLM or rules")
    print("- Open questions: fill with your LLM or rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
