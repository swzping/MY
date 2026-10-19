import { sampleData } from "../data/sampleData";
import type { AppData, Transaction } from "./types";

export const STORAGE_KEY = "personal-budget-app:data";

type StorageLike = {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
};

export async function loadAppData(storage: StorageLike): Promise<AppData> {
  try {
    const saved = await storage.getItem(STORAGE_KEY);
    if (!saved) {
      return sampleData;
    }

    const parsed = JSON.parse(saved);
    return isAppData(parsed) ? mergeWithSeedData(parsed) : sampleData;
  } catch {
    return sampleData;
  }
}

export async function saveAppData(storage: StorageLike, data: AppData): Promise<void> {
  await storage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function isAppData(value: unknown): value is AppData {
  if (!value || typeof value !== "object") {
    return false;
  }

  const data = value as AppData;

  return (
    Array.isArray(data.records) &&
    data.records.every(isTransaction) &&
    Boolean(data.budget) &&
    typeof data.budget.monthlyBudget === "number" &&
    Boolean(data.budget.categoryBudgets) &&
    typeof data.budget.categoryBudgets === "object"
  );
}

function isTransaction(value: unknown): value is Transaction {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Transaction;

  return (
    typeof record.id === "string" &&
    (record.type === "income" || record.type === "expense") &&
    typeof record.amount === "number" &&
    typeof record.category === "string" &&
    (record.subcategory === undefined || typeof record.subcategory === "string") &&
    typeof record.date === "string" &&
    typeof record.note === "string" &&
    typeof record.createdAt === "string"
  );
}

// Exact originals only: preserve user-created records and edited demo records.
const legacyDemoRecords: Transaction[] = [
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

function isLegacyDemoRecord(record: Transaction): boolean {
  return legacyDemoRecords.some((demo) =>
    (Object.keys(demo) as (keyof Transaction)[]).every((key) => record[key] === demo[key]),
  );
}

function mergeWithSeedData(savedData: AppData): AppData {
  const recordsById = new Map<string, Transaction>();

  sampleData.records.forEach((record) => {
    recordsById.set(record.id, record);
  });
  savedData.records.forEach((record) => {
    if (isLegacyDemoRecord(record)) return;
    const seed = recordsById.get(record.id);
    recordsById.set(record.id, record.subcategory === undefined && seed?.subcategory !== undefined
      ? { ...record, subcategory: seed.subcategory }
      : record);
  });

  return {
    budget: savedData.budget,
    records: [...recordsById.values()].sort((a, b) => {
      const dateCompare = b.date.localeCompare(a.date);
      return dateCompare === 0 ? b.createdAt.localeCompare(a.createdAt) : dateCompare;
    }),
  };
}
