# 股息复利计算器 - 实现计划

**Goal:** Build a web calculator that calculates compound growth of dividend stocks, showing how reinvesting dividends grows share count and total value over years.

**Architecture:** Single HTML static page. Pure client-side calculation, no API needed (user inputs data). Chart showing growth over time.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- Chart.js for charts

---

## File Structure

```
tools/dividend-compound/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/dividend-compound/index.html`

- [ ] **Step 1: Create full HTML + JavaScript**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股息复利计算器 - 股息再投滚存计算</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-5xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">股息复利计算器</h1>
            <p class="text-gray-600">计算股息再投资多年滚存后的总收益和股数增长</p>
        </header>

        <div class="grid md:grid-cols-2 gap-6">
            <!-- Input Panel -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">参数设置</h2>

                <!-- Initial Investment -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">初始投入金额 (HKD/USD)</label>
                    <input type="number" id="initialInvestment" value="10000" min="1000" step="1000"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Stock Price -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">买入股价</label>
                    <input type="number" id="stockPrice" value="20" step="0.01"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Annual Dividend Yield -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">年化股息收益率 (%)</label>
                    <input type="number" id="dividendYield" value="5" min="0" max="20" step="0.5"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Expected Annual Price Growth -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">预期股价年增长率 (%)</label>
                    <input type="number" id="priceGrowth" value="2" min="-10" max="20" step="0.5"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Holding Years -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">持有年数</label>
                    <input type="number" id="holdingYears" value="10" min="1" max="50" step="1"
                           class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>

                <!-- Currency -->
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">货币</label>
                    <div class="grid grid-cols-2 gap-2">
                        <button class="currency-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors active" data-currency="HKD">港币</button>
                        <button class="currency-btn px-3 py-2 border-2 border-gray-200 rounded-md hover:border-blue-300 transition-colors" data-currency="USD">美元</button>
                    </div>
                </div>

                <div class="mt-6 text-center">
                    <button id="calculateBtn"
                            class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed">
                        开始计算
                    </button>
                </div>
            </div>

            <!-- Result Summary -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">计算结果</h2>
                <div id="resultSummary" class="hidden space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">初始股数</div>
                            <div class="text-2xl font-bold text-gray-800" id="initialShares">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">最终股数</div>
                            <div class="text-2xl font-bold text-gray-800" id="finalShares">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">累计分红（未再投）</div>
                            <div class="text-xl font-bold text-gray-800" id="totalDividends">-</div>
                        </div>
                        <div class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600">最终持仓市值</div>
                            <div class="text-2xl font-bold text-green-600" id="finalValue">-</div>
                        </div>
                    </div>
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <div class="text-sm text-gray-600">总收益率</div>
                        <div class="text-xl font-semibold" id="totalReturn">-</div>
                    </div>
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <div class="text-sm text-gray-600">年化收益率</div>
                        <div class="text-xl font-semibold" id="annualReturn">-</div>
                    </div>
                </div>
                <div id="emptyState" class="py-12 text-center text-gray-500">
                    <p>输入参数后点击计算查看结果</p>
                </div>
            </div>
        </div>

        <!-- Growth Chart -->
        <div class="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">市值增长曲线</h2>
            <canvas id="growthChart" width="400" height="200"></canvas>
        </div>

        <!-- Comparison Table: With vs Without Reinvestment -->
        <div class="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">对比：股息再投 vs 不复投</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2 text-left">项目</th>
                            <th class="px-4 py-2 text-right">股息再投资</th>
                            <th class="px-4 py-2 text-right">股息不复投</th>
                        </tr>
                    </thead>
                    <tbody id="comparisonBody">
                    </tbody>
                </table>
            </div>
        </div>

        <footer class="mt-8 text-center text-gray-500 text-sm">
            <p>工具仅供参考，不构成投资建议 · © 2026 工具集</p>
        </footer>

        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white px-6 py-3 rounded-lg opacity-0 transition-opacity duration-300 hidden"></div>
    </div>

    <script src="../../shared/utils.js"></script>
    <script>
// DOM Elements
const initialInvestmentInput = document.getElementById('initialInvestment');
const stockPriceInput = document.getElementById('stockPrice');
const dividendYieldInput = document.getElementById('dividendYield');
const priceGrowthInput = document.getElementById('priceGrowth');
const holdingYearsInput = document.getElementById('holdingYears');
const currencyBtns = document.querySelectorAll('.currency-btn');
const calculateBtn = document.getElementById('calculateBtn');
const resultSummary = document.getElementById('resultSummary');
const emptyState = document.getElementById('emptyState');
const comparisonBody = document.getElementById('comparisonBody');

// Selected
let selectedCurrency = 'HKD';

// Currency selection
currencyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        currencyBtns.forEach(b => b.classList.remove('active', 'border-blue-500'));
        btn.classList.add('active', 'border-blue-500');
        selectedCurrency = btn.dataset.currency;
    });
});

// Calculate
calculateBtn.addEventListener('click', () => {
    const initialInvestment = parseFloat(initialInvestmentInput.value);
    const stockPrice = parseFloat(stockPriceInput.value);
    const dividendYield = parseFloat(dividendYieldInput.value) / 100;
    const priceGrowth = parseFloat(priceGrowthInput.value) / 100;
    const holdingYears = parseInt(holdingYearsInput.value);

    // Validation
    if (isNaN(initialInvestment) || initialInvestment <= 0) {
        showToast('请输入正确的初始投入金额');
        return;
    }
    if (isNaN(stockPrice) || stockPrice <= 0) {
        showToast('请输入正确的买入股价');
        return;
    }

    const resultWithReinv = calculateDividendCompound(
        initialInvestment, stockPrice, dividendYield, priceGrowth, holdingYears, true
    );
    const resultWithoutReinv = calculateDividendCompound(
        initialInvestment, stockPrice, dividendYield, priceGrowth, holdingYears, false
    );

    displayResults(resultWithReinv, resultWithoutReinv);
    drawChart(resultWithReinv.yearlyData);
    showToast('计算完成');
});

function calculateDividendCompound(initialInvestment, initialPrice, dividendYield, priceGrowth, holdingYears, reinvest) {
    let currentShares = initialInvestment / initialPrice;
    let currentPrice = initialPrice;
    let totalDividendsCash = 0;
    let yearlyData = [];
    let totalValue;

    for (let year = 1; year <= holdingYears; year++) {
        // Calculate annual dividend
        const annualDividend = currentShares * currentPrice * dividendYield;
        totalDividendsCash += annualDividend;

        if (reinvest) {
            // Reinvest dividend into more shares at current price
            const newShares = annualDividend / currentPrice;
            currentShares += newShares;
        }

        // Record yearly data
        totalValue = currentShares * currentPrice + (reinvest ? 0 : totalDividendsCash);
        yearlyData.push({
            year,
            shares: currentShares,
            price: currentPrice,
            value: totalValue
        });

        // Price grows for next year
        currentPrice = currentPrice * (1 + priceGrowth);
    }

    // Final value
    totalValue = currentShares * currentPrice + (reinvest ? 0 : totalDividendsCash);
    const totalReturn = ((totalValue - initialInvestment) / initialInvestment) * 100;
    const annualReturn = (Math.pow(totalValue / initialInvestment, 1 / holdingYears) - 1) * 100;

    return {
        initialShares: initialInvestment / initialPrice,
        finalShares: currentShares,
        totalDividends: totalDividendsCash,
        finalValue: totalValue,
        totalReturn: totalReturn,
        annualReturn: annualReturn,
        yearlyData: yearlyData
    };
}

function displayResults(resultWith, resultWithout) {
    // Update summary (with reinvestment is the main result)
    document.getElementById('initialShares').textContent = resultWith.initialShares.toFixed(2);
    document.getElementById('finalShares').textContent = resultWith.finalShares.toFixed(2);
    document.getElementById('totalDividends').textContent = formatCurrency(resultWith.totalDividends);
    document.getElementById('finalValue').textContent = formatCurrency(resultWith.finalValue);

    const returnEl = document.getElementById('totalReturn');
    returnEl.textContent = resultWith.totalReturn.toFixed(2) + '%';
    returnEl.className = resultWith.totalReturn >= 0
        ? 'text-xl font-semibold text-green-600'
        : 'text-xl font-semibold text-red-600';

    const annualEl = document.getElementById('annualReturn');
    annualEl.textContent = resultWith.annualReturn.toFixed(2) + '%';
    annualEl.className = resultWith.annualReturn >= 0
        ? 'text-xl font-semibold text-green-600'
        : 'text-xl font-semibold text-red-600';

    // Update comparison table
    comparisonBody.innerHTML = '';
    const items = [
        { label: '最终股数', withVal: resultWith.finalShares.toFixed(2), withoutVal: resultWithout.finalShares.toFixed(2) },
        { label: '累计分红', withVal: formatCurrency(resultWith.totalDividends), withoutVal: formatCurrency(resultWithout.totalDividends) },
        { label: '最终总价值', withVal: formatCurrency(resultWith.finalValue), withoutVal: formatCurrency(resultWithout.finalValue) },
        { label: '总收益率', withVal: resultWith.totalReturn.toFixed(2) + '%', withoutVal: resultWithout.totalReturn.toFixed(2) + '%' },
        { label: '年化收益率', withVal: resultWith.annualReturn.toFixed(2) + '%', withoutVal: resultWithout.annualReturn.toFixed(2) + '%' },
    ];

    items.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'border-t border-gray-200';
        row.innerHTML = `
            <td class="px-4 py-2 font-medium">${item.label}</td>
            <td class="px-4 py-2 text-right font-medium">${item.withVal}</td>
            <td class="px-4 py-2 text-right">${item.withoutVal}</td>
        `;
        comparisonBody.appendChild(row);
    });

    resultSummary.classList.remove('hidden');
    emptyState.classList.add('hidden');
}

function formatCurrency(value) {
    return `${selectedCurrency} ${value.toFixed(2)}`;
}

let chartInstance = null;

function drawChart(yearlyData) {
    const ctx = document.getElementById('growthChart').getContext('2d');

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: yearlyData.map(d => `第${d.year}年`),
            datasets: [{
                label: '累计市值',
                data: yearlyData.map(d => d.value),
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return selectedCurrency + ' ' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/dividend-compound/index.html
git commit -m "feat: add dividend compound calculator full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/dividend-compound/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 股息复利计算器

计算股息股票长期持有，股息再投资复利滚存后的最终收益，对比股息再投和不复投的差异。

## 功能特点

- 支持港股/美股不同货币
- 支持设置股价年增长率
- 计算股息再投和不复投两种情况
- 可视化市值增长曲线
- 对比表格清晰显示差异

## 使用方法

1. 输入初始投入金额
2. 输入买入股价
3. 输入年化股息收益率
4. 输入预期股价年增长率
5. 输入持有年数
6. 选择货币（港币/美元）
7. 点击计算查看结果

## 技术

- 纯前端HTML + JavaScript
- 无需API，本地计算
- Chart.js 绘图
- Tailwind CSS via CDN
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/dividend-compound/README.md index.html
git commit -m "docs: add readme and update root index for dividend compound calculator"
```

---

## Acceptance Criteria

1. Page loads correctly
2. All inputs work
3. Calculation correct with/without reinvestment
4. Chart displays growth curve
5. Comparison table shows correctly
6. Currency selection works
7. Responsive layout

Total estimated development time: **1 day**
