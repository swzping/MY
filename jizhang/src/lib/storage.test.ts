import { describe, expect, it } from "vitest";
import { sampleData } from "../data/sampleData";
import { loadAppData, saveAppData } from "./storage";
import type { AppData, Transaction } from "./types";

class MemoryStorage {
  private values = new Map<string, string>();

  async getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  async setItem(key: string, value: string) {
    this.values.set(key, value);
  }

  removeItem(key: string) {
    this.values.delete(key);
  }
}

describe("storage", () => {

  it("removes unchanged legacy demo records while preserving real records and budget", async () => {
    const storage = new MemoryStorage();
    const legacyRecords: Transaction[] = [
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
  ];
    const manualRecord: Transaction = { ...legacyRecords[1], id: "manual-1" };
    const budget = { monthlyBudget: 7777, categoryBudgets: { Food: 1000 } };
    await saveAppData(storage, { budget, records: [...sampleData.records, ...legacyRecords, manualRecord] });
    const loaded = await loadAppData(storage);
    expect(loaded.records).toHaveLength(sampleData.records.length + 1);
    expect(loaded.records).toContainEqual(manualRecord);
    expect(loaded.budget).toEqual(budget);
    const total = (type: Transaction["type"]) => loaded.records
      .filter((record) => record.type === type)
      .reduce((sum, record) => sum + record.amount, 0);
    expect(total("income")).toBeCloseTo(1727245.85, 2);
    expect(total("expense")).toBeCloseTo(1687922.85 + 86, 2);
    await saveAppData(storage, loaded);
    expect(await loadAppData(storage)).toEqual(loaded);

    const editedDemo = { ...legacyRecords[0], amount: 13000 };
    await saveAppData(storage, { budget, records: [editedDemo] });
    expect((await loadAppData(storage)).records).toContainEqual(editedDemo);
  });

  it("loads fallback data when no saved snapshot exists", async () => {
    const storage = new MemoryStorage();

    await expect(loadAppData(storage)).resolves.toEqual(sampleData);
  });

  it("saves and loads app data", async () => {
    const storage = new MemoryStorage();
    const data: AppData = {
      budget: {
        monthlyBudget: 3000,
        categoryBudgets: {
          Food: 900,
        },
      },
      records: [
        {
          id: "record-1",
          type: "expense",
          amount: 45,
          category: "Food",
          date: "2026-06-10",
          note: "Dinner",
          createdAt: "2026-06-10T19:30:00.000Z",
        },
      ],
    };

    await saveAppData(storage, data);

    const loaded = await loadAppData(storage);

    expect(loaded.budget).toEqual(data.budget);
    expect(loaded.records).toContainEqual(data.records[0]);
  });

  it("merges seeded history records into existing saved data", async () => {
    const storage = new MemoryStorage();
    const savedRecord = {
      id: "manual-record-1",
      type: "expense" as const,
      amount: 45,
      category: "Food",
      date: "2026-09-02",
      note: "Manual dinner",
      createdAt: "2026-09-02T19:30:00.000Z",
    };
    await storage.setItem(
      "personal-budget-app:data",
      JSON.stringify({
        budget: {
          monthlyBudget: 3000,
          categoryBudgets: {
            Food: 900,
          },
        },
        records: [savedRecord],
      }),
    );

    const loaded = await loadAppData(storage);

    expect(loaded.budget.monthlyBudget).toBe(3000);
    expect(loaded.records).toContainEqual(savedRecord);
    expect(loaded.records.some((record) => record.id.startsWith("history-"))).toBe(true);
  });

  it("falls back to sample data when saved JSON is corrupted", async () => {
    const storage = new MemoryStorage();
    await storage.setItem("personal-budget-app:data", "{bad json");

    await expect(loadAppData(storage)).resolves.toEqual(sampleData);
  });
});

it("backfills imported subcategories into old caches without replacing user edits", async () => {
  const storage = new MemoryStorage();
  const source = sampleData.records.find((record) => record.subcategory)!;
  const { subcategory, ...oldRecord } = source;
  await saveAppData(storage, { ...sampleData, records: [{ ...oldRecord, note: "用户修改的备注" }] });
  const loaded = await loadAppData(storage);
  expect(loaded.records.find((record) => record.id === source.id)).toEqual({ ...source, note: "用户修改的备注" });
});
