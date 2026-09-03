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

const DIRECT_CONTEXT_MESSAGE_LIMIT = 160;
const FULL_DATA_CHUNK_CHAR_LIMIT = 28000;

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
  const recentWindowSize = Math.min(analysis.messages.length, DIRECT_CONTEXT_MESSAGE_LIMIT);
  const topMembers = analysis.topMembers
    .slice(0, 12)
    .map((member, index) => `${index + 1}. ${member.name}：${member.messageCount} 条，占 ${member.percent}%，关键词：${member.keywords.join("、") || "无"}`)
    .join("\n");
  const recentMessages = analysis.messages.slice(-DIRECT_CONTEXT_MESSAGE_LIMIT).map(compactMessageLine).join("\n").slice(-24000);
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
        `上下文覆盖：本地完整导入 ${analysis.totalMessages} 条；本次模型输入包含统计摘要、最近 ${recentWindowSize} 条原文，以及最多 120 条红包/转账/支付相关补充证据。没有出现在原文片段里的早期普通消息，不应被当作已逐条阅读。`,
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

function summarizeErrorBody(body: string, contentType: string) {
  const trimmed = body.trim();
  if (!trimmed) return "";

  if (contentType.includes("application/json")) {
    try {
      const parsed = JSON.parse(trimmed) as Record<string, unknown>;
      const error = parsed.error as Record<string, unknown> | undefined;
      const message =
        (error?.message as string | undefined) ??
        (parsed.message as string | undefined) ??
        (parsed.detail as string | undefined);
      if (typeof message === "string" && message.trim()) {
        return message.trim();
      }
    } catch {
      // Fall through to text handling below.
    }
  }

  if (contentType.includes("text/html") || /^<!doctype html/i.test(trimmed) || /^<html/i.test(trimmed)) {
    const title = trimmed.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/\s+/g, " ").trim();
    if (title) return `上游返回 HTML 错页：${title}`;

    const text = trimmed
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return text ? `上游返回 HTML 错页：${text.slice(0, 120)}` : "上游返回 HTML 错页";
  }

  const compact = trimmed.replace(/\s+/g, " ");
  return compact.length > 160 ? `${compact.slice(0, 160)}…` : compact;
}

function buildTopMembersSummary(analysis: WechatModelAnalysis) {
  return analysis.topMembers
    .slice(0, 20)
    .map((member, index) => `${index + 1}. ${member.name}：${member.messageCount} 条，占 ${member.percent}%，关键词：${member.keywords.join("、") || "无"}`)
    .join("\n");
}

function buildFullDataChunks(messages: WechatModelAnalysis["messages"]) {
  const chunks: string[] = [];
  let current: string[] = [];
  let currentLength = 0;

  for (const message of messages) {
    const line = compactMessageLine(message);
    const lineLength = line.length + 1;
    if (current.length && currentLength + lineLength > FULL_DATA_CHUNK_CHAR_LIMIT) {
      chunks.push(current.join("\n"));
      current = [];
      currentLength = 0;
    }
    current.push(line);
    currentLength += lineLength;
  }

  if (current.length) chunks.push(current.join("\n"));
  return chunks;
}

function buildChunkAnalysisInput(
  analysis: WechatModelAnalysis,
  question: string,
  chunkText: string,
  chunkIndex: number,
  chunkCount: number
) {
  return [
    "全量分块分析",
    `群聊数据：${analysis.sourceName}`,
    `完整导入消息数：${analysis.totalMessages}`,
    `成员数：${analysis.memberCount}`,
    `时间范围：${analysis.timeRange}`,
    `当前分块：${chunkIndex + 1}/${chunkCount}`,
    "",
    "任务：",
    "请只基于当前分块原文，提取与用户问题相关的事实、时间、人物、金额、结论和不确定点。",
    "必须输出本分块的时间范围、消息数量判断、与用户问题相关的代表证据。不要只摘取最近聊天，也不要忽略本分块前半段。",
    "如果用户问题涉及关系、情绪、付出、变化或趋势，必须分别提取本分块里早期、中期、近期的证据；某一阶段没有证据就写明没有。",
    "如果当前分块没有相关信息，请回答“本分块未发现相关证据”。不要综合其他分块，不要编造。",
    "输出格式：",
    "1. 本块范围：",
    "2. 本块核心证据：",
    "3. 本块时间变化：早期 / 中期 / 近期",
    "4. 本块不足：",
    "",
    "用户问题：",
    question,
    "",
    "当前分块原文：",
    chunkText
  ].join("\n");
}

function buildFinalSynthesisInput(analysis: WechatModelAnalysis, question: string, chunkSummaries: string[]) {
  return [
    "分块摘要汇总",
    `群聊数据：${analysis.sourceName}`,
    `完整导入消息数：${analysis.totalMessages}`,
    `成员数：${analysis.memberCount}`,
    `时间范围：${analysis.timeRange}`,
    `已处理原文分块数：${chunkSummaries.length}`,
    `覆盖说明：模型已经逐块处理完整导入的 ${analysis.messages.length} 条原始消息；每条原文都进入了前序分块分析。`,
    "",
    "发言排行：",
    buildTopMembersSummary(analysis) || "暂无",
    "",
    "用户问题：",
    question,
    "",
    "各分块证据摘要：",
    chunkSummaries.map((summary, index) => `【分块 ${index + 1}】\n${summary}`).join("\n\n"),
    "",
    "请基于全部分块证据和全局统计给出最终中文回答。说明主要依据；证据不足时直接说不足；不要把分块摘要之外的信息当成事实。",
    "必须按全时间线组织回答，至少覆盖早期、中期、近期三个阶段；不要只基于最后几天或最后一个分块下结论。",
    "如果早期、中期、近期的互动强度、表达方式、付出方式有变化，要先描述变化，再给总体判断。",
    "当用户问你分析了多少数据、是否看到了全部数据时，必须说明已经通过分块方式处理全部原始消息，不要说自己没有看到完整数据。"
  ].join("\n");
}

async function callResponsesApi(input: string, settings: WechatModelSettings) {
  const response = await fetch(normalizeResponsesUrl(settings.apiBaseUrl), {
    method: "POST",
    headers: {
      authorization: `Bearer ${settings.apiKey.trim()}`,
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: settings.modelName.trim(),
      input
    })
  });

  if (!response.ok) {
    const detail = summarizeErrorBody(await response.text(), response.headers.get("content-type") || "");
    return {
      ok: false,
      message: `模型请求失败：HTTP ${response.status}${detail ? `，${detail}` : ""}`
    };
  }

  const text = extractText(await response.json());
  return {
    ok: Boolean(text),
    message: text || "模型没有返回可读文本。"
  };
}

async function answerWechatWithFullDataModel(
  analysis: WechatModelAnalysis,
  question: string,
  settings: WechatModelSettings
): Promise<WechatModelResult> {
  const chunks = buildFullDataChunks(analysis.messages);
  const chunkSummaries: string[] = [];

  for (const [index, chunk] of chunks.entries()) {
    const result = await callResponsesApi(buildChunkAnalysisInput(analysis, question, chunk, index, chunks.length), settings);
    if (!result.ok) {
      return {
        ok: false,
        message: `全量分块分析失败：第 ${index + 1}/${chunks.length} 块失败。\n${result.message}`
      };
    }
    chunkSummaries.push(result.message);
  }

  const finalResult = await callResponsesApi(buildFinalSynthesisInput(analysis, question, chunkSummaries), settings);
  return {
    ok: finalResult.ok,
    message: finalResult.ok
      ? `【助理】\n${finalResult.message}\n\n【全量分析说明】已让模型处理 ${analysis.messages.length} 条原文，分为 ${chunks.length} 个分块后汇总。`
      : finalResult.message
  };
}

export async function answerWechatWithModel(
  analysis: WechatModelAnalysis,
  question: string,
  settings: WechatModelSettings
): Promise<WechatModelResult> {
  if (!settings.apiKey.trim() || !settings.modelName.trim() || !settings.apiBaseUrl.trim()) {
    return { ok: false, message: "模型未配置，请先填写 Base URL、API Key 和模型名称。" };
  }

  if (analysis.messages.length > DIRECT_CONTEXT_MESSAGE_LIMIT) {
    return answerWechatWithFullDataModel(analysis, question, settings);
  }

  const result = await callResponsesApi(buildWechatModelInput(analysis, question), settings);
  return {
    ok: result.ok,
    message: result.ok ? `【助理】\n${result.message}` : result.message
  };
}
