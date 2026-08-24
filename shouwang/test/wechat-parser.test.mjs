import assert from "node:assert/strict";
import { test } from "node:test";
import {
  analyzeWechatForBrowser,
  parseWechatTextForBrowser
} from "../src/wechatBrowserAnalysis.ts";
import {
  analyzeWechatMessages,
  answerWechatQuestion
} from "../electron/wechatAnalysis.ts";

test("does not treat timestamp-only markdown lines as speakers", () => {
  const raw = [
    "# 群聊记录",
    "2026-08-13 21:03",
    "张三",
    "今晚确认预算",
    "",
    "2026-08-13 21:05",
    "李四",
    "预算我看可以推进",
    "",
    "2026-08-13 21:07",
    "张三",
    "我来整理方案"
  ].join("\n");

  const messages = parseWechatTextForBrowser(raw);
  const analysis = analyzeWechatForBrowser(messages, "sample.md");

  assert.equal(analysis.totalMessages, 3);
  assert.deepEqual(
    analysis.topMembers.map((member) => member.name),
    ["张三", "李四"]
  );
  assert.equal(analysis.topMembers[0].messageCount, 2);
});

test("does not treat markdown bullet timestamp lines as speakers", () => {
  const raw = [
    "# 群聊记录",
    "- 2026-08-13 21:03",
    "- 张三",
    "- 今晚确认预算",
    "",
    "- 2026-08-13 21:05",
    "- 李四",
    "- 预算我看可以推进",
    "",
    "- 2026-08-13 21:07",
    "- 张三",
    "- 我来整理方案"
  ].join("\n");

  const messages = parseWechatTextForBrowser(raw);
  const analysis = analyzeWechatForBrowser(messages, "sample.md");

  assert.equal(analysis.totalMessages, 3);
  assert.deepEqual(
    analysis.topMembers.map((member) => member.name),
    ["张三", "李四"]
  );
  assert.equal(analysis.topMembers[0].messageCount, 2);
});

test("local WeChat answers surface payment evidence directly", () => {
  const analysis = analyzeWechatMessages(
    [
      { speaker: "张三", content: "今天打麻将结束后结一下", timestamp: "2026-08-16 20:00:00" },
      { speaker: "李四", content: "[转账] 金额：¥60；状态：已收款", timestamp: "2026-08-16 21:00:00" }
    ],
    "sample"
  );

  const result = answerWechatQuestion(analysis, "今天谁转账了多少钱");

  assert.equal(result.ok, true);
  assert.match(result.message, /交易或输赢相关证据/);
  assert.match(result.message, /\[转账\] 金额：¥60/);
});
