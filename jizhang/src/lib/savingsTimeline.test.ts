import { expect, it } from 'vitest';
import { savingsSummary, savingsTimeline } from './savingsTimeline';
import type { Transaction } from './types';
const tx = (date: string, type: 'income' | 'expense', amount: number): Transaction => ({id: date+type, date, type, amount, category: '其他', note: '', createdAt: date});
it('uses complete calendar months and includes every expense category', () => {
 const result = savingsSummary([tx('2026-07-01','income',30000),tx('2026-09-01','expense',18000),tx('2026-10-01','expense',1000),tx('2026-11-01','income',99999)],'2026-10-19');
 expect(result.income).toBe(10000);expect(result.expense).toBe(6000);expect(result.saving).toBe(4000);
 expect(result.balance).toBe(11000);expect(result.recordedMonths).toBe(2);
});
it('calculates remaining saving time and handles zero or negative saving', () => {
 expect(savingsTimeline(1000,40000,4000)).toEqual({target:1000000,gap:960000,months:240});
 expect(savingsTimeline(2000,40000,4000).months).toBe(490);
 expect(savingsTimeline(1000,0,0).months).toBeNull();
 expect(savingsTimeline(1000,0,-100).months).toBeNull();
 expect(savingsTimeline(1000,1000000,-100).months).toBe(0);
});
