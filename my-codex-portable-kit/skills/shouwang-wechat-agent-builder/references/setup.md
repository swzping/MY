# Setup Notes

## What Gets Created

The installer writes a new app in the target directory. It does not copy an existing Shouwang project.

Generated files include:

- `package.json`
- `index.html`
- `electron/main.cjs`
- `electron/preload.cjs`
- `src/main.jsx`
- `src/App.jsx`
- `src/styles.css`
- `wechat-agent-tool/wechat_agent_cli.py`
- `work/.venv-wechat-vault`

## Dependencies

Required on the target computer:

- macOS
- WeChat for Mac with local chat data for the current user
- Python 3
- Node.js and npm
- Git, if the installer needs to fetch `yichen-wechat-local-vault`

The generated app depends on:

- `~/.codex/skills/yichen-wechat-local-vault/scripts/decrypt_all_dbs.py`
- `~/.codex/skills/yichen-wechat-local-vault/scripts/vault_cli.py`

## Verification Commands

```bash
cd <target>
work/.venv-wechat-vault/bin/python -c "from Crypto.Cipher import AES; print('ok')"
python3 wechat-agent-tool/wechat_agent_cli.py status
npm run build
npm run dev
```

## Common Failures

`No module named Crypto`:
Run the installer again. It creates `work/.venv-wechat-vault` and installs `pycryptodome`.

`vault_cli.py not found`:
Install `yichen-wechat-local-vault` into `~/.codex/skills`.

`找不到聊天对象`:
Use a more exact group name, or run:

```bash
python3 wechat-agent-tool/wechat_agent_cli.py chats --query "关键词" --limit 20
```

Model request failed:
Check Base URL, API key, and model name in the app settings.
