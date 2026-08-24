import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  createAtomicNote,
  readSuggestions,
  readWorkbench,
  type AtomicNoteFolder
} from "./workspace.js";

const knowledgeBaseRoot = process.env.KNOWLEDGE_BASE_ROOT ?? "/Users/edy/Documents/SW";

const server = new McpServer({
  name: "knowledge-workspace",
  version: "0.1.0"
});

server.registerTool(
  "read_workbench",
  {
    title: "Read knowledge workbench",
    description: "Read 00-入口/今日工作台.md from the configured knowledge base.",
    inputSchema: {}
  },
  async () => {
    const text = await readWorkbench(knowledgeBaseRoot);
    return {
      content: [{ type: "text", text }]
    };
  }
);

server.registerTool(
  "read_suggestions",
  {
    title: "Read daily suggestions",
    description: "Read 00-入口/今日整理建议.md from the configured knowledge base.",
    inputSchema: {}
  },
  async () => {
    const text = await readSuggestions(knowledgeBaseRoot);
    return {
      content: [{ type: "text", text }]
    };
  }
);

server.registerTool(
  "create_atomic_note",
  {
    title: "Create atomic note",
    description:
      "Create a Markdown atomic note under 20-原子知识 after explicit user confirmation.",
    inputSchema: {
      title: z.string().min(1).describe("Note title without .md"),
      folder: z.enum(["概念", "产品项目", "论文技术", "人物组织"]).describe("Atomic note folder"),
      body: z.string().min(1).describe("Full Markdown body to write"),
      confirmed: z
        .boolean()
        .describe("Must be true only after the user explicitly confirms the write")
    }
  },
  async ({ title, folder, body, confirmed }) => {
    const result = await createAtomicNote(knowledgeBaseRoot, {
      title,
      folder: folder as AtomicNoteFolder,
      body,
      confirmed
    });

    return {
      content: [
        {
          type: "text",
          text: `Created ${result.relativePath}`
        }
      ]
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);

