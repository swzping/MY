/// <reference types="vite/client" />

type AgentSettings = {
  licenseKey: string;
  modelProvider: "openai" | "deepseek" | "qwen" | "local";
  modelName: string;
  apiKey: string;
  apiBaseUrl: string;
  downloadPath: string;
  autoStartTasks: boolean;
  maskSensitiveFields: boolean;
};

type ElectronFileFilter = {
  name: string;
  extensions: string[];
};

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

type WechatMessageRecord = {
  speaker: string;
  content: string;
  timestamp?: string;
};

type WechatMemberStats = {
  name: string;
  messageCount: number;
  percent: number;
  keywords: string[];
  activeHours: string[];
  sampleMessages: string[];
  interactions: { name: string; count: number }[];
  tone: string;
};

type WechatAnalysis = {
  sourceName: string;
  totalMessages: number;
  memberCount: number;
  timeRange: string;
  topMembers: WechatMemberStats[];
  messages: WechatMessageRecord[];
};

type WechatImportResult = {
  ok: boolean;
  message: string;
  analysis?: WechatAnalysis;
  group?: WechatGroupProfile;
};

type WechatQuestionResult = {
  ok: boolean;
  message: string;
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

interface Window {
  shouwang: {
    loadSettings: () => Promise<AgentSettings>;
    saveSettings: (settings: AgentSettings) => Promise<AgentSettings>;
    selectDirectory: () => Promise<string | null>;
    selectFiles: (filters?: ElectronFileFilter[]) => Promise<string[]>;
    openPath: (targetPath: string) => Promise<string>;
    inspectExcel: (filePath: string) => Promise<ExcelPreview>;
    applyExcelInstruction: (
      filePath: string,
      instruction: string,
      outputDirectory?: string
    ) => Promise<ExcelInstructionResult>;
    listWechatGroups: () => Promise<WechatGroupSummary[]>;
    loadWechatGroup: (groupId: string) => Promise<WechatGroupProfile | null>;
    getWechatStorageDirectory: () => Promise<string>;
    importWechatFile: (filePath: string, groupName?: string) => Promise<WechatImportResult>;
    importWechatText: (raw: string, sourceName: string, groupName?: string) => Promise<WechatImportResult>;
    getWechatAgentStatus: () => Promise<Record<string, unknown>>;
    importWechatAgentChat: (chatName: string, limit?: number, start?: string, end?: string) => Promise<WechatImportResult>;
    importWechatClipboard: (groupName?: string) => Promise<WechatImportResult>;
    askWechatQuestion: (analysis: WechatAnalysis, question: string, settings?: AgentSettings) => Promise<WechatQuestionResult>;
  };
}
