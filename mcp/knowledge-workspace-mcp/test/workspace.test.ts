import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import {
  createAtomicNote,
  readSuggestions,
  readWorkbench,
  resolveKnowledgePath
} from "../src/workspace.js";

let root: string;

beforeEach(async () => {
  root = await mkdtemp(path.join(os.tmpdir(), "knowledge-workspace-"));
  await mkdir(path.join(root, "00-入口"), { recursive: true });
  await mkdir(path.join(root, "20-原子知识", "概念"), { recursive: true });
  await writeFile(path.join(root, "00-入口", "今日工作台.md"), "# 今日工作台\n\n## 待拆解想法\n\n- 做一个 MCP\n");
  await writeFile(path.join(root, "00-入口", "今日整理建议.md"), "# 今日整理建议\n\n建议推进 MCP。\n");
});

afterEach(async () => {
  await rm(root, { recursive: true, force: true });
});

describe("workspace readers", () => {
  test("reads today's workbench from the knowledge base root", async () => {
    const text = await readWorkbench(root);

    expect(text).toContain("# 今日工作台");
    expect(text).toContain("做一个 MCP");
  });

  test("reads today's suggestions from the knowledge base root", async () => {
    const text = await readSuggestions(root);

    expect(text).toContain("# 今日整理建议");
    expect(text).toContain("建议推进 MCP");
  });
});

describe("workspace writes", () => {
  test("rejects atomic note creation until the user confirms", async () => {
    await expect(
      createAtomicNote(root, {
        title: "未确认笔记",
        folder: "概念",
        body: "# 未确认笔记\n",
        confirmed: false
      })
    ).rejects.toThrow("User confirmation required");
  });

  test("creates a confirmed atomic note without overwriting existing files", async () => {
    const created = await createAtomicNote(root, {
      title: "我想做一个怎样的 MCP",
      folder: "概念",
      body: "# 我想做一个怎样的 MCP\n\n## 核心内容\n\n测试。\n",
      confirmed: true
    });

    const text = await readFile(created.path, "utf8");
    expect(created.relativePath).toBe("20-原子知识/概念/我想做一个怎样的 MCP.md");
    expect(text).toContain("# 我想做一个怎样的 MCP");

    await expect(
      createAtomicNote(root, {
        title: "我想做一个怎样的 MCP",
        folder: "概念",
        body: "# overwritten\n",
        confirmed: true
      })
    ).rejects.toThrow("already exists");
  });
});

describe("path safety", () => {
  test("rejects paths that escape the knowledge base root", () => {
    expect(() => resolveKnowledgePath(root, "../outside.md")).toThrow("Path escapes knowledge base root");
  });
});

