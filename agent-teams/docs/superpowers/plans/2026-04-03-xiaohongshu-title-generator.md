# 小红书标题多版本生成工具 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web tool that generates multiple different styles of Xiaohongshu (Little Red Book) titles based on user input topic, helping content creators quickly test different title options.

**Architecture:** Single HTML file static web app, using Tailwind CSS CDN for styling, calling OpenAI API to generate titles. All processing happens in the browser, no backend required. User's API key is stored in localStorage for convenience.

**Tech Stack:**
- HTML + vanilla JavaScript (no framework)
- Tailwind CSS via CDN (no build step needed)
- OpenAI API for title generation
- localStorage for saving API key
- Deploy on Vercel/Netlify as static site

---

## File Structure

```
tools/xiaohongshu-title/
├── index.html                 # Main tool page (all code here)
└── README.md                  # Short introduction
shared/
├── common.css                 # Common styles (will be created if not exist)
└── utils.js                   # Common utilities (will be created if not exist)
```

---

## Tasks

### Task 1: Create project structure and main HTML file skeleton

**Files:**
- Create: `tools/xiaohongshu-title/index.html`
- Create: `shared/common.css`
- Create: `shared/utils.js`

- [ ] **Step 1: Create the main HTML file structure**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书标题生成器 - AI多风格标题生成</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">小红书标题生成器</h1>
            <p class="text-gray-600">输入主题，一键生成10个不同风格爆款标题</p>
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
                <label class="block text-sm font-medium text-gray-700 mb-2">文章/视频主题</label>
                <textarea id="topic" placeholder="例如：分享5个新手做饭技巧，三分钟搞定早餐..." 
                          class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="3"></textarea>
            </div>

            <!-- Number of Titles -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">生成标题数量：<span id="numValue">10</span></label>
                <input type="range" id="numTitles" min="5" max="20" value="10" step="1"
                       class="w-full accent-blue-500">
            </div>

            <!-- Generate Button -->
            <div class="text-center">
                <button id="generateBtn" 
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                    生成标题
                </button>
            </div>
        </main>

        <!-- Results Area -->
        <div id="results" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">生成结果（点击标题复制）</h2>
            <div id="titlesList" class="space-y-3"></div>
        </div>

        <!-- Styles Explained -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-3">标题风格说明</h3>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                <span class="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">悬念型</span>
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">干货型</span>
                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full">福利型</span>
                <span class="px-3 py-1 bg-orange-100 text-orange-800 rounded-full">提问型</span>
                <span class="px-3 py-1 bg-red-100 text-red-800 rounded-full">故事型</span>
            </div>
        </div>

        <footer class="text-center text-gray-500 text-sm">
            <p>© 2026 工具集 · 让内容创作更高效</p>
        </footer>

        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg opacity-0 transition-opacity duration-300 hidden"></div>
    </div>

    <script src="../../shared/utils.js"></script>
    <script>
        // Main JavaScript will be added in next step
    </script>
</body>
</html>
```

- [ ] **Step 2: Create shared common.css**

```css
/* Common styles for all tools */
.hidden {
    display: none !important;
}

.toast-show {
    opacity: 1 !important;
}

.copy-success {
    background-color: #10b981 !important;
    color: white !important;
}
```

- [ ] **Step 3: Create shared utils.js**

```javascript
// Common utility functions

function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.offsetHeight; // Trigger reflow
    toast.classList.add('toast-show');
    
    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 300);
    }, duration);
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }
    
    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    return Promise.resolve();
}

function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (e) {
        console.error('Failed to save to localStorage', e);
    }
}

function getFromLocalStorage(key, defaultValue = '') {
    try {
        const value = localStorage.getItem(key);
        return value === null ? defaultValue : value;
    } catch (e) {
        console.error('Failed to get from localStorage', e);
        return defaultValue;
    }
}
```

- [ ] **Step 4: Commit**

```bash
git add tools/xiaohongshu-title/index.html shared/common.css shared/utils.js
git commit -m "feat: create xiaohongshu title generator project skeleton"
```

---

### Task 2: Implement JavaScript functionality

**Files:**
- Modify: `tools/xiaohongshu-title/index.html`

- [ ] **Step 1: Replace the script section with full implementation**

```javascript
// Configuration
const API_ENDPOINT = 'https://api.openai.com/v1/chat/completions';

// Prompt template for title generation
const PROMPT_TEMPLATE = `你是一个小红书爆款标题专家。
用户提供的主题是：{{topic}}
请生成{{number}}个不同风格的小红书标题，包含以下风格：悬念型、干货型、福利型、提问型、故事型。
每个标题控制在15-25字之间，符合小红书用户喜好，多用emoji，善于用数字吸引点击。
请直接输出JSON格式，格式如下：
[
  { "title": "标题内容", "style": "风格名称" },
  ...
]
不要有任何其他说明文字，只输出JSON。`;

// DOM Elements
const apiKeyInput = document.getElementById('apiKey');
const topicInput = document.getElementById('topic');
const numTitlesInput = document.getElementById('numTitles');
const numValueSpan = document.getElementById('numValue');
const generateBtn = document.getElementById('generateBtn');
const resultsDiv = document.getElementById('results');
const titlesListDiv = document.getElementById('titlesList');

// Style classes mapping
const styleClasses = {
    '悬念型': 'bg-purple-100 text-purple-800',
    '干货型': 'bg-blue-100 text-blue-800',
    '福利型': 'bg-green-100 text-green-800',
    '提问型': 'bg-orange-100 text-orange-800',
    '故事型': 'bg-red-100 text-red-800',
};

// Load saved API key
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = getFromLocalStorage('xiaohongshu_openai_key', '');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

// Update number display
numTitlesInput.addEventListener('input', () => {
    numValueSpan.textContent = numTitlesInput.value;
});

// Save API key when changed
apiKeyInput.addEventListener('change', () => {
    saveToLocalStorage('xiaohongshu_openai_key', apiKeyInput.value);
});

// Generate button click handler
generateBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    const topic = topicInput.value.trim();
    const numTitles = parseInt(numTitlesInput.value);
    
    // Validation
    if (!apiKey) {
        showToast('请输入OpenAI API Key');
        return;
    }
    if (!topic) {
        showToast('请输入文章主题');
        return;
    }
    
    // Disable button
    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';
    
    try {
        const titles = await generateTitles(apiKey, topic, numTitles);
        displayTitles(titles);
        resultsDiv.classList.remove('hidden');
        showToast('生成完成！点击标题即可复制');
    } catch (error) {
        console.error(error);
        showToast('生成失败：' + error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '生成标题';
    }
});

async function generateTitles(apiKey, topic, numTitles) {
    const prompt = PROMPT_TEMPLATE.replace('{{topic}}', topic).replace('{{number}}', numTitles);
    
    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({
            model: 'gpt-3.5-turbo',
            messages: [
                { role: 'user', content: prompt }
            ],
            temperature: 0.8
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'API调用失败');
    }
    
    const data = await response.json();
    const content = data.choices[0].message.content.trim();
    
    // Parse JSON response
    try {
        // Remove any possible markdown code block markers
        const cleanContent = content.replace(/^```json\n?/, '').replace(/\n?```$/, '');
        return JSON.parse(cleanContent);
    } catch (e) {
        console.error('Failed to parse JSON:', content);
        throw new Error('解析AI返回结果失败');
    }
}

function displayTitles(titles) {
    titlesListDiv.innerHTML = '';
    
    titles.forEach((item, index) => {
        const styleClass = styleClasses[item.style] || 'bg-gray-100 text-gray-800';
        
        const titleEl = document.createElement('div');
        titleEl.className = 'p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors cursor-pointer';
        titleEl.innerHTML = `
            <div class="flex items-start justify-between gap-3">
                <div class="flex-1">
                    <p class="text-lg font-medium text-gray-800 mb-2">${item.title}</p>
                    <span class="inline-block px-2 py-1 rounded text-xs ${styleClass}">${item.style}</span>
                </div>
                <span class="text-gray-400 text-sm">${index + 1}</span>
            </div>
        `;
        
        titleEl.addEventListener('click', () => {
            copyToClipboard(item.title).then(() => {
                titleEl.classList.add('copy-success');
                showToast('已复制到剪贴板');
                setTimeout(() => {
                    titleEl.classList.remove('copy-success');
                }, 500);
            });
        });
        
        titlesListDiv.appendChild(titleEl);
    });
}
```

- [ ] **Step 2: Test the page works in browser**

Open `tools/xiaohongshu-title/index.html` in a browser to verify:
- Page layout renders correctly
- API key loads from localStorage if saved
- Slider updates number display
- Validation works when clicking generate without inputs

- [ ] **Step 3: Commit**

```bash
git add tools/xiaohongshu-title/index.html
git commit -m "feat: implement full javascript functionality for title generation"
```

---

### Task 3: Add README and test completion

**Files:**
- Create: `tools/xiaohongshu-title/README.md`

- [ ] **Step 1: Create README**

```markdown
# 小红书标题多版本生成工具

输入文章主题，一键生成多个不同风格的小红书标题，帮助创作者快速测试哪个标题点击率更高。

## 功能特点

- 支持5种不同标题风格：悬念型、干货型、福利型、提问型、故事型
- 可自定义生成5-20个标题
- 点击标题一键复制到剪贴板
- API Key保存在本地浏览器，不会上传
- 纯静态页面，无需后端

## 使用方法

1. 输入你的OpenAI API Key
2. 输入文章/视频主题
3. 选择要生成的标题数量
4. 点击生成，等待几秒即可
5. 点击喜欢的标题直接复制使用

## 技术

- 纯前端HTML + JavaScript
- Tailwind CSS via CDN
- OpenAI GPT-3.5-turbo API
```

- [ ] **Step 2: Verify complete and commit**

```bash
git add tools/xiaohongshu-title/README.md
git commit -m "docs: add readme for xiaohongshu title generator"
```

---

## Post-Implementation Checks

- [ ] Verify all functionality works:
  - [ ] API key saves to localStorage ✓
  - [ ] Form validation works ✓
  - [ ] API calls succeed ✓
  - [ ] JSON parsing works ✓
  - [ ] Titles display correctly ✓
  - [ ] Click to copy works ✓
  - [ ] Toast notification shows ✓
  - [ ] Mobile responsive layout ✓

- [ ] Update root index.html to link to this tool ✓

---

## Acceptance Criteria

1. Page loads correctly on desktop and mobile
2. User can enter API key (saved locally)
3. User can enter topic and select number of titles
4. Clicking generate calls OpenAI API and returns titles
5. Each title shows its style tag
6. Clicking title copies to clipboard and shows toast
7. All styling looks clean and modern

Total estimated development time: **1-2 days**
