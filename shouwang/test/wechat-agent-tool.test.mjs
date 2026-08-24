import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildChatSearchQueries,
  buildWechatVaultRefreshCommand,
  buildWechatAgentMessagesArgs,
  getWechatAgentToolPath,
  parseAgentToolError,
  pickBestChatCandidate
} from "../electron/wechatAgentTool.ts";

test("uses project-local wechat agent tool by default", () => {
  assert.equal(getWechatAgentToolPath(), `${process.cwd()}/wechat-agent-tool/wechat_agent_cli.py`);
});

test("builds incremental vault refresh command before reading chats", () => {
  assert.deepEqual(buildWechatVaultRefreshCommand(), [
    `${process.cwd()}/work/.venv-wechat-vault/bin/python`,
    `${process.env.HOME}/.codex/skills/yichen-wechat-local-vault/scripts/decrypt_all_dbs.py`,
    "--mode",
    "incremental"
  ]);
});

test("builds paginated agent-tool message args with time range", () => {
  assert.deepEqual(
    buildWechatAgentMessagesArgs("天沐锦江老板群", 1000, 2000, "2026-04-01", "2026-08-19"),
    [
      "messages",
      "--chat",
      "天沐锦江老板群",
      "--limit",
      "1000",
      "--offset",
      "2000",
      "--start",
      "2026-04-01",
      "--end",
      "2026-08-19"
    ]
  );
});

test("parses JSON error output from agent tool failures", () => {
  assert.equal(
    parseAgentToolError({ stdout: '{"ok": false, "error": "找不到聊天对象: 天沐浴锦江老板群"}' }),
    "找不到聊天对象: 天沐浴锦江老板群"
  );
});

test("builds fallback chat search queries and picks close candidate", () => {
  assert.deepEqual(buildChatSearchQueries("天沐浴锦江老板群"), ["天沐浴锦江老板群", "锦江", "天沐浴锦江"]);
  assert.deepEqual(
    pickBestChatCandidate("天沐浴锦江老板群", [
      { display_name: "天沐锦江老板群" },
      { display_name: "天沐锦江装修业主群" }
    ]),
    { name: "天沐锦江老板群", distance: 1 }
  );
});
