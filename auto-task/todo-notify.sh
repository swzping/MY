#!/bin/zsh

TODO_FILE="/Users/edy/Documents/MY/auto_task/工作待办.md"
MODE="${1:-todo}"

if [[ ! -f "$TODO_FILE" ]]; then
  /usr/bin/osascript - "待办提醒" "没有找到 auto_task/工作待办.md" <<'APPLESCRIPT'
on run argv
  display notification (item 2 of argv) with title (item 1 of argv) sound name "Glass"
end run
APPLESCRIPT
  /usr/bin/afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1
  exit 0
fi

unfinished=$(/usr/bin/grep -E '^- \[ \] .+' "$TODO_FILE" | /usr/bin/sed 's/^- \[ \] //' | /usr/bin/head -n 3 | /usr/bin/paste -sd '；' -)

if [[ -z "$unfinished" ]]; then
  unfinished="当前没有明确的未完成事项，可以补充新的待办。"
fi

if [[ "$MODE" == "morning" ]]; then
  title="每日晨报提醒"
  message="请查看今日晨报，并优先处理：$unfinished"
else
  title="工作待办提醒"
  message="该更新待办了：$unfinished"
fi

/usr/bin/osascript - "$title" "$message" <<'APPLESCRIPT'
on run argv
  display notification (item 2 of argv) with title (item 1 of argv) sound name "Glass"
end run
APPLESCRIPT

/usr/bin/afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1
