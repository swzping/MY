import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";
import type { WechatMessage } from "./wechatAnalysis.js";

const execFileAsync = promisify(execFile);

const PROJECT_VAULT_PYTHON = path.join(process.cwd(), "work", ".venv-wechat-vault", "bin", "python");
const WECHAT_VAULT_PYTHON = process.env.WECHAT_VAULT_PYTHON || (existsSync(PROJECT_VAULT_PYTHON) ? PROJECT_VAULT_PYTHON : "python3");
const AGENT_TOOL_PATH =
  process.env.WECHAT_AGENT_TOOL_PATH ||
  path.join(process.cwd(), "wechat-agent-tool", "wechat_agent_cli.py");
const WECHAT_VAULT_REFRESH_SCRIPT =
  process.env.WECHAT_VAULT_REFRESH_SCRIPT ||
  path.join(process.env.HOME || "", ".codex", "skills", "yichen-wechat-local-vault", "scripts", "decrypt_all_dbs.py");

export function getWechatAgentToolPath() {
  return AGENT_TOOL_PATH;
}

export function buildWechatVaultRefreshCommand() {
  return [WECHAT_VAULT_PYTHON, WECHAT_VAULT_REFRESH_SCRIPT, "--mode", "incremental"];
}

type AgentMessageRecord = {
  sender?: unknown;
  sender_username?: unknown;
  time?: unknown;
  timestamp?: unknown;
  content?: unknown;
};

type AgentContactRecord = {
  username?: unknown;
  display_name?: unknown;
  nick_name?: unknown;
  remark?: unknown;
};

function asArray(value: unknown): AgentMessageRecord[] {
  if (!value || typeof value !== "object") return [];
  const record = value as Record<string, unknown>;
  const items = record.messages ?? record.items ?? record.results;
  return Array.isArray(items) ? (items as AgentMessageRecord[]) : [];
}

function asContacts(value: unknown): AgentContactRecord[] {
  if (!value || typeof value !== "object") return [];
  const record = value as Record<string, unknown>;
  const items = record.contacts ?? record.items ?? record.results;
  return Array.isArray(items) ? (items as AgentContactRecord[]) : [];
}

function normalizeSender(value: unknown, fallback: unknown) {
  const sender = String(value || fallback || "未知成员").trim();
  return sender || "未知成员";
}

function normalizeContent(value: unknown) {
  return String(value ?? "").replace(/\r\n/g, "\n").trim();
}

function toWechatMessages(payload: unknown): WechatMessage[] {
  return asArray(payload)
    .map((message) => ({
      speaker: normalizeSender(message.sender, message.sender_username),
      content: normalizeContent(message.content),
      timestamp: String(message.time ?? message.timestamp ?? "").trim()
    }))
    .filter((message) => message.speaker && message.content);
}

function sortMessagesByTimestamp(messages: WechatMessage[]) {
  return [...messages].sort((a, b) => {
    if (!a.timestamp || !b.timestamp) return 0;
    return a.timestamp.localeCompare(b.timestamp);
  });
}

async function runAgentTool(args: string[]) {
  try {
    const { stdout } = await execFileAsync("python3", [AGENT_TOOL_PATH, ...args], {
      maxBuffer: 1024 * 1024 * 20,
      timeout: 120000
    });
    return JSON.parse(stdout || "{}") as Record<string, unknown>;
  } catch (error) {
    const detail = parseAgentToolError(error);
    throw new Error(detail);
  }
}

export async function refreshWechatVault() {
  const command = buildWechatVaultRefreshCommand();
  try {
    await execFileAsync(command[0], command.slice(1), {
      maxBuffer: 1024 * 1024 * 20,
      timeout: 300000
    });
  } catch (error) {
    const detail = parseAgentToolError(error);
    throw new Error(`刷新微信本地 Vault 失败：${detail}`);
  }
}

export function parseAgentToolError(error: unknown) {
  const record = error as { stdout?: string; stderr?: string; message?: string };
  for (const text of [record.stdout, record.stderr]) {
    if (!text?.trim()) continue;
    try {
      const parsed = JSON.parse(text) as Record<string, unknown>;
      return String(parsed.error ?? parsed.message ?? text).trim();
    } catch {
      return text.trim();
    }
  }
  return record.message ?? String(error);
}

export function buildWechatAgentMessagesArgs(chatName: string, limit: number, offset: number, start = "", end = "") {
  const args = ["messages", "--chat", chatName, "--limit", String(limit)];
  if (offset) args.push("--offset", String(offset));
  if (start) args.push("--start", start);
  if (end) args.push("--end", end);
  return args;
}

export function buildChatSearchQueries(chatName: string) {
  const queries = new Set<string>();
  const compact = chatName.replace(/\s+/g, "").trim();
  if (compact) queries.add(compact);
  if (compact.includes("锦江")) queries.add("锦江");
  const withoutCommonSuffix = compact.replace(/老板群|业主群|装修群|沟通群|服务群|群$/g, "");
  if (withoutCommonSuffix.length >= 2) queries.add(withoutCommonSuffix);
  return Array.from(queries);
}

function contactName(contact: AgentContactRecord) {
  return String(contact.display_name || contact.remark || contact.nick_name || contact.username || "").trim();
}

function editDistance(left: string, right: string) {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let i = 1; i <= left.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= right.length; j += 1) {
      current[j] = Math.min(
        current[j - 1] + 1,
        previous[j] + 1,
        previous[j - 1] + (left[i - 1] === right[j - 1] ? 0 : 1)
      );
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[right.length];
}

export function pickBestChatCandidate(chatName: string, contacts: AgentContactRecord[]) {
  const normalizedInput = chatName.replace(/\s+/g, "");
  return contacts
    .map((contact) => {
      const name = contactName(contact);
      return { name, distance: editDistance(normalizedInput, name.replace(/\s+/g, "")) };
    })
    .filter((candidate) => candidate.name)
    .sort((a, b) => a.distance - b.distance)[0];
}

async function suggestChatNames(chatName: string) {
  const contacts: AgentContactRecord[] = [];
  for (const query of buildChatSearchQueries(chatName)) {
    const payload = await runAgentTool(["chats", "--query", query, "--limit", "10"]);
    contacts.push(...asContacts(payload));
    if (contacts.length) break;
  }
  return Array.from(new Set(contacts.map(contactName).filter(Boolean)));
}

async function resolveChatName(chatName: string) {
  const suggestions = await suggestChatNames(chatName);
  const best = pickBestChatCandidate(chatName, suggestions.map((name) => ({ display_name: name })));
  if (best && best.distance <= 2) return best.name;
  return chatName;
}

export async function readWechatAgentMessages(chatName: string, limit = 1000, start = "", end = "") {
  const resolvedChatName = await resolveChatName(chatName);
  const hasTimeRange = Boolean(start || end);
  if (!hasTimeRange) {
    const payload = await runAgentTool(buildWechatAgentMessagesArgs(resolvedChatName, limit, 0));
    return sortMessagesByTimestamp(toWechatMessages(payload));
  }

  const pageSize = 1000;
  const maxMessages = Math.max(limit, 50000);
  const allMessages: WechatMessage[] = [];

  for (let offset = 0; offset < maxMessages; offset += pageSize) {
    const payload = await runAgentTool(buildWechatAgentMessagesArgs(resolvedChatName, pageSize, offset, start, end));
    const pageMessages = toWechatMessages(payload);
    allMessages.push(...pageMessages);
    if (pageMessages.length < pageSize) break;
  }

  return sortMessagesByTimestamp(allMessages);
}

export async function getWechatAgentStatus() {
  return runAgentTool(["status"]);
}
