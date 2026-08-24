export type WechatModelSettings = {
  modelName: string;
  apiKey: string;
  apiBaseUrl: string;
};

export type WechatModelAnalysis = {
  sourceName: string;
  totalMessages: number;
  memberCount: number;
  timeRange: string;
  topMembers: Array<{
    name: string;
    messageCount: number;
    percent: number;
    keywords: string[];
  }>;
  messages: Array<{
    speaker: string;
    content: string;
    timestamp?: string;
  }>;
};

export type WechatModelResult = {
  ok: boolean;
  message: string;
};

type ChatMessage = {
  role: "system" | "user";
  content: string;
};

export function normalizeResponsesUrl(baseUrl: string) {
  const trimmed = baseUrl.trim().replace(/\/+$/, "");
  if (trimmed.endsWith("/responses")) return trimmed;
  if (trimmed.endsWith("/v1")) return `${trimmed}/responses`;
  return `${trimmed}/v1/responses`;
}

function compactMessageLine(message: WechatModelAnalysis["messages"][number]) {
  const time = message.timestamp ? `[${message.timestamp}] ` : "";
  return `${time}${message.speaker}: ${message.content}`.slice(0, 500);
}

function isPaymentRelatedMessage(message: WechatModelAnalysis["messages"][number]) {
  return /红包|转账|收款|付款|支付|金额|￥|¥|打麻|麻将|输|赢/.test(message.content);
}

export function buildWechatModelMessages(analysis: WechatModelAnalysis, question: string): ChatMessage[] {
  const topMembers = analysis.topMembers
    .slice(0, 12)
    .map((member, index) => `${index + 1}. ${member.name}：${member.messageCount} 条，占 ${member.percent}%，关键词：${member.keywords.join("、") || "无"}`)
    .join("\n");
  const recentMessages = analysis.messages.slice(-160).map(compactMessageLine).join("\n").slice(-24000);
  const paymentEvidence = analysis.messages
    .filter(isPaymentRelatedMessage)
    .slice(-120)
    .map(compactMessageLine)
    .join("\n")
    .slice(-18000);

  return [
    {
      role: "system",
      content:
        "你是一个严谨的微信群聊天记录分析助手。只能基于用户提供的聊天上下文回答，不要编造不存在的消息、人物或时间。回答要直接、具体、中文输出。如果证据不足，要说明不足。涉及个人评价时只做行为观察，不做心理、人格、健康、家庭、身份属性推断。"
    },
    {
      role: "user",
      content: [
        `群聊数据：${analysis.sourceName}`,
        `消息数：${analysis.totalMessages}`,
        `成员数：${analysis.memberCount}`,
        `时间范围：${analysis.timeRange}`,
        "",
        "发言排行：",
        topMembers || "暂无",
        "",
        "最近聊天记录：",
        recentMessages || "暂无",
        "",
        "红包/转账/收款相关记录：",
        paymentEvidence || "暂无",
        "",
        `用户问题：${question}`
      ].join("\n")
    }
  ];
}

export function buildWechatModelInput(analysis: WechatModelAnalysis, question: string) {
  return buildWechatModelMessages(analysis, question)
    .map((message) => `${message.role === "system" ? "系统要求" : "用户上下文"}：\n${message.content}`)
    .join("\n\n");
}

function extractText(payload: unknown) {
  const record = payload as Record<string, unknown>;
  const choices = record.choices as Array<Record<string, unknown>> | undefined;
  const firstChoice = choices?.[0];
  const message = firstChoice?.message as Record<string, unknown> | undefined;
  const content = message?.content;
  if (typeof content === "string") return content.trim();
  if (Array.isArray(content)) {
    return content
      .map((item) => (typeof item === "string" ? item : String((item as Record<string, unknown>)?.text ?? "")))
      .join("")
      .trim();
  }
  if (typeof record.output_text === "string") return record.output_text.trim();
  const output = record.output as Array<Record<string, unknown>> | undefined;
  if (Array.isArray(output)) {
    return output
      .flatMap((item) => (Array.isArray(item.content) ? item.content : []))
      .map((contentItem) => {
        const contentRecord = contentItem as Record<string, unknown>;
        return typeof contentRecord.text === "string" ? contentRecord.text : "";
      })
      .join("")
      .trim();
  }
  return "";
}

export async function answerWechatWithModel(
  analysis: WechatModelAnalysis,
  question: string,
  settings: WechatModelSettings
): Promise<WechatModelResult> {
  if (!settings.apiKey.trim() || !settings.modelName.trim() || !settings.apiBaseUrl.trim()) {
    return { ok: false, message: "模型未配置，请先填写 Base URL、API Key 和模型名称。" };
  }

  const response = await fetch(normalizeResponsesUrl(settings.apiBaseUrl), {
    method: "POST",
    headers: {
      authorization: `Bearer ${settings.apiKey.trim()}`,
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: settings.modelName.trim(),
      input: buildWechatModelInput(analysis, question)
    })
  });

  if (!response.ok) {
    const detail = await response.text();
    return {
      ok: false,
      message: `模型请求失败：HTTP ${response.status}${detail ? `，${detail.slice(0, 300)}` : ""}`
    };
  }

  const text = extractText(await response.json());
  return {
    ok: Boolean(text),
    message: text ? `【助理】\n${text}` : "模型没有返回可读文本。"
  };
}
