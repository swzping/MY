import { readFile } from "node:fs/promises";
import path from "node:path";
import XLSX from "xlsx";

export type WechatMessage = {
  speaker: string;
  content: string;
  timestamp?: string;
};

export type WechatMemberStats = {
  name: string;
  messageCount: number;
  percent: number;
  keywords: string[];
  activeHours: string[];
  sampleMessages: string[];
  interactions: { name: string; count: number }[];
  tone: string;
};

export type WechatAnalysis = {
  sourceName: string;
  totalMessages: number;
  memberCount: number;
  timeRange: string;
  topMembers: WechatMemberStats[];
  messages: WechatMessage[];
};

export type WechatQuestionResult = {
  ok: boolean;
  message: string;
};

const stopWords = new Set([
  "这个",
  "那个",
  "就是",
  "然后",
  "我们",
  "你们",
  "他们",
  "一下",
  "可以",
  "不是",
  "没有",
  "什么",
  "怎么",
  "还是",
  "因为",
  "所以",
  "哈哈",
  "哈哈哈"
]);

function cleanSpeaker(value: string) {
  return value.replace(/^[@\s]+/, "").trim();
}

function stripMarkdownListMarker(line: string) {
  return line.replace(/^\s*[-*+]\s+/, "").replace(/^\s*\d+\.\s+/, "").trim();
}

function isTimestampOnly(line: string) {
  return /^\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?$/.test(line);
}

function isMarkdownHeading(line: string) {
  return /^#{1,6}\s+/.test(line);
}

function stripNoise(content: string) {
  return content.replace(/\[[^\]]+\]/g, " ").replace(/https?:\/\/\S+/g, " 链接 ");
}

function extractHour(timestamp?: string) {
  if (!timestamp) return "";
  const match = timestamp.match(/\b([01]?\d|2[0-3]):[0-5]\d/);
  if (!match) return "";
  return `${match[1].padStart(2, "0")}:00`;
}

function splitTerms(text: string) {
  const normalized = stripNoise(text);
  const chineseTerms = normalized.match(/[\u4e00-\u9fa5]{2,}/g) ?? [];
  const latinTerms = normalized.match(/[a-zA-Z0-9_]{3,}/g) ?? [];
  return [...chineseTerms, ...latinTerms]
    .map((term) => term.trim())
    .filter((term) => term.length >= 2 && !stopWords.has(term));
}

function parseTextMessages(raw: string): WechatMessage[] {
  const messages: WechatMessage[] = [];
  let current: WechatMessage | null = null;
  let pendingTimestamp = "";
  let pendingSpeaker = "";

  function ensureCurrentIsTracked() {
    if (current && current.speaker && current.content && !messages.includes(current)) {
      messages.push(current);
    }
  }

  for (const originalLine of raw.split(/\r?\n/)) {
    const line = stripMarkdownListMarker(originalLine.trim());
    if (!line) continue;
    if (isMarkdownHeading(line)) continue;

    if (isTimestampOnly(line)) {
      ensureCurrentIsTracked();
      current = null;
      pendingTimestamp = line;
      pendingSpeaker = "";
      continue;
    }

    const messagePatterns = [
      /^(?<time>\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.*)$/,
      /^\[(?<time>[^\]]+)\]\s*(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.*)$/,
      /^(?<speaker>[^:：]{1,40})\s+(?<time>\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s*(?<content>.*)$/,
      /^(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.+)$/
    ];
    const headerPatterns = [
      /^(?<time>\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(?<speaker>[^:：]{1,40})$/,
      /^(?<speaker>[^:：]{1,40})\s+(?<time>\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)$/,
      /^\[(?<time>[^\]]+)\]\s*(?<speaker>[^:：]{1,40})$/
    ];

    const match = messagePatterns.map((pattern) => line.match(pattern)).find(Boolean);
    if (match?.groups) {
      pendingTimestamp = "";
      pendingSpeaker = "";
      ensureCurrentIsTracked();
      current = {
        speaker: cleanSpeaker(match.groups.speaker),
        content: match.groups.content.trim(),
        timestamp: match.groups.time?.trim()
      };
      if (current.speaker && current.content) messages.push(current);
    } else {
      const headerMatch = headerPatterns.map((pattern) => line.match(pattern)).find(Boolean);
      if (headerMatch?.groups) {
        pendingTimestamp = "";
        pendingSpeaker = "";
        ensureCurrentIsTracked();
        current = {
          speaker: cleanSpeaker(headerMatch.groups.speaker),
          content: "",
          timestamp: headerMatch.groups.time?.trim()
        };
      } else if (pendingTimestamp && !pendingSpeaker && line.length <= 40) {
        pendingSpeaker = cleanSpeaker(line);
      } else if (pendingTimestamp && pendingSpeaker) {
        current = {
          speaker: pendingSpeaker,
          content: line,
          timestamp: pendingTimestamp
        };
        ensureCurrentIsTracked();
        pendingTimestamp = "";
        pendingSpeaker = "";
      } else if (current) {
        current.content = current.content ? `${current.content}\n${line}` : line;
        ensureCurrentIsTracked();
      }
    }
  }

  return messages.filter((message) => message.speaker.length <= 40 && message.content);
}

export function readWechatMessagesFromText(raw: string) {
  return parseTextMessages(raw);
}

function parseRows(rows: Record<string, unknown>[]): WechatMessage[] {
  const columns = Object.keys(rows[0] ?? {});
  const speakerColumn = columns.find((column) => /成员|昵称|发送者|发言人|speaker|name/i.test(column)) ?? columns[0];
  const contentColumn = columns.find((column) => /消息|内容|文本|content|message/i.test(column)) ?? columns[1];
  const timeColumn = columns.find((column) => /时间|日期|time|date/i.test(column));

  if (!speakerColumn || !contentColumn) return [];

  return rows
    .map((row) => ({
      speaker: cleanSpeaker(String(row[speakerColumn] ?? "")),
      content: String(row[contentColumn] ?? "").trim(),
      timestamp: timeColumn ? String(row[timeColumn] ?? "").trim() : undefined
    }))
    .filter((message) => message.speaker && message.content);
}

function flattenRecords(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value.flatMap((item) => flattenRecords(item));
  }
  if (!value || typeof value !== "object") return [];

  const record = value as Record<string, unknown>;
  const nestedKeys = ["messages", "data", "items", "list", "records", "chatlogs"];
  for (const key of nestedKeys) {
    if (Array.isArray(record[key])) return flattenRecords(record[key]);
  }
  return [record];
}

function parseJsonMessages(raw: string): WechatMessage[] {
  try {
    const records = flattenRecords(JSON.parse(raw));
    const messages = parseRows(records);
    if (messages.length) return messages;

    return records
      .map((record) => ({
        speaker: cleanSpeaker(
          String(
            record.senderName ??
              record.sender ??
              record.fromName ??
              record.fromUserName ??
              record.speaker ??
              record.name ??
              record.remark ??
              "未知成员"
          )
        ),
        content: String(record.content ?? record.text ?? record.message ?? record.msg ?? record.body ?? "").trim(),
        timestamp: String(record.time ?? record.createTime ?? record.createdAt ?? record.datetime ?? record.date ?? "")
      }))
      .filter((message) => message.speaker && message.content);
  } catch {
    return [];
  }
}

export async function readWechatMessagesFromFile(filePath: string) {
  const extension = path.extname(filePath).toLowerCase();
  if ([".xlsx", ".xls", ".csv"].includes(extension)) {
    const workbook = XLSX.readFile(filePath, { cellDates: true });
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    return parseRows(XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: "" }));
  }

  const raw = await readFile(filePath, "utf-8");
  if (extension === ".json") {
    const messages = parseJsonMessages(raw);
    if (messages.length) return messages;
  }
  return parseTextMessages(raw);
}

export function analyzeWechatMessages(messages: WechatMessage[], sourceName = "剪贴板聊天记录"): WechatAnalysis {
  const bySpeaker = new Map<string, WechatMessage[]>();
  for (const message of messages) {
    bySpeaker.set(message.speaker, [...(bySpeaker.get(message.speaker) ?? []), message]);
  }

  const topMembers = Array.from(bySpeaker.entries())
    .map(([name, memberMessages]) => buildMemberStats(name, memberMessages, messages))
    .sort((a, b) => b.messageCount - a.messageCount);

  const timestamps = messages.map((message) => message.timestamp).filter(Boolean) as string[];

  return {
    sourceName,
    totalMessages: messages.length,
    memberCount: bySpeaker.size,
    timeRange: timestamps.length ? `${timestamps[0]} - ${timestamps[timestamps.length - 1]}` : "未识别时间",
    topMembers,
    messages
  };
}

function buildMemberStats(name: string, memberMessages: WechatMessage[], allMessages: WechatMessage[]): WechatMemberStats {
  const termCount = new Map<string, number>();
  const hourCount = new Map<string, number>();
  const interactionCount = new Map<string, number>();

  for (const message of memberMessages) {
    for (const term of splitTerms(message.content)) {
      termCount.set(term, (termCount.get(term) ?? 0) + 1);
    }
    const hour = extractHour(message.timestamp);
    if (hour) hourCount.set(hour, (hourCount.get(hour) ?? 0) + 1);
    for (const other of new Set(allMessages.map((item) => item.speaker))) {
      if (other !== name && message.content.includes(other)) {
        interactionCount.set(other, (interactionCount.get(other) ?? 0) + 1);
      }
    }
  }

  return {
    name,
    messageCount: memberMessages.length,
    percent: allMessages.length ? Math.round((memberMessages.length / allMessages.length) * 1000) / 10 : 0,
    keywords: topEntries(termCount, 8).map(([term]) => term),
    activeHours: topEntries(hourCount, 3).map(([hour]) => hour),
    sampleMessages: memberMessages
      .filter((message) => message.content.length >= 4)
      .slice(-5)
      .map((message) => message.content.slice(0, 80)),
    interactions: topEntries(interactionCount, 5).map(([interactionName, count]) => ({ name: interactionName, count })),
    tone: inferTone(memberMessages)
  };
}

function topEntries(map: Map<string, number>, limit: number) {
  return Array.from(map.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

function inferTone(messages: WechatMessage[]) {
  const text = messages.map((message) => message.content).join("\n");
  const questionCount = (text.match(/[?？]/g) ?? []).length;
  const laughCount = (text.match(/哈|笑|😂|😄/g) ?? []).length;
  const actionCount = (text.match(/可以|建议|安排|推进|确认|处理|报名|链接|资料/g) ?? []).length;
  if (actionCount >= Math.max(questionCount, laughCount)) return "偏行动推进，常围绕安排、确认和资料流转发言";
  if (questionCount > laughCount) return "偏提问讨论，常通过问题推动信息澄清";
  if (laughCount > 0) return "偏轻松互动，聊天里有较多回应和玩笑语气";
  return "整体中性，主要是信息表达和日常回应";
}

export function answerWechatQuestion(analysis: WechatAnalysis, question: string): WechatQuestionResult {
  const normalized = question.trim();
  if (!analysis.totalMessages) return { ok: false, message: "还没有可分析的聊天记录，请先导入这个群的历史消息。" };

  if (/红包|转账|收款|付款|支付|金额|输赢|谁赢|赢了多少|输了多少/.test(normalized)) {
    const evidence = analysis.messages
      .filter((message) => /红包|转账|收款|付款|支付|金额|￥|¥|打麻|麻将|输|赢/.test(message.content))
      .slice(-30)
      .map((message) => `${message.timestamp ? `[${message.timestamp}] ` : ""}${message.speaker}: ${message.content}`);

    if (!evidence.length) {
      return {
        ok: true,
        message: "当前导入数据里没有识别到明确的红包、转账、收款或支付记录。可能是历史消息没有导入到对应时间范围，也可能是微信支付类消息在 vault 中没有被解析成可读字段。"
      };
    }

    return {
      ok: true,
      message: [
        `我在当前导入数据里找到 ${evidence.length} 条交易或输赢相关证据：`,
        evidence.join("\n"),
        "",
        "结论只能基于这些记录判断；如果只有聊天口头提到收入/输赢，而没有明确红包或转账金额，就不能当作最终结算证明。"
      ].join("\n")
    };
  }

  if (/谁.*活跃|最活跃|发言.*最多/.test(normalized)) {
    const lines = analysis.topMembers.slice(0, 5).map((member, index) => `${index + 1}. ${member.name}：${member.messageCount} 条，占 ${member.percent}%`);
    return { ok: true, message: `这个群最活跃的成员是：\n${lines.join("\n")}` };
  }

  const member = analysis.topMembers.find((item) => normalized.includes(item.name)) ?? analysis.topMembers[0];
  if (!member) return { ok: false, message: "没有识别到要分析的群友。" };

  return {
    ok: true,
    message: [
      `基于当前导入的 ${analysis.totalMessages} 条消息，对「${member.name}」的观察如下：`,
      `- 发言量：${member.messageCount} 条，占全群 ${member.percent}%。`,
      `- 常见话题：${member.keywords.length ? member.keywords.join("、") : "暂未提取到稳定关键词"}。`,
      `- 活跃时间：${member.activeHours.length ? member.activeHours.join("、") : "聊天记录里没有稳定时间信息"}。`,
      `- 互动对象：${member.interactions.length ? member.interactions.map((item) => `${item.name}(${item.count})`).join("、") : "没有明显点名互动"}。`,
      `- 语气特征：${member.tone}。`,
      `- 近期代表内容：${member.sampleMessages.length ? member.sampleMessages.join(" / ") : "暂无可展示样本"}。`,
      "以上是基于聊天文本的行为观察，不等同于心理或人格判断。"
    ].join("\n")
  };
}
