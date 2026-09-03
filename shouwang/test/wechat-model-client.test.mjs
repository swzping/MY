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

test("summarizes HTML error pages without dumping source", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      "<!doctype html><html><head><title>Bad Gateway</title></head><body><h1>502</h1><p>upstream failed</p></body></html>",
      { status: 502, headers: { "content-type": "text/html; charset=utf-8" } }
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

    assert.equal(result.ok, false);
    assert.match(result.message, /HTTP 502/);
    assert.match(result.message, /Bad Gateway/);
    assert.doesNotMatch(result.message, /<!DOCTYPE html>/i);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("summarizes JSON error messages", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        error: {
          message: "Invalid model name."
        }
      }),
      { status: 400, headers: { "content-type": "application/json" } }
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

    assert.equal(result.ok, false);
    assert.match(result.message, /Invalid model name\./);
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

test("tells the model when raw message context is sampled", () => {
  const messages = Array.from({ length: 200 }, (_, index) => ({
    speaker: `群友${index % 3}`,
    content: `消息 ${index}`,
    timestamp: `2026-08-18 10:${String(index % 60).padStart(2, "0")}`
  }));

  const modelMessages = buildWechatModelMessages(
    {
      sourceName: "群聊",
      totalMessages: messages.length,
      memberCount: 3,
      timeRange: "2026-08-18 10:00 - 2026-08-18 10:59",
      topMembers: [],
      messages
    },
    "为什么拿不到全部数据"
  );

  assert.match(modelMessages[1].content, /完整导入 200 条/);
  assert.match(modelMessages[1].content, /最近 160 条原文/);
  assert.doesNotMatch(modelMessages[1].content, /消息 0/);
  assert.match(modelMessages[1].content, /消息 199/);
});

test("sends all raw messages through full-data chunk analysis", async () => {
  const originalFetch = globalThis.fetch;
  const inputs = [];
  globalThis.fetch = async (_url, init) => {
    const body = JSON.parse(String(init?.body || "{}"));
    inputs.push(body.input);
    const outputText = body.input.includes("分块摘要汇总") ? "最终回答" : "分块摘要";
    return new Response(JSON.stringify({ output_text: outputText }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  };

  try {
    const rawMessages = Array.from({ length: 170 }, (_, index) => ({
      speaker: `群友${index % 2}`,
      content: `完整原文 ${index}`,
      timestamp: `2026-08-18 11:${String(index % 60).padStart(2, "0")}`
    }));

    const result = await answerWechatWithModel(
      {
        sourceName: "群聊",
        totalMessages: rawMessages.length,
        memberCount: 2,
        timeRange: "2026-08-18 11:00 - 2026-08-18 11:59",
        topMembers: [],
        messages: rawMessages
      },
      "请分析全部数据",
      { modelName: "gpt-5.5", apiKey: "sk-test", apiBaseUrl: "https://relay.example.com/v1" }
    );

    assert.equal(result.ok, true);
    assert.match(result.message, /最终回答/);
    assert.equal(inputs.length, 2);
    assert.match(inputs[0], /全量分块分析/);
    assert.match(inputs[0], /完整原文 0/);
    assert.match(inputs[0], /完整原文 169/);
    assert.match(inputs[0], /必须输出本分块的时间范围/);
    assert.match(inputs[0], /不要只摘取最近聊天/);
    assert.match(inputs[1], /分块摘要汇总/);
    assert.match(inputs[1], /分块摘要/);
    assert.match(inputs[1], /已经逐块处理完整导入的 170 条原始消息/);
    assert.match(inputs[1], /不要说自己没有看到完整数据/);
    assert.match(inputs[1], /按全时间线组织回答/);
    assert.match(inputs[1], /早期、中期、近期/);
  } finally {
    globalThis.fetch = originalFetch;
  }
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
