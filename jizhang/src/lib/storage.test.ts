import { describe, expect, it } from "vitest";
import { sampleData } from "../data/sampleData";
import { loadAppData, saveAppData } from "./storage";
import type { AppData } from "./types";

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
    expect(loaded.records[0]).toEqual(savedRecord);
    expect(loaded.records.some((record) => record.id.startsWith("history-"))).toBe(true);
  });

  it("falls back to sample data when saved JSON is corrupted", async () => {
    const storage = new MemoryStorage();
    await storage.setItem("personal-budget-app:data", "{bad json");

    await expect(loadAppData(storage)).resolves.toEqual(sampleData);
  });
});
