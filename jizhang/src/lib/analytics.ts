import type { BudgetLevel, BudgetState, RecordInput, Transaction } from "./types";

export type MonthlyTotals = {
  income: number;
  expense: number;
  net: number;
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

export type TrendPoint = {
  date: string;
  label: string;
  amount: number;
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
