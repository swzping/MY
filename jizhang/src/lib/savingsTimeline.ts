import type { Transaction } from './types';
import { previousMonths } from './financialSafety';

export function savingsSummary(records: Transaction[], today: string) {
  const months = previousMonths(today);
  const valid = records.filter(r => r.date <= today);
  const recent = valid.filter(r => months.includes(r.date.slice(0, 7)));
  const total = (rows: Transaction[], type: 'income' | 'expense') =>
    rows.filter(r => r.type === type).reduce((sum, r) => sum + r.amount, 0);
  const income = total(recent, 'income') / 3;
  const expense = total(recent, 'expense') / 3;
  return {
    months, income, expense, saving: income - expense,
    balance: total(valid, 'income') - total(valid, 'expense'),
    recordedMonths: new Set(recent.map(r => r.date.slice(0, 7))).size,
  };
}

export function savingsTimeline(monthlyExpense: number, capital: number, monthlySaving: number) {
  const target = monthlyExpense * 12 / 0.012;
  const gap = Math.max(0, target - capital);
  return { target, gap, months: gap === 0 ? 0 : monthlySaving > 0 ? Math.ceil(gap / monthlySaving) : null };
}
