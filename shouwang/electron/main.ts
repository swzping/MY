import { app, BrowserWindow, clipboard, dialog, ipcMain, shell } from "electron";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import XLSX from "xlsx";
import {
  analyzeWechatMessages,
  answerWechatQuestion,
  readWechatMessagesFromFile,
  readWechatMessagesFromText,
  type WechatAnalysis,
  type WechatMessage
} from "./wechatAnalysis.js";
import { getWechatAgentStatus, readWechatAgentMessages, refreshWechatVault } from "./wechatAgentTool.js";
import { answerWechatWithModel } from "./modelClient.js";
import { DEFAULT_AGENT_SETTINGS, type SharedAgentSettings } from "../shared/defaultSettings.js";

type AgentSettings = SharedAgentSettings;

type ExcelPreview = {
  filePath: string;
  sheetName: string;
  columns: string[];
  rowCount: number;
  sampleRows: Record<string, unknown>[];
};

type ExcelInstructionResult = {
  ok: boolean;
  message: string;
  outputPath?: string;
  preview?: ExcelPreview;
};

type WechatImportResult = {
  ok: boolean;
  message: string;
  analysis?: WechatAnalysis;
  group?: WechatGroupProfile;
};

type WechatGroupSummary = {
  id: string;
  name: string;
  sourceName: string;
  totalMessages: number;
  memberCount: number;
  updatedAt: string;
  storagePath: string;
};

type WechatGroupProfile = WechatGroupSummary & {
  analysis: WechatAnalysis;
};

const defaultSettings = (): AgentSettings => ({
  ...DEFAULT_AGENT_SETTINGS,
  downloadPath: app.getPath("downloads")
});

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const isDev = Boolean(process.env.VITE_DEV_SERVER_URL);

const configPath = () => path.join(app.getPath("userData"), "settings.json");
const wechatGroupsDirectory = () => path.join(app.getPath("userData"), "wechat-groups");

async function readSettings(): Promise<AgentSettings> {
  try {
    const raw = await readFile(configPath(), "utf-8");
    return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch {
    return defaultSettings();
  }
}

async function saveSettings(settings: AgentSettings) {
  await mkdir(app.getPath("userData"), { recursive: true });
  await writeFile(configPath(), JSON.stringify(settings, null, 2), "utf-8");
  return settings;
}

function safeGroupId(name: string) {
  const normalized = name
    .trim()
    .replace(/[^\u4e00-\u9fa5a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  return normalized || `wechat-group-${Date.now()}`;
}

function groupStoragePath(groupId: string) {
  return path.join(wechatGroupsDirectory(), `${groupId}.json`);
}

async function saveWechatGroup(groupName: string, analysis: WechatAnalysis): Promise<WechatGroupProfile> {
  const name = groupName.trim() || analysis.sourceName.replace(/\.[^.]+$/, "") || "未命名微信群";
  const id = safeGroupId(name);
  const storagePath = groupStoragePath(id);
  const profile: WechatGroupProfile = {
    id,
    name,
    sourceName: analysis.sourceName,
    totalMessages: analysis.totalMessages,
    memberCount: analysis.memberCount,
    updatedAt: new Date().toLocaleString("zh-CN", { hour12: false }),
    storagePath,
    analysis
  };

  await mkdir(wechatGroupsDirectory(), { recursive: true });
  await writeFile(storagePath, JSON.stringify(profile, null, 2), "utf-8");
  return profile;
}

async function readWechatGroup(storagePath: string): Promise<WechatGroupProfile | null> {
  try {
    return JSON.parse(await readFile(storagePath, "utf-8")) as WechatGroupProfile;
  } catch {
    return null;
  }
}

async function listWechatGroups(): Promise<WechatGroupSummary[]> {
  await mkdir(wechatGroupsDirectory(), { recursive: true });
  const files = await readdir(wechatGroupsDirectory());
  const groups = await Promise.all(
    files
      .filter((file) => file.endsWith(".json"))
      .map((file) => readWechatGroup(path.join(wechatGroupsDirectory(), file)))
  );

  return groups
    .filter((group): group is WechatGroupProfile => Boolean(group))
    .map(({ analysis: _analysis, ...summary }) => summary)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

function readExcelPreview(filePath: string): ExcelPreview {
  const workbook = XLSX.readFile(filePath, { cellDates: true });
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: "" });
  const columns = rows.length
    ? Object.keys(rows[0])
    : (XLSX.utils.sheet_to_json<string[]>(sheet, { header: 1 })[0] ?? []).map(String);

  return {
    filePath,
    sheetName,
    columns,
    rowCount: rows.length,
    sampleRows: rows.slice(0, 8)
  };
}

function normalizeText(value: string) {
  return value.trim().toLowerCase();
}

function findColumn(columns: string[], instruction: string) {
  const normalizedInstruction = normalizeText(instruction);
  return columns.find((column) => normalizedInstruction.includes(normalizeText(column)));
}

async function applyExcelInstruction(filePath: string, instruction: string, outputDirectory?: string): Promise<ExcelInstructionResult> {
  const workbook = XLSX.readFile(filePath, { cellDates: true });
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  let rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: "" });
  const columns = rows.length
    ? Object.keys(rows[0])
    : (XLSX.utils.sheet_to_json<string[]>(sheet, { header: 1 })[0] ?? []).map(String);

  if (!rows.length) {
    return { ok: false, message: "这个 Excel 暂时没有可处理的数据行。" };
  }

  const normalized = normalizeText(instruction);
  let message = "";

  if (normalized.includes("删除") && (normalized.includes("空") || normalized.includes("为空"))) {
    const column = findColumn(columns, instruction);
    if (!column) {
      return { ok: false, message: `没有找到要判断为空的列。可用列：${columns.join("、")}` };
    }
    const before = rows.length;
    rows = rows.filter((row) => String(row[column] ?? "").trim() !== "");
    message = `已删除「${column}」为空的 ${before - rows.length} 行。`;
  } else if ((normalized.includes("汇总") || normalized.includes("分组")) && columns.length >= 2) {
    const groupColumn = findColumn(columns, instruction) ?? columns[0];
    const numericColumns = columns.filter((column) => rows.some((row) => typeof row[column] === "number" || Number(row[column]) === Number(row[column])));
    const sumColumn = numericColumns.find((column) => column !== groupColumn) ?? numericColumns[0];
    if (!sumColumn) {
      return { ok: false, message: "没有找到可以汇总的数字列。" };
    }
    const summary = new Map<string, number>();
    for (const row of rows) {
      const key = String(row[groupColumn] || "未填写");
      const amount = Number(row[sumColumn]) || 0;
      summary.set(key, (summary.get(key) ?? 0) + amount);
    }
    rows = Array.from(summary.entries()).map(([key, value]) => ({
      [groupColumn]: key,
      [`${sumColumn}汇总`]: value
    }));
    message = `已按「${groupColumn}」汇总「${sumColumn}」。`;
  } else if (normalized.includes("去重") || normalized.includes("重复")) {
    const column = findColumn(columns, instruction) ?? columns[0];
    const seen = new Set<string>();
    const before = rows.length;
    rows = rows.filter((row) => {
      const value = String(row[column] ?? "");
      if (seen.has(value)) return false;
      seen.add(value);
      return true;
    });
    message = `已按「${column}」去重，移除 ${before - rows.length} 行重复数据。`;
  } else {
    return {
      ok: false,
      message: "当前本地规则还不理解这条指令。可以先试：删除某列为空的行、按某列汇总、按某列去重。后续可接入模型 API 做更强的指令解析。"
    };
  }

  const outputDir = outputDirectory || app.getPath("downloads");
  await mkdir(outputDir, { recursive: true });
  const parsed = path.parse(filePath);
  const outputPath = path.join(outputDir, `${parsed.name}-智能处理-${Date.now()}.xlsx`);
  const newWorkbook = XLSX.utils.book_new();
  const newSheet = XLSX.utils.json_to_sheet(rows);
  XLSX.utils.book_append_sheet(newWorkbook, newSheet, "处理结果");
  XLSX.writeFile(newWorkbook, outputPath);

  return {
    ok: true,
    message,
    outputPath,
    preview: readExcelPreview(outputPath)
  };
}

async function importWechatMessages(messages: WechatMessage[], sourceName: string, groupName = ""): Promise<WechatImportResult> {
  if (!messages.length) {
    return {
      ok: false,
      message: "没有识别到聊天消息。支持格式示例：张三：今天开会吗，或 2026/08/17 10:30 张三：今天开会吗。"
    };
  }

  const analysis = analyzeWechatMessages(messages, sourceName);
  const group = await saveWechatGroup(groupName, analysis);
  return {
    ok: true,
    message: `已导入「${group.name}」：${analysis.totalMessages} 条消息，${analysis.memberCount} 位群友。`,
    analysis,
    group
  };
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1060,
    minHeight: 720,
    title: "守望智能体",
    backgroundColor: "#111827",
    show: false,
    titleBarStyle: "hiddenInset",
    trafficLightPosition: { x: 18, y: 18 },
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  win.once("ready-to-show", () => {
    win.show();
    win.focus();
  });

  if (isDev) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL!);
  } else {
    win.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(() => {
  ipcMain.handle("settings:load", readSettings);
  ipcMain.handle("settings:save", (_event, settings: AgentSettings) => saveSettings(settings));
  ipcMain.handle("dialog:selectDirectory", async () => {
    const result = await dialog.showOpenDialog({ properties: ["openDirectory", "createDirectory"] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle("dialog:selectFiles", async (_event, filters?: Electron.FileFilter[]) => {
    const result = await dialog.showOpenDialog({
      properties: ["openFile", "multiSelections"],
      filters
    });
    return result.canceled ? [] : result.filePaths;
  });
  ipcMain.handle("shell:openPath", (_event, targetPath: string) => shell.openPath(targetPath));
  ipcMain.handle("excel:inspect", (_event, filePath: string) => readExcelPreview(filePath));
  ipcMain.handle("excel:applyInstruction", (_event, filePath: string, instruction: string, outputDirectory?: string) =>
    applyExcelInstruction(filePath, instruction, outputDirectory)
  );
  ipcMain.handle("wechat:listGroups", listWechatGroups);
  ipcMain.handle("wechat:loadGroup", async (_event, groupId: string) => readWechatGroup(groupStoragePath(groupId)));
  ipcMain.handle("wechat:getStorageDirectory", async () => {
    await mkdir(wechatGroupsDirectory(), { recursive: true });
    return wechatGroupsDirectory();
  });
  ipcMain.handle("wechat:importFile", async (_event, filePath: string, groupName?: string) => {
    const messages = await readWechatMessagesFromFile(filePath);
    return importWechatMessages(messages, path.basename(filePath), groupName);
  });
  ipcMain.handle("wechat:importText", async (_event, raw: string, sourceName: string, groupName?: string) =>
    importWechatMessages(raw ? readWechatMessagesFromText(raw) : [], sourceName || "文本聊天记录", groupName)
  );
  ipcMain.handle("wechat:agentStatus", getWechatAgentStatus);
  ipcMain.handle("wechat:importAgentChat", async (_event, chatName: string, limit?: number, start?: string, end?: string) => {
    const name = chatName.trim();
    if (!name) {
      return {
        ok: false,
        message: "请先填写要导入的微信群名称。"
      };
    }
    await refreshWechatVault();
    const messages = await readWechatAgentMessages(name, limit || 1000, start || "", end || "");
    return importWechatMessages(messages, `wechat-agent-tool:${name}`, name);
  });
  ipcMain.handle("wechat:importClipboard", async (_event, groupName?: string) => {
    const text = clipboard.readText();
    return importWechatMessages(text ? readWechatMessagesFromText(text) : [], "剪贴板聊天记录", groupName);
  });
  ipcMain.handle("wechat:ask", async (_event, analysis: WechatAnalysis, question: string, providedSettings?: AgentSettings) => {
    const settings = { ...(await readSettings()), ...(providedSettings ?? {}) };
    if (settings.apiKey.trim() && settings.apiBaseUrl.trim() && settings.modelName.trim()) {
      const modelAnswer = await answerWechatWithModel(analysis, question, settings);
      if (modelAnswer.ok) return modelAnswer;
      const fallback = answerWechatQuestion(analysis, question);
      return {
        ok: fallback.ok,
        message: `${modelAnswer.message}\n\n已临时使用本地规则回答：\n${fallback.message}`
      };
    }
    return answerWechatQuestion(analysis, question);
  });

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
