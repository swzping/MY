import assert from "node:assert/strict";
import { test } from "node:test";

import {
  answerWechatWithModel,
  buildWechatModelInput,
  buildWechatModelMessages,
  normalizeResponsesUrl
} from "../shared/wechatModelClient.ts";

test("normalizes OpenAI-compatible base URLs to responses endpoint", () => {
  assert.equal(normalizeResponsesUrl("https://relay.example.com"), "https://relay.example.com/v1/responses");
  assert.equal(normalizeResponsesUrl("https://relay.example.com/v1"), "https://relay.example.com/v1/responses");
  assert.equal(normalizeResponsesUrl("https://relay.example.com/v1/responses"), "https://relay.example.com/v1/responses");
});

test("reads text from Responses API output content", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        output: [
          {
            content: [{ type: "output_text", text: "OK" }]
          }
        ]
      }),
      { status: 200, headers: { "content-type": "application/json" } }
    );

  try {
    const result = await answerWechatWithModel(
      {
        sourceName: "群聊",
        totalMessages: 1,
        memberCount: 1,
        timeRange: "未识别时间",
        topMembers: [],
        messages: [{ speaker: "张三", content: "测试消息" }]
      },
      "问一下",
      { modelName: "gpt-5.5", apiKey: "sk-test", apiBaseUrl: "https://relay.example.com/v1" }
    );

    assert.equal(result.ok, true);
    assert.match(result.message, /【助理】\nOK/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("builds bounded WeChat context with recent messages", () => {
  const messages = buildWechatModelMessages(
    {
      sourceName: "群聊",
      totalMessages: 2,
      memberCount: 2,
      timeRange: "2026-08-18 09:00 - 2026-08-18 09:05",
      topMembers: [
        {
          name: "张三",
          messageCount: 1,
          percent: 50,
          keywords: ["物业"],
          activeHours: [],
          sampleMessages: [],
          interactions: [],
          tone: "中性"
        }
      ],
      messages: [
        { speaker: "张三", content: "物业说今天处理停车位", timestamp: "2026-08-18 09:00" },
        { speaker: "李四", content: "最新消息是下午三点开会", timestamp: "2026-08-18 09:05" }
      ]
    },
    "最新消息是什么"
  );

  assert.equal(messages.at(-1)?.role, "user");
  assert.match(messages[1].content, /最新消息是下午三点开会/);
  assert.match(messages[1].content, /张三：1 条/);
  assert.match(buildWechatModelInput(
    {
      sourceName: "群聊",
      totalMessages: 1,
      memberCount: 1,
      timeRange: "未识别时间",
      topMembers: [],
      messages: [{ speaker: "张三", content: "测试消息" }]
    },
    "问一下"
  ), /input|用户上下文|测试消息/);
});

test("adds payment evidence outside the recent-message window", () => {
  const oldMessages = Array.from({ length: 170 }, (_, index) => ({
    speaker: "群友",
    content: index === 0 ? "[转账] 金额：¥60；状态：已收款" : `普通消息 ${index}`,
    timestamp: `2026-08-16 10:${String(index % 60).padStart(2, "0")}`
  }));

  const messages = buildWechatModelMessages(
    {
      sourceName: "群聊",
      totalMessages: oldMessages.length,
      memberCount: 1,
      timeRange: "2026-08-16 10:00 - 2026-08-16 10:59",
      topMembers: [],
      messages: oldMessages
    },
    "谁转账了"
  );

  assert.match(messages[1].content, /红包\/转账\/收款相关记录/);
  assert.match(messages[1].content, /\[转账\] 金额：¥60/);
});
