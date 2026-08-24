import type { AppData } from "../lib/types";

export const sampleData: AppData = {
  budget: {
    monthlyBudget: 5200,
    categoryBudgets: {
      Food: 1600,
      Transport: 600,
      Shopping: 1000,
      Housing: 1800,
      Entertainment: 500,
    },
  },
  records: [
    {
      id: "sample-1",
      type: "income",
      amount: 12000,
      category: "Salary",
      date: "2026-06-01",
      note: "本月工资",
      createdAt: "2026-06-01T09:00:00.000Z",
    },
    {
      id: "sample-2",
      type: "expense",
      amount: 86,
      category: "Food",
      date: "2026-06-12",
      note: "午餐和咖啡",
      createdAt: "2026-06-12T12:30:00.000Z",
    },
    {
      id: "sample-3",
      type: "expense",
      amount: 38,
      category: "Transport",
      date: "2026-06-13",
      note: "地铁充值",
      createdAt: "2026-06-13T18:10:00.000Z",
    },
    {
      id: "sample-4",
      type: "expense",
      amount: 328,
      category: "Shopping",
      date: "2026-06-15",
      note: "生活用品",
      createdAt: "2026-06-15T20:10:00.000Z",
    },
  ],
};
