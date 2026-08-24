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
    ].join('\n');

    expect(summarizeMarkdown(markdown)).toBe('这里整理 MCP 的定位和边界。');
  });

  it('builds tags with source documents and related tags', () => {
    const files = [
      {
        path: 'study/ai-tools/mcp-notes.md',
        content: '# MCP 笔记\n\nMCP 是能力接入协议。\n\n## Tools、Resources、Prompts 的区别\n\n## 和 Skill 的区别',
      },
      {
        path: 'study/ai-tools/agent-engineering.md',
        content: '# Agent 工程总览\n\nCodex 是 coding agent。\n\n## MCP 的位置\n\n## Skill 的位置',
      },
    ];

    const data = buildStudyData(files);
    const mcp = data.tags.find((tag) => tag.name === 'MCP');

    expect(mcp).toMatchObject({
      name: 'MCP',
      category: 'term',
      description: 'MCP 是能力接入协议，让 AI 客户端以统一方式访问工具、资源和外部系统。',
    });
    expect(mcp?.sources).toContain('study/ai-tools/mcp-notes.md');
    expect(mcp?.related).toContain('Skill');
    expect(data.documents).toHaveLength(2);
  });

  it('uses curated descriptions for important known tags', () => {
    const data = buildStudyData([
      {
        path: 'study/ai-tools/mcp-notes.md',
        content: '# MCP 笔记\n\n同一个能力希望被多个 AI 客户端复用，例如 Codex、Claude、Cursor、ChatGPT。',
      },
      {
        path: 'study/ai-tools/agent-engineering.md',
        content: '# Agent 工程总览\n\nCodex：面向软件工程的 coding agent。',
      },
    ]);

    expect(data.tags.find((tag) => tag.name === 'Codex')?.description).toBe('Codex 是面向软件工程的 coding agent，适合读代码、改代码、跑测试和协作开发。');
  });

  it('keeps generic markdown headings out of the term cloud', () => {
    const data = buildStudyData([
      {
        path: 'study/ai-tools/agent-engineering.md',
        content: '# Agent 工程总览\n\n## 学习路径\n\n## 常见错误\n\n## MCP 的位置\n\n## 使用方式',
      },
    ]);

    expect(data.tags.map((tag) => tag.name)).toContain('MCP');
    expect(data.tags.map((tag) => tag.name)).not.toContain('学习路径');
    expect(data.tags.map((tag) => tag.name)).not.toContain('常见错误');
    expect(data.tags.map((tag) => tag.name)).not.toContain('使用方式');
  });

  it('adds current AI glossary terms even when notes do not mention them yet', () => {
    const data = buildStudyData([
      {
        path: 'study/README.md',
        content: '# 学习记录\n\n这里用来整理学习过程中遇到的概念。',
      },
    ]);

    const termNames = data.tags.filter((tag) => tag.category === 'term').map((tag) => tag.name);

    expect(termNames).toContain('Embeddings');
    expect(termNames).toContain('Structured Outputs');
    expect(termNames).toContain('Function Calling');
    expect(termNames).toContain('RAG');
    expect(data.tags.find((tag) => tag.name === 'Embeddings')?.sources).toContain('https://platform.openai.com/docs/guides/embeddings');
  });

  it('adds mainstream coding agent products even when notes do not mention them yet', () => {
    const data = buildStudyData([
      {
        path: 'study/README.md',
        content: '# 学习记录\n\n这里用来整理 AI 工具。',
      },
    ]);

    const agentNames = data.tags.filter((tag) => tag.category === 'agent').map((tag) => tag.name);

    expect(agentNames).toContain('Trae');
    expect(agentNames).toContain('Devin');
    expect(agentNames).toContain('Windsurf');
    expect(agentNames).toContain('GitHub Copilot');
    expect(agentNames).toContain('Replit Agent');
    expect(agentNames).toContain('JetBrains Junie');
    expect(agentNames).toContain('Amazon Q Developer');
    expect(agentNames).toContain('Gemini CLI');
    expect(agentNames).toContain('Kiro');
    expect(agentNames).toContain('Jules');
    expect(agentNames).toContain('Firebase Studio');
    expect(agentNames).toContain('Base44');
    expect(agentNames).toContain('WorkBuddy');
    expect(agentNames).toContain('CodeBuddy');
    expect(data.tags.find((tag) => tag.name === 'Trae')?.sources).toContain('https://www.trae.ai/');
    expect(data.tags.find((tag) => tag.name === 'WorkBuddy')?.sources).toContain('https://www.tencentcloud.com/act/pro/workbuddy');
  });

  it('does not match short English terms inside unrelated words', () => {
    const data = buildStudyData([
      {
        path: 'study/ai-tools/glossary.md',
        content: '# AI 工具术语表\n\n开源视频工作流依赖 Node.js、FFmpeg 和素材管理。',
      },
    ]);

    expect(data.tags.find((tag) => tag.name === 'Node')?.sources).not.toContain('study/ai-tools/glossary.md');
  });

  it('keeps generic template headings out of project tags', () => {
    const data = buildStudyData([
      {
        path: 'study/ai-tools/templates/agent-project-structure.md',
        content: '# Agent 项目结构模板\n\n## Commands\n\n## Output\n\n## Setup\n\n## Safety\n\n## Agent 项目结构模板',
      },
    ]);

    const projectNames = data.tags.filter((tag) => tag.category === 'project').map((tag) => tag.name);

    expect(projectNames).toContain('Agent 项目结构模板');
    expect(projectNames).not.toContain('Commands');
    expect(projectNames).not.toContain('Output');
    expect(projectNames).not.toContain('Setup');
    expect(projectNames).not.toContain('Safety');
  });

  it('keeps generic resource headings out of resource tags', () => {
    const data = buildStudyData([
      {
        path: 'study/ai-tools/people-and-resources.md',
        content: '# AI 工具人物与资源\n\n## 资源总览\n\n## agency-agents 项目简介\n\n## Michael Sitarzewski / msitarzewski',
      },
    ]);

    const resourceNames = data.tags.filter((tag) => tag.category === 'resource').map((tag) => tag.name);

    expect(resourceNames).toContain('Michael Sitarzewski');
    expect(resourceNames).not.toContain('资源总览');
    expect(resourceNames).not.toContain('agency-agents 项目简介');
    expect(resourceNames).not.toContain('AI 工具人物与资源');
  });

  it('keeps trend framework headings out while preserving daily news titles', () => {
    const data = buildStudyData([
      {
        path: 'study/news-trends/README.md',
        content: '# 新闻、技术与趋势判断\n\n## 使用目标\n\n## 判断原则\n\n## YYYY-MM-DD 标题',
      },
      {
        path: 'study/news-trends/daily/2026-07-01.md',
        content: '# 2026-07-01 今日新闻与趋势记录\n\n## OpenAI 强化 agent 工作叙事\n\n## 今日行动\n\n## 今日总览',
      },
    ]);

    const trendNames = data.tags.filter((tag) => tag.category === 'trend').map((tag) => tag.name);

    expect(trendNames).toContain('OpenAI 强化 agent 工作叙事');
    expect(trendNames).not.toContain('2026-07-01 今日新闻与趋势记录');
    expect(trendNames).not.toContain('使用目标');
    expect(trendNames).not.toContain('判断原则');
    expect(trendNames).not.toContain('YYYY-MM-DD 标题');
    expect(trendNames).not.toContain('今日行动');
    expect(trendNames).not.toContain('今日总览');
  });
});
