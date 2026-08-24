# 电商标题智能生成工具 - 实现计划

**Goal:** Build a web tool that generates optimized product titles for e-commerce based on core product keywords, combining popular high-traffic keywords to improve search ranking.

**Architecture:** Single HTML static page. Uses OpenAI API to generate optimized titles based on user input keywords.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- OpenAI API

---

## File Structure

```
tools/ecommerce-title-gen/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/ecommerce-title-gen/index.html`

- [ ] **Step 1: Create full HTML + JavaScript**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>电商标题智能生成器 - 优化搜索权重</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">电商标题智能生成器</h1>
            <p class="text-gray-600">输入产品核心词，AI生成搜索优化的高权重标题</p>
        </header>

        <main class="bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- API Key -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-..."
                       class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">API Key存储在你本地浏览器，不会上传到我们服务器</p>
            </div>

            <!-- Core Product -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">产品核心词</label>
                <input type="text" id="coreProduct" placeholder="例如：连衣裙，蓝牙耳机..."
                       class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>

            <!-- Attributes -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">产品属性/特点（每行一个）</label>
                <textarea id="attributes" placeholder="例如：&#10;纯棉&#10;显瘦&#10;大码&#10;夏季新款"
                          class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="5"></textarea>
            </div>

            <!-- Platform -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">平台</label>
                <div class="grid grid-cols-2 gap-2">
                    <button class="platform-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-platform="pdd">拼多多</button>
                    <button class="platform-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-platform="taobao">淘宝</button>
                </div>
            </div>

            <!-- Number of Titles -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">生成标题数量：<span id="numValue">5</span></label>
                <input type="range" id="numTitles" min="3" max="10" value="5" step="1"
                       class="w-full accent-blue-500">
            </div>

            <div class="text-center">
                <button id="generateBtn"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                    生成标题
                </button>
            </div>
        </main>

        <!-- Results -->
        <div id="results" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">生成结果（点击标题复制）</h2>
            <div id="titlesList" class="space-y-3"></div>
        </div>

        <footer class="text-center text-gray-500 text-sm">
            <p>© 2026 工具集 · 小而美，解决真问题</p>
        </footer>

        <!-- Toast -->
        <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg opacity-0 transition-opacity duration-300 hidden"></div>
    </div>

    <script src="../../shared/utils.js"></script>
    <script>
// Configuration
const API_ENDPOINT = 'https://api.openai.com/v1/chat/completions';

// DOM Elements
const apiKeyInput = document.getElementById('apiKey');
const coreProductInput = document.getElementById('coreProduct');
const attributesInput = document.getElementById('attributes');
const platformBtns = document.querySelectorAll('.platform-btn');
const numTitlesInput = document.getElementById('numTitles');
const numValueSpan = document.getElementById('numValue');
const generateBtn = document.getElementById('generateBtn');
const resultsDiv = document.getElementById('results');
const titlesListDiv = document.getElementById('titlesList');

// State
let selectedPlatform = 'pdd';
let selectedNumTitles = 5;

// Load saved API key
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = getFromLocalStorage('openai_api_key', '');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

// Update number
numTitlesInput.addEventListener('input', () => {
    numValueSpan.textContent = numTitlesInput.value;
    selectedNumTitles = parseInt(numTitlesInput.value);
});

// Save API key
apiKeyInput.addEventListener('change', () => {
    saveToLocalStorage('openai_api_key', apiKeyInput.value);
});

// Platform selection
platformBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        platformBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedPlatform = btn.dataset.platform;
    });
});

// Generate
generateBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    const coreProduct = coreProductInput.value.trim();
    const attributesText = attributesInput.value.trim();

    // Validation
    if (!apiKey) {
        showToast('请输入OpenAI API Key');
        return;
    }
    if (!coreProduct) {
        showToast('请输入产品核心词');
        return;
    }

    const attributes = attributesText.split('\\n').map(l => l.trim()).filter(l => l);

    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const titles = await generateTitles(apiKey, coreProduct, attributes, selectedPlatform, selectedNumTitles);
        displayTitles(titles);
        showToast('生成完成！点击标题复制');
    } catch (error) {
        console.error(error);
        showToast('生成失败：' + error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '生成标题';
    }
});

async function generateTitles(apiKey, coreProduct, attributes, platform, count) {
    const platformName = platform === 'pdd' ? '拼多多' : '淘宝';

    const prompt = `你是一个电商标题优化专家，请为${platformName}平台的${coreProduct}生成${count}个搜索优化标题。

产品属性特点：
${attributes.join('\\n')}

要求：
- 每个标题控制在30-60字符
- 把核心词和属性关键词放前面提高搜索权重
- 符合${platformName}平台用户搜索习惯
- 请直接输出JSON数组格式：["标题1", "标题2", ...]
- 不要任何其他说明文字`;

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

function displayTitles(titles) {
    titlesListDiv.innerHTML = '';

    titles.forEach((title, index) => {
        const titleEl = document.createElement('div');
        titleEl.className = 'p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors cursor-pointer';
        titleEl.innerHTML = `
            <div class="flex items-start justify-between gap-3">
                <p class="text-gray-800 text-lg">${title}</p>
                <span class="text-gray-400 text-sm">${index + 1}</span>
            </div>
        `;

        titleEl.addEventListener('click', () => {
            copyToClipboard(title).then(() => {
                titleEl.classList.add('copy-success');
                showToast('已复制到剪贴板');
                setTimeout(() => {
                    titleEl.classList.remove('copy-success');
                }, 500);
            });
        });

        titlesListDiv.appendChild(titleEl);
    });

    resultsDiv.classList.remove('hidden');
}
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/ecommerce-title-gen/index.html
git commit -m "feat: add ecommerce title generator full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/ecommerce-title-gen/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 电商标题智能生成器

输入产品核心词和属性，AI生成搜索优化的高权重电商标题，适合拼多多/淘宝。

## 功能特点

- 支持拼多多/淘宝不同平台搜索习惯优化
- 自定义生成标题数量（3-10个）
- 点击标题一键复制
- API Key本地存储，隐私安全
- 纯静态页面，无需后端

## 使用方法

1. 输入OpenAI API Key
2. 输入产品核心词
3. 每行输入一个产品属性/特点
4. 选择平台
5. 选择生成数量
6. 点击生成，点击标题复制使用

## 技术

- OpenAI GPT API
- 纯前端HTML + JavaScript
- Tailwind CSS via CDN
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/ecommerce-title-gen/README.md index.html
git commit -m "docs: add readme and update root index for ecommerce title generator"
```

---

## Acceptance Criteria

1. Page loads correctly
2. User inputs all required info
3. Calls OpenAI API to generate titles
4. Displays generated titles, click to copy
5. Platform selection works
6. Responsive layout

Total estimated development time: **1 day**
