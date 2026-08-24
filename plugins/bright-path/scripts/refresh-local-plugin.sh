#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_CREATOR="/Users/edy/.codex/skills/.system/plugin-creator/scripts"

python3 "${PLUGIN_CREATOR}/update_plugin_cachebuster.py" "${PLUGIN_ROOT}"
python3 "${PLUGIN_ROOT}/scripts/format-plugin-json.py"
python3 "${PLUGIN_CREATOR}/validate_plugin.py" "${PLUGIN_ROOT}"

printf '\nBright Path refreshed: %s\n' "${PLUGIN_ROOT}"
