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

    await expect(loadAppData(storage)).resolves.toEqual(data);
  });

  it("falls back to sample data when saved JSON is corrupted", async () => {
    const storage = new MemoryStorage();
    await storage.setItem("personal-budget-app:data", "{bad json");

    await expect(loadAppData(storage)).resolves.toEqual(sampleData);
  });
});
