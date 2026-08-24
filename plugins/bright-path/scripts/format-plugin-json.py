#!/usr/bin/env python3
"""Format Bright Path plugin.json without escaping Chinese text."""

from __future__ import annotations

import json
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"


def main() -> None:
    payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    PLUGIN_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
