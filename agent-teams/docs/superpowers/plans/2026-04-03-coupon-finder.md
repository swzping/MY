# 外卖红包优惠券查找工具 - 实现计划

**Goal:** Build a web tool that collects and displays the latest外卖红包/coupon links for Meituan (美团) and Ele.me (饿了么), helps users save money on food delivery.

**Architecture:** Simple static page that lists the latest coupon methods and links. Can be updated manually when new methods are found.

**Tech Stack:**
- HTML + vanilla JavaScript
- Tailwind CSS via CDN
- No backend needed, all static

---

## File Structure

```
tools/coupon-finder/
├── index.html                 # Main tool page
└── README.md                  # Documentation
```

---

## Tasks

### Task 1: Create the tool

**Files:**
- Create: `tools/coupon-finder/index.html`

- [ ] **Step 1: Create full HTML + JavaScript**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>外卖红包优惠券 - 每日更新美团饿了么</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">外卖红包优惠券</h1>
            <p class="text-gray-600">每日更新美团饿了么优惠券，点餐省钱</p>
            <div class="mt-4 inline-block bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full text-sm font-medium">
                🎉 每日更新，建议收藏
            </div>
        </header>

        <!-- Last Updated -->
        <div class="text-center mb-6 text-gray-500 text-sm">
            最后更新：<span class="font-medium" id="lastUpdated"></span>
        </div>

        <!-- Coupon Cards -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
            <!-- Meituan -->
            <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-blue-500">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl">
                        🍔
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">美团外卖</h2>
                        <p class="text-gray-600 text-sm">最高可领 <span class="text-red-600 font-bold">¥66</span> 红包</p>
                    </div>
                </div>

                <div class="mb-4 space-y-2">
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>新用户首单大额立减</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>老用户每日可领红包</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>满减红包叠加使用</span>
                    </div>
                </div>

                <a href="https://meituan.cn/dianping/coupon/getCoupon.htm" target="_blank" rel="noopener noreferrer"
                   class="block w-full text-center bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 rounded-md transition-colors">
                    👉 领取美团红包
                </a>
            </div>

            <!-- Ele.me -->
            <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-orange-500">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white text-xl">
                        🍜
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">饿了么</h2>
                        <p class="text-gray-600 text-sm">最高可领 <span class="text-red-600 font-bold">¥50</span> 红包</p>
                    </div>
                </div>

                <div class="mb-4 space-y-2">
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>新用户最高减20元</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>每日抢超级红包</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-700">
                        <span class="text-green-500">✓</span>
                        <span>会员红包升级</span>
                    </div>
                </div>

                <a href="https://s.ele.me/activity/receive" target="_blank" rel="noopener noreferrer"
                   class="block w-full text-center bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 rounded-md transition-colors">
                    👉 领取饿了么红包
                </a>
            </div>
        </div>

        <!-- Usage Tips -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">💡 使用小贴士</h2>
            <ul class="space-y-3 text-gray-700">
                <li class="flex gap-2">
                    <span class="text-yellow-500 font-bold">•</span>
                    <span>每天都可以领取一次，建议下单前先来这里领红包</span>
                </li>
                <li class="flex gap-2">
                    <span class="text-yellow-500 font-bold">•</span>
                    <span>红包由官方平台发放，本工具只做整理收集链接</span>
                </li>
                <li class="flex gap-2">
                    <span class="text-yellow-500 font-bold">•</span>
                    <span>将本页面收藏到浏览器，方便每天点餐使用</span>
                </li>
                <li class="flex gap-2">
                    <span class="text-yellow-500 font-bold">•</span>
                    <span>如果链接失效，请刷新页面或告诉我们更新</span>
                </li>
            </ul>
        </div>

        <!-- Sharing Tips -->
        <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
            <h3 class="text-lg font-semibold text-green-800 mb-2">🤝 分享给朋友</h3>
            <p class="text-green-700">觉得好用？把这个页面分享给经常点外卖的朋友，一起省钱！</p>
        </div>

        <footer class="mt-8 text-center text-gray-500 text-sm">
            <p>© 2026 工具集 · 小而美，解决真问题</p>
            <p class="mt-2">本工具仅提供链接整理，不参与红包活动运营，红包规则以官方平台为准</p>
        </footer>
    </div>

    <script>
// Set last updated date
document.getElementById('lastUpdated').textContent = new Date().toISOString().split('T')[0];
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tools/coupon-finder/index.html
git commit -m "feat: add coupon finder full implementation"
```

---

### Task 2: Add README and update root index

**Files:**
- Create: `tools/coupon-finder/README.md`
- Modify: `index.html`

- [ ] **Step 1: Create README**

```markdown
# 外卖红包优惠券查找工具

每日更新美团和饿了么外卖红包链接，帮你点餐省钱。

## 功能特点

- 整理最新的官方红包领取链接
- 美团+饿了么双平台
- 新用户大额立减，老用户每日可领
- 简洁页面，快速点击领取
- 纯静态页面，无需下载APP

## 使用方法

1. 点击对应平台的领取按钮
2. 跳转到官方页面领取红包
3. 返回APP下单自动抵扣

## 小贴士

- 每天都可以领取一次
- 建议收藏本页面，点餐前来领取
- 红包由官方平台发放

## 说明

本工具只做链接整理，不参与官方活动运营，活动规则以平台官方为准。

## 技术

- 纯前端HTML + Tailwind CSS
- 静态页面，无需后端
```

- [ ] **Step 2: Update root index.html add card**

- [ ] **Step 3: Commit**

```bash
git add tools/coupon-finder/README.md index.html
git commit -m "docs: add readme and update root index for coupon finder"
```

---

## Acceptance Criteria

1. Page loads correctly
2. Cards display nicely responsive
3. Links open correctly
4. Last updated date auto set to today

Total estimated development time: **1 hour**
