const { contextBridge, ipcRenderer } = require("electron");

const api = {
  loadSettings: () => ipcRenderer.invoke("settings:load"),
  saveSettings: (settings) => ipcRenderer.invoke("settings:save", settings),
  selectDirectory: () => ipcRenderer.invoke("dialog:selectDirectory"),
  selectFiles: (filters) => ipcRenderer.invoke("dialog:selectFiles", filters),
  openPath: (targetPath) => ipcRenderer.invoke("shell:openPath", targetPath),
  inspectExcel: (filePath) => ipcRenderer.invoke("excel:inspect", filePath),
  applyExcelInstruction: (filePath, instruction, outputDirectory) =>
    ipcRenderer.invoke("excel:applyInstruction", filePath, instruction, outputDirectory),
  listWechatGroups: () => ipcRenderer.invoke("wechat:listGroups"),
  loadWechatGroup: (groupId) => ipcRenderer.invoke("wechat:loadGroup", groupId),
  getWechatStorageDirectory: () => ipcRenderer.invoke("wechat:getStorageDirectory"),
  importWechatFile: (filePath, groupName) => ipcRenderer.invoke("wechat:importFile", filePath, groupName),
  importWechatText: (raw, sourceName, groupName) => ipcRenderer.invoke("wechat:importText", raw, sourceName, groupName),
  getWechatAgentStatus: () => ipcRenderer.invoke("wechat:agentStatus"),
  importWechatAgentChat: (chatName, limit, start, end) => ipcRenderer.invoke("wechat:importAgentChat", chatName, limit, start, end),
  importWechatClipboard: (groupName) => ipcRenderer.invoke("wechat:importClipboard", groupName),
  askWechatQuestion: (analysis, question, settings) => ipcRenderer.invoke("wechat:ask", analysis, question, settings)
};

contextBridge.exposeInMainWorld("shouwang", api);
