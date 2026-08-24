import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export type AtomicNoteFolder = "概念" | "产品项目" | "论文技术" | "人物组织";

export interface CreateAtomicNoteInput {
  title: string;
  folder: AtomicNoteFolder;
  body: string;
  confirmed: boolean;
}

export interface CreatedAtomicNote {
  path: string;
  relativePath: string;
}

export function normalizeRoot(root: string): string {
  return path.resolve(root);
}

export function resolveKnowledgePath(root: string, relativePath: string): string {
  const resolvedRoot = normalizeRoot(root);
  const fullPath = path.resolve(resolvedRoot, relativePath);
  const relative = path.relative(resolvedRoot, fullPath);

  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Path escapes knowledge base root");
  }

  return fullPath;
}

export async function readKnowledgeFile(root: string, relativePath: string): Promise<string> {
  return readFile(resolveKnowledgePath(root, relativePath), "utf8");
}

export async function readWorkbench(root: string): Promise<string> {
  return readKnowledgeFile(root, "00-入口/今日工作台.md");
}

export async function readSuggestions(root: string): Promise<string> {
  return readKnowledgeFile(root, "00-入口/今日整理建议.md");
}

export async function createAtomicNote(
  root: string,
  input: CreateAtomicNoteInput
): Promise<CreatedAtomicNote> {
  if (!input.confirmed) {
    throw new Error("User confirmation required");
  }

  const title = input.title.trim();
  if (!title) {
    throw new Error("Title is required");
  }

  if (title.includes("/") || title.includes("\\")) {
    throw new Error("Title cannot contain path separators");
  }

  const relativePath = path.posix.join("20-原子知识", input.folder, `${title}.md`);
  const filePath = resolveKnowledgePath(root, relativePath);

  await mkdir(path.dirname(filePath), { recursive: true });

  try {
    await writeFile(filePath, input.body, { flag: "wx" });
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "EEXIST") {
      throw new Error(`Atomic note already exists: ${relativePath}`);
    }
    throw error;
  }

  return { path: filePath, relativePath };
}

