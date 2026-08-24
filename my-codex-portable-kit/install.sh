#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CODEX_HOME/backups/portable-kit-$STAMP"

say() { printf '\n==> %s\n' "$*"; }
copy_dir_contents() {
  local src="$1"
  local dest="$2"
  mkdir -p "$dest"
  if [ -d "$src" ]; then
    find "$src" -mindepth 1 -maxdepth 1 -print0 | while IFS= read -r -d '' item; do
      local name
      name="$(basename "$item")"
      rm -rf "$dest/$name"
      cp -R "$item" "$dest/$name"
    done
  fi
}

say "Installing portable Codex kit"
mkdir -p "$CODEX_HOME" "$AGENTS_HOME" "$BACKUP_DIR"

say "Backing up existing portable targets to $BACKUP_DIR"
[ -d "$CODEX_HOME/skills" ] && cp -R "$CODEX_HOME/skills" "$BACKUP_DIR/skills"
[ -d "$CODEX_HOME/rules" ] && cp -R "$CODEX_HOME/rules" "$BACKUP_DIR/rules"
[ -d "$CODEX_HOME/plugins/cache" ] && mkdir -p "$BACKUP_DIR/plugins" && cp -R "$CODEX_HOME/plugins/cache" "$BACKUP_DIR/plugins/cache"
[ -f "$CODEX_HOME/config.toml" ] && cp "$CODEX_HOME/config.toml" "$BACKUP_DIR/config.toml"
[ -f "$CODEX_HOME/instructions.md" ] && cp "$CODEX_HOME/instructions.md" "$BACKUP_DIR/instructions.md"
[ -d "$AGENTS_HOME/skills" ] && mkdir -p "$BACKUP_DIR/agents" && cp -R "$AGENTS_HOME/skills" "$BACKUP_DIR/agents/skills"
[ -d "$AGENTS_HOME/plugins" ] && mkdir -p "$BACKUP_DIR/agents" && cp -R "$AGENTS_HOME/plugins" "$BACKUP_DIR/agents/plugins"

say "Installing Codex skills"
copy_dir_contents "$KIT_DIR/skills" "$CODEX_HOME/skills"

if [ -d "$KIT_DIR/agents/skills" ]; then
  say "Installing global Agent skills"
  copy_dir_contents "$KIT_DIR/agents/skills" "$AGENTS_HOME/skills"
fi

if [ -d "$KIT_DIR/agents/plugins" ]; then
  say "Installing global Agent plugin marketplace"
  copy_dir_contents "$KIT_DIR/agents/plugins" "$AGENTS_HOME/plugins"
fi

say "Installing rules"
mkdir -p "$CODEX_HOME/rules"
if [ -f "$KIT_DIR/rules/default.rules" ]; then
  cp "$KIT_DIR/rules/default.rules" "$CODEX_HOME/rules/default.rules"
fi

if [ -f "$KIT_DIR/instructions.md" ]; then
  say "Installing global instructions"
  cp "$KIT_DIR/instructions.md" "$CODEX_HOME/instructions.md"
fi

if [ -d "$KIT_DIR/plugins/cache" ]; then
  say "Installing third-party plugin cache"
  mkdir -p "$CODEX_HOME/plugins/cache"
  copy_dir_contents "$KIT_DIR/plugins/cache" "$CODEX_HOME/plugins/cache"
fi

say "Preparing portable config template"
if [ -f "$KIT_DIR/templates/config-portable.toml" ]; then
  cp "$KIT_DIR/templates/config-portable.toml" "$CODEX_HOME/config.portable-kit.toml"
  printf 'Portable config template copied to: %s\n' "$CODEX_HOME/config.portable-kit.toml"
  printf 'Review it, then merge desired sections into: %s\n' "$CODEX_HOME/config.toml"
fi

say "Verification"
skill_count="$(find "$CODEX_HOME/skills" -maxdepth 2 -type f -name SKILL.md | wc -l | tr -d ' ')"
agent_skill_count="$(find "$AGENTS_HOME/skills" -maxdepth 2 -type f -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')"
printf 'Installed/available skills: %s\n' "$skill_count"
printf 'Installed/available Agent skills: %s\n' "$agent_skill_count"
printf 'Backup directory: %s\n' "$BACKUP_DIR"

cat <<'NOTE'

Next steps:
1. Restart Codex so new skills are loaded.
2. Login/authenticate Codex normally on this machine.
3. Review ~/.codex/config.portable-kit.toml before copying any settings into ~/.codex/config.toml.

This installer intentionally does not copy auth.json, sqlite databases, logs, sessions, shell snapshots, or history.
It also does not bundle OpenAI built-in/runtime plugin caches; Codex should recreate those on each machine.
It installs Agent skills as plain files under ~/.agents/skills and restores ~/.agents/plugins marketplace metadata, but does not restore runtime package-manager state.
Automation templates are kept under automations/ for manual recreation; this installer does not copy or enable ~/.codex/automations.
NOTE
