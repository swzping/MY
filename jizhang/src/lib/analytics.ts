import type { BudgetLevel, BudgetState, RecordInput, Transaction } from "./types";

export type MonthlyTotals = {
  income: number;
  expense: number;
  net: number;
};

export type ReportTotals = MonthlyTotals & {
  savingsRate: number;
};

export type BudgetStatus = {
  limit: number;
  spent: number;
  remaining: number;
  percent: number;
  level: BudgetLevel;
};

export type CategorySpending = {
  category: string;
  amount: number;
  percent: number;
};

export type ReportCategory = CategorySpending;

export type TrendPoint = {
  date: string;
  label: string;
  amount: number;
};

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

export function getMonthlyTotals(records: Transaction[], date: string): MonthlyTotals {
  const monthKey = date.slice(0, 7);
  const monthlyRecords = records.filter((record) => record.date.startsWith(monthKey));
  const income = sumRecords(monthlyRecords, "income");
  const expense = sumRecords(monthlyRecords, "expense");

  return {
    income,
    expense,
    net: income - expense,
  };
}

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

export function getBudgetStatus(
  records: Transaction[],
  budget: BudgetState,
  date: string,
): BudgetStatus {
  const spent = getMonthlyTotals(records, date).expense;
  const limit = Math.max(0, budget.monthlyBudget);
  const percent = limit === 0 ? 0 : Math.round((spent / limit) * 100);
  const remaining = limit - spent;

  return {
    limit,
    spent,
    remaining,
    percent,
    level: getBudgetLevel(percent, remaining),
  };
}

export function getCategorySpending(records: Transaction[], date: string): CategorySpending[] {
  const monthKey = date.slice(0, 7);
  const totals = new Map<string, number>();

  records
    .filter((record) => record.type === "expense" && record.date.startsWith(monthKey))
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

export function buildSevenDayTrend(records: Transaction[], endDate: string): TrendPoint[] {
  const end = parseLocalDate(endDate);

  return Array.from({ length: 7 }, (_, index) => {
    const current = new Date(end);
    current.setDate(end.getDate() - (6 - index));
    const date = formatDate(current);
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

export function validateRecordInput(input: RecordInput): string[] {
  const errors: string[] = [];

  if (!Number.isFinite(input.amount) || input.amount <= 0) {
    errors.push("金额必须大于 0");
  }

  if (!input.category.trim()) {
    errors.push("请选择分类");
  }

  if (!input.date.trim()) {
    errors.push("请选择日期");
  }

  return errors;
}

export function getCategoryBudgetStatuses(
  records: Transaction[],
  budget: BudgetState,
  date: string,
): Array<BudgetStatus & { category: string }> {
  const spending = getCategorySpending(records, date);

  return Object.entries(budget.categoryBudgets).map(([category, limit]) => {
    const spent = spending.find((item) => item.category === category)?.amount ?? 0;
    const safeLimit = Math.max(0, limit);
    const percent = safeLimit === 0 ? 0 : Math.round((spent / safeLimit) * 100);

    return {
      category,
      limit: safeLimit,
      spent,
      remaining: safeLimit - spent,
      percent,
      level: getBudgetLevel(percent, safeLimit - spent),
    };
  });
}

export function getRecentRecords(records: Transaction[], limit = 5): Transaction[] {
  return [...records]
    .sort((a, b) => {
      const dateCompare = b.date.localeCompare(a.date);
      return dateCompare === 0 ? b.createdAt.localeCompare(a.createdAt) : dateCompare;
    })
    .slice(0, limit);
}

function sumRecords(records: Transaction[], type: "income" | "expense") {
  return records
    .filter((record) => record.type === type)
    .reduce((sum, record) => sum + record.amount, 0);
}

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

function getBudgetLevel(percent: number, remaining: number): BudgetLevel {
  if (remaining < 0 || percent > 100) {
    return "over";
  }

  if (percent >= 80) {
    return "near";
  }

  return "healthy";
}

function parseLocalDate(date: string) {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
