# Study Tag Cloud Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent frontend page for `study/` that generates a synchronized tag cloud from Markdown notes, groups tags by category, and shows tag summaries on hover/focus/click.

**Architecture:** Create a standalone Vite React app in `study-site/`. A Node generation script scans `study/**/*.md`, applies lightweight taxonomy rules, and writes `study-site/src/data/study-data.json`; React components consume that JSON for filters, tag cloud rendering, and detail panels.

**Tech Stack:** Node.js, Vite, React, TypeScript, Vitest, CSS modules/global CSS, no backend server.

---

## File Structure

- Create `study-site/package.json`: app scripts for dev, build, test, and study data generation.
- Create `study-site/index.html`, `study-site/tsconfig.json`, `study-site/vite.config.ts`: Vite React project setup.
- Create `study-site/scripts/study-taxonomy.ts`: taxonomy rules, Markdown parsing, and pure data generation functions.
- Create `study-site/scripts/generate-study-data.ts`: CLI wrapper that reads `/study` and writes JSON.
- Create `study-site/scripts/study-taxonomy.test.ts`: Vitest coverage for category inference, description extraction, and related tags.
- Create `study-site/src/data/study-data.json`: generated data file.
- Create `study-site/src/types.ts`: shared `StudyTag`, `StudyDocument`, and category types.
- Create `study-site/src/App.tsx`: page composition and state.
- Create `study-site/src/components/CategoryFilter.tsx`: category buttons.
- Create `study-site/src/components/TagCloud.tsx`: categorized tag rendering.
- Create `study-site/src/components/TagTooltip.tsx`: hover/focus/click summary popover.
- Create `study-site/src/components/StudyHighlights.tsx`: selected tag details, reading paths, and source documents.
- Create `study-site/src/main.tsx` and `study-site/src/index.css`: app entry and visual system.

## Task 1: Scaffold Vite React App And Test Harness

**Files:**
- Create: `study-site/package.json`
- Create: `study-site/index.html`
- Create: `study-site/tsconfig.json`
- Create: `study-site/vite.config.ts`
- Create: `study-site/src/main.tsx`
- Create: `study-site/src/App.tsx`
- Create: `study-site/src/index.css`

- [ ] **Step 1: Create project manifest**

Create `study-site/package.json`:

```json
{
  "name": "study-site",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "generate:study": "tsx scripts/generate-study-data.ts"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.4.1",
    "vite": "^6.3.5",
    "typescript": "~5.8.3",
    "tsx": "^4.20.3",
    "vitest": "^3.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.511.0"
  },
  "devDependencies": {
    "@types/node": "^22.15.30",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1"
  }
}
```

- [ ] **Step 2: Create Vite config files**

Create `study-site/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Study Knowledge Atlas</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `study-site/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "types": ["node", "vitest/globals"]
  },
  "include": ["src", "scripts"]
}
```

Create `study-site/vite.config.ts`:

```ts
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
});
```

- [ ] **Step 3: Create minimal React entry**

Create `study-site/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `study-site/src/App.tsx`:

```tsx
export default function App() {
  return (
    <main className="app-shell">
      <h1>Study Knowledge Atlas</h1>
    </main>
  );
}
```

Create `study-site/src/index.css`:

```css
:root {
  color: #d8e2ff;
  background: #0d1117;
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  padding: 32px;
}
```

- [ ] **Step 4: Install dependencies**

Run:

```bash
cd study-site && npm install
```

Expected: `package-lock.json` is created and npm exits with code 0.

- [ ] **Step 5: Verify scaffold builds**

Run:

```bash
cd study-site && npm run build
```

Expected: TypeScript and Vite build complete successfully.

## Task 2: Generate Study Data With TDD

**Files:**
- Create: `study-site/scripts/study-taxonomy.test.ts`
- Create: `study-site/scripts/study-taxonomy.ts`
- Create: `study-site/scripts/generate-study-data.ts`
- Create: `study-site/src/types.ts`
- Create: `study-site/src/data/study-data.json`

- [ ] **Step 1: Write failing tests for taxonomy generation**

Create `study-site/scripts/study-taxonomy.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { buildStudyData, inferTagCategory, summarizeMarkdown } from './study-taxonomy';

describe('study taxonomy', () => {
  it('categorizes known terms by taxonomy rules', () => {
    expect(inferTagCategory('MCP', 'study/ai-tools/mcp-notes.md')).toBe('term');
    expect(inferTagCategory('Codex', 'study/ai-tools/agent-engineering.md')).toBe('agent');
    expect(inferTagCategory('TradingAgents', 'study/ai-tools/projects.md')).toBe('project');
    expect(inferTagCategory('官方文档', 'study/ai-tools/people-and-resources.md')).toBe('resource');
    expect(inferTagCategory('AI 圈新闻', 'study/news-trends/classification.md')).toBe('trend');
  });

  it('extracts the first useful paragraph as a hover summary', () => {
    const markdown = [
      '# MCP 笔记',
      '',
      '这里整理 MCP 的定位和边界。',
      '',
      '## 为什么需要 MCP',
      '',
      'MCP 让 AI 客户端连接外部工具。',
    ].join('\\n');

    expect(summarizeMarkdown(markdown)).toBe('这里整理 MCP 的定位和边界。');
  });

  it('builds tags with source documents and related tags', () => {
    const files = [
      {
        path: 'study/ai-tools/mcp-notes.md',
        content: '# MCP 笔记\\n\\nMCP 是能力接入协议。\\n\\n## Tools、Resources、Prompts 的区别\\n\\n## 和 Skill 的区别',
      },
      {
        path: 'study/ai-tools/agent-engineering.md',
        content: '# Agent 工程总览\\n\\nCodex 是 coding agent。\\n\\n## MCP 的位置\\n\\n## Skill 的位置',
      },
    ];

    const data = buildStudyData(files);
    const mcp = data.tags.find((tag) => tag.name === 'MCP');

    expect(mcp).toMatchObject({
      name: 'MCP',
      category: 'term',
      description: 'MCP 是能力接入协议。',
    });
    expect(mcp?.sources).toContain('study/ai-tools/mcp-notes.md');
    expect(mcp?.related).toContain('Skill');
    expect(data.documents).toHaveLength(2);
  });
});
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd study-site && npm test -- scripts/study-taxonomy.test.ts
```

Expected: FAIL because `scripts/study-taxonomy.ts` does not exist.

- [ ] **Step 3: Create shared types**

Create `study-site/src/types.ts`:

```ts
export type StudyTagCategory = 'term' | 'agent' | 'resource' | 'project' | 'trend' | 'action';

export interface StudyDocument {
  path: string;
  title: string;
  summary: string;
  category: StudyTagCategory;
}

export interface StudyTag {
  name: string;
  category: StudyTagCategory;
  description: string;
  weight: number;
  sources: string[];
  related: string[];
}

export interface StudyData {
  generatedAt: string;
  documents: StudyDocument[];
  tags: StudyTag[];
}
```

- [ ] **Step 4: Implement minimal taxonomy generator**

Create `study-site/scripts/study-taxonomy.ts`:

```ts
import type { StudyData, StudyDocument, StudyTag, StudyTagCategory } from '../src/types';

export interface MarkdownFile {
  path: string;
  content: string;
}

const CATEGORY_LABELS: Record<StudyTagCategory, string> = {
  term: '概念 / 名词 / 术语',
  agent: 'Agent / 工具 / 平台',
  resource: '收藏地址 / 人物 / 资源',
  project: '项目 / 案例 / 模板',
  trend: '新闻趋势',
  action: '学习行动',
};

const TERM_TAGS = ['MCP', 'Skill', 'LangGraph', 'Workflow', 'Tool', 'Memory', 'Eval', 'Context', 'Resources', 'Prompts'];
const AGENT_TAGS = ['Codex', 'Claude Code', 'Hermes Agent', 'OpenClaw', 'Cursor', 'AI Model Hub', 'AiToEarn'];
const RESOURCE_TAGS = ['官方文档', 'GitHub', 'Skills Catalog', 'Michael Sitarzewski', 'API Docs', '论文', '博客'];
const PROJECT_TAGS = ['TradingAgents', 'TradingAgents-CN', 'a-stock-data', 'QuantDinger', 'AI-Trader', 'Agent 项目结构模板'];
const TREND_TAGS = ['AI 圈新闻', '技术更新', '社会热点', '行业热点', '经济热点'];
const ACTION_TAGS = ['观察', '立即试用', '深入学习', '记录案例', '暂不跟进'];

const TAG_RULES: Array<{ category: StudyTagCategory; names: string[] }> = [
  { category: 'term', names: TERM_TAGS },
  { category: 'agent', names: AGENT_TAGS },
  { category: 'resource', names: RESOURCE_TAGS },
  { category: 'project', names: PROJECT_TAGS },
  { category: 'trend', names: TREND_TAGS },
  { category: 'action', names: ACTION_TAGS },
];

export function inferTagCategory(name: string, path: string): StudyTagCategory {
  for (const rule of TAG_RULES) {
    if (rule.names.includes(name)) return rule.category;
  }
  if (path.includes('projects') || path.includes('templates/')) return 'project';
  if (path.includes('people-and-resources')) return 'resource';
  if (path.includes('news-trends')) return 'trend';
  return 'term';
}

export function summarizeMarkdown(markdown: string): string {
  const lines = markdown
    .split('\\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && !line.startsWith('|') && !line.startsWith('---') && !line.startsWith('```'));
  const first = lines.find((line) => !line.startsWith('- ') && !/^\\d+\\./.test(line));
  return first ? trimSentence(first) : '这是一条来自 study 笔记的学习标签。';
}

export function buildStudyData(files: MarkdownFile[]): StudyData {
  const documents: StudyDocument[] = files.map((file) => {
    const title = extractTitle(file.content) ?? file.path.split('/').pop() ?? file.path;
    return {
      path: file.path,
      title,
      summary: summarizeMarkdown(file.content),
      category: inferTagCategory(title.replace(/ 笔记| 总览| 项目整理/g, ''), file.path),
    };
  });

  const tagMap = new Map<string, StudyTag>();

  for (const file of files) {
    const candidates = collectCandidates(file);
    for (const candidate of candidates) {
      const category = inferTagCategory(candidate, file.path);
      const existing = tagMap.get(candidate);
      if (existing) {
        existing.weight += 1;
        if (!existing.sources.includes(file.path)) existing.sources.push(file.path);
        continue;
      }

      tagMap.set(candidate, {
        name: candidate,
        category,
        description: buildDescription(candidate, category, file.content),
        weight: baseWeight(candidate),
        sources: [file.path],
        related: [],
      });
    }
  }

  const tags = Array.from(tagMap.values())
    .map((tag) => ({
      ...tag,
      related: Array.from(
        new Set(
          Array.from(tagMap.values())
            .filter((other) => other.name !== tag.name && sharesSource(tag, other))
            .slice(0, 6)
            .map((other) => other.name),
        ),
      ),
    }))
    .sort((a, b) => b.weight - a.weight || a.name.localeCompare(b.name));

  return {
    generatedAt: new Date().toISOString(),
    documents,
    tags,
  };
}

export { CATEGORY_LABELS, TAG_RULES };

function collectCandidates(file: MarkdownFile): string[] {
  const headings = file.content
    .split('\\n')
    .map((line) => line.match(/^#{1,3}\\s+(.+)$/)?.[1]?.trim())
    .filter((heading): heading is string => Boolean(heading))
    .map(cleanHeading);

  const known = TAG_RULES.flatMap((rule) => rule.names).filter((name) => file.content.includes(name));
  return Array.from(new Set([...known, ...headings])).filter((name) => name.length >= 2 && name.length <= 32);
}

function extractTitle(content: string): string | undefined {
  return content.match(/^#\\s+(.+)$/m)?.[1]?.trim();
}

function cleanHeading(heading: string): string {
  return heading.replace(/^\\d+[.、]\\s*/, '').replace(/`/g, '').trim();
}

function trimSentence(text: string): string {
  return text.length > 92 ? `${text.slice(0, 91)}...` : text;
}

function buildDescription(name: string, category: StudyTagCategory, markdown: string): string {
  const escaped = name.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
  const line = markdown
    .split('\\n')
    .map((item) => item.trim())
    .find((item) => new RegExp(escaped, 'i').test(item) && !item.startsWith('#'));
  return line ? trimSentence(line.replace(/^-\\s*/, '')) : `${name} 属于${CATEGORY_LABELS[category]}，来自 study 学习笔记。`;
}

function baseWeight(name: string): number {
  if (['MCP', 'Skill', 'LangGraph', 'Codex', 'Claude Code', 'TradingAgents'].includes(name)) return 8;
  if (name.length <= 8) return 5;
  return 3;
}

function sharesSource(left: StudyTag, right: StudyTag): boolean {
  return left.sources.some((source) => right.sources.includes(source));
}
```

- [ ] **Step 5: Run tests and verify GREEN**

Run:

```bash
cd study-site && npm test -- scripts/study-taxonomy.test.ts
```

Expected: PASS.

- [ ] **Step 6: Create CLI data generator**

Create `study-site/scripts/generate-study-data.ts`:

```ts
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { buildStudyData, type MarkdownFile } from './study-taxonomy';

const root = path.resolve(process.cwd(), '..');
const studyDir = path.join(root, 'study');
const outputFile = path.join(process.cwd(), 'src/data/study-data.json');

async function main() {
  const files = await readMarkdownFiles(studyDir);
  const data = buildStudyData(files);
  await fs.mkdir(path.dirname(outputFile), { recursive: true });
  await fs.writeFile(outputFile, `${JSON.stringify(data, null, 2)}\\n`, 'utf8');
  console.log(`Generated ${data.tags.length} tags from ${data.documents.length} documents.`);
}

async function readMarkdownFiles(dir: string): Promise<MarkdownFile[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) return readMarkdownFiles(fullPath);
      if (!entry.isFile() || !entry.name.endsWith('.md')) return [];
      const content = await fs.readFile(fullPath, 'utf8');
      return [{ path: path.relative(root, fullPath), content }];
    }),
  );
  return files.flat().sort((a, b) => a.path.localeCompare(b.path));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

- [ ] **Step 7: Generate initial JSON data**

Run:

```bash
cd study-site && npm run generate:study
```

Expected: `study-site/src/data/study-data.json` is created and the command reports nonzero document/tag counts.

## Task 3: Build Tag Cloud Components

**Files:**
- Create: `study-site/src/components/CategoryFilter.tsx`
- Create: `study-site/src/components/TagTooltip.tsx`
- Create: `study-site/src/components/TagCloud.tsx`
- Create: `study-site/src/components/StudyHighlights.tsx`
- Modify: `study-site/src/App.tsx`

- [ ] **Step 1: Create category filter**

Create `study-site/src/components/CategoryFilter.tsx`:

```tsx
import type { StudyTagCategory } from '../types';

interface CategoryFilterProps {
  activeCategory: StudyTagCategory | 'all';
  counts: Record<StudyTagCategory, number>;
  onChange: (category: StudyTagCategory | 'all') => void;
}

const labels: Record<StudyTagCategory | 'all', string> = {
  all: '全部',
  term: '术语',
  agent: 'Agent',
  resource: '收藏',
  project: '项目',
  trend: '趋势',
  action: '行动',
};

export function CategoryFilter({ activeCategory, counts, onChange }: CategoryFilterProps) {
  const categories = Object.keys(labels) as Array<StudyTagCategory | 'all'>;

  return (
    <div className="category-filter" aria-label="标签分类筛选">
      {categories.map((category) => (
        <button
          key={category}
          type="button"
          className={activeCategory === category ? 'category-pill active' : 'category-pill'}
          onClick={() => onChange(category)}
        >
          <span>{labels[category]}</span>
          <strong>{category === 'all' ? Object.values(counts).reduce((sum, count) => sum + count, 0) : counts[category]}</strong>
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create tooltip component**

Create `study-site/src/components/TagTooltip.tsx`:

```tsx
import type { StudyTag } from '../types';

interface TagTooltipProps {
  tag: StudyTag;
}

const categoryNames = {
  term: '概念 / 名词 / 术语',
  agent: 'Agent / 工具 / 平台',
  resource: '收藏地址 / 人物 / 资源',
  project: '项目 / 案例 / 模板',
  trend: '新闻趋势',
  action: '学习行动',
};

export function TagTooltip({ tag }: TagTooltipProps) {
  return (
    <span className="tag-tooltip" role="tooltip">
      <span className="tooltip-category">{categoryNames[tag.category]}</span>
      <strong>{tag.name}</strong>
      <span>{tag.description}</span>
      <span className="tooltip-source">来源：{tag.sources.slice(0, 2).join('、')}</span>
      {tag.related.length > 0 ? <span className="tooltip-source">相关：{tag.related.slice(0, 4).join(' / ')}</span> : null}
    </span>
  );
}
```

- [ ] **Step 3: Create tag cloud**

Create `study-site/src/components/TagCloud.tsx`:

```tsx
import type { StudyTag, StudyTagCategory } from '../types';
import { TagTooltip } from './TagTooltip';

interface TagCloudProps {
  tags: StudyTag[];
  selectedTagName: string;
  onSelectTag: (tag: StudyTag) => void;
}

const categoryNames: Record<StudyTagCategory, string> = {
  term: '概念名词术语',
  agent: 'Agent 工具平台',
  resource: '收藏地址资源',
  project: '项目案例模板',
  trend: '新闻趋势',
  action: '学习行动',
};

export function TagCloud({ tags, selectedTagName, onSelectTag }: TagCloudProps) {
  const groups = groupByCategory(tags);

  return (
    <section className="tag-cloud-panel" aria-label="知识标签云">
      {Object.entries(groups).map(([category, groupTags]) => (
        <div key={category} className={`tag-cluster cluster-${category}`}>
          <div className="cluster-heading">
            <span>{categoryNames[category as StudyTagCategory]}</span>
            <strong>{groupTags.length}</strong>
          </div>
          <div className="tag-orbit">
            {groupTags.map((tag) => (
              <button
                key={`${tag.category}-${tag.name}`}
                type="button"
                className={selectedTagName === tag.name ? 'tag-token selected' : 'tag-token'}
                style={{ '--weight': Math.min(tag.weight, 10) } as React.CSSProperties}
                onClick={() => onSelectTag(tag)}
              >
                <span>{tag.name}</span>
                <TagTooltip tag={tag} />
              </button>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

function groupByCategory(tags: StudyTag[]): Record<StudyTagCategory, StudyTag[]> {
  return tags.reduce(
    (groups, tag) => {
      groups[tag.category].push(tag);
      return groups;
    },
    { term: [], agent: [], resource: [], project: [], trend: [], action: [] } as Record<StudyTagCategory, StudyTag[]>,
  );
}
```

- [ ] **Step 4: Create highlights panel**

Create `study-site/src/components/StudyHighlights.tsx`:

```tsx
import type { StudyData, StudyTag } from '../types';

interface StudyHighlightsProps {
  data: StudyData;
  selectedTag: StudyTag;
}

export function StudyHighlights({ data, selectedTag }: StudyHighlightsProps) {
  const sourceDocs = data.documents.filter((doc) => selectedTag.sources.includes(doc.path));
  const recentDocs = data.documents.slice(0, 5);

  return (
    <aside className="study-highlights" aria-label="标签详情">
      <div className="detail-card featured">
        <span className="eyebrow">当前标签</span>
        <h2>{selectedTag.name}</h2>
        <p>{selectedTag.description}</p>
        <div className="related-row">
          {selectedTag.related.slice(0, 6).map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </div>

      <div className="detail-card">
        <span className="eyebrow">来源笔记</span>
        {sourceDocs.map((doc) => (
          <div key={doc.path} className="source-line">
            <strong>{doc.title}</strong>
            <span>{doc.path}</span>
          </div>
        ))}
      </div>

      <div className="detail-card">
        <span className="eyebrow">阅读路径</span>
        {recentDocs.map((doc) => (
          <div key={doc.path} className="source-line compact">
            <strong>{doc.title}</strong>
            <span>{doc.summary}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
```

- [ ] **Step 5: Wire app state to generated data**

Replace `study-site/src/App.tsx`:

```tsx
import { useMemo, useState } from 'react';
import { BrainCircuit, Network, RefreshCw, Search } from 'lucide-react';
import rawData from './data/study-data.json';
import { CategoryFilter } from './components/CategoryFilter';
import { StudyHighlights } from './components/StudyHighlights';
import { TagCloud } from './components/TagCloud';
import type { StudyData, StudyTag, StudyTagCategory } from './types';

const data = rawData as StudyData;

export default function App() {
  const [activeCategory, setActiveCategory] = useState<StudyTagCategory | 'all'>('all');
  const [selectedTag, setSelectedTag] = useState<StudyTag>(data.tags[0]);

  const counts = useMemo(() => {
    return data.tags.reduce(
      (acc, tag) => {
        acc[tag.category] += 1;
        return acc;
      },
      { term: 0, agent: 0, resource: 0, project: 0, trend: 0, action: 0 } as Record<StudyTagCategory, number>,
    );
  }, []);

  const visibleTags = activeCategory === 'all' ? data.tags : data.tags.filter((tag) => tag.category === activeCategory);

  return (
    <main className="app-shell">
      <section className="hero-band">
        <div className="hero-copy">
          <span className="eyebrow">Personal Knowledge Atlas</span>
          <h1>Study 学习知识星图</h1>
          <p>把 Markdown 笔记同步成可筛选的标签云，用悬停简介快速回忆概念、Agent、收藏资源和项目案例。</p>
          <div className="hero-actions">
            <span><Network size={16} /> {data.tags.length} 个标签</span>
            <span><BrainCircuit size={16} /> {data.documents.length} 篇笔记</span>
            <span><RefreshCw size={16} /> npm run generate:study</span>
          </div>
        </div>
        <div className="search-shell" aria-label="视觉搜索框">
          <Search size={18} />
          <span>点击分类或悬停标签查看简介</span>
        </div>
      </section>

      <CategoryFilter activeCategory={activeCategory} counts={counts} onChange={setActiveCategory} />

      <section className="workspace-grid">
        <TagCloud tags={visibleTags} selectedTagName={selectedTag.name} onSelectTag={setSelectedTag} />
        <StudyHighlights data={data} selectedTag={selectedTag} />
      </section>
    </main>
  );
}
```

## Task 4: Apply Production Styling And Responsive Behavior

**Files:**
- Modify: `study-site/src/index.css`

- [ ] **Step 1: Replace CSS with final visual system**

Replace `study-site/src/index.css` with a complete responsive stylesheet:

```css
:root {
  color: #d8e2ff;
  background: #0d1117;
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background:
    linear-gradient(rgba(125, 211, 252, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(125, 211, 252, 0.04) 1px, transparent 1px),
    radial-gradient(circle at 78% 8%, rgba(251, 191, 36, 0.13), transparent 24rem),
    radial-gradient(circle at 18% 12%, rgba(125, 211, 252, 0.18), transparent 27rem),
    #0d1117;
  background-size: 42px 42px, 42px 42px, auto, auto, auto;
}

button {
  font: inherit;
}

.app-shell {
  width: min(1440px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  padding: 28px;
}

.hero-band {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 24px;
  align-items: end;
  padding: 20px 0 24px;
}

.eyebrow {
  color: #7dd3fc;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h1 {
  max-width: 780px;
  margin: 10px 0;
  color: #f8fbff;
  font-size: clamp(38px, 6vw, 78px);
  line-height: 0.95;
  letter-spacing: 0;
}

.hero-copy p {
  max-width: 720px;
  margin: 0;
  color: #9fb3d9;
  font-size: 18px;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-actions span,
.search-shell,
.category-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.045);
  color: #c7d2fe;
}

.hero-actions span {
  padding: 8px 11px;
  font-size: 13px;
}

.search-shell {
  justify-content: flex-start;
  padding: 16px 18px;
  color: #94a3b8;
}

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 8px 0 22px;
}

.category-pill {
  cursor: pointer;
  padding: 10px 13px;
  transition: border-color 160ms ease, background 160ms ease, color 160ms ease;
}

.category-pill strong {
  color: #f8fbff;
}

.category-pill.active,
.category-pill:hover,
.category-pill:focus-visible {
  border-color: rgba(125, 211, 252, 0.72);
  background: rgba(125, 211, 252, 0.12);
  color: #f8fbff;
  outline: none;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 22px;
  align-items: start;
}

.tag-cloud-panel,
.study-highlights {
  min-width: 0;
}

.tag-cloud-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.tag-cluster,
.detail-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.043);
  box-shadow: 0 22px 60px rgba(0, 0, 0, 0.25);
}

.tag-cluster {
  min-height: 230px;
  padding: 16px;
  position: relative;
  overflow: visible;
}

.cluster-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #9fb3d9;
  font-size: 13px;
  font-weight: 800;
}

.tag-orbit {
  display: flex;
  flex-wrap: wrap;
  align-content: center;
  gap: 10px;
  min-height: 170px;
  padding-top: 16px;
}

.tag-token {
  --weight: 4;
  position: relative;
  cursor: pointer;
  border: 1px solid rgba(216, 226, 255, 0.16);
  border-radius: 999px;
  padding: 7px 11px;
  background: rgba(13, 17, 23, 0.72);
  color: #d8e2ff;
  font-size: calc(12px + var(--weight) * 1.25px);
  letter-spacing: 0;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.tag-token:hover,
.tag-token:focus-visible,
.tag-token.selected {
  z-index: 5;
  transform: translateY(-2px);
  border-color: rgba(125, 211, 252, 0.84);
  box-shadow: 0 0 28px rgba(125, 211, 252, 0.23);
  outline: none;
}

.cluster-term .tag-token { color: #7dd3fc; }
.cluster-agent .tag-token { color: #fde68a; }
.cluster-resource .tag-token { color: #a7f3d0; }
.cluster-project .tag-token { color: #fca5a5; }
.cluster-trend .tag-token { color: #c4b5fd; }
.cluster-action .tag-token { color: #f0f9ff; }

.tag-tooltip {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 10px);
  width: min(320px, 82vw);
  transform: translateX(-50%) translateY(6px);
  pointer-events: none;
  opacity: 0;
  display: grid;
  gap: 7px;
  border: 1px solid rgba(125, 211, 252, 0.28);
  border-radius: 8px;
  background: rgba(10, 14, 22, 0.98);
  padding: 12px;
  color: #d8e2ff;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.48);
  transition: opacity 120ms ease, transform 120ms ease;
}

.tag-token:hover .tag-tooltip,
.tag-token:focus-visible .tag-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.tooltip-category,
.tooltip-source {
  color: #94a3b8;
  font-size: 12px;
}

.study-highlights {
  display: grid;
  gap: 14px;
  position: sticky;
  top: 18px;
}

.detail-card {
  padding: 16px;
}

.detail-card.featured {
  background: linear-gradient(145deg, rgba(125, 211, 252, 0.16), rgba(255, 255, 255, 0.045));
}

.detail-card h2 {
  margin: 8px 0;
  color: #f8fbff;
  font-size: 32px;
  line-height: 1.1;
}

.detail-card p {
  color: #c7d2fe;
  line-height: 1.7;
}

.related-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.related-row span {
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  padding: 6px 9px;
  color: #9fb3d9;
  font-size: 12px;
}

.source-line {
  display: grid;
  gap: 4px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.source-line:last-child {
  border-bottom: 0;
}

.source-line strong {
  color: #f8fbff;
}

.source-line span {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.45;
}

.source-line.compact strong {
  font-size: 13px;
}

@media (max-width: 1080px) {
  .hero-band,
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .study-highlights {
    position: static;
  }
}

@media (max-width: 760px) {
  .app-shell {
    padding: 18px;
  }

  .hero-copy h1 {
    font-size: 42px;
  }

  .hero-copy p {
    font-size: 16px;
  }

  .tag-cloud-panel {
    grid-template-columns: 1fr;
  }

  .tag-cluster {
    min-height: 0;
  }

  .tag-orbit {
    min-height: 0;
  }
}
```

- [ ] **Step 2: Build after styling**

Run:

```bash
cd study-site && npm run build
```

Expected: PASS with generated `dist/`.

## Task 5: Verify Sync, UI, And Accessibility

**Files:**
- Modify only if verification exposes issues.

- [ ] **Step 1: Run full verification commands**

Run:

```bash
cd study-site && npm run generate:study && npm test && npm run build
```

Expected: all commands pass.

- [ ] **Step 2: Start dev server**

Run:

```bash
cd study-site && npm run dev
```

Expected: Vite prints a local URL, typically `http://127.0.0.1:5173/`.

- [ ] **Step 3: Browser check desktop**

Open the dev server URL. Verify:

- The page first viewport shows title, sync command hint, category filter, tag cloud, and detail panel.
- Hovering `MCP`, `Skill`, `Codex`, or `TradingAgents` shows a tooltip with category, description, source, and related tags.
- Clicking a tag updates the detail panel.
- Switching category filters changes visible tag groups.

- [ ] **Step 4: Browser check mobile**

Resize to a mobile width around 390 px. Verify:

- No text overlaps.
- Tag buttons wrap within their clusters.
- Tooltip stays readable or clicking a tag still updates the detail panel.
- Detail panel stacks under the tag cloud.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add study-site
git commit -m "feat: add study tag cloud frontend"
```

Expected: commit succeeds without staging unrelated existing changes in `study/`, `health/`, `jizhang/`, or `Chinese-Classics/`.

## Self-Review

- Spec coverage: data sync is covered by Task 2 and Task 5; hover summaries by Task 3 and Task 4; classification by Task 2 and Task 3; visual direction by Task 4.
- Placeholder scan: no TBD/TODO/fill-in-later language remains in executable steps.
- Type consistency: `StudyTagCategory`, `StudyTag`, `StudyDocument`, and `StudyData` are defined in Task 2 and reused consistently in Tasks 3 and 4.
