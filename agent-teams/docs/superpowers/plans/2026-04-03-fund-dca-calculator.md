# 基金定投智能计算器&回测工具 - 实现计划

**Goal:** Build a web tool that backtests different dollar-cost averaging (DCA) strategies for mutual funds/index funds, comparing different frequencies and take-profit strategies to show actual historical returns.

**Architecture:** Single HTML static page. Uses free Eastmoney API to get historical fund data, performs backtest calculation in browser, displays results with chart.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- Chart.js for charts via CDN
- Free public fund API from Eastmoney
- localStorage for user settings

---

## File Structure

```
tools/fund-dca-calculator/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/fund-dca-calculator/index.html`

- [ ] **Step 1: Create full HTML**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金定投回测计算器 - 对比不同策略收益</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-5xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">基金定投回测计算器</h1>
            <p class="text-gray-600">输入基金代码，回测不同定投策略的历史收益</p>
        </header>

        <div class="grid md:grid-cols-2 gap-6">
            <!-- Input Panel -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">参数设置</h2>

                <!-- Fund Code -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">基金代码</label>
                    <input type="text" id="fundCode" placeholder="例如：161725 (招商中证白酒)"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Start Date -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">开始日期</label>
                    <input type="date" id="startDate"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Monthly Investment -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">每期定投金额 (元)</label>
                    <input type="number" id="investmentAmount" value="1000" min="100" step="100"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Frequency -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">定投频率</label>
                    <div class="grid grid-cols-3 gap-2">
                        <button class="freq-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-freq="weekly">每周</button>
                        <button class="freq-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-freq="biweekly">每两周</button>
                        <button class="freq-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-freq="monthly">每月</button>
                    </div>
                </div>

                <!-- Take Profit -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">止盈设置</label>
                    <div class="grid grid-cols-2 gap-2">
                        <button class="tp-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-tp="none">不止盈</button>
                        <button class="tp-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-tp="percent">收益率止盈</button>
                    </div>
                </div>

                <div id="tpPercentRow" class="mb-4 hidden">
                    <label class="block text-sm font-medium text-gray-700 mb-2">止盈收益率 (%)</label>
                    <input type="number" id="takeProfitPercent" value="20" min="5" max="100" step="5"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <div class="mt-6 text-center">
                    <button id="calculateBtn"
                            class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                        开始回测
                    </button>
                </div>
            </div>

            <!-- Result Summary -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">回测结果</h2>
                <div id="resultSummary" class="hidden space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">总投入</div>
                            <div class="text-2xl font-bold text-gray-800" id="totalInvestment">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">当前市值</div>
                            <div class="text-2xl font-bold text-gray-800" id="currentValue">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">收益率</div>
                            <div class="text-2xl font-bold" id="returnPercentage">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">年化收益率</div>
                            <div class="text-2xl font-bold" id="annualReturn">-</div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <div class="text-sm text-gray-600">定投次数</div>
                        <div class="text-xl font-semibold text-gray-800" id="totalTimes">-</div>
                    </div>
                </div>
                <div id="loading" class="hidden py-12 text-center text-gray-500">
                    <p>正在获取数据计算中...</p>
                </div>
                <div id="error" class="hidden py-12 text-center text-red-500">
                    <p id="errorMessage">获取数据失败</p>
                </div>
            </div>
        </div>

        <!-- Chart -->
        <div class="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">累计收益曲线</h2>
            <canvas id="equityChart" width="400" height="200"></canvas>
        </div>

        <!-- Comparison with different strategies -->
        <div class="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">策略对比</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2 text-left">策略</th>
                            <th class="px-4 py-2 text-right">总投入</th>
                            <th class="px-4 py-2 text-right">期末市值</th>
                            <th class="px-4 py-2 text-right">收益率</th>
                            <th class="px-4 py-2 text-right">年化</th>
                        </tr>
                    </thead>
                    <tbody id="comparisonBody">
                    </tbody>
                </table>
            </div>
            <div class="mt-4 text-center">
                <button id="compareBtn" class="hidden inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-md transition-colors">
                    对比其他频率策略
                </button>
            </div>
        </div>

        <footer class="mt-8 text-center text-gray-500 text-sm">
            <p>数据来源：东方财富 · 工具仅供参考，不构成投资建议</p>
            <p>© 2026 工具集 · 小而美，解决真问题</p>
        </footer>

        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg opacity-0 transition-opacity duration-300 hidden"></div>
    </div>

    <script src="../../shared/utils.js"></script>
    <script>
// Configuration
const API_BASE = 'https://api.doctorxiong.club/v1/fund';

// DOM Elements
const fundCodeInput = document.getElementById('fundCode');
const startDateInput = document.getElementById('startDate');
const investmentAmountInput = document.getElementById('investmentAmount');
const frequencyBtns = document.querySelectorAll('.freq-btn');
const tpBtns = document.querySelectorAll('.tp-btn');
const takeProfitPercentInput = document.getElementById('takeProfitPercent');
const tpPercentRow = document.getElementById('tpPercentRow');
const calculateBtn = document.getElementById('calculateBtn');
const resultSummary = document.getElementById('resultSummary');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const totalInvestmentEl = document.getElementById('totalInvestment');
const currentValueEl = document.getElementById('currentValue');
const returnPercentageEl = document.getElementById('returnPercentage');
const annualReturnEl = document.getElementById('annualReturn');
const totalTimesEl = document.getElementById('totalTimes');
const comparisonBody = document.getElementById('comparisonBody');
const compareBtn = document.getElementById('compareBtn');

// Selected options
let selectedFrequency = 'weekly';
let selectedTp = 'none';
let chartInstance = null;

// Set default start date to 5 years ago
document.addEventListener('DOMContentLoaded', () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 5);
    startDateInput.value = date.toISOString().split('T')[0];
});

// Frequency selection
frequencyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        frequencyBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedFrequency = btn.dataset.freq;
    });
});

// Take profit selection
tpBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tpBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedTp = btn.dataset.tp;
        if (selectedTp === 'percent') {
            tpPercentRow.classList.remove('hidden');
        } else {
            tpPercentRow.classList.add('hidden');
        }
    });
});

// Calculate button click
calculateBtn.addEventListener('click', async () => {
    const fundCode = fundCodeInput.value.trim();
    const startDate = startDateInput.value;
    const investmentAmount = parseFloat(investmentAmountInput.value);

    // Validation
    if (!fundCode || fundCode.length !== 6) {
        showToast('请输入正确的6位数基金代码');
        return;
    }
    if (!startDate) {
        showToast('请选择开始日期');
        return;
    }
    if (isNaN(investmentAmount) || investmentAmount <= 0) {
        showToast('请输入正确的定投金额');
        return;
    }

    calculateBtn.disabled = true;
    resultSummary.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    comparisonBody.innerHTML = '';
    compareBtn.classList.add('hidden');

    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }

    try {
        const data = await fetchFundData(fundCode);
        const result = runBacktest(data, startDate, investmentAmount, selectedFrequency, selectedTp,
            selectedTp === 'percent' ? parseFloat(takeProfitPercentInput.value) / 100 : 0);
        displayResult(result);
        // Enable comparison
        compareBtn.classList.remove('hidden');
        compareBtn.onclick = () => runComparisons(fundCode, data, startDate, investmentAmount, selectedTp,
            selectedTp === 'percent' ? parseFloat(takeProfitPercentInput.value) / 100 : 0);
    } catch (err) {
        console.error(err);
        errorDiv.classList.remove('hidden');
        errorMessage.textContent = err.message;
    } finally {
        calculateBtn.disabled = false;
        loadingDiv.classList.add('hidden');
    }
});

async function fetchFundData(fundCode) {
    const response = await fetch(`${API_BASE}/detail?code=${fundCode}`);
    if (!response.ok) {
        throw new Error('获取基金数据失败');
    }
    const data = await response.json();
    if (!data || !data.data || !data.data.netWorthData) {
        throw new Error('未找到该基金数据，请检查代码是否正确');
    }
    // Sort by date
    data.data.netWorthData.sort((a, b) => new Date(a[0]) - new Date(b[0]));
    return data.data;
}

function generateDCAdates(startDate, endDate, frequency) {
    const dates = [];
    let current = new Date(startDate);
    const end = new Date();

    const increment = {
        weekly: 7,
        biweekly: 14,
        monthly: 30
    }[frequency];

    while (current <= end) {
        dates.push(new Date(current).toISOString().split('T')[0]);
        current.setDate(current.getDate() + increment);
    }

    return dates;
}

function findNearestNavPrice(dateStr, navData) {
    // Find the closest date after or equal to the target date
    for (let i = 0; i < navData.length; i++) {
        if (navData[i][0] >= dateStr) {
            return parseFloat(navData[i][1]);
        }
    }
    return parseFloat(navData[navData.length - 1][1]);
}

function runBacktest(fundData, startDateStr, amountPerPeriod, frequency, takeProfitType, takeProfitPercent) {
    const navData = fundData.netWorthData;
    const dcaDates = generateDCAdates(startDateStr, frequency);
    let totalShares = 0;
    let totalInvestment = 0;
    const equityCurve = [];
    let currentTotalInvestment = 0;

    // If we have take profit, we need to track accumulated profit
    let hasTakeProfit = takeProfitType === 'percent';

    dcaDates.forEach((dcaDate, index) => {
        const nav = findNearestNavPrice(dcaDate, navData);
        const sharesBought = amountPerPeriod / nav;
        totalShares += sharesBought;
        totalInvestment += amountPerPeriod;
        currentTotalInvestment = totalInvestment;

        // Check take profit
        if (hasTakeProfit) {
            const currentNav = findNearestNavPrice(dcaDate, navData);
            const costPerShare = totalInvestment / totalShares;
            const profitPercent = (currentNav - costPerShare) / costPerShare;
            if (profitPercent >= takeProfitPercent) {
                // Sell all, reset
                totalShares = 0;
                totalInvestment = 0;
            }
        }

        // Record for chart
        const currentNav = findNearestNavPrice(dcaDate, navData);
        equityCurve.push({
            date: dcaDate,
            equity: totalShares * currentNav,
            investment: currentTotalInvestment
        });
    });

    // Get final value
    const finalNav = parseFloat(navData[navData.length - 1][1]);
    const finalValue = totalShares * finalNav;
    const returnPct = ((finalValue - totalInvestment) / totalInvestment) * 100;

    // Calculate annualized return (XIRR approximation)
    const start = new Date(startDateStr);
    const end = new Date(navData[navData.length - 1][0]);
    const years = (end - start) / (1000 * 60 * 60 * 24 * 365);
    const annualReturn = (Math.pow(finalValue / totalInvestment, 1 / years) - 1) * 100;

    return {
        totalInvestment,
        finalValue,
        returnPercentage: returnPct,
        annualReturn,
        totalTimes: dcaDates.length,
        equityCurve
    };
}

function displayResult(result) {
    totalInvestmentEl.textContent = result.totalInvestment.toFixed(0) + ' 元';
    currentValueEl.textContent = result.finalValue.toFixed(2) + ' 元';

    // Color coding for return
    returnPercentageEl.textContent = result.returnPercentage.toFixed(2) + '%';
    returnPercentageEl.className = result.returnPercentage >= 0
        ? 'text-2xl font-bold text-green-600'
        : 'text-2xl font-bold text-red-600';

    annualReturnEl.textContent = result.annualReturn.toFixed(2) + '%';
    annualReturnEl.className = result.annualReturn >= 0
        ? 'text-2xl font-bold text-green-600'
        : 'text-2xl font-bold text-red-600';

    totalTimesEl.textContent = result.totalTimes;

    resultSummary.classList.remove('hidden');

    // Draw chart
    const ctx = document.getElementById('equityChart').getContext('2d');
    const labels = result.equityCurve.filter((_, i) => i % Math.max(1, Math.floor(result.equityCurve.length / 50)) === 0);

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.map(d => d.date),
            datasets: [
                {
                    label: '累计市值',
                    data: labels.map(d => d.equity),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: '累计投入',
                    data: labels.map(d => d.investment),
                    borderColor: 'rgb(156, 163, 175)',
                    backgroundColor: 'rgba(156, 163, 175, 0.1)',
                    fill: true,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(0) + '元';
                        }
                    }
                }
            }
        }
    });

    showToast('回测完成');
}

async function runComparisons(fundCode, fundData, startDate, investmentAmount, takeProfitType, takeProfitPercent) {
    const frequencies = [
        { key: 'weekly', name: '每周定投' },
        { key: 'biweekly', name: '每两周定投' },
        { key: 'monthly', name: '每月定投' }
    ];

    comparisonBody.innerHTML = '';

    frequencies.forEach(freq => {
        const result = runBacktest(fundData, startDate, investmentAmount, freq.key, takeProfitType, takeProfitPercent);
        const row = document.createElement('tr');
        row.className = 'border-t border-gray-200';
        const returnClass = result.returnPercentage >= 0 ? 'text-green-600' : 'text-red-600';
        const annualClass = result.annualReturn >= 0 ? 'text-green-600' : 'text-red-600';
        row.innerHTML = `
            <td class="px-4 py-2 font-medium">${freq.name}</td>
            <td class="px-4 py-2 text-right">${result.totalInvestment.toFixed(0)}</td>
            <td class="px-4 py-2 text-right">${result.finalValue.toFixed(2)}</td>
            <td class="px-4 py-2 text-right font-medium ${returnClass}">${result.returnPercentage.toFixed(2)}%</td>
            <td class="px-4 py-2 text-right font-medium ${annualClass}">${result.annualReturn.toFixed(2)}%</td>
        `;
        comparisonBody.appendChild(row);
    });

    showToast('策略对比完成');
}
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/fund-dca-calculator/index.html
git commit -m "feat: add fund DCA backtest calculator full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/fund-dca-calculator/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 基金定投回测计算器

输入基金代码，回测不同定投策略（每周/每两周/每月）在历史上的实际收益，支持收益率止盈测试。

## 功能特点

- 输入基金代码，自动获取历史净值数据
- 支持三种定投频率：每周/每两周/每月
- 支持收益率止盈测试
- 一键对比不同策略的收益差异
- 可视化累计收益曲线
- 计算年化收益率

## 使用方法

1. 输入6位数基金代码（例如：161725 招商中证白酒）
2. 选择开始回测日期（默认5年前）
3. 输入每期定投金额
4. 选择定投频率和是否止盈
5. 点击开始回测，等待结果
6. 可以一键对比三种不同频率策略

## 技术

- 数据来源：免费公开基金API
- 纯前端计算，Chart.js画图
- Tailwind CSS via CDN
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/fund-dca-calculator/README.md index.html
git commit -m "docs: add readme and update root index for fund dca calculator"
```

---

## Acceptance Criteria

1. Page loads correctly
2. User can input fund code and parameters
3. Fetches historical data from API
4. Runs backtest calculation correctly
5. Displays result summary with chart
6. Can compare different frequency strategies
7. Responsive layout

Total estimated development time: **1-2 days**
