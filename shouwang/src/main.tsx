import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";
import { analyzeWechatForBrowser, answerWechatForBrowser, parseWechatTextForBrowser } from "./wechatBrowserAnalysis";
import { DEFAULT_AGENT_SETTINGS } from "../shared/defaultSettings";
import { answerWechatWithModel } from "../shared/wechatModelClient";

if (!window.shouwang) {
  const bridgeMessage = navigator.userAgent.includes("Electron")
    ? "Electron 桌面桥接未加载，请重启应用或检查 preload 配置"
    : "浏览器预览模式不能扫描本机文件，请使用 Electron 桌面窗口";

  window.shouwang = {
    loadSettings: async () => DEFAULT_AGENT_SETTINGS,
    saveSettings: async (settings) => settings,
    selectDirectory: async () => "",
    selectFiles: async () => [],
    openPath: async () => "",
    inspectExcel: async (filePath) => ({
      filePath,
      sheetName: "Sheet1",
      columns: ["客户", "销售额", "日期"],
      rowCount: 0,
      sampleRows: []
    }),
    applyExcelInstruction: async () => ({
      ok: false,
      message: "浏览器预览模式无法直接修改本地文件，请在 Electron 中运行。"
    }),
    listWechatGroups: async () => [],
    loadWechatGroup: async () => null,
    getWechatStorageDirectory: async () => bridgeMessage,
    importWechatFile: async () => ({
      ok: false,
      message: "浏览器预览模式无法读取本地聊天文件，请在 Electron 中运行。"
    }),
    importWechatText: async (raw, sourceName, groupName) => {
      const messages = parseWechatTextForBrowser(raw);
      if (!messages.length) {
        return {
          ok: false,
          message: "没有识别到聊天消息。支持：张三：今天开会吗，或 JSON/CSV 导出的聊天记录。"
        };
      }
      const analysis = analyzeWechatForBrowser(messages, sourceName || "浏览器导入");
      const name = groupName?.trim() || analysis.sourceName.replace(/\.[^.]+$/, "") || "未命名聊天数据";
      return {
        ok: true,
        message: `已导入「${name}」：${analysis.totalMessages} 条消息，${analysis.memberCount} 位成员。`,
        analysis,
        group: {
          id: `browser-${Date.now()}`,
          name,
          sourceName: analysis.sourceName,
          totalMessages: analysis.totalMessages,
          memberCount: analysis.memberCount,
          updatedAt: new Date().toLocaleString("zh-CN", { hour12: false }),
          storagePath: "浏览器预览模式：数据仅保存在当前页面内存中",
          analysis
        }
      };
    },
    getWechatAgentStatus: async () => ({
      ok: false,
      error: "浏览器预览模式不能调用本机 Python CLI，请使用 Electron 桌面窗口。"
    }),
    importWechatAgentChat: async () => ({
      ok: false,
      message: "浏览器预览模式不能调用 wechat-agent-tool。网页里请直接导入 md/txt/json/csv 文件。"
    }),
    importWechatClipboard: async () => ({
      ok: false,
      message: "浏览器预览模式无法读取系统剪贴板，请在 Electron 中运行。"
    }),
    askWechatQuestion: async (analysis, question, settings) => {
      const nextSettings = settings ?? DEFAULT_AGENT_SETTINGS;
      if (nextSettings.apiKey.trim() && nextSettings.apiBaseUrl.trim() && nextSettings.modelName.trim()) {
        const modelAnswer = await answerWechatWithModel(analysis, question, nextSettings);
        if (modelAnswer.ok) return modelAnswer;
        const fallback = answerWechatForBrowser(analysis, question);
        return {
          ok: fallback.ok,
          message: `${modelAnswer.message}\n\n已临时使用本地规则回答：\n${fallback.message}`
        };
      }
      return answerWechatForBrowser(analysis, question);
    }
  };
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
