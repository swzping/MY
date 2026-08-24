# 短视频口播稿生成器 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Build a web tool that generates complete video scripts/outlines for short-form video (15s/30s/60s) based on user topic, helping creators save time on script writing.

**Architecture:** Single HTML file static web app, same pattern as xiaohongshu-title generator. Uses OpenAI API, all processing in browser. User's API key stored in localStorage.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- OpenAI API for script generation
- localStorage for API key persistence
- Shared utils from `shared/` directory

---

## File Structure

```
tools/video-script/
├── index.html                 # Main tool page (all code here)
└── README.md                  # Short introduction
```

Reuses existing shared files:
- `shared/common.css`
- `shared/utils.js`

---

## Tasks

### Task 1: Create project file

**Files:**
- Create: `tools/video-script/index.html`

- [ ] **Step 1: Create the main HTML file**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>短视频口播稿生成器 - AI一键写脚本</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">短视频口播稿生成器</h1>
            <p class="text-gray-600">输入主题，一键生成分时长口播脚本</p>
        </header>

        <main class="bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- API Key Settings -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-..."
                       class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">API Key存储在你本地浏览器，不会上传到我们服务器</p>
            </div>

            <!-- Topic Input -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">视频主题</label>
                <textarea id="topic" placeholder="例如：为什么年轻人越来越喜欢做饭，分享三个原因..."
                          class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="3"></textarea>
            </div>

            <!-- Video Duration -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">视频时长</label>
                <div class="grid grid-cols-3 gap-3">
                    <button class="duration-btn px-4 py-3 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-duration="15">
                        <div class="font-semibold">15秒</div>
                        <div class="text-xs text-gray-500">口播</div>
                    </button>
                    <button class="duration-btn px-4 py-3 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-duration="30">
                        <div class="font-semibold">30秒</div>
                        <div class="text-xs text-gray-500">黄金时长</div>
                    </button>
                    <button class="duration-btn px-4 py-3 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-duration="60">
                        <div class="font-semibold">60秒</div>
                        <div class="text-xs text-gray-500">干货分享</div>
                    </button>
                </div>
            </div>

            <!-- Style -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">口播风格</label>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <button class="style-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-style="干货">
                        干货
                    </button>
                    <button class="style-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-style="故事">
                        故事
                    </button>
                    <button class="style-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-style="提问">
                        提问
                    </button>
                    <button class="style-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-style="分享">
                        分享
                    </button>
                </div>
            </div>

            <!-- Generate Button -->
            <div class="text-center">
                <button id="generateBtn"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                    生成口播稿
                </button>
            </div>
        </main>

        <!-- Results Area -->
        <div id="results" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">生成结果（点击段落复制）</h2>
            <div id="scriptContainer" class="space-y-4"></div>
        </div>

        <footer class="text-center text-gray-500 text-sm">
            <p>© 2026 工具集 · 让内容创作更高效</p>
        </footer>

        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg opacity-0 transition-opacity duration-300 hidden"></div>
    </div>

    <script src="../../shared/utils.js"></script>
    <script>
        // JavaScript implementation below
    </script>
</body>
</html>
```

- [ ] **Step 2: Add full JavaScript implementation**

```javascript
// Configuration
const API_ENDPOINT = 'https://api.openai.com/v1/chat/completions';

// Prompt template
const PROMPT_TEMPLATE = `你是一个短视频内容专家，用户需要一个{{duration}}秒的{{style}}风格口播稿。
主题是：{{topic}}

请按照钩子（开头3秒）+ 内容（主体）+ 结尾引导（点赞关注）的结构生成，控制字数符合时长要求（15秒≈30-40字，30秒≈60-80字，60秒≈120-150字）。

请直接输出JSON格式：
{
  "hook": "开头钩子文案",
  "content": ["内容分段1", "内容分段2", ...],
  "ending": "结尾引导文案",
  "wordCount": 总字数
}
不要任何其他说明文字，只输出JSON。`;

// DOM Elements
const apiKeyInput = document.getElementById('apiKey');
const topicInput = document.getElementById('topic');
const durationBtns = document.querySelectorAll('.duration-btn');
const styleBtns = document.querySelectorAll('.style-btn');
const generateBtn = document.getElementById('generateBtn');
const resultsDiv = document.getElementById('results');
const scriptContainer = document.getElementById('scriptContainer');

// Selected values
let selectedDuration = '15';
let selectedStyle = '干货';

// Load saved API key
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = getFromLocalStorage('openai_api_key', '');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

// Save API key when changed
apiKeyInput.addEventListener('change', () => {
    saveToLocalStorage('openai_api_key', apiKeyInput.value);
});

// Duration selection
durationBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        durationBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedDuration = btn.dataset.duration;
    });
});

// Style selection
styleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        styleBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedStyle = btn.dataset.style;
    });
});

// Generate button click
generateBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    const topic = topicInput.value.trim();

    // Validation
    if (!apiKey) {
        showToast('请输入OpenAI API Key');
        return;
    }
    if (!topic) {
        showToast('请输入视频主题');
        return;
    }

    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const script = await generateScript(apiKey, topic, selectedDuration, selectedStyle);
        displayScript(script);
        resultsDiv.classList.remove('hidden');
        showToast('生成完成！点击段落复制');
    } catch (error) {
        console.error(error);
        showToast('生成失败：' + error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '生成口播稿';
    }
});

async function generateScript(apiKey, topic, duration, style) {
    const prompt = PROMPT_TEMPLATE
        .replace('{{duration}}', duration)
        .replace('{{style}}', style)
        .replace('{{topic}}', topic);

    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({
            model: 'gpt-3.5-turbo',
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.7
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'API调用失败');
    }

    const data = await response.json();
    const content = data.choices[0].message.content.trim();

    try {
        const cleanContent = content.replace(/^```json\n?/, '').replace(/\n?```$/, '');
        return JSON.parse(cleanContent);
    } catch (e) {
        console.error('Failed to parse JSON:', content);
        throw new Error('解析AI返回结果失败');
    }
}

function displayScript(script) {
    scriptContainer.innerHTML = '';

    // Hook
    const hookEl = createScriptBlock('开头钩子', script.hook);
    scriptContainer.appendChild(hookEl);

    // Content sections
    script.content.forEach((content, index) => {
        const contentEl = createScriptBlock(\`内容\${index + 1}\`, content);
        scriptContainer.appendChild(contentEl);
    });

    // Ending
    const endingEl = createScriptBlock('结尾引导', script.ending);
    scriptContainer.appendChild(endingEl);

    // Word count info
    const infoEl = document.createElement('div');
    infoEl.className = 'text-center text-gray-500 text-sm pt-4';
    infoEl.textContent = \`总字数：\${script.wordCount} 字，适合\${selectedDuration}秒口播\`;
    scriptContainer.appendChild(infoEl);
}

function createScriptBlock(title, content) {
    const block = document.createElement('div');
    block.className = 'p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors cursor-pointer';
    block.innerHTML = `
        <div class="mb-2">
            <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">${title}</span>
        </div>
        <p class="text-gray-800 text-lg">${content}</p>
    `;

    block.addEventListener('click', () => {
        copyToClipboard(content).then(() => {
            block.classList.add('copy-success');
            showToast('已复制到剪贴板');
            setTimeout(() => {
                block.classList.remove('copy-success');
            }, 500);
        });
    });

    return block;
}
```

- [ ] **Step 3: Commit**

```bash
git add tools/video-script/index.html
git commit -m "feat: add video script generator full implementation"
```

---

### Task 2: Add README

**Files:**
- Create: `tools/video-script/README.md`

- [ ] **Step 1: Create README**

```markdown
# 短视频口播稿生成器

输入视频主题，一键生成结构化短视频口播脚本，分钩子/内容/结尾，适合15秒/30秒/60秒不同时长。

## 功能特点

- 支持三种时长：15秒/30秒/60秒
- 支持四种风格：干货/故事/提问/分享
- 结构化输出：钩子 + 分段内容 + 结尾引导
- 点击任意段落一键复制到剪贴板
- API Key本地存储，隐私安全
- 纯静态页面，无需后端

## 使用方法

1. 输入OpenAI API Key
2. 输入视频主题
3. 选择时长和风格
4. 点击生成，得到结构化口播稿
5. 点击段落直接复制使用

## 技术

- 纯前端HTML + JavaScript
- Tailwind CSS via CDN
- OpenAI GPT-3.5-turbo API
```

- [ ] **Step 2: Update root index.html to add link**

Open `/index.html` and add a new card for this tool in the grid.

- [ ] **Step 3: Commit**

```bash
git add tools/video-script/README.md index.html
git commit -m "docs: add readme and update root index for video script generator"
```

---

## Acceptance Criteria

1. Page loads correctly on desktop and mobile
2. User can select duration (15/30/60s) and style
3. API key saved to localStorage
4. Generate script via OpenAI API
5. Display script in structured blocks (hook/content/ending)
6. Click block to copy with toast notification
7. Clean modern styling with Tailwind

Total estimated development time: **1 day**
