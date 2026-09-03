# Jizhang Report Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing Analysis tab into a monthly and yearly report center using the imported `history.xlsx` records plus in-app records.

**Architecture:** Convert workbook history into the existing static `Transaction[]` seed format, then keep all report aggregation inside `src/lib/analytics.ts`. `App.tsx` should only select report mode/period and render report objects through existing React Native components.

**Tech Stack:** Expo 51, React Native, TypeScript, Vitest, bundled Python/pandas for one-time workbook extraction.

---

## File Structure

- Modify `src/data/sampleData.ts`: replace or extend seed records with converted records from `history.xlsx` while preserving the existing `AppData` shape.
- Modify `src/lib/analytics.ts`: add report types and pure monthly/yearly aggregation helpers.
- Modify `src/lib/analytics.test.ts`: add failing tests for the new report helpers before implementation.
- Modify `App.tsx`: upgrade `AnalysisScreen` to render the monthly/yearly report UI.

---

### Task 1: Add Report Analytics Tests

**Files:**
- Modify: `src/lib/analytics.test.ts`

- [ ] **Step 1: Write failing tests for monthly and yearly reports**

Add these imports:

```ts
import {
  getLatestRecordDate,
  getMonthlyReport,
  getYearlyReport,
} from "./analytics";
```

Add this fixture near the existing `records` fixture:

```ts
const reportRecords: Transaction[] = [
  {
    id: "r1",
    type: "expense",
    amount: 100,
    category: "食",
    date: "2026-08-01",
    note: "早午晚餐",
    createdAt: "2026-08-01T10:00:00.000Z",
  },
  {
    id: "r2",
    type: "expense",
    amount: 60,
    category: "行",
    date: "2026-08-02",
    note: "公共交通",
    createdAt: "2026-08-02T10:00:00.000Z",
  },
  {
    id: "r3",
    type: "income",
    amount: 1000,
    category: "职业收入",
    date: "2026-08-03",
    note: "工资收入",
    createdAt: "2026-08-03T10:00:00.000Z",
  },
  {
    id: "r4",
    type: "expense",
    amount: 40,
    category: "食",
    date: "2026-07-31",
    note: "水果零食",
    createdAt: "2026-07-31T10:00:00.000Z",
  },
  {
    id: "r5",
    type: "income",
    amount: 500,
    category: "副业",
    date: "2026-01-10",
    note: "经营所得",
    createdAt: "2026-01-10T10:00:00.000Z",
  },
];
```

Add these tests:

```ts
it("selects the latest valid record date", () => {
  expect(getLatestRecordDate(reportRecords)).toBe("2026-08-03");
});

it("builds a monthly report with totals, daily trend, categories, and records", () => {
  const report = getMonthlyReport(reportRecords, "2026-08");

  expect(report.totals).toEqual({
    income: 1000,
    expense: 160,
    net: 840,
    savingsRate: 84,
  });
  expect(report.dailyTrend.filter((point) => point.amount > 0)).toEqual([
    { date: "2026-08-01", label: "08/01", amount: 100 },
    { date: "2026-08-02", label: "08/02", amount: 60 },
  ]);
  expect(report.categories).toEqual([
    { category: "食", amount: 100, percent: 63 },
    { category: "行", amount: 60, percent: 38 },
  ]);
  expect(report.records.map((record) => record.id)).toEqual(["r3", "r2", "r1"]);
});

it("builds a yearly report with monthly summaries and category ranking", () => {
  const report = getYearlyReport(reportRecords, "2026");

  expect(report.totals).toEqual({
    income: 1500,
    expense: 200,
    net: 1300,
    savingsRate: 87,
  });
  expect(report.monthlySummaries.filter((month) => month.income > 0 || month.expense > 0)).toEqual([
    { month: "2026-01", label: "1月", income: 500, expense: 0, net: 500 },
    { month: "2026-07", label: "7月", income: 0, expense: 40, net: -40 },
    { month: "2026-08", label: "8月", income: 1000, expense: 160, net: 840 },
  ]);
  expect(report.topExpenseMonths).toEqual([
    { month: "2026-08", label: "8月", income: 1000, expense: 160, net: 840 },
    { month: "2026-07", label: "7月", income: 0, expense: 40, net: -40 },
  ]);
  expect(report.categories).toEqual([
    { category: "食", amount: 140, percent: 70 },
    { category: "行", amount: 60, percent: 30 },
  ]);
});

it("uses zero savings rate when income is zero", () => {
  expect(getMonthlyReport(reportRecords, "2026-07").totals.savingsRate).toBe(0);
});
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
npm test -- src/lib/analytics.test.ts
```

Expected: FAIL because `getLatestRecordDate`, `getMonthlyReport`, and `getYearlyReport` are not exported yet.

---

### Task 2: Implement Report Analytics

**Files:**
- Modify: `src/lib/analytics.ts`

- [ ] **Step 1: Add report types and helpers**

Add exported types:

```ts
export type ReportTotals = MonthlyTotals & {
  savingsRate: number;
};

export type ReportCategory = CategorySpending;

export type MonthlyReport = {
  month: string;
  totals: ReportTotals;
  dailyTrend: TrendPoint[];
  categories: ReportCategory[];
  records: Transaction[];
};

export type MonthSummary = {
  month: string;
  label: string;
  income: number;
  expense: number;
  net: number;
};

export type YearlyReport = {
  year: string;
  totals: ReportTotals;
  monthlySummaries: MonthSummary[];
  topExpenseMonths: MonthSummary[];
  categories: ReportCategory[];
};
```

Add implementations:

```ts
export function getLatestRecordDate(records: Transaction[]): string {
  return records
    .filter((record) => isValidDateKey(record.date))
    .map((record) => record.date)
    .sort((a, b) => b.localeCompare(a))[0] ?? formatDate(new Date());
}

export function getMonthlyReport(records: Transaction[], month: string): MonthlyReport {
  const monthlyRecords = getRecordsForMonth(records, month);
  const income = sumRecords(monthlyRecords, "income");
  const expense = sumRecords(monthlyRecords, "expense");

  return {
    month,
    totals: buildReportTotals(income, expense),
    dailyTrend: buildMonthExpenseTrend(monthlyRecords, month),
    categories: getCategoryRanking(monthlyRecords),
    records: getRecentRecords(monthlyRecords, 30),
  };
}

export function getYearlyReport(records: Transaction[], year: string): YearlyReport {
  const yearlyRecords = records.filter((record) => record.date.startsWith(`${year}-`));
  const income = sumRecords(yearlyRecords, "income");
  const expense = sumRecords(yearlyRecords, "expense");
  const monthlySummaries = Array.from({ length: 12 }, (_, index) => {
    const month = `${year}-${String(index + 1).padStart(2, "0")}`;
    const monthRecords = getRecordsForMonth(yearlyRecords, month);
    const monthIncome = sumRecords(monthRecords, "income");
    const monthExpense = sumRecords(monthRecords, "expense");

    return {
      month,
      label: `${index + 1}月`,
      income: monthIncome,
      expense: monthExpense,
      net: monthIncome - monthExpense,
    };
  });

  return {
    year,
    totals: buildReportTotals(income, expense),
    monthlySummaries,
    topExpenseMonths: monthlySummaries
      .filter((summary) => summary.expense > 0)
      .sort((a, b) => b.expense - a.expense)
      .slice(0, 3),
    categories: getCategoryRanking(yearlyRecords),
  };
}
```

Add private helpers:

```ts
function getRecordsForMonth(records: Transaction[], month: string) {
  return records.filter((record) => record.date.startsWith(month));
}

function buildReportTotals(income: number, expense: number): ReportTotals {
  const net = income - expense;
  return {
    income,
    expense,
    net,
    savingsRate: income <= 0 ? 0 : Math.round((net / income) * 100),
  };
}

function buildMonthExpenseTrend(records: Transaction[], month: string): TrendPoint[] {
  const [yearValue, monthValue] = month.split("-").map(Number);
  const daysInMonth = new Date(yearValue, monthValue, 0).getDate();

  return Array.from({ length: daysInMonth }, (_, index) => {
    const day = String(index + 1).padStart(2, "0");
    const date = `${month}-${day}`;
    const amount = records
      .filter((record) => record.type === "expense" && record.date === date)
      .reduce((sum, record) => sum + record.amount, 0);

    return {
      date,
      label: date.slice(5).replace("-", "/"),
      amount,
    };
  });
}

function getCategoryRanking(records: Transaction[]): ReportCategory[] {
  const totals = new Map<string, number>();

  records
    .filter((record) => record.type === "expense")
    .forEach((record) => {
      totals.set(record.category, (totals.get(record.category) ?? 0) + record.amount);
    });

  const totalExpense = [...totals.values()].reduce((sum, amount) => sum + amount, 0);

  return [...totals.entries()]
    .map(([category, amount]) => ({
      category,
      amount,
      percent: totalExpense === 0 ? 0 : Math.round((amount / totalExpense) * 100),
    }))
    .sort((a, b) => b.amount - a.amount);
}

function isValidDateKey(date: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(date);
}
```

- [ ] **Step 2: Run tests and verify GREEN**

Run:

```bash
npm test -- src/lib/analytics.test.ts
```

Expected: PASS.

- [ ] **Step 3: Commit analytics changes**

Run:

```bash
git add jizhang/src/lib/analytics.ts jizhang/src/lib/analytics.test.ts
git commit -m "Add monthly and yearly report analytics"
```

---

### Task 3: Convert `history.xlsx` Into Seed Records

**Files:**
- Modify: `src/data/sampleData.ts`

- [ ] **Step 1: Extract workbook rows**

Run this from `/Users/edy/Documents/MY/jizhang`:

```bash
/Users/edy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
import json
import pandas as pd

path = "history.xlsx"
frames = []
for sheet_name, tx_type in [("收入", "income"), ("支出", "expense")]:
    df = pd.read_excel(path, sheet_name=sheet_name)
    for index, row in df.iterrows():
        date = pd.to_datetime(row["日期"], errors="coerce")
        amount = pd.to_numeric(row["金额"], errors="coerce")
        if pd.isna(date) or pd.isna(amount):
            continue
        category = str(row["一级分类"]).strip()
        subcategory = "" if pd.isna(row["二级分类"]) else str(row["二级分类"]).strip()
        remark = "" if pd.isna(row["备注"]) else str(row["备注"]).strip()
        note = " · ".join(part for part in [subcategory, remark] if part)
        frames.append({
            "id": f"history-{tx_type}-{index + 1}",
            "type": tx_type,
            "amount": float(amount),
            "category": category,
            "date": date.strftime("%Y-%m-%d"),
            "note": note,
            "createdAt": date.isoformat(),
        })

frames.sort(key=lambda record: (record["date"], record["createdAt"]), reverse=True)
print(json.dumps(frames, ensure_ascii=False, indent=2))
PY
```

Use the resulting JSON array as `records` in `sampleData`.

- [ ] **Step 2: Preserve budget defaults**

Keep the existing `budget` object from `sampleData.ts`. Only replace the `records` array.

- [ ] **Step 3: Run storage and analytics tests**

Run:

```bash
npm test -- src/lib/storage.test.ts src/lib/analytics.test.ts
```

Expected: PASS. Storage tests should still load the new `sampleData` fallback successfully.

- [ ] **Step 4: Commit seed data changes**

Run:

```bash
git add jizhang/src/data/sampleData.ts
git commit -m "Import jizhang history records"
```

---

### Task 4: Upgrade Existing Analysis Page

**Files:**
- Modify: `App.tsx`

- [ ] **Step 1: Update imports**

Import new helpers:

```ts
  getLatestRecordDate,
  getMonthlyReport,
  getYearlyReport,
```

- [ ] **Step 2: Add local report state to `AnalysisScreen`**

Inside `AnalysisScreen`, derive the latest date and add state:

```ts
const latestDate = getLatestRecordDate(records);
const [reportMode, setReportMode] = useState<"month" | "year">("month");
const [selectedMonth, setSelectedMonth] = useState(latestDate.slice(0, 7));
const [selectedYear, setSelectedYear] = useState(latestDate.slice(0, 4));
const monthlyReport = useMemo(() => getMonthlyReport(records, selectedMonth), [records, selectedMonth]);
const yearlyReport = useMemo(() => getYearlyReport(records, selectedYear), [records, selectedYear]);
```

- [ ] **Step 3: Replace old analysis content with report UI**

Render:

- Segmented mode switch using `SegmentButton`.
- Period selector row with previous/next buttons.
- Four `MetricCard`s for income, expense, net, and savings rate.
- Monthly trend bars when `reportMode === "month"`.
- Yearly month bars and top expense months when `reportMode === "year"`.
- Category ranking and recent records.

Use existing colors: green `#16805f`, muted text `#6d817c`, panel background `#ffffff`, page background `#f7faf9`.

- [ ] **Step 4: Add small helper components**

Add focused components below `AnalysisScreen`:

```ts
function PeriodSwitcher(...)
function ReportMetricGrid(...)
function MonthlyTrendChart(...)
function YearlyTrendChart(...)
function CategoryRanking(...)
function TopExpenseMonths(...)
```

Keep components pure and prop-driven.

- [ ] **Step 5: Add styles**

Extend `StyleSheet.create` with styles for:

- report mode segmented control.
- period switch buttons.
- 4-card metric grid.
- compact trend bars.
- yearly month summary rows.
- category ranking rows.

- [ ] **Step 6: Run typecheck**

Run:

```bash
npm run typecheck
```

Expected: PASS.

- [ ] **Step 7: Run app**

Run:

```bash
npm run web
```

Expected: Expo web starts and the Analysis tab renders without runtime errors.

- [ ] **Step 8: Commit UI changes**

Run:

```bash
git add jizhang/App.tsx
git commit -m "Upgrade analysis tab with reports"
```

---

### Task 5: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run full test suite**

Run:

```bash
npm test -- --run
```

Expected: PASS.

- [ ] **Step 2: Run typecheck**

Run:

```bash
npm run typecheck
```

Expected: PASS.

- [ ] **Step 3: Check git status**

Run:

```bash
git -C /Users/edy/Documents/MY status --short
```

Expected: only unrelated pre-existing changes may remain, especially files under `shouwang/` and the untracked `jizhang/history.xlsx` source workbook.
