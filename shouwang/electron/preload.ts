import { contextBridge, ipcRenderer } from "electron";

const api = {
  loadSettings: () => ipcRenderer.invoke("settings:load"),
  saveSettings: (settings: unknown) => ipcRenderer.invoke("settings:save", settings),
  selectDirectory: () => ipcRenderer.invoke("dialog:selectDirectory"),
  selectFiles: (filters?: Electron.FileFilter[]) => ipcRenderer.invoke("dialog:selectFiles", filters),
  openPath: (targetPath: string) => ipcRenderer.invoke("shell:openPath", targetPath),
  inspectExcel: (filePath: string) => ipcRenderer.invoke("excel:inspect", filePath),
  applyExcelInstruction: (filePath: string, instruction: string, outputDirectory?: string) =>
    ipcRenderer.invoke("excel:applyInstruction", filePath, instruction, outputDirectory),
  listWechatGroups: () => ipcRenderer.invoke("wechat:listGroups"),
  loadWechatGroup: (groupId: string) => ipcRenderer.invoke("wechat:loadGroup", groupId),
  getWechatStorageDirectory: () => ipcRenderer.invoke("wechat:getStorageDirectory"),
  importWechatFile: (filePath: string, groupName?: string) => ipcRenderer.invoke("wechat:importFile", filePath, groupName),
  importWechatText: (raw: string, sourceName: string, groupName?: string) =>
    ipcRenderer.invoke("wechat:importText", raw, sourceName, groupName),
  getWechatAgentStatus: () => ipcRenderer.invoke("wechat:agentStatus"),
  importWechatAgentChat: (chatName: string, limit?: number, start?: string, end?: string) =>
    ipcRenderer.invoke("wechat:importAgentChat", chatName, limit, start, end),
  importWechatClipboard: (groupName?: string) => ipcRenderer.invoke("wechat:importClipboard", groupName),
  askWechatQuestion: (analysis: unknown, question: string, settings?: unknown) =>
    ipcRenderer.invoke("wechat:ask", analysis, question, settings)
};

contextBridge.exposeInMainWorld("shouwang", api);

export type ShouwangApi = typeof api;
