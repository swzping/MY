#!/usr/bin/env python3
"""Extract readable Codex conversation history into small markdown packets.

This script is intentionally read-only against ~/.codex. It scans the session
index and JSONL rollout files, ranks matching threads, and exports cleaned text
for memo creation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization|cookie)(['\"\s:=]+)[^\s'\",]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{12,}"),
]


@dataclass
class ThreadIndex:
    id: str
    title: str
    updated_at: str


@dataclass
class ThreadExport:
    id: str
    title: str
    updated_at: str
    source: Path
    score: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--query", default="", help="Search terms for title and message text.")
    parser.add_argument("--thread-id", action="append", default=[], help="Specific thread ID to export. Repeatable.")
    parser.add_argument("--since", help="Include threads updated on or after YYYY-MM-DD.")
    parser.add_argument("--until", help="Include threads updated on or before YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=50000)
    parser.add_argument("--out", default="work/conversation-memory")
    parser.add_argument("--include-archived", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def load_index(codex_home: Path) -> dict[str, ThreadIndex]:
    index_path = codex_home / "session_index.jsonl"
    items: dict[str, ThreadIndex] = {}
    if not index_path.exists():
        return items
    with index_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            thread_id = str(raw.get("id") or "")
            if not thread_id:
                continue
            items[thread_id] = ThreadIndex(
                id=thread_id,
                title=str(raw.get("thread_name") or "Untitled"),
                updated_at=str(raw.get("updated_at") or ""),
            )
    return items


def iter_session_files(codex_home: Path, include_archived: bool) -> Iterable[Path]:
    sessions = codex_home / "sessions"
    if sessions.exists():
        yield from sessions.rglob("*.jsonl")
        yield from sessions.rglob("*.json")
    archived = codex_home / "archived_sessions"
    if include_archived and archived.exists():
        yield from archived.glob("*.jsonl")
        yield from archived.glob("*.json")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def in_date_range(updated_at: str, since: datetime | None, until: datetime | None) -> bool:
    parsed = parse_date(updated_at)
    if parsed is None:
        return True
    if since and parsed < since:
        return False
    if until:
        inclusive_until = until.replace(hour=23, minute=59, second=59, microsecond=999999)
        if parsed > inclusive_until:
            return False
    return True


def find_thread_id(path: Path, first_objects: list[dict[str, Any]]) -> str:
    for obj in first_objects:
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        meta = payload.get("id") or obj.get("id")
        if isinstance(meta, str) and meta:
            return meta
        session_meta = payload.get("session_meta")
        if isinstance(session_meta, dict) and isinstance(session_meta.get("id"), str):
            return session_meta["id"]
    match = re.search(r"rollout-(?:\d{4}[^-]*-)?([0-9a-f]{8,}[-0-9a-f]*)", path.name)
    return match.group(1) if match else path.stem


def read_jsonl_objects(path: Path, max_lines: int | None = None) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for idx, line in enumerate(handle):
            if max_lines is not None and idx >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                objects.append(obj)
    return objects


def redact(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(lambda m: f"{m.group(1) if m.groups() else '[REDACTED]'} [REDACTED]", result)
    return result


def stringify_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    if isinstance(value, dict):
        for key in ("text", "content", "message"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def extract_event_text(obj: dict[str, Any]) -> tuple[str, str] | None:
    payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
    event_type = obj.get("type") or payload.get("type")

    if event_type == "session_meta":
        return None
    if event_type in {"token_count", "reasoning"}:
        return None

    role = payload.get("role") or obj.get("role")
    content = ""

    if event_type == "response_item":
        item_type = payload.get("type")
        if item_type in {"function_call", "function_call_output", "reasoning"}:
            return None
        role = payload.get("role") or role or "assistant"
        content = stringify_content(payload.get("content") or payload.get("text"))
    elif event_type == "event_msg":
        inner_type = payload.get("type")
        if inner_type in {"token_count", "agent_reasoning_delta", "raw_model_stream_event"}:
            return None
        role = payload.get("role") or role or "event"
        content = stringify_content(payload.get("message") or payload.get("content") or payload.get("text"))
    else:
        content = stringify_content(
            obj.get("content")
            or obj.get("text")
            or payload.get("content")
            or payload.get("text")
            or payload.get("message")
        )

    if not content.strip():
        return None
    if len(content) > 200000:
        content = content[:200000] + "\n[TRUNCATED]"
    role = str(role or "unknown")
    if role in {"system", "developer", "tool"}:
        return None
    return role, redact(content.strip())


def clean_thread_text(path: Path, max_chars: int) -> tuple[str, str]:
    objects = read_jsonl_objects(path)
    thread_id = find_thread_id(path, objects[:5])
    chunks = []
    total = 0
    for obj in objects:
        extracted = extract_event_text(obj)
        if not extracted:
            continue
        role, text = extracted
        chunk = f"\n\n### {role}\n{text}"
        if total + len(chunk) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                chunks.append(chunk[:remaining] + "\n[TRUNCATED]")
            break
        chunks.append(chunk)
        total += len(chunk)
    return thread_id, "".join(chunks).strip()


def score_match(query_terms: list[str], title: str, text: str) -> int:
    if not query_terms:
        return 1
    hay_title = title.lower()
    hay_text = text.lower()
    score = 0
    for term in query_terms:
        if term in hay_title:
            score += 10
        score += min(hay_text.count(term), 5)
    return score


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return cleaned[:120] or "thread"


def write_exports(exports: list[ThreadExport], out_dir: Path, query: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for item in exports:
        filename = f"{safe_filename(item.updated_at[:10])}-{safe_filename(item.title)}-{item.id[:8]}.md"
        path = out_dir / filename
        body = [
            f"# Extracted Thread: {item.title}",
            "",
            f"- id: `{item.id}`",
            f"- updated_at: `{item.updated_at}`",
            f"- source: `{item.source}`",
            f"- match_score: `{item.score}`",
            "",
            "## Cleaned Conversation Text",
            "",
            item.text or "[No readable conversation text extracted.]",
            "",
        ]
        path.write_text("\n".join(body), encoding="utf-8")
        index.append(
            {
                "id": item.id,
                "title": item.title,
                "updated_at": item.updated_at,
                "source": str(item.source),
                "export": str(path),
                "score": item.score,
            }
        )
    (out_dir / "index.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now().astimezone().isoformat(),
                "query": query,
                "exports": index,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Exported {len(exports)} thread(s) to {out_dir}")
    for item in exports:
        print(f"- {item.title} | {item.id} | {item.updated_at} | score={item.score}")


def main() -> int:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser()
    out_dir = Path(args.out).expanduser()
    index = load_index(codex_home)
    since = parse_date(args.since)
    until = parse_date(args.until)
    query_terms = [term.lower() for term in re.findall(r"[\w\u4e00-\u9fff.-]+", args.query) if term.strip()]
    wanted_ids = set(args.thread_id)

    exports: list[ThreadExport] = []
    for path in iter_session_files(codex_home, args.include_archived):
        try:
            objects = read_jsonl_objects(path, max_lines=5)
            thread_id = find_thread_id(path, objects)
            meta = index.get(thread_id, ThreadIndex(thread_id, path.stem, ""))
            if wanted_ids and thread_id not in wanted_ids:
                continue
            if not in_date_range(meta.updated_at, since, until):
                continue
            actual_id, text = clean_thread_text(path, args.max_chars)
            if actual_id and actual_id != thread_id:
                thread_id = actual_id
                meta = index.get(thread_id, meta)
            score = score_match(query_terms, meta.title, text)
            if query_terms and score <= 0:
                continue
            exports.append(
                ThreadExport(
                    id=thread_id,
                    title=meta.title,
                    updated_at=meta.updated_at,
                    source=path,
                    score=score,
                    text=text,
                )
            )
        except Exception as exc:
            print(f"Skipping {path}: {exc}")

    exports.sort(key=lambda item: (item.score, item.updated_at), reverse=True)
    write_exports(exports[: max(args.limit, 0)], out_dir, args.query)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
