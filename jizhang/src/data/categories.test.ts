import { expect, it } from 'vitest';
import { getCategoryOptions } from './categories';
import type { Transaction } from '../lib/types';
it('uses historical two-level categories, separates income and expense and preserves the current legacy selection', () => {
  const expenses = getCategoryOptions('expense', []);
  expect(expenses['食']).toEqual(['早午晚餐', '水果零食']);
  expect(expenses.Food).toBeUndefined();
  expect(expenses['职业收入']).toBeUndefined();
  expect(getCategoryOptions('income', [])['职业收入']).toContain('工资收入');
  const old = {type:'expense',category:'Food',subcategory:''} as Transaction;
  expect(getCategoryOptions('expense', [old]).Food).toBeUndefined();
  expect(getCategoryOptions('expense', [old], old).Food).toEqual(['']);
  expect(getCategoryOptions('expense', [], { category:'食', subcategory:'自定义旧小类' })['食']).toContain('自定义旧小类');
});
