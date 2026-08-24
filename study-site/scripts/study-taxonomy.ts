import type { StudyData, StudyDocument, StudyTag, StudyTagCategory } from '../src/types';

export interface MarkdownFile {
  path: string;
  content: string;
}

export const CATEGORY_LABELS: Record<StudyTagCategory, string> = {
  term: '概念 / 名词 / 术语',
  agent: 'Agent / 工具 / 平台',
  resource: '收藏地址 / 人物 / 资源',
  project: '项目 / 案例 / 模板',
  trend: '新闻趋势',
  action: '学习行动',
};

const AI_GLOSSARY_TERMS = [
  'LLM',
  'Transformer',
  'Token',
  'Context Window',
  'Prompt Engineering',
  'System Prompt',
  'Chain of Thought',
  'Tool Calling',
  'Function Calling',
  'Structured Outputs',
  'JSON Schema',
  'Embeddings',
  'Vector Database',
  'Vector Store',
  'RAG',
  'Retrieval',
  'Fine-tuning',
  'Distillation',
  'Inference',
  'Latency',
  'Temperature',
  'Top-p',
  'Multimodal',
  'Vision Model',
  'Speech to Text',
  'Text to Speech',
  'ReAct',
  'Planner',
  'Handoff',
  'Guardrails',
  'Tracing',
  'Evaluation',
  'Evals',
  'Benchmark',
  'Hallucination',
  'Grounding',
  'Prompt Caching',
  'Batch API',
  'Computer Use',
  'Sandbox',
  'Model Context',
  'MCP',
  'Tools',
  'Resources',
  'Prompts',
  'Skill',
  'LangGraph',
  'Workflow',
  'State Graph',
  'Node',
  'Edge',
  'Checkpoint',
  'Tool',
  'Memory',
  'Eval',
  'Context',
];

const TERM_TAGS = AI_GLOSSARY_TERMS;
const AGENT_TAGS = [
  'Codex',
  'Claude Code',
  'Trae',
  'Cursor',
  'Windsurf',
  'Devin',
  'GitHub Copilot',
  'Replit Agent',
  'Gemini CLI',
  'Kiro',
  'Jules',
  'Firebase Studio',
  'Base44',
  'WorkBuddy',
  'CodeBuddy',
  'Amazon Q Developer',
  'JetBrains Junie',
  'Tabnine',
  'Continue',
  'Cline',
  'Roo Code',
  'Aider',
  'Bolt.new',
  'Lovable',
  'v0',
  'Sourcegraph Cody',
  'Qodo',
  'CodeRabbit',
  'OpenClaw',
  'Hermes Agent',
  'AI Model Hub',
  'AiToEarn',
];
const RESOURCE_TAGS = ['官方文档', 'GitHub', 'Skills Catalog', 'Michael Sitarzewski', 'API Docs', '论文', '博客'];
const PROJECT_TAGS = ['TradingAgents', 'TradingAgents-CN', 'a-stock-data', 'QuantDinger', 'AI-Trader', 'Agent 项目结构模板'];
const TREND_TAGS = ['AI 圈新闻', '技术更新', '社会热点', '行业热点', '经济热点'];
const ACTION_TAGS = ['观察', '立即试用', '深入学习', '记录案例', '暂不跟进'];

const PROJECT_DOCUMENT_TAGS = ['AI 工具开源项目案例', 'TradingAgents 项目整理', 'Agent 项目结构模板'];
const RESOURCE_DOCUMENT_TAGS = ['Michael Sitarzewski'];
const GENERIC_SECTION_TAGS = new Set([
  'Commands',
  'Inputs',
  'Output',
  'Project',
  'Purpose',
  'Rules',
  'Safety',
  'Setup',
  'State',
  'Test',
  'Architecture',
  'Development',
  'Environment',
  'Human Approval',
  'Project Name',
  'Verification',
  'What It Does',
  'When To Use',
  '最小结构',
  '目录职责',
  '采用建议',
  '项目总览',
  '完整 Agent 工程结构',
  'Agent Instructions',
  'AGENTS.md 模板',
  'README.md 模板',
  '资源总览',
  'agency-agents 项目简介',
  '使用目标',
  '判断原则',
  '判断层级',
  '核心文档',
  '每日记录',
  '快速记录模板',
  'YYYY-MM-DD 标题',
  '总览',
  '今日总览',
  '今日行动',
  '今日个人判断',
  '一句话框架',
  '个人行动清单',
  '事实层',
  '机制层',
  '职业层',
  '行业层',
  '经济层',
  '时间尺度',
  '评分模板',
  '快速判断：新闻还是趋势',
]);
const DAILY_RECORD_TITLE_PATTERN = /^\d{4}-\d{2}-\d{2}\s+今日新闻与趋势记录$/;

const CURATED_DESCRIPTIONS: Record<string, string> = {
  LLM: 'LLM 是大语言模型，擅长基于上下文生成、理解和转换自然语言与代码。',
  Transformer: 'Transformer 是现代大模型的核心神经网络架构，依靠注意力机制处理序列信息。',
  Token: 'Token 是模型处理文本的基本单位，成本、上下文长度和生成长度通常都按 token 计算。',
  'Context Window': 'Context Window 是模型一次请求能看到的最大上下文范围。',
  'Prompt Engineering': 'Prompt Engineering 是设计指令、上下文和示例来稳定引导模型输出的方法。',
  'System Prompt': 'System Prompt 是高优先级指令，用来定义模型角色、边界和行为规则。',
  'Chain of Thought': 'Chain of Thought 是让模型显式或隐式分解推理步骤的提示方法。',
  'Tool Calling': 'Tool Calling 是模型选择并调用外部工具来完成查询、执行动作或获取数据的能力。',
  'Function Calling': 'Function Calling 是让模型按函数参数结构调用外部代码或 API 的工具调用方式。',
  'Structured Outputs': 'Structured Outputs 让模型按指定 JSON Schema 生成结构化结果，减少解析和校验成本。',
  'JSON Schema': 'JSON Schema 是描述 JSON 数据结构、字段和约束的标准格式。',
  Embeddings: 'Embeddings 是把文本、图片等内容映射成向量表示，用于搜索、聚类、推荐和 RAG。',
  'Vector Database': 'Vector Database 用于存储和检索向量，支持语义相似度搜索。',
  'Vector Store': 'Vector Store 是向量存储层，常用于检索增强生成和语义搜索。',
  RAG: 'RAG 是检索增强生成，先从外部知识库检索相关内容，再交给模型回答。',
  Retrieval: 'Retrieval 是从知识库、文档或搜索系统中取回相关信息的步骤。',
  'Fine-tuning': 'Fine-tuning 是在特定数据上继续训练模型，使其更适配某类任务或风格。',
  Distillation: 'Distillation 是把大模型能力迁移到更小模型的训练方法。',
  Inference: 'Inference 是模型根据输入生成输出的运行过程。',
  Latency: 'Latency 是从请求发出到拿到响应的延迟，是产品体验和成本的重要指标。',
  Temperature: 'Temperature 控制生成随机性，数值越高输出通常越发散。',
  'Top-p': 'Top-p 是 nucleus sampling 参数，用概率质量截断候选 token 集合。',
  Multimodal: 'Multimodal 指模型能处理文本、图像、音频、视频等多种模态。',
  'Vision Model': 'Vision Model 是能理解图像或视觉输入的模型。',
  'Speech to Text': 'Speech to Text 把语音转成文字，常用于语音输入、会议记录和字幕。',
  'Text to Speech': 'Text to Speech 把文字合成为语音，常用于语音助手和朗读场景。',
  ReAct: 'ReAct 是把推理和行动交替组织起来的 agent 提示/流程模式。',
  Planner: 'Planner 是负责拆解目标、安排步骤和选择工具的规划模块或角色。',
  Handoff: 'Handoff 是 agent 或流程之间转交任务、上下文和控制权的机制。',
  Guardrails: 'Guardrails 是限制输入输出、工具调用和风险行为的安全与质量边界。',
  Tracing: 'Tracing 记录 agent 运行过程、工具调用和中间状态，方便调试与评估。',
  Evaluation: 'Evaluation 是对模型或 agent 输出质量进行测试、评分和对比的过程。',
  Evals: 'Evals 是可重复运行的评估集或评测流程，用来发现回归和比较模型表现。',
  Benchmark: 'Benchmark 是用于比较模型、工具或流程能力的标准测试。',
  Hallucination: 'Hallucination 指模型生成看似合理但不真实或无依据的信息。',
  Grounding: 'Grounding 是让模型回答依托可验证来源、检索内容或真实环境状态。',
  'Prompt Caching': 'Prompt Caching 复用重复上下文的计算结果，用于降低延迟和成本。',
  'Batch API': 'Batch API 用于异步批量处理大量请求，常用于离线任务和成本优化。',
  'Computer Use': 'Computer Use 是让模型通过浏览器或桌面界面观察并操作软件的能力。',
  Sandbox: 'Sandbox 是隔离执行环境，用来限制代码、工具或 agent 的权限和影响范围。',
  'Model Context': 'Model Context 是提供给模型的任务指令、历史、工具结果和外部知识集合。',
  MCP: 'MCP 是能力接入协议，让 AI 客户端以统一方式访问工具、资源和外部系统。',
  Tools: 'Tools 是 MCP 或 Agent 系统暴露给模型调用的外部动作集合。',
  Resources: 'Resources 是 MCP 暴露给 AI 客户端读取的外部数据、文件或上下文资源。',
  Prompts: 'Prompts 是可复用提示模板，用来标准化某类任务的输入方式。',
  Skill: 'Skill 是可复用工作方法包，用来沉淀流程、模板、脚本和检查清单。',
  LangGraph: 'LangGraph 用图结构编排 Agent、LLM、Tool 和 State，适合复杂多步流程。',
  Workflow: 'Workflow 是预先设计好的步骤、分支和验收流程，决定任务按什么顺序发生。',
  'State Graph': 'State Graph 是用状态和节点流转表达复杂 agent 工作流的图结构。',
  Node: 'Node 是图式工作流中的处理节点，通常负责一次模型调用、工具调用或状态更新。',
  Edge: 'Edge 是图式工作流中节点之间的流转关系，决定下一步进入哪个节点。',
  Checkpoint: 'Checkpoint 是长流程中的状态保存点，用于恢复、调试和继续执行。',
  Tool: 'Tool 是 Agent 可调用的原子动作，例如查数据、写文件、调 API 或执行命令。',
  Memory: 'Memory 保存长期偏好、历史事实、任务状态或外部知识，帮助 Agent 复用上下文。',
  Eval: 'Eval 用于验证 Agent 输出和流程结果，是质量控制层。',
  Codex: 'Codex 是面向软件工程的 coding agent，适合读代码、改代码、跑测试和协作开发。',
  'Claude Code': 'Claude Code 是 Anthropic 的 agentic coding 工具，也可通过 Agent SDK 构建自定义 agent。',
  Trae: 'Trae 是面向软件开发的 AI IDE / coding agent 产品，强调从需求到代码的协作开发体验。',
  Cursor: 'Cursor 是 AI-first 代码编辑器，围绕代码库问答、自动编辑和 agent 模式提升开发效率。',
  Windsurf: 'Windsurf 是 Codeium 推出的 agentic IDE，强调多文件上下文和自动化代码修改流程。',
  Devin: 'Devin 是 Cognition 推出的 AI 软件工程 agent，定位为可规划、编码、调试和交付任务的工程助手。',
  'GitHub Copilot': 'GitHub Copilot 是 GitHub 的 AI 编程助手，覆盖代码补全、聊天、代码审查和 agent mode。',
  'Replit Agent': 'Replit Agent 是 Replit 的应用构建 agent，可从自然语言需求生成、运行和迭代应用。',
  'Gemini CLI': 'Gemini CLI 是 Google 推出的开源终端 AI agent，把 Gemini 能力带到命令行开发流程。',
  Kiro: 'Kiro 是 AWS 推出的 agentic IDE，强调从规格、设计到代码实现的规范化开发流程。',
  Jules: 'Jules 是 Google 的异步 coding agent，可接收开发任务并在代码库中规划和修改代码。',
  'Firebase Studio': 'Firebase Studio 是 Google/Firebase 的云端 AI 应用开发环境，面向全栈应用生成和迭代。',
  Base44: 'Base44 是从自然语言生成业务应用的 AI app builder，面向快速搭建内部工具和产品原型。',
  WorkBuddy: 'WorkBuddy 是腾讯云推出的个人 AI agent workspace，面向文档、研究、办公和多场景 AI 工作流。',
  CodeBuddy: 'CodeBuddy 是腾讯云推出的 AI 编码助手 / coding agent，面向代码生成、理解、调试和开发协作。',
  'Amazon Q Developer': 'Amazon Q Developer 是 AWS 的 AI 编程助手，面向云开发、代码生成、迁移和运维排查。',
  'JetBrains Junie': 'JetBrains Junie 是 JetBrains IDE 内的 coding agent，用于理解项目、改代码和执行开发任务。',
  Tabnine: 'Tabnine 是面向团队和企业的 AI 代码助手，强调私有化、代码补全和团队知识适配。',
  Continue: 'Continue 是开源 AI 代码助手，可在 IDE 中连接不同模型、上下文和自定义开发工作流。',
  Cline: 'Cline 是 VS Code 内的开源 coding agent，可读写文件、运行命令并协助完成开发任务。',
  'Roo Code': 'Roo Code 是 VS Code 生态里的 AI coding agent，支持多模式协作和工具调用。',
  Aider: 'Aider 是终端里的 AI pair programming 工具，直接基于 git 仓库读写代码。',
  'Bolt.new': 'Bolt.new 是 StackBlitz 的浏览器内 AI 应用构建工具，适合快速生成和运行 Web 应用。',
  Lovable: 'Lovable 是面向产品原型和 Web 应用生成的 AI app builder，可从自然语言生成前端和后端。',
  v0: 'v0 是 Vercel 的 AI UI / Web 生成工具，适合从提示词生成界面和应用片段。',
  'Sourcegraph Cody': 'Sourcegraph Cody 是面向代码库理解、搜索和生成的 AI 编程助手。',
  Qodo: 'Qodo 是面向代码质量、测试生成和代码审查的 AI 开发工具。',
  CodeRabbit: 'CodeRabbit 是 AI 代码审查工具，面向 Pull Request 总结、审查和反馈。',
  'Hermes Agent': 'Hermes Agent 是围绕长期记忆、工具网关和 Skill 自改进设计的 agent runtime。',
  OpenClaw: 'OpenClaw 更接近个人自动化助手，侧重消息渠道、网页、设备和个人任务执行。',
  TradingAgents: 'TradingAgents 是用多智能体模拟金融投研流程的 LangGraph 案例。',
  'TradingAgents-CN': 'TradingAgents-CN 是 TradingAgents 的中文生态版本，适合观察本地化投研 agent 实践。',
  'a-stock-data': 'a-stock-data 是 A 股数据工具包，可作为金融 agent 的数据能力来源。',
};

const CURATED_SOURCES: Record<string, string> = {
  Embeddings: 'https://platform.openai.com/docs/guides/embeddings',
  'Structured Outputs': 'https://platform.openai.com/docs/guides/structured-outputs',
  'Function Calling': 'https://platform.openai.com/docs/guides/function-calling',
  'Tool Calling': 'https://platform.openai.com/docs/guides/function-calling',
  'Prompt Caching': 'https://platform.openai.com/docs/guides/prompt-caching',
  'Batch API': 'https://platform.openai.com/docs/guides/batch',
  Guardrails: 'https://openai.github.io/openai-agents-python/guardrails/',
  Handoff: 'https://openai.github.io/openai-agents-python/handoffs/',
  Tracing: 'https://openai.github.io/openai-agents-python/tracing/',
  MCP: 'https://modelcontextprotocol.io/docs/concepts/tools',
  Tools: 'https://modelcontextprotocol.io/docs/concepts/tools',
  Resources: 'https://modelcontextprotocol.io/docs/concepts/resources',
  Prompts: 'https://modelcontextprotocol.io/docs/concepts/prompts',
  LangGraph: 'https://langchain-ai.github.io/langgraph/',
  'Claude Code': 'https://docs.anthropic.com/en/docs/claude-code/overview',
  Trae: 'https://www.trae.ai/',
  Cursor: 'https://cursor.com/',
  Windsurf: 'https://windsurf.com/',
  Devin: 'https://devin.ai/',
  'GitHub Copilot': 'https://docs.github.com/en/copilot',
  'Replit Agent': 'https://docs.replit.com/replitai/agent',
  'Gemini CLI': 'https://github.com/google-gemini/gemini-cli',
  Kiro: 'https://kiro.dev/',
  Jules: 'https://jules.google/',
  'Firebase Studio': 'https://firebase.studio/',
  Base44: 'https://base44.com/',
  WorkBuddy: 'https://www.tencentcloud.com/act/pro/workbuddy',
  CodeBuddy: 'https://www.tencentcloud.com/products/codebuddy',
  'Amazon Q Developer': 'https://aws.amazon.com/q/developer/',
  'JetBrains Junie': 'https://www.jetbrains.com/junie/',
  Tabnine: 'https://www.tabnine.com/',
  Continue: 'https://www.continue.dev/',
  Cline: 'https://cline.bot/',
  'Roo Code': 'https://roocode.com/',
  Aider: 'https://aider.chat/',
  'Bolt.new': 'https://bolt.new/',
  Lovable: 'https://lovable.dev/',
  v0: 'https://v0.dev/',
  'Sourcegraph Cody': 'https://sourcegraph.com/cody',
  Qodo: 'https://www.qodo.ai/',
  CodeRabbit: 'https://www.coderabbit.ai/',
};

export const TAG_RULES: Array<{ category: StudyTagCategory; names: string[] }> = [
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
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && !line.startsWith('|') && !line.startsWith('---') && !line.startsWith('```'));
  const first = lines.find((line) => !line.startsWith('- ') && !/^\d+\./.test(line));
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

  addCuratedAiTerms(tagMap);
  addCuratedAgentProducts(tagMap);

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

function collectCandidates(file: MarkdownFile): string[] {
  const headings = file.content
    .split('\n')
    .map((line) => line.match(/^#{1,3}\s+(.+)$/)?.[1]?.trim())
    .filter((heading): heading is string => Boolean(heading))
    .flatMap(cleanHeading)
    .filter((heading) => isAllowedHeadingTag(heading, file.path));

  const known = TAG_RULES.flatMap((rule) => rule.names).filter((name) => hasTermOccurrence(file.content, name));
  return Array.from(new Set([...known, ...headings])).filter((name) => name.length >= 2 && name.length <= 32);
}

function extractTitle(content: string): string | undefined {
  return content.match(/^#\s+(.+)$/m)?.[1]?.trim();
}

function cleanHeading(heading: string): string[] {
  const cleaned = heading.replace(/^\d+[.、]\s*/, '').replace(/`/g, '').trim();
  const knownTerms = TERM_TAGS.filter((term) => cleaned.includes(term));
  return knownTerms.length > 0 ? knownTerms : [cleaned];
}

function isAllowedHeadingTag(name: string, path: string): boolean {
  if (GENERIC_SECTION_TAGS.has(name)) return false;
  if (DAILY_RECORD_TITLE_PATTERN.test(name)) return false;
  if (TERM_TAGS.includes(name)) return true;

  const category = inferTagCategory(name, path);
  if (category === 'term') return false;
  if (category === 'project') return isProjectTag(name);
  if (category === 'resource') return isResourceTag(name);
  if (category === 'trend') return isTrendTag(name, path);
  return true;
}

function trimSentence(text: string): string {
  return text.length > 92 ? `${text.slice(0, 91)}...` : text;
}

function buildDescription(name: string, category: StudyTagCategory, markdown: string): string {
  if (CURATED_DESCRIPTIONS[name]) return CURATED_DESCRIPTIONS[name];

  const escaped = escapeRegExp(name);
  const line = markdown
    .split('\n')
    .map((item) => item.trim())
    .find((item) => new RegExp(escaped, 'i').test(item) && !item.startsWith('#'));
  return line ? trimSentence(line.replace(/^-\s*/, '')) : `${name} 属于${CATEGORY_LABELS[category]}，来自 study 学习笔记。`;
}

function baseWeight(name: string): number {
  if (['LLM', 'MCP', 'Skill', 'LangGraph', 'Embeddings', 'RAG', 'Function Calling', 'Structured Outputs', 'Codex', 'Claude Code', 'TradingAgents'].includes(name)) return 8;
  if (name.length <= 8) return 5;
  return 3;
}

function isProjectTag(name: string): boolean {
  return PROJECT_TAGS.includes(name) || PROJECT_DOCUMENT_TAGS.includes(name);
}

function isResourceTag(name: string): boolean {
  return RESOURCE_TAGS.includes(name) || RESOURCE_DOCUMENT_TAGS.some((resource) => name.includes(resource));
}

function isTrendTag(name: string, path: string): boolean {
  if (TREND_TAGS.includes(name) || ACTION_TAGS.includes(name)) return true;
  return path.includes('/daily/') && !GENERIC_SECTION_TAGS.has(name);
}

function addCuratedAiTerms(tagMap: Map<string, StudyTag>): void {
  for (const name of TERM_TAGS) {
    const existing = tagMap.get(name);
    const source = CURATED_SOURCES[name] ?? 'https://platform.openai.com/docs';

    if (existing) {
      existing.description = CURATED_DESCRIPTIONS[name] ?? existing.description;
      if (!existing.sources.includes(source)) existing.sources.push(source);
      existing.weight = Math.max(existing.weight, baseWeight(name));
      continue;
    }

    tagMap.set(name, {
      name,
      category: 'term',
      description: CURATED_DESCRIPTIONS[name] ?? `${name} 是 AI 工程常用术语，适合放入术语云持续跟踪。`,
      weight: baseWeight(name),
      sources: [source],
      related: [],
    });
  }
}

function addCuratedAgentProducts(tagMap: Map<string, StudyTag>): void {
  for (const name of AGENT_TAGS) {
    const existing = tagMap.get(name);
    const source = CURATED_SOURCES[name] ?? 'https://github.com/topics/ai-coding-assistant';

    if (existing) {
      existing.description = CURATED_DESCRIPTIONS[name] ?? existing.description;
      if (!existing.sources.includes(source)) existing.sources.push(source);
      existing.weight = Math.max(existing.weight, baseWeight(name));
      continue;
    }

    tagMap.set(name, {
      name,
      category: 'agent',
      description: CURATED_DESCRIPTIONS[name] ?? `${name} 是 AI 编程或 agent 工具生态中的产品，适合持续跟踪定位和能力变化。`,
      weight: baseWeight(name),
      sources: [source],
      related: [],
    });
  }
}

function sharesSource(left: StudyTag, right: StudyTag): boolean {
  return left.sources.some((source) => right.sources.includes(source));
}

function hasTermOccurrence(content: string, name: string): boolean {
  if (!/^[A-Za-z][A-Za-z0-9 -]*$/.test(name)) return content.includes(name);
  const escaped = escapeRegExp(name).replace(/\\ /g, '\\s+');
  return new RegExp(`(^|[^A-Za-z0-9.])${escaped}([^A-Za-z0-9.]|$)`, 'i').test(content);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
