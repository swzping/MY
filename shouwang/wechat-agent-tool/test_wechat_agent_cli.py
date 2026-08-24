import json
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wechat_agent_cli as cli


class WeChatAgentCliTests(unittest.TestCase):
    def test_messages_translates_to_history_json(self):
        command = cli.build_vault_command(
            "messages",
            chat="天沐锦江老板群",
            start="2026-08-01",
            limit=20,
            message_type="text",
            media=True,
        )

        self.assertEqual(command[:2], [cli.python_bin(), str(cli.VAULT_CLI)])
        self.assertEqual(
            command[2:],
            [
                "history",
                "天沐锦江老板群",
                "--limit",
                "20",
                "--start-time",
                "2026-08-01",
                "--type",
                "text",
                "--media",
                "--format",
                "json",
            ],
        )

    def test_search_supports_multiple_chat_filters(self):
        command = cli.build_vault_command(
            "search",
            keyword="物业费",
            chats=["群A", "好友B"],
            limit=10,
        )

        self.assertIn("--chat", command)
        self.assertEqual(command.count("--chat"), 2)
        self.assertEqual(command[-2:], ["--format", "json"])

    def test_run_vault_parses_json(self):
        completed = subprocess.CompletedProcess(
            args=["python", "vault_cli.py"],
            returncode=0,
            stdout='{"ok": true, "items": [1]}',
            stderr="",
        )
        with patch("subprocess.run", return_value=completed):
            result = cli.run_vault(["python", "vault_cli.py"])

        self.assertEqual(result, {"ok": True, "items": [1]})

    def test_run_vault_wraps_text_output(self):
        completed = subprocess.CompletedProcess(
            args=["python", "vault_cli.py"],
            returncode=0,
            stdout="/tmp/chat.md\nExported 3 messages.\n",
            stderr="",
        )
        with patch("subprocess.run", return_value=completed):
            result = cli.run_vault(["python", "vault_cli.py"])

        self.assertEqual(result["text"], "/tmp/chat.md\nExported 3 messages.")

    def test_run_vault_raises_on_failure(self):
        completed = subprocess.CompletedProcess(
            args=["python", "vault_cli.py"],
            returncode=2,
            stdout="",
            stderr="bad chat",
        )
        with patch("subprocess.run", return_value=completed):
            with self.assertRaises(cli.VaultCommandError) as caught:
                cli.run_vault(["python", "vault_cli.py"])

        self.assertIn("bad chat", str(caught.exception))

    def test_cli_prints_json(self):
        with patch("wechat_agent_cli.run_vault", return_value={"count": 1}):
            with patch("builtins.print") as mocked_print:
                code = cli.main(["recent", "--limit", "1"])

        self.assertEqual(code, 0)
        payload = json.loads(mocked_print.call_args.args[0])
        self.assertEqual(payload, {"count": 1})


if __name__ == "__main__":
    unittest.main()
