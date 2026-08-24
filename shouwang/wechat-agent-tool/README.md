# WeChat Agent Tool

Local read-only CLI for simple agents to query your decrypted WeChat vault.

## Quick Start

```bash
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py status
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py chats --query "锦江" --limit 10
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py recent --limit 20
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py messages --chat "天沐锦江老板群" --limit 50
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py search --keyword "物业费" --chat "天沐锦江老板群" --limit 30
python3 /Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py stats --chat "天沐锦江老板群"
```

## Can It Query Other Groups and Friends?

Yes. Use `chats --query` to find any available group or private chat, then pass the returned display name or username to `messages`, `search`, `stats`, `members`, or `export`.

## Agent Integration

Call the CLI from your own Python agent:

```python
import json
import subprocess

cmd = [
    "python3",
    "/Users/edy/Documents/Codex/2026-08-18/https-github-com-mcncarl-yichen-skills/outputs/wechat-agent-tool/wechat_agent_cli.py",
    "messages",
    "--chat",
    "天沐锦江老板群",
    "--limit",
    "50",
]
result = subprocess.run(cmd, capture_output=True, text=True, check=True)
messages = json.loads(result.stdout)
```

## Privacy

This tool is read-only. It does not extract keys, decrypt databases, open WeChat, or run a network server. It delegates to the local decrypted vault at:

`/Users/edy/Library/Application Support/wechat-local-vault/decrypted/current`

Keep outputs local. Chat data can contain private messages.
