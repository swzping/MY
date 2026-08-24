---
name: shouwang-wechat-agent-builder
description: Generate or repair a portable macOS Electron + React desktop agent for local WeChat group chat analysis. Use when the user wants to create a fresh WeChat analysis app on another computer, scaffold a new local desktop intelligent agent, install dependencies for yichen-wechat-local-vault integration, configure OpenAI-compatible model settings, or reproduce the Shouwang-style WeChat import and chat Q&A workflow without copying an existing project.
---

# Shouwang WeChat Agent Builder

## Purpose

Use this skill to create a new standalone desktop app that analyzes local WeChat group history. The generated app is created from bundled templates and does not copy an existing project directory.

The generated app:

- Runs on macOS with Electron + React + Vite.
- Imports a group by name from the local `yichen-wechat-local-vault`.
- Refreshes the vault with incremental decrypt before import.
- Supports start/end date filters.
- Saves imported group snapshots under Electron `userData`.
- Provides a chat-like question box backed by an OpenAI-compatible Responses API.
- Adds transfer/red-packet/payment-related messages to the model context when present.

## Quick Start

Run the generator:

```bash
python3 ~/.codex/skills/shouwang-wechat-agent-builder/scripts/install_shouwang_wechat_agent.py \
  --target ~/Documents/shouwang-wechat-agent
```

Then start the generated desktop app:

```bash
cd ~/Documents/shouwang-wechat-agent
npm run dev
```

Use options when needed:

```bash
python3 ~/.codex/skills/shouwang-wechat-agent-builder/scripts/install_shouwang_wechat_agent.py \
  --target ~/Documents/shouwang-wechat-agent \
  --base-url "https://ap1.upit.top/51Token/v1" \
  --model "gpt-5.5"
```

Never pass a real API key in a shared transcript. Prefer entering it in the generated app settings UI.

## Workflow

1. Confirm the target machine is macOS and has WeChat desktop data for the signed-in user.
2. Run `scripts/install_shouwang_wechat_agent.py` with a target directory.
3. If `~/.codex/skills/yichen-wechat-local-vault` is missing, let the script install it from `mcncarl/yichen-skills`.
4. Let the script create `work/.venv-wechat-vault` and install `pycryptodome`.
5. Start the generated app with `npm run dev`.
6. In the app, set model Base URL, model name, and API key.
7. Enter a WeChat group name and optional date range, then click import.

## Safety Boundaries

- Do not copy WeChat databases, keys, decrypted vaults, or chat snapshots between computers.
- Do not print keys, wxids, salts, or large raw chat contents.
- The generated app reads only the target computer's local vault.
- If vault refresh fails, fix the vault skill/key setup on that computer instead of falling back silently to stale data.

## Troubleshooting

Use `references/setup.md` for detailed setup, common failures, and verification commands.
