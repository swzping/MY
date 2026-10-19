export type TransactionType = "income" | "expense";

export type Transaction = {
  id: string;
  type: TransactionType;
  amount: number;
  category: string;
  subcategory?: string;
  excelSync?: "pending" | "synced";
  updatedAt?: string;
  excelOriginal?: Pick<Transaction, "id" | "type" | "amount" | "category" | "subcategory" | "date" | "createdAt" | "note">;
  date: string;
  note: string;
  createdAt: string;
};

export type BudgetState = {
  monthlyBudget: number;
  categoryBudgets: Record<string, number>;
};

export type AppData = {
  records: Transaction[];
  budget: BudgetState;
};

export type RecordInput = {
  amount: number;
  category: string;
  date: string;
};

export type BudgetLevel = "healthy" | "near" | "over";
