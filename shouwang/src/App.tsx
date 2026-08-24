import {
  BadgeCheck,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Clapperboard,
  Download,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  MessageSquare,
  KeyRound,
  Landmark,
  PlayCircle,
  ReceiptText,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Video,
  type LucideIcon
} from "lucide-react";
import { clsx } from "clsx";
import { useEffect, useMemo, useRef, useState } from "react";
import { DEFAULT_AGENT_SETTINGS } from "../shared/defaultSettings";

type ServiceStatus = "ready" | "vip" | "soon";

type Service = {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  status: ServiceStatus;
  filters: ElectronFileFilter[];
  actions: string[];
};

type Task = {
  id: string;
  serviceId: string;
  serviceTitle: string;
  files: string[];
  createdAt: string;
  state: "queued" | "checking" | "ready";
};

type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  outputPath?: string;
};

const services: Service[] = [
  {
    id: "excel",
    title: "Excel 智能处理",
    description: "表格清洗、字段归类、批量汇总、异常数据检查和报表生成。",
    icon: FileSpreadsheet,
    status: "ready",
    filters: [{ name: "Excel", extensions: ["xlsx", "xls", "csv"] }],
    actions: ["上传表格", "自动识别字段", "生成结果"]
  },
  {
    id: "word-ppt",
    title: "Word / PPT 办公助手",
    description: "合同摘要、文档排版、PPT 大纲生成、演示稿润色和格式检查。",
    icon: FileText,
    status: "ready",
    filters: [{ name: "Office 文档", extensions: ["doc", "docx", "ppt", "pptx", "pdf"] }],
    actions: ["解析文档", "提取重点", "导出成稿"]
  },
  {
    id: "video-cut",
    title: "视频剪辑工作流",
    description: "素材上传、自动分镜、口播切片、字幕草稿和短视频脚本建议。",
    icon: Clapperboard,
    status: "vip",
    filters: [{ name: "视频", extensions: ["mp4", "mov", "mkv", "avi"] }],
    actions: ["导入素材", "识别片段", "输出剪辑建议"]
  },
  {
    id: "vip-video",
    title: "VIP 视频观看",
    description: "适合做成合规聚合入口：会员资源管理、观看记录、内部课程分发。",
    icon: PlayCircle,
    status: "soon",
    filters: [{ name: "播放列表", extensions: ["m3u8", "json", "txt"] }],
    actions: ["导入片单", "校验权限", "打开播放"]
  },
  {
    id: "tax",
    title: "财税智能顾问",
    description: "票据分类、税务问答、经营数据看板、申报材料辅助检查。",
    icon: Landmark,
    status: "vip",
    filters: [{ name: "财税资料", extensions: ["xlsx", "xls", "pdf", "jpg", "png"] }],
    actions: ["上传资料", "识别风险", "生成建议"]
  },
  {
    id: "invoice",
    title: "发票审批",
    description: "发票验真、抬头核对、报销单匹配、审批流状态追踪。",
    icon: ReceiptText,
    status: "ready",
    filters: [{ name: "发票文件", extensions: ["pdf", "ofd", "jpg", "jpeg", "png"] }],
    actions: ["导入发票", "规则校验", "提交审批"]
  },
  {
    id: "wechat",
    title: "微信群历史分析",
    description: "导入群聊文本或表格后，用对话方式分析某位群友、活跃成员、话题和互动关系。",
    icon: MessageSquare,
    status: "ready",
    filters: [{ name: "聊天记录", extensions: ["txt", "md", "json", "csv", "xlsx", "xls"] }],
    actions: ["导入记录", "建立画像", "对话分析"]
  }
];

const defaultSettings: AgentSettings = DEFAULT_AGENT_SETTINGS;

const providerLabels: Record<AgentSettings["modelProvider"], string> = {
  openai: "OpenAI",
  deepseek: "DeepSeek",
  qwen: "通义千问",
  local: "本地模型"
};

const desktopApi = () => window.shouwang;
const isElectronRuntime = () => navigator.userAgent.includes("Electron");

function maskValue(value: string) {
  if (!value) return "";
  if (value.length <= 8) return "*".repeat(value.length);
  return `${value.slice(0, 4)}${"*".repeat(Math.min(12, value.length - 8))}${value.slice(-4)}`;
}

function keyLooksActive(key: string) {
  return /^SW-[A-Z0-9]{4,}-[A-Z0-9]{4,}/i.test(key.trim());
}

export function App() {
  const [activeServiceId, setActiveServiceId] = useState(services[0].id);
  const [view, setView] = useState<"workspace" | "settings">("workspace");
  const [settings, setSettings] = useState<AgentSettings>(defaultSettings);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeFile, setActiveFile] = useState<string>("");
  const [excelPreview, setExcelPreview] = useState<ExcelPreview | null>(null);
  const [wechatAnalysis, setWechatAnalysis] = useState<WechatAnalysis | null>(null);
  const [wechatGroups, setWechatGroups] = useState<WechatGroupSummary[]>([]);
  const [selectedWechatGroup, setSelectedWechatGroup] = useState<WechatGroupProfile | null>(null);
  const [wechatStorageDirectory, setWechatStorageDirectory] = useState("");
  const [wechatImportGroupName, setWechatImportGroupName] = useState("");
  const [wechatImportStartDate, setWechatImportStartDate] = useState("");
  const [wechatImportEndDate, setWechatImportEndDate] = useState("");
  const wechatFileInputRef = useRef<HTMLInputElement | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "上传 Excel 后，你可以直接告诉我怎么改。比如：删除销售额为空的行、按客户汇总、按客户去重。"
    }
  ]);
  const [wechatMessages, setWechatMessages] = useState<ChatMessage[]>([
    {
      id: "wechat-welcome",
      role: "assistant",
      content: "导入微信群历史消息后，可以问我：分析一下张三、谁最活跃、李四最近主要聊什么。"
    }
  ]);
  const [isModelConfigOpen, setIsModelConfigOpen] = useState(false);
  const [saveState, setSaveState] = useState<"idle" | "saved">("idle");

  const activeService = useMemo(
    () => services.find((service) => service.id === activeServiceId) ?? services[0],
    [activeServiceId]
  );
  const licenseActive = keyLooksActive(settings.licenseKey);
  const apiReady = Boolean(settings.apiKey.trim() && settings.modelName.trim());

  useEffect(() => {
    desktopApi().loadSettings().then((loaded) => {
      setSettings({ ...defaultSettings, ...loaded });
    });
    refreshWechatGroups();
  }, []);

  async function refreshWechatGroups(preferredGroupId?: string) {
    const [groups, storageDirectory] = await Promise.all([
      desktopApi().listWechatGroups(),
      desktopApi().getWechatStorageDirectory()
    ]);
    setWechatGroups(groups);
    setWechatStorageDirectory(storageDirectory);

    const nextGroupId = preferredGroupId ?? selectedWechatGroup?.id ?? groups[0]?.id;
    if (nextGroupId) {
      await selectWechatGroup(nextGroupId);
    }
  }

  async function selectWechatGroup(groupId: string) {
    const group = await desktopApi().loadWechatGroup(groupId);
    if (!group) return;
    setSelectedWechatGroup(group);
    setWechatAnalysis(group.analysis);
    setWechatImportGroupName(group.name);
    setWechatMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `已切换到「${group.name}」。存储位置：${group.storagePath}`
      }
    ]);
  }

  async function saveSettings(next = settings) {
    const saved = await desktopApi().saveSettings(next);
    setSettings(saved);
    setSaveState("saved");
    window.setTimeout(() => setSaveState("idle"), 1600);
  }

  async function chooseDownloadPath() {
    const selected = await desktopApi().selectDirectory();
    if (!selected) return;
    const next = { ...settings, downloadPath: selected };
    setSettings(next);
    await saveSettings(next);
  }

  async function uploadFor(service: Service) {
    if (service.id === "wechat") {
      if (!isElectronRuntime()) {
        wechatFileInputRef.current?.click();
        return;
      }
      if (wechatImportGroupName.trim()) {
        await importWechatAgentChat(wechatImportGroupName.trim(), wechatImportStartDate, wechatImportEndDate);
        return;
      }
    }

    const files = await desktopApi().selectFiles(service.filters);
    if (!files.length) {
      if (service.id === "wechat") {
        setWechatMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "没有选择文件。也可以在数据名称里填写群名后导入本地 Vault。"
          }
        ]);
      }
      return;
    }

    const firstFile = files[0];

    setActiveFile(firstFile);
    if (service.id === "excel") {
      try {
        const preview = await desktopApi().inspectExcel(firstFile);
        setExcelPreview(preview);
        setChatMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `已读取「${firstFile.split("/").pop()}」。工作表：${preview.sheetName}，共 ${preview.rowCount} 行，字段：${preview.columns.join("、")}。`
          }
        ]);
      } catch (error) {
        setChatMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `读取 Excel 失败：${String(error)}`
          }
        ]);
      }
    } else if (service.id === "wechat") {
      await importWechatFilePath(firstFile, wechatImportGroupName);
    }

    setTasks((current) => [
      {
        id: crypto.randomUUID(),
        serviceId: service.id,
        serviceTitle: service.title,
        files,
        createdAt: new Date().toLocaleString("zh-CN", { hour12: false }),
        state: apiReady && licenseActive ? "ready" : "checking"
      },
      ...current
    ]);
  }

  async function importWechatFilePath(filePath: string, groupName = wechatImportGroupName) {
    try {
      const result = await desktopApi().importWechatFile(filePath, groupName);
      await applyWechatImportResult(result);
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.message
        }
      ]);
    } catch (error) {
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `读取聊天记录失败：${String(error)}`
        }
      ]);
    }
  }

  async function importWechatAgentChat(chatName: string, startDate = "", endDate = "") {
    try {
      const rangeText = startDate || endDate ? `（${startDate || "不限"} 至 ${endDate || "不限"}）` : "";
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `正在刷新本地 Vault 并导入「${chatName}」${rangeText}...`
        }
      ]);
      const result = await desktopApi().importWechatAgentChat(chatName, 1000, startDate, endDate);
      await applyWechatImportResult(result);
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.message
        }
      ]);
    } catch (error) {
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `读取本地 Vault 失败：${String(error)}`
        }
      ]);
    }
  }

  async function importWechatBrowserFile(file: File) {
    try {
      const raw = await file.text();
      const result = await desktopApi().importWechatText(raw, file.name, wechatImportGroupName);
      await applyWechatImportResult(result);
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.message
        }
      ]);
    } catch (error) {
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `读取聊天记录失败：${String(error)}`
        }
      ]);
    }
  }

  async function applyWechatImportResult(result: WechatImportResult) {
    if (result.analysis) setWechatAnalysis(result.analysis);
    if (result.group) {
      setSelectedWechatGroup(result.group);
      setWechatImportGroupName(result.group.name);
      await refreshWechatGroups(result.group.id);
    }
  }

  async function importWechatClipboard(groupName = wechatImportGroupName) {
    try {
      const result = await desktopApi().importWechatClipboard(groupName);
      await applyWechatImportResult(result);
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.message
        }
      ]);
      if (result.ok) {
        setTasks((current) => [
          {
            id: crypto.randomUUID(),
            serviceId: "wechat",
            serviceTitle: "微信群历史分析",
            files: ["剪贴板聊天记录"],
            createdAt: new Date().toLocaleString("zh-CN", { hour12: false }),
            state: "ready"
          },
          ...current
        ]);
      }
    } catch (error) {
      setWechatMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `读取剪贴板失败：${String(error)}`
        }
      ]);
    }
  }

  return (
    <div className="app-shell">
      <input
        ref={wechatFileInputRef}
        className="hidden-file-input"
        type="file"
        accept=".txt,.md,.json,.csv"
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) void importWechatBrowserFile(file);
        }}
      />
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Bot size={25} />
          </div>
          <div>
            <div className="brand-name">守望智能体</div>
            <div className="brand-subtitle">桌面商业服务平台</div>
          </div>
        </div>

        <nav className="nav-list">
          <button className={clsx("nav-item", view === "workspace" && "active")} onClick={() => setView("workspace")}>
            <Sparkles size={18} />
            服务工作台
          </button>
          <button className={clsx("nav-item", view === "settings" && "active")} onClick={() => setView("settings")}>
            <Settings size={18} />
            系统设置
          </button>
        </nav>

        <div className="sidebar-section-title">商业模块</div>
        <div className="service-nav">
          {services.map((service) => {
            const Icon = service.icon;
            return (
              <button
                key={service.id}
                className={clsx("service-nav-item", activeServiceId === service.id && "active")}
                onClick={() => {
                  setActiveServiceId(service.id);
                  setView("workspace");
                }}
              >
                <Icon size={18} />
                <span>{service.title}</span>
              </button>
            );
          })}
        </div>

        <div className="license-panel">
          <ShieldCheck size={18} />
          <div>
            <strong>{licenseActive ? "授权已识别" : "等待授权 Key"}</strong>
            <span>{licenseActive ? "可开放付费模块" : "建议销售 SW- 开头激活码"}</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <p className="eyebrow">AI Agent Console</p>
            <h1>{view === "settings" ? "设置与商业化" : activeService.title}</h1>
          </div>
          <div className="topbar-actions">
            <StatusPill active={licenseActive} icon={KeyRound} label={licenseActive ? "Key 有效" : "未激活"} />
            <StatusPill active={apiReady} icon={BadgeCheck} label={apiReady ? providerLabels[settings.modelProvider] : "模型未配置"} />
          </div>
        </header>

        {view === "workspace" ? (
          <Workspace
            activeService={activeService}
            tasks={tasks}
            settings={settings}
            licenseActive={licenseActive}
            apiReady={apiReady}
            activeFile={activeFile}
            excelPreview={excelPreview}
            chatMessages={chatMessages}
            wechatAnalysis={wechatAnalysis}
            wechatMessages={wechatMessages}
            selectedWechatGroup={selectedWechatGroup}
            wechatStorageDirectory={wechatStorageDirectory}
            wechatImportGroupName={wechatImportGroupName}
            wechatImportStartDate={wechatImportStartDate}
            wechatImportEndDate={wechatImportEndDate}
            onChatMessagesChange={setChatMessages}
            onWechatMessagesChange={setWechatMessages}
            onWechatImportGroupNameChange={setWechatImportGroupName}
            onWechatImportStartDateChange={setWechatImportStartDate}
            onWechatImportEndDateChange={setWechatImportEndDate}
            onUpload={() => uploadFor(activeService)}
            onImportWechatClipboard={importWechatClipboard}
            onOpenSettings={() => setView("settings")}
            onOpenModelConfig={() => setIsModelConfigOpen(true)}
          />
        ) : (
          <SettingsView
            settings={settings}
            saveState={saveState}
            onChange={setSettings}
            onSave={() => saveSettings()}
            onChooseDownloadPath={chooseDownloadPath}
          />
        )}
      </main>

      {isModelConfigOpen && (
        <ModelConfigModal
          settings={settings}
          saveState={saveState}
          onChange={setSettings}
          onClose={() => setIsModelConfigOpen(false)}
          onSave={() => saveSettings()}
        />
      )}
    </div>
  );
}

function StatusPill({
  active,
  label,
  icon: Icon
}: {
  active: boolean;
  label: string;
  icon: LucideIcon;
}) {
  return (
    <div className={clsx("status-pill", active && "active")}>
      <Icon size={16} />
      {label}
    </div>
  );
}

function Workspace({
  activeService,
  tasks,
  settings,
  licenseActive,
  apiReady,
  activeFile,
  excelPreview,
  chatMessages,
  wechatAnalysis,
  wechatMessages,
  selectedWechatGroup,
  wechatStorageDirectory,
  wechatImportGroupName,
  wechatImportStartDate,
  wechatImportEndDate,
  onChatMessagesChange,
  onWechatMessagesChange,
  onWechatImportGroupNameChange,
  onWechatImportStartDateChange,
  onWechatImportEndDateChange,
  onUpload,
  onImportWechatClipboard,
  onOpenSettings,
  onOpenModelConfig
}: {
  activeService: Service;
  tasks: Task[];
  settings: AgentSettings;
  licenseActive: boolean;
  apiReady: boolean;
  activeFile: string;
  excelPreview: ExcelPreview | null;
  chatMessages: ChatMessage[];
  wechatAnalysis: WechatAnalysis | null;
  wechatMessages: ChatMessage[];
  selectedWechatGroup: WechatGroupProfile | null;
  wechatStorageDirectory: string;
  wechatImportGroupName: string;
  wechatImportStartDate: string;
  wechatImportEndDate: string;
  onChatMessagesChange: (messages: ChatMessage[] | ((messages: ChatMessage[]) => ChatMessage[])) => void;
  onWechatMessagesChange: (messages: ChatMessage[] | ((messages: ChatMessage[]) => ChatMessage[])) => void;
  onWechatImportGroupNameChange: (groupName: string) => void;
  onWechatImportStartDateChange: (date: string) => void;
  onWechatImportEndDateChange: (date: string) => void;
  onUpload: () => void;
  onImportWechatClipboard: (groupName?: string) => void;
  onOpenSettings: () => void;
  onOpenModelConfig: () => void;
}) {
  const serviceTasks = tasks.filter((task) => task.serviceId === activeService.id);
  const Icon = activeService.icon;

  if (activeService.id === "wechat") {
    return (
      <WechatAnalysisPage
        analysis={wechatAnalysis}
        messages={wechatMessages}
        settings={settings}
        selectedGroup={selectedWechatGroup}
        storageDirectory={wechatStorageDirectory}
        importGroupName={wechatImportGroupName}
        importStartDate={wechatImportStartDate}
        importEndDate={wechatImportEndDate}
        onMessagesChange={onWechatMessagesChange}
        onImportGroupNameChange={onWechatImportGroupNameChange}
        onImportStartDateChange={onWechatImportStartDateChange}
        onImportEndDateChange={onWechatImportEndDateChange}
        onUpload={onUpload}
        onOpenModelConfig={onOpenModelConfig}
      />
    );
  }

  return (
    <div className="workspace-grid">
      <section className="primary-panel">
        <div className="service-heading">
          <div className="service-icon">
            <Icon size={34} strokeWidth={1.8} />
          </div>
          <div>
            <div className={clsx("service-status", activeService.status)}>
              {activeService.status === "ready" ? "基础版可用" : activeService.status === "vip" ? "VIP 模块" : "建议合规确认"}
            </div>
            <h2>{activeService.title}</h2>
            <p>{activeService.description}</p>
          </div>
        </div>

        <div className="drop-zone">
          <UploadCloud size={42} />
          <div>
            <h3>{activeService.id === "wechat" ? "导入群聊历史消息" : "上传文件并创建智能任务"}</h3>
            <p>
              {activeService.id === "wechat"
                ? "支持 txt/md/json/csv/xlsx 聊天记录，也可以导入 Vault 类工具已导出的文件，或从剪贴板导入。"
                : "当前版本先完成桌面端上传入口、授权检查和任务队列，后续可接 Python/Node 后端实现真实解析、剪辑或审批流。"}
            </p>
          </div>
          <div className="drop-actions">
            {activeService.id === "wechat" && (
              <button className="secondary-button" onClick={() => onImportWechatClipboard()}>
                <MessageSquare size={18} />
                从剪贴板
              </button>
            )}
            <button className="primary-button" onClick={onUpload}>
              <UploadCloud size={18} />
              选择文件
            </button>
          </div>
        </div>

        <div className="workflow-row">
          {activeService.actions.map((action, index) => (
            <div className="workflow-step" key={action}>
              <span>{index + 1}</span>
              {action}
              {index < activeService.actions.length - 1 && <ChevronRight size={16} />}
            </div>
          ))}
        </div>
      </section>

      <aside className="side-panel">
        <h3>运行条件</h3>
        <Requirement ok={licenseActive} label="商业授权 Key" detail={licenseActive ? maskValue(settings.licenseKey) : "未填写或格式不正确"} />
        <Requirement ok={apiReady} label="模型服务" detail={apiReady ? `${providerLabels[settings.modelProvider]} · ${settings.modelName}` : "请设置模型与 API Key"} />
        <Requirement ok={Boolean(settings.downloadPath)} label="下载路径" detail={settings.downloadPath || "未选择"} />
        <button className="secondary-button full" onClick={onOpenSettings}>
          <Settings size={17} />
          打开设置
        </button>
        <button className="secondary-button full" onClick={onOpenModelConfig}>
          <Bot size={17} />
          模型配置
        </button>
      </aside>

      {activeService.id === "excel" && (
        <AgentChatPanel
          activeFile={activeFile}
          excelPreview={excelPreview}
          messages={chatMessages}
          settings={settings}
          onMessagesChange={onChatMessagesChange}
          onOpenModelConfig={onOpenModelConfig}
        />
      )}

      <section className="task-panel">
        <div className="section-title">
          <h3>任务队列</h3>
          <span>{serviceTasks.length} 个任务</span>
        </div>
        {serviceTasks.length ? (
          <div className="task-list">
            {serviceTasks.map((task) => (
              <div className="task-item" key={task.id}>
                <div>
                  <strong>{task.files.length} 个文件 · {task.serviceTitle}</strong>
                  <span>{task.files.map((file) => file.split("/").pop()).join("、")}</span>
                </div>
                <div className={clsx("task-state", task.state)}>{task.state === "ready" ? "可处理" : "待配置"}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Video size={26} />
            <p>还没有任务。选择文件后会出现在这里。</p>
          </div>
        )}
      </section>
    </div>
  );
}

function AgentChatPanel({
  activeFile,
  excelPreview,
  messages,
  settings,
  onMessagesChange,
  onOpenModelConfig
}: {
  activeFile: string;
  excelPreview: ExcelPreview | null;
  messages: ChatMessage[];
  settings: AgentSettings;
  onMessagesChange: (messages: ChatMessage[] | ((messages: ChatMessage[]) => ChatMessage[])) => void;
  onOpenModelConfig: () => void;
}) {
  const [draft, setDraft] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  async function sendInstruction() {
    const instruction = draft.trim();
    if (!instruction || !activeFile || isRunning) return;
    setDraft("");
    setIsRunning(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: instruction
    };
    onMessagesChange((current) => [...current, userMessage]);

    try {
      const result = await desktopApi().applyExcelInstruction(activeFile, instruction, settings.downloadPath);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.ok
          ? `${result.message} 已生成新文件：${result.outputPath?.split("/").pop()}`
          : result.message,
        outputPath: result.outputPath
      };
      onMessagesChange((current) => [...current, assistantMessage]);
    } catch (error) {
      onMessagesChange((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `处理失败：${String(error)}`
        }
      ]);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section className="agent-panel">
      <div className="section-title">
        <div>
          <h3>文件对话修改</h3>
          <span>{activeFile ? activeFile.split("/").pop() : "先上传一个 Excel 文件"}</span>
        </div>
        <button className="secondary-button" onClick={onOpenModelConfig}>
          <Bot size={17} />
          模型配置
        </button>
      </div>

      {excelPreview && (
        <div className="file-context">
          <div>
            <strong>{excelPreview.sheetName}</strong>
            <span>{excelPreview.rowCount} 行 · {excelPreview.columns.length} 个字段</span>
          </div>
          <div className="column-tags">
            {excelPreview.columns.slice(0, 8).map((column) => (
              <span key={column}>{column}</span>
            ))}
          </div>
        </div>
      )}

      <div className="chat-list">
        {messages.map((message) => (
          <div className={clsx("chat-message", message.role)} key={message.id}>
            <div>{message.content}</div>
            {message.outputPath && (
              <button className="link-button" onClick={() => desktopApi().openPath(message.outputPath!)}>
                打开生成文件
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="chat-input-row">
        <MessageSquare size={18} />
        <input
          value={draft}
          disabled={!activeFile || isRunning}
          placeholder={activeFile ? "输入修改要求，例如：删除销售额为空的行" : "先上传 Excel 文件"}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") sendInstruction();
          }}
        />
        <button className="primary-button" disabled={!activeFile || isRunning || !draft.trim()} onClick={sendInstruction}>
          <Send size={17} />
          {isRunning ? "处理中" : "发送"}
        </button>
      </div>
    </section>
  );
}

function WechatAnalysisPage({
  analysis,
  messages,
  settings,
  selectedGroup,
  storageDirectory,
  importGroupName,
  importStartDate,
  importEndDate,
  onMessagesChange,
  onImportGroupNameChange,
  onImportStartDateChange,
  onImportEndDateChange,
  onUpload,
  onOpenModelConfig
}: {
  analysis: WechatAnalysis | null;
  messages: ChatMessage[];
  settings: AgentSettings;
  selectedGroup: WechatGroupProfile | null;
  storageDirectory: string;
  importGroupName: string;
  importStartDate: string;
  importEndDate: string;
  onMessagesChange: (messages: ChatMessage[] | ((messages: ChatMessage[]) => ChatMessage[])) => void;
  onImportGroupNameChange: (groupName: string) => void;
  onImportStartDateChange: (date: string) => void;
  onImportEndDateChange: (date: string) => void;
  onUpload: () => void;
  onOpenModelConfig: () => void;
}) {
  const [draft, setDraft] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  async function askQuestion() {
    const question = draft.trim();
    if (!question || !analysis || isRunning) return;
    setDraft("");
    setIsRunning(true);

    onMessagesChange((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: question
      }
    ]);

    try {
      const result = await desktopApi().askWechatQuestion(analysis, question, settings);
      onMessagesChange((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.message
        }
      ]);
    } catch (error) {
      onMessagesChange((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `分析失败：${String(error)}`
        }
      ]);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="wechat-page">
      <section className="wechat-import-panel">
        <div className="wechat-page-heading">
          <div>
            <p className="eyebrow">Wechat Data QA</p>
            <h2>聊天数据问答</h2>
          </div>
          <span>{analysis ? `${analysis.totalMessages} 条消息 · ${analysis.memberCount} 位成员` : "等待导入"}</span>
        </div>

        <div className="wechat-import-layout">
          <label>
            数据名称
            <input
              value={importGroupName}
              placeholder="例如：天沐锦江老板群"
              onChange={(event) => onImportGroupNameChange(event.target.value)}
            />
          </label>
          <div className="date-range-fields">
            <label>
              开始时间
              <input
                type="date"
                value={importStartDate}
                onChange={(event) => onImportStartDateChange(event.target.value)}
              />
            </label>
            <label>
              结束时间
              <input
                type="date"
                value={importEndDate}
                onChange={(event) => onImportEndDateChange(event.target.value)}
              />
            </label>
          </div>
          <div className="import-actions">
            <button className="primary-button" onClick={onUpload}>
              <UploadCloud size={18} />
              导入数据
            </button>
          </div>
        </div>

        <div className="storage-line">
          <FolderOpen size={16} />
          <span>{selectedGroup ? selectedGroup.storagePath : storageDirectory || "等待创建本地存储目录"}</span>
        </div>
      </section>

      {analysis && (
        <div className="wechat-summary">
          <div>
            <strong>{analysis.totalMessages}</strong>
            <span>消息数</span>
          </div>
          <div>
            <strong>{analysis.memberCount}</strong>
            <span>群友数</span>
          </div>
          <div>
            <strong>{analysis.timeRange}</strong>
            <span>时间范围</span>
          </div>
        </div>
      )}

      {analysis && (
        <div className="member-strip">
          {analysis.topMembers.slice(0, 8).map((member) => (
            <button
              key={member.name}
              className="member-chip"
              onClick={() => setDraft(`分析一下${member.name}`)}
              title={`分析 ${member.name}`}
            >
              <strong>{member.name}</strong>
              <span>{member.messageCount} 条 · {member.percent}%</span>
            </button>
          ))}
        </div>
      )}

      <section className="wechat-chat-panel">
        <div className="section-title">
          <div>
            <h3>对话分析</h3>
            <span>{analysis ? "可以直接提问某位群友、话题、活跃度和互动关系" : "导入后这里开始分析"}</span>
          </div>
          <button className="secondary-button" onClick={onOpenModelConfig}>
            <Bot size={17} />
            模型配置
          </button>
        </div>

        <div className="chat-list wechat-chat-list">
          {messages.map((message) => (
            <div className={clsx("chat-message", message.role)} key={message.id}>
              <div>{message.content}</div>
            </div>
          ))}
        </div>

        <div className="chat-input-row">
          <MessageSquare size={18} />
          <input
            value={draft}
            disabled={!analysis || isRunning}
            placeholder={analysis ? "例如：分析一下张三 / 谁最活跃 / 李四主要聊什么" : "先导入群聊记录"}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") askQuestion();
            }}
          />
          <button className="primary-button" disabled={!analysis || isRunning || !draft.trim()} onClick={askQuestion}>
            <Send size={17} />
            {isRunning ? "分析中" : "发送"}
          </button>
        </div>
      </section>
    </div>
  );
}

function Requirement({ ok, label, detail }: { ok: boolean; label: string; detail: string }) {
  return (
    <div className="requirement">
      <CheckCircle2 className={clsx(ok && "ok")} size={19} />
      <div>
        <strong>{label}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function SettingsView({
  settings,
  saveState,
  onChange,
  onSave,
  onChooseDownloadPath
}: {
  settings: AgentSettings;
  saveState: "idle" | "saved";
  onChange: (settings: AgentSettings) => void;
  onSave: () => void;
  onChooseDownloadPath: () => void;
}) {
  const visibleApiKey = settings.maskSensitiveFields ? maskValue(settings.apiKey) : settings.apiKey;

  return (
    <div className="settings-layout">
      <section className="settings-panel">
        <div className="section-title">
          <h3>商业授权</h3>
          <CircleDollarSign size={20} />
        </div>
        <label>
          授权 Key
          <input
            value={settings.licenseKey}
            placeholder="SW-XXXX-XXXX-XXXX"
            onChange={(event) => onChange({ ...settings, licenseKey: event.target.value })}
          />
        </label>
        <p className="hint">建议后续把 Key 校验放到你的服务器：绑定设备指纹、套餐权限、到期时间和模块开关。</p>
      </section>

      <section className="settings-panel">
        <div className="section-title">
          <h3>模型配置</h3>
          <Bot size={20} />
        </div>
        <div className="field-grid">
          <label>
            服务商
            <select
              value={settings.modelProvider}
              onChange={(event) =>
                onChange({ ...settings, modelProvider: event.target.value as AgentSettings["modelProvider"] })
              }
            >
              <option value="deepseek">DeepSeek</option>
              <option value="qwen">通义千问</option>
              <option value="openai">OpenAI</option>
              <option value="local">本地模型</option>
            </select>
          </label>
          <label>
            模型名称
            <input
              value={settings.modelName}
              placeholder="deepseek-chat"
              onChange={(event) => onChange({ ...settings, modelName: event.target.value })}
            />
          </label>
        </div>
        <label>
          API Base URL
          <input
            value={settings.apiBaseUrl}
            placeholder="https://api.example.com"
            onChange={(event) => onChange({ ...settings, apiBaseUrl: event.target.value })}
          />
        </label>
        <label>
          模型 API Key
          <input
            value={settings.apiKey}
            type={settings.maskSensitiveFields ? "password" : "text"}
            placeholder={visibleApiKey || "sk-..."}
            onChange={(event) => onChange({ ...settings, apiKey: event.target.value })}
          />
        </label>
      </section>

      <section className="settings-panel">
        <div className="section-title">
          <h3>本地偏好</h3>
          <Download size={20} />
        </div>
        <label>
          下载/输出存储路径
          <div className="path-row">
            <input value={settings.downloadPath} readOnly placeholder="选择输出目录" />
            <button className="icon-button" title="选择目录" onClick={onChooseDownloadPath}>
              <FolderOpen size={18} />
            </button>
          </div>
        </label>
        <label className="switch-row">
          <input
            type="checkbox"
            checked={settings.autoStartTasks}
            onChange={(event) => onChange({ ...settings, autoStartTasks: event.target.checked })}
          />
          上传后自动进入处理队列
        </label>
        <label className="switch-row">
          <input
            type="checkbox"
            checked={settings.maskSensitiveFields}
            onChange={(event) => onChange({ ...settings, maskSensitiveFields: event.target.checked })}
          />
          默认隐藏敏感字段
        </label>
      </section>

      <section className="settings-panel strategy-panel">
        <div className="section-title">
          <h3>产品建议</h3>
          <BarChart3 size={20} />
        </div>
        <ul>
          <li>先做高频刚需：Excel 处理、发票审批、财税资料整理最容易收费。</li>
          <li>VIP 视频观看要确认版权与合规边界，建议定位为内部课程/企业资料播放器。</li>
          <li>Key 售卖建议分为基础版、专业版、企业版，按模块和用量控制。</li>
          <li>文档与视频处理建议拆成本地任务队列，避免大文件阻塞界面。</li>
        </ul>
      </section>

      <div className="save-bar">
        <button className="primary-button" onClick={onSave}>
          <ShieldCheck size={18} />
          {saveState === "saved" ? "已保存" : "保存设置"}
        </button>
      </div>
    </div>
  );
}

function ModelConfigModal({
  settings,
  saveState,
  onChange,
  onClose,
  onSave
}: {
  settings: AgentSettings;
  saveState: "idle" | "saved";
  onChange: (settings: AgentSettings) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <div className="modal-backdrop">
      <section className="model-modal">
        <div className="modal-header">
          <div>
            <p className="eyebrow">Model Gateway</p>
            <h2>模型配置</h2>
          </div>
          <button className="secondary-button" onClick={onClose}>关闭</button>
        </div>

        <div className="field-grid">
          <label>
            服务商
            <select
              value={settings.modelProvider}
              onChange={(event) =>
                onChange({ ...settings, modelProvider: event.target.value as AgentSettings["modelProvider"] })
              }
            >
              <option value="deepseek">DeepSeek</option>
              <option value="qwen">通义千问</option>
              <option value="openai">OpenAI</option>
              <option value="local">本地模型</option>
            </select>
          </label>
          <label>
            模型名称
            <input
              value={settings.modelName}
              placeholder="deepseek-chat"
              onChange={(event) => onChange({ ...settings, modelName: event.target.value })}
            />
          </label>
        </div>

        <label>
          API Base URL
          <input
            value={settings.apiBaseUrl}
            placeholder="https://api.deepseek.com"
            onChange={(event) => onChange({ ...settings, apiBaseUrl: event.target.value })}
          />
        </label>

        <label>
          API Key
          <input
            value={settings.apiKey}
            type={settings.maskSensitiveFields ? "password" : "text"}
            placeholder="sk-..."
            onChange={(event) => onChange({ ...settings, apiKey: event.target.value })}
          />
        </label>

        <label className="switch-row">
          <input
            type="checkbox"
            checked={settings.maskSensitiveFields}
            onChange={(event) => onChange({ ...settings, maskSensitiveFields: event.target.checked })}
          />
          默认隐藏 API Key
        </label>

        <p className="hint">
          当前版本先用本地规则执行 Excel 修改。接入模型后，模型负责把用户自然语言转换为结构化操作计划，文件仍由本地工具安全执行。
        </p>

        <div className="save-bar">
          <button className="primary-button" onClick={onSave}>
            <ShieldCheck size={18} />
            {saveState === "saved" ? "已保存" : "保存模型配置"}
          </button>
        </div>
      </section>
    </div>
  );
}
