import tempfile
import unittest
from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import excel_sync
from excel_sync import append_record, Handler
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
import json

SOURCE = Path(__file__).resolve().parents[1] / 'history.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'history.xlsx'
        copyfile(SOURCE, self.path)
        self.record = dict(id='test-record-1', type='expense', amount=12.34,
                           category='餐饮', date='2026-10-19', note='测试 < & =SUM(A1)', createdAt='2026-10-19T01:00:00Z')

    def test_append_retry_and_preserve_zip_parts(self):
        before = self.path.read_bytes()
        with ZipFile(self.path) as z:
            parts = {n: z.read(n) for n in z.namelist()}
        self.assertEqual(append_record(self.path, self.record), 'written')
        after = self.path.read_bytes()
        self.assertEqual(append_record(self.path, self.record), 'exists')
        self.assertEqual(self.path.read_bytes(), after)
        self.assertEqual(len(list((self.path.parent / '.excel-backups').glob('*.xlsx'))), 1)
        self.assertEqual(next((self.path.parent / '.excel-backups').glob('*.xlsx')).read_bytes(), before)
        with ZipFile(self.path) as z:
            changed = [n for n in parts if parts[n] != z.read(n)]
            self.assertEqual(len(changed), 1)
            root = ET.fromstring(z.read(changed[0]))
            rows = root.findall('s:sheetData/s:row', NS)
            last = next(row for row in rows if self.record['id'] in ''.join(row.itertext()))
            self.assertLess(rows.index(last), 5)
            self.assertIn('12.34', [e.text for e in last.findall('.//s:v', NS)])
            self.assertIn(self.record['note'], [e.text for e in last.findall('.//s:t', NS)])
            self.assertFalse(last.findall('.//s:f', NS))

    def test_sorted_insertion_for_new_and_backdated_records(self):
        for i, day in enumerate(['2027-01-01', '2024-01-01', '2019-01-01']):
            append_record(self.path, {**self.record, 'id': f'insert-{i}', 'date': day})
        with ZipFile(self.path) as z:
            strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
            root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            rows = root.findall('s:sheetData/s:row', NS)
            dates = []
            for n, row in enumerate(rows, 1):
                self.assertEqual(row.get('r'), str(n))
                for cell in row:
                    self.assertTrue(cell.get('r').endswith(str(n)))
                    if excel_sync.column_number(cell.get('r')) == 2 and n > 1:
                        dates.append(excel_sync.parse_date(excel_sync.cell_text(cell, strings)))
            self.assertEqual(dates, sorted(dates, reverse=True))

    def test_update_and_retry_without_duplicate(self):
        append_record(self.path, self.record)
        updated = {**self.record, 'amount': 98.76, 'date': '2026-10-20',
                   'excelOriginal': self.record.copy()}
        self.assertEqual(excel_sync.update_record(self.path, updated), 'updated')
        self.assertEqual(excel_sync.update_record(self.path, updated), 'exists')
        with ZipFile(self.path) as z:
            xml = z.read('xl/worksheets/sheet1.xml').decode()
            self.assertEqual(xml.count('test-record-1'), 1)
            self.assertIn('98.76', xml)
        moved = {**updated, 'type': 'income', 'excelOriginal': {k:v for k,v in updated.items() if k != 'excelOriginal'}}
        self.assertEqual(excel_sync.update_record(self.path, moved), 'updated')
        with ZipFile(self.path) as z:
            self.assertNotIn('test-record-1', z.read('xl/worksheets/sheet1.xml').decode())
            self.assertIn('test-record-1', z.read('xl/worksheets/sheet2.xml').decode())

    def test_update_imported_record_and_reject_external_changes(self):
        with ZipFile(self.path) as z:
            strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
            root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            rows = root.findall('s:sheetData/s:row', NS)
            original_count = len(rows)
            cells = {excel_sync.column_number(c.get('r')): excel_sync.cell_text(c, strings) for c in rows[1]}
            timestamp = excel_sync.parse_date(cells[2])
            original = dict(id='history-expense-test', type='expense', amount=float(cells[7]),
                date=timestamp.strftime('%Y-%m-%d'), createdAt=timestamp.isoformat(),
                category=cells[3].strip(), subcategory=cells[4].strip(), note=cells.get(13, '').strip())
        updated = {**original, 'amount': 77.77, 'note': '修改备注', 'excelOriginal': original}
        self.assertEqual(excel_sync.update_record(self.path, updated), 'updated')
        self.assertEqual(excel_sync.update_record(self.path, updated), 'exists')
        with ZipFile(self.path) as z:
            new_rows = ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('s:sheetData/s:row', NS)
            self.assertEqual(len(new_rows), original_count)
        with self.assertRaises(ValueError):
            excel_sync.update_record(self.path, {**updated, 'amount': 88.88})

    def test_income_and_invalid_input(self):
        self.record['type'] = 'income'
        self.assertEqual(append_record(self.path, self.record), 'written')
        original = self.path.read_bytes()
        for field, value in [('amount', -1), ('amount', float('nan')), ('date', '2026-02-30'), ('id', 'history-income-1')]:
            record = {**self.record, field: value}
            with self.assertRaises(ValueError):
                append_record(self.path, record)
            self.assertEqual(self.path.read_bytes(), original)

    def test_http_append_retry_and_origin_rejection(self):
        previous_root = excel_sync.ROOT
        excel_sync.ROOT = self.path.parent
        self.addCleanup(setattr, excel_sync, 'ROOT', previous_root)
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f'http://127.0.0.1:{server.server_port}/records'
        def send(origin):
            request = Request(url, data=json.dumps(self.record).encode(), headers={
                'Host': '127.0.0.1:8787', 'Origin': origin, 'Content-Type': 'application/json'})
            return build_opener(ProxyHandler({})).open(request)
        original = self.path.read_bytes()
        with self.assertRaises(HTTPError) as error:
            send('https://example.com')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        self.assertEqual(original, self.path.read_bytes())
        with send('http://localhost:8081') as response:
            self.assertEqual(json.load(response)['status'], 'written')
        with send('http://localhost:8081') as response:
            self.assertEqual(json.load(response)['status'], 'exists')

    def test_workbook_lock_blocks_write(self):
        for name in ['~$history.xlsx', '.~history.xlsx']:
            lock = self.path.parent / name
            lock.touch()
            with self.assertRaises(ValueError):
                append_record(self.path, self.record)
            lock.unlink()

if __name__ == '__main__':
    unittest.main()
