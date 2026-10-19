import { describe, expect, it, vi } from 'vitest';
import { syncRecordToExcel, queueUnsyncedRecords } from './excelSync';
import type { Transaction } from './types';
const record: Transaction = { id: 'manual-test', type: 'expense', amount: 12.34,
  category: 'Food', date: '2026-10-19', note: '午餐', createdAt: '2026-10-19T00:00:00Z' };
describe('Excel synchronization', () => {
  it('sends a stable ID and a readable category', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: record.id, status: 'written' }) });
    await syncRecordToExcel(record, fetcher);
    const payload = JSON.parse(fetcher.mock.calls[0][1].body);
    expect(payload.id).toBe(record.id);
    expect(payload.category).toBe('餐饮');
    expect(payload.amount).toBe(12.34);
  });
  it('accepts an idempotent retry and rejects errors or mismatched acknowledgements', async () => {
    await expect(syncRecordToExcel(record, vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: record.id, status: 'exists' }) }))).resolves.toBeUndefined();
    await expect(syncRecordToExcel(record, vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: '文件被占用' }) }))).rejects.toThrow('文件被占用');
    await expect(syncRecordToExcel(record, vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 'wrong', status: 'written' }) }))).rejects.toThrow();
  });
});

it('queues earlier manual records but excludes imports, examples, and acknowledged records', async () => {
  const input: Transaction[] = [record,
    { ...record, id: 'history-expense-1' },
    { ...record, id: 'sample-1' },
    { ...record, id: 'done', excelSync: 'synced' },
    { ...record, id: 'waiting', excelSync: 'pending' }];
  const output = queueUnsyncedRecords(input);
  expect(output[0].excelSync).toBe('pending');
  expect(output.slice(1)).toEqual(input.slice(1));
  expect(queueUnsyncedRecords(output)).toEqual(output);
});
