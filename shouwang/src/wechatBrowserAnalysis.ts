type BrowserWechatMessage = {
  speaker: string;
  content: string;
  timestamp?: string;
};

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

function parseInlineMessage(line: string): BrowserWechatMessage | null {
  if (isTimestampOnly(line) || isMarkdownHeading(line)) return null;

  const match =
    line.match(/^(?<time>\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.*)$/) ??
    line.match(/^\[(?<time>[^\]]+)\]\s*(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.*)$/) ??
    line.match(/^(?<speaker>[^:：]{1,40})[:：]\s*(?<content>.+)$/);

  if (!match?.groups?.speaker || !match.groups.content?.trim()) return null;
  return {
    speaker: cleanSpeaker(match.groups.speaker),
    content: match.groups.content.trim(),
    timestamp: match.groups.time?.trim()
  };
}

function parseDelimitedRows(raw: string) {
  const lines = raw.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return [];
  const delimiter = raw.includes("\t") ? "\t" : ",";
  const headers = lines[0].split(delimiter).map((item) => item.trim());
  const speakerIndex = headers.findIndex((item) => /成员|昵称|发送者|发言人|speaker|name/i.test(item));
  const contentIndex = headers.findIndex((item) => /消息|内容|文本|content|message/i.test(item));
  const timeIndex = headers.findIndex((item) => /时间|日期|time|date/i.test(item));
  if (speakerIndex < 0 || contentIndex < 0) return [];

  return lines.slice(1).map((line) => {
    const cells = line.split(delimiter);
    return {
      speaker: cleanSpeaker(cells[speakerIndex] ?? ""),
      content: (cells[contentIndex] ?? "").trim(),
      timestamp: timeIndex >= 0 ? (cells[timeIndex] ?? "").trim() : undefined
    };
  }).filter((message) => message.speaker && message.content);
}

function flattenRecords(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) return value.flatMap((item) => flattenRecords(item));
  if (!value || typeof value !== "object") return [];
  const record = value as Record<string, unknown>;
  for (const key of ["messages", "data", "items", "list", "records", "chatlogs"]) {
    if (Array.isArray(record[key])) return flattenRecords(record[key]);
  }
  return [record];
}

function parseJsonMessages(raw: string): BrowserWechatMessage[] {
  try {
    return flattenRecords(JSON.parse(raw)).map((record) => ({
      speaker: cleanSpeaker(
        String(record.senderName ?? record.sender ?? record.fromName ?? record.fromUserName ?? record.speaker ?? record.name ?? "未知成员")
      ),
      content: String(record.content ?? record.text ?? record.message ?? record.msg ?? record.body ?? "").trim(),
      timestamp: String(record.time ?? record.createTime ?? record.createdAt ?? record.datetime ?? record.date ?? "")
    })).filter((message) => message.speaker && message.content);
  } catch {
    return [];
  }
}

export function parseWechatTextForBrowser(raw: string): BrowserWechatMessage[] {
  const jsonMessages = parseJsonMessages(raw);
  if (jsonMessages.length) return jsonMessages;

  const rowMessages = parseDelimitedRows(raw);
  if (rowMessages.length) return rowMessages;

  const messages: BrowserWechatMessage[] = [];
  let pendingTimestamp = "";
  let pendingSpeaker = "";

  for (const originalLine of raw.split(/\r?\n/)) {
    const line = stripMarkdownListMarker(originalLine.trim());
    if (!line || isMarkdownHeading(line)) continue;

    if (isTimestampOnly(line)) {
      pendingTimestamp = line;
      pendingSpeaker = "";
      continue;
    }

    const inlineMessage = parseInlineMessage(line);
    if (inlineMessage) {
      messages.push(inlineMessage);
      pendingTimestamp = "";
      pendingSpeaker = "";
      continue;
    }

    if (pendingTimestamp && !pendingSpeaker && line.length <= 40) {
      pendingSpeaker = cleanSpeaker(line);
      continue;
    }

    if (pendingTimestamp && pendingSpeaker) {
      messages.push({
        speaker: pendingSpeaker,
        content: line,
        timestamp: pendingTimestamp
      });
      pendingTimestamp = "";
      pendingSpeaker = "";
    }
  }

  return messages.filter((message) => message.speaker && message.content);
}

function topEntries(map: Map<string, number>, limit: number) {
  return Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, limit);
}

export function analyzeWechatForBrowser(messages: BrowserWechatMessage[], sourceName: string): WechatAnalysis {
  const bySpeaker = new Map<string, BrowserWechatMessage[]>();
  for (const message of messages) {
    bySpeaker.set(message.speaker, [...(bySpeaker.get(message.speaker) ?? []), message]);
  }

  const topMembers = Array.from(bySpeaker.entries()).map(([name, memberMessages]) => {
    const terms = new Map<string, number>();
    for (const message of memberMessages) {
      for (const term of message.content.match(/[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9_]{3,}/g) ?? []) {
        terms.set(term, (terms.get(term) ?? 0) + 1);
      }
    }
    return {
      name,
      messageCount: memberMessages.length,
      percent: messages.length ? Math.round((memberMessages.length / messages.length) * 1000) / 10 : 0,
      keywords: topEntries(terms, 8).map(([term]) => term),
      activeHours: [],
      sampleMessages: memberMessages.slice(0, 3).map((message) => message.content),
      interactions: [],
      tone: "根据已导入文本做本地规则分析"
    };
  }).sort((a, b) => b.messageCount - a.messageCount);

  const timestamps = messages.map((message) => message.timestamp).filter(Boolean);
  return {
    sourceName,
    totalMessages: messages.length,
    memberCount: bySpeaker.size,
    timeRange: timestamps.length ? `${timestamps[0]} - ${timestamps[timestamps.length - 1]}` : "未识别时间",
    topMembers,
    messages
  };
}

export function answerWechatForBrowser(analysis: WechatAnalysis, question: string): WechatQuestionResult {
  const member = analysis.topMembers.find((item) => question.includes(item.name));
  if (member) {
    return {
      ok: true,
      message: `${member.name} 共发言 ${member.messageCount} 条，占 ${member.percent}%。常见关键词：${member.keywords.join("、") || "暂未提取"}。\n\n代表消息：\n${member.sampleMessages.map((item) => `- ${item}`).join("\n")}`
    };
  }

  const top = analysis.topMembers.slice(0, 5);
  return {
    ok: true,
    message: `这份数据共 ${analysis.totalMessages} 条消息，${analysis.memberCount} 位成员。最活跃的是：${top.map((item) => `${item.name} ${item.messageCount} 条`).join("、")}。`
  };
}
