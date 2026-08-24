# 批量字幕生成&关键词打标工具 - 实现计划

**Goal:** Build a web tool that transcribes audio/video to subtitles and automatically extracts keywords for video tagging, helping video creators save time on post-production.

**Architecture:** Single HTML file static web app. Uses OpenAI Whisper API via OpenAI API for transcription, then GPT extracts keywords. All processing through OpenAI API, API key stored locally.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- OpenAI API (Whisper for transcription + GPT for keywords)
- File API for reading uploaded audio/video files
- localStorage for API key
- Shared utils

---

## File Structure

```
tools/subtitle-tag/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/subtitle-tag/index.html`

- [ ] **Step 1: Create full HTML + JavaScript**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>字幕生成&关键词打标 - AI自动转写提词</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">字幕生成&关键词打标</h1>
            <p class="text-gray-600">上传音频/视频，自动转字幕+提取关键词标签</p>
        </header>

        <main class="bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- API Key Settings -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-..."
                       class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">API Key存储在你本地浏览器，不会上传到我们服务器</p>
            </div>

            <!-- File Upload -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">上传音频/视频文件</label>
                <input type="file" id="fileInput" accept="audio/*,video/*"
                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">支持mp3, wav, mp4, mov等格式，文件建议不超过25MB</p>
            </div>

            <!-- Number of Keywords -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">提取关键词数量：<span id="numValue">10</span></label>
                <input type="range" id="numKeywords" min="5" max="20" value="10" step="1"
                       class="w-full accent-blue-500">
            </div>

            <!-- Generate Button -->
            <div class="text-center">
                <button id="processBtn"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                    开始处理
                </button>
            </div>
        </main>

        <!-- Progress Area -->
        <div id="progressArea" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">处理进度</h2>
            <div class="mb-4">
                <div class="w-full bg-gray-200 rounded-full h-2.5">
                    <div id="progressBar" class="bg-blue-600 h-2.5 rounded-full w-0"></div>
                </div>
            </div>
            <p id="progressText" class="text-sm text-gray-600"></p>
        </div>

        <!-- Results Area -->
        <div id="results" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- Subtitle Result -->
            <div class="mb-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">字幕内容（点击复制）</h2>
                <div id="subtitleContainer" class="p-4 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:border-blue-300 transition-colors">
                    <p id="subtitleText"></p>
                </div>
                <button id="copySubtitleBtn" class="mt-2 text-sm text-blue-600 hover:text-blue-700">复制全部字幕</button>
            </div>

            <!-- Keywords Result -->
            <div class="mb-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">推荐标签（点击复制）</h2>
                <div id="keywordsContainer" class="flex flex-wrap gap-2"></div>
            </div>

            <!-- Download SRT -->
            <div class="text-center">
                <a id="downloadSrtBtn" class="hidden inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-md transition-colors">
                    下载SRT字幕文件
                </a>
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
// Configuration
const API_ENDPOINT = 'https://api.openai.com/v1';

// DOM Elements
const apiKeyInput = document.getElementById('apiKey');
const fileInput = document.getElementById('fileInput');
const numKeywordsInput = document.getElementById('numKeywords');
const numValueSpan = document.getElementById('numValue');
const processBtn = document.getElementById('processBtn');
const progressArea = document.getElementById('progressArea');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const resultsDiv = document.getElementById('results');
const subtitleContainer = document.getElementById('subtitleContainer');
const subtitleText = document.getElementById('subtitleText');
const keywordsContainer = document.getElementById('keywordsContainer');
const copySubtitleBtn = document.getElementById('copySubtitleBtn');
const downloadSrtBtn = document.getElementById('downloadSrtBtn');

// State
let currentFile = null;
let fullSubtitle = '';
let srtContent = '';
let selectedNumKeywords = 10;

// Load saved API key
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = getFromLocalStorage('openai_api_key', '');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

// Save API key
apiKeyInput.addEventListener('change', () => {
    saveToLocalStorage('openai_api_key', apiKeyInput.value);
});

// Update number display
numKeywordsInput.addEventListener('input', () => {
    numValueSpan.textContent = numKeywordsInput.value;
    selectedNumKeywords = parseInt(numKeywordsInput.value);
});

// File selection
fileInput.addEventListener('change', (e) => {
    currentFile = e.target.files[0];
    if (currentFile) {
        showToast(\`已选择文件：\${currentFile.name} (\${formatFileSize(currentFile.size)})\`);
    }
});

// Copy full subtitle
copySubtitleBtn.addEventListener('click', () => {
    copyToClipboard(fullSubtitle).then(() => {
        showToast('完整字幕已复制到剪贴板');
    });
});

// Process button click
processBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();

    // Validation
    if (!apiKey) {
        showToast('请输入OpenAI API Key');
        return;
    }
    if (!currentFile) {
        showToast('请先上传音频/视频文件');
        return;
    }
    if (currentFile.size > 25 * 1024 * 1024) {
        showToast('文件大小建议不超过25MB');
        return;
    }

    processBtn.disabled = true;
    progressArea.classList.remove('hidden');
    resultsDiv.classList.add('hidden');

    try {
        updateProgress(10, '正在转写字幕...');
        const transcription = await transcribeAudio(apiKey, currentFile);
        fullSubtitle = transcription.text;
        srtContent = generateSrt(transcription.segments);

        updateProgress(60, '正在提取关键词...');
        const keywords = await extractKeywords(apiKey, transcription.text, selectedNumKeywords);

        updateProgress(100, '处理完成');
        displayResults(transcription.text, keywords);
        showToast('处理完成！');
    } catch (error) {
        console.error(error);
        showToast('处理失败：' + error.message);
    } finally {
        processBtn.disabled = false;
        progressArea.classList.add('hidden');
    }
});

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateProgress(percent, text) {
    progressBar.style.width = percent + '%';
    progressText.textContent = text;
}

async function transcribeAudio(apiKey, file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', 'whisper-1');
    formData.append('response_format', 'verbose_json');

    const response = await fetch(API_ENDPOINT + '/audio/transcriptions', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + apiKey
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || '转写失败');
    }

    return await response.json();
}

async function extractKeywords(apiKey, text, numKeywords) {
    const prompt = \`请从下面这个视频字幕内容中提取\${numKeywords}个最重要的关键词/标签，用于视频SEO推荐。请直接输出JSON数组格式：["关键词1", "关键词2", ...]，不要任何其他说明。

字幕内容：
\${text}\`;

    const response = await fetch(API_ENDPOINT + '/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + apiKey
        },
        body: JSON.stringify({
            model: 'gpt-3.5-turbo',
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.5
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || '关键词提取失败');
    }

    const data = await response.json();
    const content = data.choices[0].message.content.trim();

    try {
        const cleanContent = content.replace(/^```json\n?/, '').replace(/\n?```$/, '');
        return JSON.parse(cleanContent);
    } catch (e) {
        console.error('Failed to parse JSON:', content);
        throw new Error('解析关键词失败');
    }
}

function displayResults(subtitle, keywords) {
    // Display subtitle
    subtitleText.textContent = subtitle;

    // Click to copy whole subtitle
    subtitleContainer.addEventListener('click', () => {
        copyToClipboard(subtitle).then(() => {
            subtitleContainer.classList.add('copy-success');
            showToast('字幕已复制');
            setTimeout(() => {
                subtitleContainer.classList.remove('copy-success');
            }, 500);
        });
    });

    // Display keywords
    keywordsContainer.innerHTML = '';
    keywords.forEach(keyword => {
        const tag = document.createElement('span');
        tag.className = 'px-4 py-2 bg-blue-100 text-blue-800 rounded-full cursor-pointer hover:bg-blue-200 transition-colors';
        tag.textContent = keyword;
        tag.addEventListener('click', () => {
            copyToClipboard(keyword).then(() => {
                tag.classList.add('copy-success');
                showToast('关键词已复制');
                setTimeout(() => {
                    tag.classList.remove('copy-success');
                }, 500);
            });
        });
        keywordsContainer.appendChild(tag);
    });

    // Enable download SRT
    downloadSrtBtn.classList.remove('hidden');
    downloadSrtBtn.href = URL.createObjectURL(new Blob([srtContent], { type: 'text/plain' }));
    downloadSrtBtn.download = currentFile.name.replace(/\.[^.]+$/, '.srt');

    resultsDiv.classList.remove('hidden');
}

function generateSrt(segments) {
    if (!segments) return '';

    let srt = '';
    segments.forEach((seg, index) => {
        const start = formatSrtTime(seg.start);
        const end = formatSrtTime(seg.end);
        srt += \`\${index + 1}
\${start} --> \${end}
\${seg.text}

\`;
    });
    return srt;
}

function formatSrtTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds - Math.floor(seconds)) * 1000);
    return \`\${String(hours).padStart(2, '0')}:\${String(minutes).padStart(2, '0')}:\${String(secs).padStart(2, '0')},\${String(ms).padStart(3, '0')}\`;
}
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/subtitle-tag/index.html
git commit -m "feat: add subtitle keyword generator full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/subtitle-tag/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 字幕生成&关键词打标工具

上传音频或视频文件，自动转写字幕 + AI提取关键词标签，帮短视频创作者节省后期制作时间。

## 功能特点

- 自动转写：支持多种音频视频格式转写字幕
- 关键词提取：AI自动从内容中提取推荐标签，利于SEO
- 可下载SRT字幕文件导入剪辑软件
- 点击任意关键词或完整字幕一键复制
- API Key本地存储，隐私安全
- 纯静态页面，无需后端

## 使用方法

1. 输入OpenAI API Key
2. 上传音频或视频文件（建议≤25MB）
3. 选择需要提取的关键词数量（5-20个）
4. 点击开始处理，等待转写和提取
5. 复制字幕或关键词，可下载SRT文件

## 技术

- OpenAI Whisper API 语音转文字
- OpenAI GPT 提取关键词
- 纯前端HTML + JavaScript
- Tailwind CSS via CDN
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/subtitle-tag/README.md index.html
git commit -m "docs: add readme and update root index for subtitle generator"
```

---

## Acceptance Criteria

1. Page loads correctly
2. File upload works (audio/video)
3. Transcribe via OpenAI Whisper API
4. Extract keywords via GPT
5. Display subtitle and keywords, click to copy
6. Download SRT file works
7. Responsive layout

Total estimated development time: **1 day**
