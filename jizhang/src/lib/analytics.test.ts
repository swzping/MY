import { describe, expect, it } from "vitest";
import {
  buildSevenDayTrend,
  getBudgetStatus,
  getCategorySpending,
  getMonthlyTotals,
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
});
