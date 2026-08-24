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
    return isAppData(parsed) ? parsed : sampleData;
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
    typeof record.date === "string" &&
    typeof record.note === "string" &&
    typeof record.createdAt === "string"
  );
}
