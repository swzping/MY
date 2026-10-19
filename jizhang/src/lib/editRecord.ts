import type { Transaction } from './types';

export function editableNote(record: Transaction): string {
  if (record.id.startsWith('history-') && !record.updatedAt && record.subcategory) {
    if (record.note === record.subcategory) return '';
    const prefix = record.subcategory + ' · ';
    if (record.note.startsWith(prefix)) return record.note.slice(prefix.length);
  }
  return record.note;
}

export function editRecord(original: Transaction, changes: Partial<Pick<Transaction,
  'type' | 'amount' | 'category' | 'subcategory' | 'date' | 'note'>>, sync: boolean): Transaction {
  const { id, type, amount, category, subcategory, date, createdAt } = original;
  return {
    ...original, ...changes, updatedAt: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    ...(sync ? {
      excelSync: 'pending' as const,
      excelOriginal: original.excelOriginal ?? { id, type, amount, category, subcategory, date, createdAt, note: editableNote(original) },
    } : {}),
  };
}
