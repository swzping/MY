#!/usr/bin/env python3
"""Create a standalone Shouwang-style WeChat analysis desktop app."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


VAULT_REPO = "https://github.com/mcncarl/yichen-skills.git"
VAULT_SKILL_REL = "yichen-wechat-local-vault"


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(command))
    return subprocess.run(command, cwd=cwd, check=check)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_empty_or_allowed(target: Path, force: bool) -> None:
    if not target.exists():
        target.mkdir(parents=True)
        return
    if any(target.iterdir()) and not force:
        raise SystemExit(f"Target is not empty: {target}\nUse --force to overwrite generated files.")
    target.mkdir(parents=True, exist_ok=True)


def ensure_vault_skill(skip: bool) -> None:
    skill_dir = Path.home() / ".codex/skills/yichen-wechat-local-vault"
    if skill_dir.exists():
        print(f"Vault skill found: {skill_dir}")
        return
    if skip:
        print(f"Vault skill missing: {skill_dir}")
        return
    if not shutil.which("git"):
        print("git not found; install yichen-wechat-local-vault manually.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = Path(tmp) / "yichen-skills"
        run(["git", "clone", "--depth", "1", VAULT_REPO, str(repo_dir)])
        candidates = list(repo_dir.rglob(VAULT_SKILL_REL))
        if not candidates:
            print("Could not find yichen-wechat-local-vault in cloned repo.")
            return
        skill_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(candidates[0], skill_dir)
        print(f"Installed vault skill: {skill_dir}")


def install_python_env(target: Path, skip_install: bool) -> None:
    venv_python = target / "work/.venv-wechat-vault/bin/python"
    if not venv_python.exists():
        run(["python3", "-m", "venv", str(target / "work/.venv-wechat-vault")])
    if not skip_install:
        run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "pycryptodome"])


def npm_install(target: Path, skip_install: bool) -> None:
    if skip_install:
        return
    if not shutil.which("npm"):
        print("npm not found; install Node.js, then run npm install in the target folder.")
        return
    run(["npm", "install"], cwd=target)


def create_files(target: Path, base_url: str, model: str) -> None:
    package = {
        "name": target.name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "main": "electron/main.cjs",
        "scripts": {
            "dev": "concurrently -k \"npm:dev:renderer\" \"npm:dev:electron\"",
            "dev:renderer": "vite --host 127.0.0.1",
            "dev:electron": "wait-on tcp:127.0.0.1:5173 && electron .",
            "build": "vite build"
        },
        "dependencies": {
            "@vitejs/plugin-react": "^4.3.4",
            "concurrently": "^9.2.1",
            "electron": "30.5.1",
            "vite": "^5.4.21",
            "wait-on": "^8.0.5",
            "react": "^18.3.1",
            "react-dom": "^18.3.1"
        },
        "devDependencies": {}
    }
    write(target / "package.json", json.dumps(package, ensure_ascii=False, indent=2))
    write(target / "index.html", """<div id="root"></div><script type="module" src="/src/main.jsx"></script>
""")
    write(target / "wechat-agent-tool/wechat_agent_cli.py", WECHAT_AGENT_CLI)
    write(target / "electron/preload.cjs", PRELOAD_CJS)
    write(target / "electron/main.cjs", ELECTRON_MAIN_CJS)
    write(target / "src/main.jsx", SRC_MAIN_JSX)
    write(target / "src/App.jsx", SRC_APP_JSX.replace("__DEFAULT_BASE_URL__", base_url).replace("__DEFAULT_MODEL__", model))
    write(target / "src/styles.css", SRC_STYLES_CSS)
    write(target / ".gitignore", "node_modules\ndist\nwork\n.DS_Store\n")


WECHAT_AGENT_CLI = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path.home() / ".codex/skills/yichen-wechat-local-vault"
VAULT_CLI = SKILL_DIR / "scripts/vault_cli.py"
LOCAL_VENV_PYTHON = Path(__file__).resolve().parents[1] / "work/.venv-wechat-vault/bin/python"


class VaultCommandError(RuntimeError):
    pass


def python_bin() -> str:
    return str(LOCAL_VENV_PYTHON) if LOCAL_VENV_PYTHON.exists() else sys.executable


def build_vault_command(action: str, **kwargs: Any) -> list[str]:
    command = [python_bin(), str(VAULT_CLI)]
    if action == "status":
        return command + ["status", "--format", "json"]
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
        command.extend(["--format", "json"])
        return command
    raise ValueError(f"unknown action: {action}")


def run_vault(command: list[str]) -> dict[str, Any]:
    if not VAULT_CLI.exists():
        raise VaultCommandError(f"vault_cli.py not found: {VAULT_CLI}")
    completed = subprocess.run(command, capture_output=True, text=True)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        raise VaultCommandError(stderr or stdout or f"exit code {completed.returncode}")
    if not stdout:
        return {"ok": True}
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {"text": stdout}
    return parsed if isinstance(parsed, dict) else {"items": parsed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read local decrypted WeChat vault as JSON.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    chats = sub.add_parser("chats")
    chats.add_argument("--query", default="")
    chats.add_argument("--limit", type=int, default=50)
    messages = sub.add_parser("messages")
    messages.add_argument("--chat", required=True)
    messages.add_argument("--limit", type=int, default=1000)
    messages.add_argument("--offset", type=int, default=0)
    messages.add_argument("--start", default="")
    messages.add_argument("--end", default="")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run_vault(build_vault_command(args.command, **{k: v for k, v in vars(args).items() if k != "command"})), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


PRELOAD_CJS = r'''const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("wechatAgent", {
  getStorageDirectory: () => ipcRenderer.invoke("wechat:getStorageDirectory"),
  importChat: (chatName, start, end) => ipcRenderer.invoke("wechat:importChat", chatName, start, end),
  loadGroups: () => ipcRenderer.invoke("wechat:loadGroups"),
  loadGroup: (id) => ipcRenderer.invoke("wechat:loadGroup", id),
  ask: (analysis, question, settings) => ipcRenderer.invoke("wechat:ask", analysis, question, settings)
});
'''


ELECTRON_MAIN_CJS = r'''const { app, BrowserWindow, ipcMain } = require("electron");
const { execFile } = require("node:child_process");
const fs = require("node:fs/promises");
const path = require("node:path");

const isDev = Boolean(process.env.VITE_DEV_SERVER_URL);
const root = process.cwd();
const agentCli = path.join(root, "wechat-agent-tool", "wechat_agent_cli.py");
const venvPython = path.join(root, "work", ".venv-wechat-vault", "bin", "python");
const vaultRefresh = path.join(app.getPath("home"), ".codex", "skills", "yichen-wechat-local-vault", "scripts", "decrypt_all_dbs.py");

function run(command, args, timeout = 180000) {
  return new Promise((resolve, reject) => {
    execFile(command, args, { timeout, maxBuffer: 1024 * 1024 * 30 }, (error, stdout, stderr) => {
      if (error) {
        error.message = stderr || stdout || error.message;
        reject(error);
        return;
      }
      resolve(stdout);
    });
  });
}

function groupsDir() {
  return path.join(app.getPath("userData"), "wechat-groups");
}

function safeId(name) {
  return (name || "wechat-group").trim().replace(/[^\u4e00-\u9fa5a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48) || `wechat-${Date.now()}`;
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 820,
    webPreferences: { preload: path.join(__dirname, "preload.cjs") }
  });
  if (isDev) await win.loadURL(process.env.VITE_DEV_SERVER_URL);
  else await win.loadFile(path.join(root, "dist", "index.html"));
}

function toMessages(payload) {
  const rows = payload.messages || payload.items || payload.results || [];
  return rows.map((item) => ({
    speaker: String(item.sender || item.sender_username || "未知成员").trim(),
    content: String(item.content || "").trim(),
    timestamp: String(item.time || item.timestamp || "").trim()
  })).filter((m) => m.speaker && m.content).sort((a, b) => (a.timestamp || "").localeCompare(b.timestamp || ""));
}

function analyze(messages, sourceName) {
  const bySpeaker = new Map();
  for (const message of messages) bySpeaker.set(message.speaker, [...(bySpeaker.get(message.speaker) || []), message]);
  const topMembers = [...bySpeaker.entries()].map(([name, rows]) => ({
    name,
    messageCount: rows.length,
    percent: messages.length ? Math.round(rows.length / messages.length * 1000) / 10 : 0,
    keywords: [...String(rows.map((m) => m.content).join("\n")).matchAll(/[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9_]{3,}/g)].slice(0, 8).map((m) => m[0])
  })).sort((a, b) => b.messageCount - a.messageCount);
  const times = messages.map((m) => m.timestamp).filter(Boolean);
  return {
    sourceName,
    totalMessages: messages.length,
    memberCount: bySpeaker.size,
    timeRange: times.length ? `${times[0]} - ${times[times.length - 1]}` : "未识别时间",
    topMembers,
    messages
  };
}

function modelInput(analysis, question) {
  const top = analysis.topMembers.slice(0, 12).map((m, i) => `${i + 1}. ${m.name}: ${m.messageCount} 条，占 ${m.percent}%`).join("\n");
  const line = (m) => `${m.timestamp ? `[${m.timestamp}] ` : ""}${m.speaker}: ${m.content}`.slice(0, 500);
  const recent = analysis.messages.slice(-180).map(line).join("\n").slice(-26000);
  const payments = analysis.messages.filter((m) => /红包|转账|收款|付款|支付|金额|￥|¥|打麻|麻将|输|赢/.test(m.content)).slice(-120).map(line).join("\n").slice(-18000);
  return [
    "系统要求：你是严谨的微信群聊天记录分析助手。只能基于提供的聊天上下文回答，不要编造。证据不足时直接说明。",
    "",
    `群聊数据：${analysis.sourceName}`,
    `消息数：${analysis.totalMessages}`,
    `成员数：${analysis.memberCount}`,
    `时间范围：${analysis.timeRange}`,
    "",
    "发言排行：",
    top || "暂无",
    "",
    "最近聊天记录：",
    recent || "暂无",
    "",
    "红包/转账/收款相关记录：",
    payments || "暂无",
    "",
    `用户问题：${question}`
  ].join("\n");
}

async function fallbackAnswer(analysis, question) {
  if (/红包|转账|收款|付款|支付|金额|输赢|谁赢|赢了多少|输了多少/.test(question)) {
    const evidence = analysis.messages.filter((m) => /红包|转账|收款|付款|支付|金额|￥|¥|打麻|麻将|输|赢/.test(m.content)).slice(-40);
    if (!evidence.length) return "当前导入数据里没有识别到明确的红包、转账、收款或支付记录。";
    return ["找到这些交易或输赢相关证据：", ...evidence.map((m) => `${m.timestamp ? `[${m.timestamp}] ` : ""}${m.speaker}: ${m.content}`)].join("\n");
  }
  return `已导入 ${analysis.totalMessages} 条消息，成员 ${analysis.memberCount} 位。最活跃成员：${analysis.topMembers.slice(0, 5).map((m) => `${m.name}(${m.messageCount})`).join("、") || "暂无"}`;
}

ipcMain.handle("wechat:getStorageDirectory", async () => {
  await fs.mkdir(groupsDir(), { recursive: true });
  return groupsDir();
});

ipcMain.handle("wechat:loadGroups", async () => {
  await fs.mkdir(groupsDir(), { recursive: true });
  const files = (await fs.readdir(groupsDir())).filter((file) => file.endsWith(".json"));
  const rows = [];
  for (const file of files) {
    try {
      const data = JSON.parse(await fs.readFile(path.join(groupsDir(), file), "utf-8"));
      rows.push({ id: data.id, name: data.name, totalMessages: data.analysis.totalMessages, updatedAt: data.updatedAt, storagePath: data.storagePath });
    } catch {}
  }
  return rows.sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
});

ipcMain.handle("wechat:loadGroup", async (_event, id) => {
  try {
    return JSON.parse(await fs.readFile(path.join(groupsDir(), `${id}.json`), "utf-8"));
  } catch {
    return null;
  }
});

ipcMain.handle("wechat:importChat", async (_event, chatName, start, end) => {
  const name = String(chatName || "").trim();
  if (!name) return { ok: false, message: "请先填写微信群名称。" };
  await run(venvPython, [vaultRefresh, "--mode", "incremental"], 300000);
  const all = [];
  const page = 1000;
  for (let offset = 0; offset < 50000; offset += page) {
    const args = [agentCli, "messages", "--chat", name, "--limit", String(page), "--offset", String(offset)];
    if (start) args.push("--start", start);
    if (end) args.push("--end", end);
    const payload = JSON.parse(await run("python3", args));
    const rows = toMessages(payload);
    all.push(...rows);
    if (rows.length < page) break;
  }
  const analysis = analyze(all, `wechat-agent-tool:${name}`);
  const id = safeId(name);
  const storagePath = path.join(groupsDir(), `${id}.json`);
  const profile = { id, name, analysis, updatedAt: new Date().toLocaleString("zh-CN", { hour12: false }), storagePath };
  await fs.mkdir(groupsDir(), { recursive: true });
  await fs.writeFile(storagePath, JSON.stringify(profile, null, 2), "utf-8");
  return { ok: true, message: `已导入「${name}」：${analysis.totalMessages} 条消息，${analysis.memberCount} 位成员。`, group: profile, analysis };
});

ipcMain.handle("wechat:ask", async (_event, analysis, question, settings) => {
  const q = String(question || "").trim();
  if (!analysis || !q) return { ok: false, message: "请先导入数据并输入问题。" };
  if (!settings?.apiKey || !settings?.apiBaseUrl || !settings?.modelName) {
    return { ok: true, message: await fallbackAnswer(analysis, q) };
  }
  const base = String(settings.apiBaseUrl).trim().replace(/\/+$/, "");
  const url = base.endsWith("/responses") ? base : base.endsWith("/v1") ? `${base}/responses` : `${base}/v1/responses`;
  const res = await fetch(url, {
    method: "POST",
    headers: { authorization: `Bearer ${settings.apiKey}`, "content-type": "application/json" },
    body: JSON.stringify({ model: settings.modelName, input: modelInput(analysis, q) })
  });
  if (!res.ok) return { ok: true, message: `模型请求失败：HTTP ${res.status}\n\n本地规则回答：\n${await fallbackAnswer(analysis, q)}` };
  const data = await res.json();
  const text = data.output_text || (data.output || []).flatMap((o) => o.content || []).map((c) => c.text || "").join("") || data.choices?.[0]?.message?.content || "";
  return { ok: true, message: text ? `【助理】\n${text}` : await fallbackAnswer(analysis, q) };
});

app.whenReady().then(createWindow);
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
'''


SRC_MAIN_JSX = r'''import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
'''


SRC_APP_JSX = r'''import { useEffect, useState } from "react";

const defaultSettings = {
  apiBaseUrl: "__DEFAULT_BASE_URL__",
  modelName: "__DEFAULT_MODEL__",
  apiKey: ""
};

function loadSettings() {
  try {
    return { ...defaultSettings, ...JSON.parse(localStorage.getItem("wechat-agent-settings") || "{}") };
  } catch {
    return defaultSettings;
  }
}

export function App() {
  const [settings, setSettings] = useState(loadSettings);
  const [groupName, setGroupName] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [groups, setGroups] = useState([]);
  const [storage, setStorage] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([{ role: "assistant", content: "填写群名和时间范围后导入本机微信 vault，然后直接提问。" }]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    window.wechatAgent.getStorageDirectory().then(setStorage);
    window.wechatAgent.loadGroups().then(setGroups);
  }, []);

  function saveSettings(next) {
    setSettings(next);
    localStorage.setItem("wechat-agent-settings", JSON.stringify(next));
  }

  async function importChat() {
    setBusy(true);
    setMessages((rows) => [...rows, { role: "assistant", content: `正在刷新本地 Vault 并导入「${groupName}」...` }]);
    try {
      const result = await window.wechatAgent.importChat(groupName, start, end);
      if (result.analysis) setAnalysis(result.analysis);
      setMessages((rows) => [...rows, { role: "assistant", content: result.message }]);
      setGroups(await window.wechatAgent.loadGroups());
    } catch (error) {
      setMessages((rows) => [...rows, { role: "assistant", content: `导入失败：${String(error)}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    if (!question.trim()) return;
    const q = question.trim();
    setQuestion("");
    setMessages((rows) => [...rows, { role: "user", content: q }]);
    const result = await window.wechatAgent.ask(analysis, q, settings);
    setMessages((rows) => [...rows, { role: "assistant", content: result.message }]);
  }

  return (
    <main>
      <section className="toolbar">
        <h1>微信群历史分析智能体</h1>
        <span>{analysis ? `${analysis.totalMessages} 条消息 · ${analysis.memberCount} 位成员` : "等待导入"}</span>
      </section>

      <section className="panel import-panel">
        <label>群名称<input value={groupName} onChange={(e) => setGroupName(e.target.value)} placeholder="输入微信群名称" /></label>
        <label>开始时间<input type="date" value={start} onChange={(e) => setStart(e.target.value)} /></label>
        <label>结束时间<input type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></label>
        <button onClick={importChat} disabled={busy || !groupName.trim()}>{busy ? "导入中" : "导入数据"}</button>
      </section>

      <section className="panel settings">
        <label>Base URL<input value={settings.apiBaseUrl} onChange={(e) => saveSettings({ ...settings, apiBaseUrl: e.target.value })} /></label>
        <label>模型<input value={settings.modelName} onChange={(e) => saveSettings({ ...settings, modelName: e.target.value })} /></label>
        <label>API Key<input type="password" value={settings.apiKey} onChange={(e) => saveSettings({ ...settings, apiKey: e.target.value })} placeholder="本机保存" /></label>
      </section>

      <section className="grid">
        <aside className="panel">
          <h2>本机存储</h2>
          <p className="path">{storage}</p>
          <h2>已导入群</h2>
          {groups.map((group) => <button className="group" key={group.id} onClick={async () => {
            const profile = await window.wechatAgent.loadGroup(group.id);
            if (profile?.analysis) setAnalysis(profile.analysis);
          }}>{group.name}<small>{group.totalMessages} 条</small></button>)}
        </aside>

        <section className="panel chat">
          <div className="chat-list">
            {messages.map((message, index) => <div key={index} className={message.role}>{message.content}</div>)}
          </div>
          <div className="ask">
            <input value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} placeholder={analysis ? "问：谁最活跃 / 8月16日谁转账了多少钱" : "先导入群聊"} />
            <button onClick={ask} disabled={!analysis || !question.trim()}>发送</button>
          </div>
        </section>
      </section>
    </main>
  );
}
'''


SRC_STYLES_CSS = r'''* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fb; color: #263244; }
main { width: min(1180px, calc(100vw - 36px)); margin: 24px auto; }
.toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
h1 { margin: 0; font-size: 26px; }
h2 { font-size: 15px; margin: 0 0 10px; }
.panel { background: #fff; border: 1px solid #dce4f0; border-radius: 8px; padding: 16px; box-shadow: 0 10px 30px rgba(31, 45, 68, .06); }
.import-panel, .settings { display: grid; grid-template-columns: 1.4fr 160px 160px 120px; gap: 12px; align-items: end; margin-bottom: 12px; }
.settings { grid-template-columns: 1fr 180px 260px; }
label { display: grid; gap: 6px; font-size: 13px; font-weight: 650; color: #46556d; }
input { height: 40px; border: 1px solid #cdd8e6; border-radius: 6px; padding: 0 12px; font: inherit; background: #fff; }
button { height: 40px; border: 0; border-radius: 6px; background: #2859d6; color: #fff; font-weight: 700; cursor: pointer; }
button:disabled { background: #aab5c5; cursor: not-allowed; }
.grid { display: grid; grid-template-columns: 300px 1fr; gap: 12px; }
.path { word-break: break-all; font-size: 12px; color: #6c7a90; }
.group { width: 100%; display: flex; justify-content: space-between; align-items: center; margin: 8px 0; background: #edf3ff; color: #263244; }
.group small { color: #6c7a90; }
.chat { min-height: 520px; display: grid; grid-template-rows: 1fr auto; }
.chat-list { overflow: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px; white-space: pre-wrap; }
.assistant, .user { max-width: 86%; padding: 12px 14px; border-radius: 8px; line-height: 1.55; }
.assistant { align-self: flex-start; background: #eef3f8; }
.user { align-self: flex-end; background: #2859d6; color: #fff; }
.ask { display: grid; grid-template-columns: 1fr 92px; gap: 10px; margin-top: 12px; }
@media (max-width: 860px) {
  .import-panel, .settings, .grid { grid-template-columns: 1fr; }
}
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a standalone WeChat analysis desktop app.")
    parser.add_argument("--target", required=True, help="Target directory for the generated app.")
    parser.add_argument("--base-url", default="https://ap1.upit.top/51Token/v1")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--force", action="store_true", help="Allow overwriting generated files in a non-empty target.")
    parser.add_argument("--skip-install", action="store_true", help="Write files only; skip npm and pip install.")
    parser.add_argument("--skip-vault-skill-install", action="store_true", help="Do not attempt to install yichen-wechat-local-vault.")
    args = parser.parse_args(argv)

    if sys.platform != "darwin":
        print("Warning: this app is designed for macOS WeChat local data.")

    target = Path(args.target).expanduser().resolve()
    ensure_empty_or_allowed(target, args.force)
    create_files(target, args.base_url, args.model)
    os.chmod(target / "wechat-agent-tool/wechat_agent_cli.py", 0o755)
    ensure_vault_skill(args.skip_vault_skill_install)
    install_python_env(target, args.skip_install)
    npm_install(target, args.skip_install)

    print("\nDone.")
    print(f"App directory: {target}")
    print("Start it with:")
    print(f"  cd {target}")
    print("  npm run dev")
    print("\nIf vault is not configured yet, use yichen-wechat-local-vault on that computer first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
