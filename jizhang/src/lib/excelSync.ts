import { categoryLabels } from '../data/categories';
import type { Transaction } from './types';

export async function syncRecordToExcel(record: Transaction, fetcher: typeof fetch = fetch): Promise<void> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetcher('http://127.0.0.1:8787/records', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...record, category: categoryLabels[record.category] ?? record.category,
        ...(record.excelOriginal ? { excelOriginal: { ...record.excelOriginal,
          category: categoryLabels[record.excelOriginal.category] ?? record.excelOriginal.category } } : {}) }),
      signal: controller.signal,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '表格同步失败');
    if (result.id !== record.id || !['written', 'exists', 'updated'].includes(result.status)) {
      throw new Error('未收到表格写入确认，请重试');
    }
  } catch (error) {
    if (error instanceof TypeError || (error instanceof Error && error.name === 'AbortError')) {
      throw new Error('无法连接表格同步服务，请启动服务后重试');
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function queueUnsyncedRecords(records: Transaction[]): Transaction[] {
  return records.map((record) => record.excelSync === undefined
    && !record.id.startsWith('history-') && !record.id.startsWith('sample-')
    ? { ...record, excelSync: 'pending' as const }
    : record);
}
