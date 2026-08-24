#!/usr/bin/env python3
"""
Read-only JSON wrapper for yichen-wechat-local-vault.

This script is intended for simple local agents. It delegates all WeChat vault
access to the installed skill's vault_cli.py and returns bounded JSON output.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path.home() / ".codex/skills/yichen-wechat-local-vault"
VAULT_CLI = SKILL_DIR / "scripts/vault_cli.py"
LOCAL_VENV_PYTHON = (
    Path(__file__).resolve().parents[1] / "work/.venv-wechat-vault/bin/python"
)


class VaultCommandError(RuntimeError):
    pass


def python_bin() -> str:
    if LOCAL_VENV_PYTHON.exists():
        return str(LOCAL_VENV_PYTHON)
    return sys.executable


def add_common_time_args(command: list[str], args: argparse.Namespace) -> None:
    if getattr(args, "start", ""):
        command.extend(["--start-time", args.start])
    if getattr(args, "end", ""):
        command.extend(["--end-time", args.end])


def build_vault_command(action: str, **kwargs: Any) -> list[str]:
    command = [python_bin(), str(VAULT_CLI)]

    if action == "status":
        return command + ["status", "--format", "json"]

    if action == "recent":
        return command + ["sessions", "--limit", str(kwargs["limit"]), "--format", "json"]

    if action == "chats":
        command.extend(["contacts", "--limit", str(kwargs["limit"]), "--format", "json"])
        if kwargs.get("query"):
            command.extend(["--query", kwargs["query"]])
        return command

    if action == "messages":
        command.extend(["history", kwargs["chat"], "--limit", str(kwargs["limit"])])
        if kwargs.get("offset"):
            command.extend(["--offset", str(kwargs["offset"])])
        if kwargs.get("start"):
            command.extend(["--start-time", kwargs["start"]])
        if kwargs.get("end"):
            command.extend(["--end-time", kwargs["end"]])
        if kwargs.get("message_type"):
            command.extend(["--type", kwargs["message_type"]])
        if kwargs.get("media"):
            command.append("--media")
        command.extend(["--format", "json"])
        return command

    if action == "search":
        command.extend(["search", kwargs["keyword"], "--limit", str(kwargs["limit"])])
        if kwargs.get("offset"):
            command.extend(["--offset", str(kwargs["offset"])])
        for chat in kwargs.get("chats") or []:
            command.extend(["--chat", chat])
        if kwargs.get("start"):
            command.extend(["--start-time", kwargs["start"]])
        if kwargs.get("end"):
            command.extend(["--end-time", kwargs["end"]])
        if kwargs.get("message_type"):
            command.extend(["--type", kwargs["message_type"]])
        command.extend(["--format", "json"])
        return command

    if action == "stats":
        command.extend(["stats", kwargs["chat"]])
        if kwargs.get("start"):
            command.extend(["--start-time", kwargs["start"]])
        if kwargs.get("end"):
            command.extend(["--end-time", kwargs["end"]])
        command.extend(["--format", "json"])
        return command

    if action == "members":
        return command + ["members", kwargs["group"], "--format", "json"]

    if action == "export":
        command.extend(["export", kwargs["chat"], "--format", kwargs["format"]])
        command.extend(["--limit", str(kwargs["limit"])])
        if kwargs.get("output"):
            command.extend(["--output", kwargs["output"]])
        if kwargs.get("start"):
            command.extend(["--start-time", kwargs["start"]])
        if kwargs.get("end"):
            command.extend(["--end-time", kwargs["end"]])
        if kwargs.get("message_type"):
            command.extend(["--type", kwargs["message_type"]])
        if kwargs.get("media"):
            command.append("--media")
        return command

    raise ValueError(f"unknown action: {action}")


def run_vault(command: list[str]) -> dict[str, Any]:
    if not VAULT_CLI.exists():
        raise VaultCommandError(f"vault_cli.py not found: {VAULT_CLI}")

    completed = subprocess.run(command, capture_output=True, text=True)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()

    if completed.returncode != 0:
        detail = stderr or stdout or f"exit code {completed.returncode}"
        raise VaultCommandError(detail)

    if not stdout:
        return {"ok": True}

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {"text": stdout}

    if isinstance(parsed, dict):
        return parsed
    return {"items": parsed}


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent-friendly read-only CLI for decrypted WeChat vault data."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Check decrypted vault status")

    p = sub.add_parser("recent", help="List recent sessions")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("chats", help="Search groups and friends")
    p.add_argument("--query", default="")
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("messages", help="Read bounded history for a group or friend")
    p.add_argument("--chat", required=True)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")
    p.add_argument("--type", dest="message_type")
    p.add_argument("--media", action="store_true")

    p = sub.add_parser("search", help="Search messages globally or in chats")
    p.add_argument("--keyword", required=True)
    p.add_argument("--chat", dest="chats", action="append")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")
    p.add_argument("--type", dest="message_type")

    p = sub.add_parser("stats", help="Get stats for one group or friend")
    p.add_argument("--chat", required=True)
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")

    p = sub.add_parser("members", help="List group members")
    p.add_argument("--group", required=True)

    p = sub.add_parser("export", help="Export bounded chat history to a file")
    p.add_argument("--chat", required=True)
    p.add_argument("--format", choices=["markdown", "txt"], default="markdown")
    p.add_argument("--output")
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")
    p.add_argument("--type", dest="message_type")
    p.add_argument("--media", action="store_true")

    return parser


def namespace_to_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {key: value for key, value in vars(args).items() if key != "command"}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = build_vault_command(args.command, **namespace_to_kwargs(args))

    try:
        result = run_vault(command)
    except VaultCommandError as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1

    print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
