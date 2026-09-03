import { describe, expect, it } from "vitest";
import {
  buildSevenDayTrend,
  getLatestRecordDate,
  getBudgetStatus,
  getCategorySpending,
  getMonthlyTotals,
  getMonthlyReport,
  getYearlyReport,
  validateRecordInput,
} from "./analytics";
import type { BudgetState, Transaction } from "./types";

const records: Transaction[] = [
  {
    id: "1",
    type: "expense",
    amount: 80,
    category: "Food",
    date: "2026-06-02",
    note: "Lunch",
    createdAt: "2026-06-02T10:00:00.000Z",
  },
  {
    id: "2",
    type: "expense",
    amount: 120,
    category: "Transport",
    date: "2026-06-04",
    note: "Taxi",
    createdAt: "2026-06-04T10:00:00.000Z",
  },
  {
    id: "3",
    type: "income",
    amount: 5000,
    category: "Salary",
    date: "2026-06-05",
    note: "June salary",
    createdAt: "2026-06-05T10:00:00.000Z",
  },
  {
    id: "4",
    type: "expense",
    amount: 50,
    category: "Food",
    date: "2026-05-25",
    note: "Old month",
    createdAt: "2026-05-25T10:00:00.000Z",
  },
];

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

describe("analytics", () => {
  it("calculates monthly income, expense, and net totals", () => {
    expect(getMonthlyTotals(records, "2026-06-15")).toEqual({
      income: 5000,
      expense: 200,
      net: 4800,
    });
  });

  it("reports budget remaining amount and status level", () => {
    const budget: BudgetState = {
      monthlyBudget: 250,
      categoryBudgets: {
        Food: 100,
      },
    };

    expect(getBudgetStatus(records, budget, "2026-06-15")).toEqual({
      limit: 250,
      spent: 200,
      remaining: 50,
      percent: 80,
      level: "near",
    });
  });

  it("groups monthly expense spending by category from highest to lowest", () => {
    expect(getCategorySpending(records, "2026-06-15")).toEqual([
      { category: "Transport", amount: 120, percent: 60 },
      { category: "Food", amount: 80, percent: 40 },
    ]);
  });

  it("builds a seven-day expense trend ending on the selected date", () => {
    expect(buildSevenDayTrend(records, "2026-06-05")).toEqual([
      { date: "2026-05-30", label: "05/30", amount: 0 },
      { date: "2026-05-31", label: "05/31", amount: 0 },
      { date: "2026-06-01", label: "06/01", amount: 0 },
      { date: "2026-06-02", label: "06/02", amount: 80 },
      { date: "2026-06-03", label: "06/03", amount: 0 },
      { date: "2026-06-04", label: "06/04", amount: 120 },
      { date: "2026-06-05", label: "06/05", amount: 0 },
    ]);
  });

  it("validates required record input", () => {
    expect(
      validateRecordInput({
        amount: 0,
        category: "",
        date: "",
      }),
    ).toEqual(["金额必须大于 0", "请选择分类", "请选择日期"]);
  });

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
});
