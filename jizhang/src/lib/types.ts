export type TransactionType = "income" | "expense";

export type Transaction = {
  id: string;
  type: TransactionType;
  amount: number;
  category: string;
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
