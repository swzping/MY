# 健身计划自动生成器 - 实现计划

**Goal:** Build a web tool that generates personalized workout plans based on user's goals, fitness level, available equipment, days per week. Uses OpenAI API to generate the plan.

**Architecture:** Single static HTML page, user inputs parameters, calls OpenAI API to generate customized workout plan. API Key stored locally.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- OpenAI API
- Local storage for API Key

---

## File Structure

```
tools/workout-generator/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/workout-generator/index.html`

- [ ] **Step 1: Create full HTML + JavaScript**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>健身计划自动生成器 - 定制你的训练计划</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">健身计划自动生成器</h1>
            <p class="text-gray-600">输入你的目标和条件，AI生成个性化健身计划</p>
        </header>

        <main class="bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- API Key -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-..."
                       class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">API Key存储在你本地浏览器，不会上传到我们服务器</p>
            </div>

            <div class="grid md:grid-cols-2 gap-6">
                <!-- Fitness Goal -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">健身目标</label>
                    <select id="fitnessGoal" class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="weight_loss">减脂减重</option>
                        <option value="muscle_gain">增肌增重</option>
                        <option value="strength">增强力量</option>
                        <option value="endurance">提升耐力</option>
                        <option value="flexibility">柔韧性舒展</option>
                        <option value="keep_fit">保持健康</option>
                    </select>
                </div>

                <!-- Fitness Level -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">健身水平</label>
                    <select id="fitnessLevel" class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="beginner">新手入门</option>
                        <option value="intermediate">中级训练者</option>
                        <option value="advanced">高级训练者</option>
                    </select>
                </div>

                <!-- Training Days -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">每周训练天数：<span id="daysValue">4</span></label>
                    <input type="range" id="trainingDays" min="3" max="6" value="4" step="1"
                           class="w-full accent-blue-500">
                </div>

                <!-- Gender -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">性别</label>
                    <div class="grid grid-cols-2 gap-2">
                        <button class="gender-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-gender="male">男</button>
                        <button class="gender-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-gender="female">女</button>
                    </div>
                </div>
            </div>

            <!-- Equipment -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">可用器械</label>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="full_gym" checked>
                        <span>健身房全套器械</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="dumbbell" checked>
                        <span>哑铃</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="barbell" checked>
                        <span>杠铃</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="bench">
                        <span>卧推凳</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="pull_up_bar">
                        <span>单杠</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="resistance_bands">
                        <span>弹力带</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="kettlebell">
                        <span>壶铃</span>
                    </label>
                    <label class="flex items-center gap-2 p-2 border border-gray-200 rounded cursor-pointer hover:border-blue-300 transition-colors">
                        <input type="checkbox" name="equipment" value="bodyweight">
                        <span>无器械（仅自重）</span>
                    </label>
                </div>
            </div>

            <!-- Additional Notes -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">额外要求（可选）</label>
                <textarea id="additionalNotes" placeholder="例如：我想重点练腹肌，我膝盖有伤需要避免深蹲..."
                          class="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="3"></textarea>
            </div>

            <div class="text-center">
                <button id="generateBtn"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                    生成健身计划
                </button>
            </div>
        </main>

        <!-- Results -->
        <div id="results" class="hidden bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">你的个性化健身计划（点击段落复制）</h2>
            <div id="workoutContent" class="space-y-4 text-gray-700 leading-relaxed">
            </div>
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
const fitnessGoalSelect = document.getElementById('fitnessGoal');
const fitnessLevelSelect = document.getElementById('fitnessLevel');
const trainingDaysInput = document.getElementById('trainingDays');
const daysValueSpan = document.getElementById('daysValue');
const genderBtns = document.querySelectorAll('.gender-btn');
const additionalNotesInput = document.getElementById('additionalNotes');
const generateBtn = document.getElementById('generateBtn');
const resultsDiv = document.getElementById('results');
const workoutContentDiv = document.getElementById('workoutContent');

// State
let selectedGender = 'male';
let selectedDays = 4;

// Load saved API key
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = getFromLocalStorage('openai_api_key', '');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
});

// Update days
trainingDaysInput.addEventListener('input', () => {
    daysValueSpan.textContent = trainingDaysInput.value;
    selectedDays = parseInt(trainingDaysInput.value);
});

// Save API key
apiKeyInput.addEventListener('change', () => {
    saveToLocalStorage('openai_api_key', apiKeyInput.value);
});

// Gender selection
genderBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        genderBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedGender = btn.dataset.gender;
    });
});

// Get goal name
function getGoalName(goal) {
    const names = {
        weight_loss: '减脂减重',
        muscle_gain: '增肌增重',
        strength: '增强力量',
        endurance: '提升耐力',
        flexibility: '柔韧性舒展',
        keep_fit: '保持健康'
    };
    return names[goal] || goal;
}

// Get level name
function getLevelName(level) {
    const names = {
        beginner: '新手入门（训练少于1年）',
        intermediate: '中级训练者（训练1-3年）',
        advanced: '高级训练者（训练3年以上）'
    };
    return names[level] || level;
}

// Generate
generateBtn.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();

    if (!apiKey) {
        showToast('请输入OpenAI API Key');
        return;
    }

    // Get selected equipment
    const equipmentChecked = Array.from(document.querySelectorAll('input[name="equipment"]:checked'))
        .map(el => el.value);

    const equipmentNames = {
        full_gym: '健身房全套器械',
        dumbbell: '哑铃',
        barbell: '杠铃',
        bench: '卧推凳',
        pull_up_bar: '单杠',
        resistance_bands: '弹力带',
        kettlebell: '壶铃',
        bodyweight: '无器械（仅自重训练）'
    };

    const equipmentList = equipmentChecked.map(e => equipmentNames[e] || e);

    const goal = fitnessGoalSelect.value;
    const level = fitnessLevelSelect.value;
    const additionalNotes = additionalNotesInput.value.trim();

    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';

    try {
        const plan = await generateWorkoutPlan(apiKey, goal, level, selectedDays, selectedGender, equipmentList, additionalNotes);
        displayPlan(plan);
        showToast('健身计划生成完成！');
    } catch (error) {
        console.error(error);
        showToast('生成失败：' + error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '生成健身计划';
    }
});

async function generateWorkoutPlan(apiKey, goal, level, days, gender, equipment, notes) {
    const goalName = getGoalName(goal);
    const levelName = getLevelName(level);
    const genderName = gender === 'male' ? '男性' : '女性';

    let prompt = `你是一位专业的健身教练，请为一位${genderName}生成一个每周${days}天的健身计划。\n\n`;
    prompt += `健身目标：${goalName}\n`;
    prompt += `健身水平：${levelName}\n`;
    prompt += `可用器械：${equipment.join('、')}\n`;

    if (notes) {
        prompt += `\n额外要求：${notes}\n`;
    }

    prompt += `\n请生成一份完整的每周训练计划，要求：
1. 分天安排训练部位
2. 每个动作推荐组数和次数
3. 给出热身建议
4. 给出拉伸放松建议
5. 给出饮食建议（根据目标）
6. 给出休息建议
7. 用markdown格式输出，分多个小节

请直接输出计划内容，不要多余开场白。`;

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
    return data.choices[0].message.content.trim();
}

function displayPlan(plan) {
    // Split into sections by headings
    workoutContentDiv.innerHTML = '';

    // Simple markdown parsing - split by headings
    const sections = plan.split(/(?=^#{1,3} )/m);

    sections.forEach(section => {
        if (!section.trim()) return;

        // Check if it's a heading
        const headingMatch = section.match(/^(#{1,3}) (.*)$/m);

        if (headingMatch) {
            const level = headingMatch[1].length;
            const title = headingMatch[2];
            const content = section.slice(headingMatch[0].length).trim();

            let headingClass = '';
            if (level === 1) headingClass = 'text-2xl font-bold text-gray-800 mt-6 mb-4';
            if (level === 2) headingClass = 'text-xl font-semibold text-gray-800 mt-4 mb-2';
            if (level === 3) headingClass = 'text-lg font-semibold text-gray-800 mt-3 mb-2';

            const headingEl = document.createElement('div');
            headingEl.className = headingClass;
            headingEl.textContent = title;
            workoutContentDiv.appendChild(headingEl);

            if (content) {
                const contentEl = document.createElement('div');
                contentEl.className = 'px-2 mb-3 whitespace-pre-line';
                contentEl.textContent = content;
                contentEl.addEventListener('click', () => {
                    copyToClipboard(contentEl.textContent.trim());
                    showToast('已复制到剪贴板');
                });
                workoutContentDiv.appendChild(contentEl);
            }
        } else {
            const el = document.createElement('div');
            el.className = 'px-2 mb-3 whitespace-pre-line';
            el.textContent = section;
            el.addEventListener('click', () => {
                copyToClipboard(el.textContent.trim());
                showToast('已复制到剪贴板');
            });
            workoutContentDiv.appendChild(el);
        }
    });

    resultsDiv.classList.remove('hidden');
    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/workout-generator/index.html
git commit -m "feat: add workout plan generator full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/workout-generator/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 健身计划自动生成器

输入你的健身目标、训练水平、可用器械，AI生成个性化的每周健身计划。

## 功能特点

- 支持多种健身目标：减脂/增肌/力量/耐力/保持健康
- 适配不同训练水平：新手/中级/高级
- 可选每周训练天数：3-6天
- 支持健身房器械、哑铃、无器械等多种配置
- API Key本地存储，隐私安全
- 点击任意段落一键复制
- 纯静态页面，无需后端

## 使用方法

1. 输入OpenAI API Key
2. 选择健身目标和你的训练水平
3. 选择每周训练天数和性别
4. 勾选你可用的健身器械
5. 填写额外要求（可选）
6. 点击生成，获取你的个性化计划

## 技术

- OpenAI GPT API
- 纯前端HTML + JavaScript
- localStorage本地存储
- Tailwind CSS via CDN
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/workout-generator/README.md index.html
git commit -m "docs: add readme and update root index for workout generator"
```

---

## Acceptance Criteria

1. Page loads correctly
2. All input selections work
3. Calls OpenAI API to generate workout plan
4. Displays formatted plan correctly
5. Click to copy works
6. Responsive layout

Total estimated development time: **1 day**
