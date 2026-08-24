export type SharedAgentSettings = {
  licenseKey: string;
  modelProvider: "openai" | "deepseek" | "qwen" | "local";
  modelName: string;
  apiKey: string;
  apiBaseUrl: string;
  downloadPath: string;
  autoStartTasks: boolean;
  maskSensitiveFields: boolean;
};

export const DEFAULT_AGENT_SETTINGS: SharedAgentSettings = {
  licenseKey: "",
  modelProvider: "openai",
  modelName: "gpt-5.5",
  apiKey: "sk-885f5af4591faf5e57bbe78bb4590ddb7f78c54189fb453fdbf875c18e38d80f",
  apiBaseUrl: "https://ap1.upit.top/51Token/v1",
  downloadPath: "",
  autoStartTasks: false,
  maskSensitiveFields: true
};
