import { expect, it } from 'vitest';
import { editRecord, editableNote } from './editRecord';
import type { Transaction } from './types';
const original: Transaction = {id:'history-expense-1',type:'expense',amount:30,category:'食',subcategory:'餐饮',date:'2026-10-10',createdAt:'2026-10-10T12:00:00',note:'餐饮 · 午餐'};
it('keeps identity, stores original for Excel matching, and preserves it across pending edits', () => {
 const edited=editRecord(original,{amount:40,note:'晚餐'},true);
 expect(edited.id).toBe(original.id);
 expect(edited.createdAt).toBe(original.createdAt);
 expect(edited.excelSync).toBe('pending');
 expect(edited.excelOriginal?.amount).toBe(30);
 expect(edited.excelOriginal?.note).toBe('午餐');
 expect(editRecord(edited,{amount:50},true).excelOriginal).toEqual(edited.excelOriginal);
 expect(editableNote(original)).toBe('午餐');
});
