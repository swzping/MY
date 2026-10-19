"""Local date-sorted XLSX sync. Only the target sheet XML is patched."""
import fcntl
import json
import math
import os
import posixpath
import re
import tempfile
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def validate(record):
    if not isinstance(record, dict):
        raise ValueError('账单格式不正确')
    for field in ['id', 'category', 'date', 'note', 'createdAt']:
        value = record.get(field)
        if not isinstance(value, str) or len(value) > 10000 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
            raise ValueError('账单字段不正确')
    if not record['id'] or record['id'].startswith(('history-', 'sample-')):
        raise ValueError('只允许同步新账单')
    if not record['category'].strip() or record.get('type') not in ('income', 'expense'):
        raise ValueError('账单分类不正确')
    amount = record.get('amount')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError('金额必须大于零')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', record['date']):
        raise ValueError('日期格式不正确')
    date.fromisoformat(record['date'])
    sub = record.get('subcategory', '')
    if not isinstance(sub, str) or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', sub):
        raise ValueError('小类不正确')


def column(number):
    result = ''
    while number:
        number, digit = divmod(number - 1, 26)
        result = chr(65 + digit) + result
    return result


def column_number(ref):
    value = 0
    for char in re.match('[A-Z]+', ref)[0]:
        value = value * 26 + ord(char) - 64
    return value


def cell_text(cell, strings):
    if cell.get('t') == 'inlineStr':
        return ''.join(cell.itertext())
    value = cell.find('s:v', NS)
    if value is None:
        return ''
    return strings[int(value.text)] if cell.get('t') == 's' else value.text or ''


def cell_xml(ref, value, style=None):
    attrs = f' r="{ref}"' + (f' s="{style}"' if style is not None else '')
    if isinstance(value, (int, float)):
        return f'<c{attrs}><v>{value}</v></c>'
    return f'<c{attrs} t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>'


def parse_date(value):
    if not value:
        return datetime.min
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(value))
    except ValueError:
        pass
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y/%m/%d'):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError('无法识别账单日期，未排序：' + value)


def sort_sheet(xml, strings):
    root = ET.fromstring(xml)
    # This ledger contains plain values. Refuse to move formulas or referenced ranges.
    for tag in ('f', 'mergeCell', 'tablePart', 'conditionalFormatting', 'dataValidation'):
        if root.find('.//s:' + tag, NS) is not None:
            raise ValueError('表格包含公式或特殊区域，无法安全排序')
    match = re.search(r'(<sheetData\b[^>]*>)(.*?)(</sheetData>)', xml, re.S)
    if not match:
        raise ValueError('不支持的工作表结构')
    rows = re.findall(r'<row\b[^>]*(?:/>|>.*?</row>)', match[2], re.S)
    if len(rows) < 2:
        return xml
    def element(text):
        return ET.fromstring('<worksheet xmlns="' + NS['s'] + '">' + text + '</worksheet>')[0]
    headers = {cell_text(c, strings): column_number(c.get('r')) for c in element(rows[0])}
    date_col = headers.get('日期')
    if not date_col:
        raise ValueError('缺少日期列')
    def key(text):
        for cell in element(text):
            if column_number(cell.get('r')) == date_col:
                return parse_date(cell_text(cell, strings))
        return datetime.min
    ordered = [rows[0]] + sorted(rows[1:], key=key, reverse=True)
    renumbered = []
    for n, row in enumerate(ordered, 1):
        row = re.sub(r'(<row\b[^>]*?\br=")[0-9]+(" )', lambda m: m[1] + str(n) + m[2], row)
        row = re.sub(r'(<row\b[^>]*?\br=")[0-9]+(")', lambda m: m[1] + str(n) + m[2], row, count=1)
        row = re.sub(r'(<c\b[^>]*?\br=")([A-Z]+)[0-9]+(")', lambda m: m[1] + m[2] + str(n) + m[3], row)
        renumbered.append(row)
    return xml[:match.start(2)] + ''.join(renumbered) + xml[match.end(2):]


def sort_existing_workbook(path):
    path = Path(path)
    with open(path.with_suffix('.sync.lock'), 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any((path.parent / n).exists() for n in ('~$' + path.name, '.~' + path.name, '.~lock.' + path.name + '#')):
            raise ValueError('请先保存并关闭表格')
        original = path.read_bytes()
        with ZipFile(path) as archive:
            strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in archive.namelist() else []
            updates = {n: sort_sheet(archive.read(n).decode('utf-8'), strings).encode('utf-8')
                       for n in archive.namelist() if re.fullmatch(r'xl/worksheets/sheet[0-9]+.xml', n)}
            backups = path.parent / '.excel-backups'
            backups.mkdir(exist_ok=True)
            (backups / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '-before-sort.xlsx')).write_bytes(original)
            fd, temp = tempfile.mkstemp(suffix='.xlsx', dir=path.parent)
            os.close(fd)
            try:
                with ZipFile(temp, 'w') as output:
                    for entry in archive.infolist():
                        output.writestr(entry, updates.get(entry.filename, archive.read(entry.filename)))
                if path.read_bytes() != original:
                    raise ValueError('文件已更新，请重试')
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)


def append_record(path, record):
    validate(record)
    path = Path(path)
    with open(path.with_suffix('.sync.lock'), 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any((path.parent / name).exists() for name in ('~$' + path.name, '.~' + path.name, '.~lock.' + path.name + '#')):
            raise ValueError('请先关闭 Excel/WPS 中的 history.xlsx，再重试')
        original = path.read_bytes()
        with ZipFile(path) as archive:
            strings = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
            rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
            sheets = ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets', NS)
            target = None
            for sheet in sheets:
                rel = rels[sheet.get(RID)]
                name = rel.lstrip('/') if rel.startswith('/') else posixpath.normpath('xl/' + rel)
                xml = archive.read(name).decode('utf-8')
                root = ET.fromstring(xml)
                rows = root.findall('s:sheetData/s:row', NS)
                if not rows:
                    continue
                headers = {cell_text(c, strings): column_number(c.get('r')) for c in rows[0]}
                id_col = headers.get('账单ID')
                if id_col:
                    for row in rows[1:]:
                        for cell in row:
                            if column_number(cell.get('r')) == id_col and cell_text(cell, strings) == record['id']:
                                return 'exists'
                if sheet.get('name') == ('收入' if record['type'] == 'income' else '支出'):
                    target = name, xml, root, rows, headers
            if target is None:
                raise ValueError('找不到收入或支出工作表')
            name, xml, root, rows, headers = target
            if not {'日期', '一级分类', '二级分类', '金额', '备注'}.issubset(headers):
                raise ValueError('表格缺少必要列，未写入')
            if '</sheetData>' not in xml:
                raise ValueError('暂不支持此表格结构')
            max_col = max(column_number(c.get('r')) for row in rows for c in row)
            if '账单ID' not in headers:
                max_col += 1
                headers['账单ID'] = max_col
                xml = xml.replace('</row>', cell_xml(f'{column(max_col)}1', '账单ID') + '</row>', 1)
            number = max(int(row.get('r')) for row in rows) + 1
            values = {'交易类型': '收入' if record['type'] == 'income' else '支出',
                      '日期': record['date'] + ' 00:00:00', '一级分类': record['category'],
                      '二级分类': record.get('subcategory', ''), '金额': record['amount'],
                      '备注': record['note'], '账户币种': 'CNY', '账单ID': record['id']}
            styles = {column_number(c.get('r')): c.get('s') for c in rows[-1]}
            row_xml = f'<row r="{number}">' + ''.join(
                cell_xml(f'{column(col)}{number}', values.get(header, ''), styles.get(col))
                for header, col in sorted(headers.items(), key=lambda pair: pair[1])) + '</row>'
            xml = xml.replace('</sheetData>', row_xml + '</sheetData>')
            xml = re.sub(r'<dimension\b[^>]*/>', f'<dimension ref="A1:{column(max_col)}{number}"/>', xml, count=1)
            xml = sort_sheet(xml, strings)
            ET.fromstring(xml)
            backups = path.parent / '.excel-backups'
            backups.mkdir(exist_ok=True)
            backup = backups / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.xlsx')
            backup.write_bytes(original)
            fd, temp = tempfile.mkstemp(suffix='.xlsx', dir=path.parent)
            os.close(fd)
            try:
                with ZipFile(temp, 'w') as output:
                    for entry in archive.infolist():
                        output.writestr(entry, xml.encode('utf-8') if entry.filename == name else archive.read(entry.filename))
                if path.read_bytes() != original:
                    raise ValueError('表格已被其他程序更新，请重试')
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
    return 'written'


def update_record(path, record):
    validate({**record, 'id': 'edit-validation'})
    original_record = record.get('excelOriginal')
    if not isinstance(original_record, dict):
        raise ValueError('缺少原账单，无法更新')
    validate({**original_record, 'id': 'edit-validation'})
    path = Path(path)
    with open(path.with_suffix('.sync.lock'), 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any((path.parent / n).exists() for n in ('~$' + path.name, '.~' + path.name, '.~lock.' + path.name + '#')):
            raise ValueError('请先保存并关闭 Excel/WPS 中的 history.xlsx，再重试')
        before = path.read_bytes()
        with ZipFile(path) as archive:
            strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in archive.namelist() else []
            rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
            sheets = {}
            for sheet in ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets', NS):
                if sheet.get('name') not in ('收入', '支出'):
                    continue
                rel = rels[sheet.get(RID)]
                name = rel.lstrip('/') if rel.startswith('/') else posixpath.normpath('xl/' + rel)
                xml = archive.read(name).decode()
                rows = ET.fromstring(xml).findall('s:sheetData/s:row', NS)
                headers = {cell_text(c, strings): column_number(c.get('r')) for c in rows[0]}
                sheets[sheet.get('name')] = dict(name=name, xml=xml, rows=rows, headers=headers)
            def values(row, info):
                bycol = {column_number(c.get('r')): cell_text(c, strings) for c in row}
                return {label: bycol.get(col, '') for label, col in info['headers'].items()}
            def matches(v, tx):
                return (parse_date(v.get('日期', '')).strftime('%Y-%m-%d') == tx['date']
                    and float(v.get('金额') or 0) == tx['amount']
                    and v.get('一级分类', '').strip() == tx['category'].strip()
                    and v.get('二级分类', '').strip() == (tx.get('subcategory') or '').strip()
                    and v.get('备注', '').strip() == tx['note'].strip())
            found = []
            for title, info in sheets.items():
                for row in info['rows'][1:]:
                    v = values(row, info)
                    if v.get('账单ID') == record['id']:
                        found.append((title, info, row, v))
            if not found:
                old_title = '收入' if original_record['type'] == 'income' else '支出'
                info = sheets[old_title]
                for row in info['rows'][1:]:
                    v = values(row, info)
                    if not v.get('账单ID') and matches(v, original_record):
                        # Imported records retain the original transaction timestamp.
                        if record['id'].startswith('history-') and parse_date(v['日期']) != datetime.fromisoformat(original_record['createdAt']):
                            continue
                        found.append((old_title, info, row, v))
            if not found and not record['id'].startswith('history-'):
                # An edited, not-yet-exported manual record is still a new Excel row.
                fcntl.flock(lock, fcntl.LOCK_UN)
                return append_record(path, record)
            if len(found) != 1:
                raise ValueError('无法唯一定位原账单，请核对表格；未写入')
            old_title, source, row, current = found[0]
            new_title = '收入' if record['type'] == 'income' else '支出'
            if current.get('账单ID') == record['id'] and old_title == new_title and matches(current, record):
                return 'exists'
            if old_title != ('收入' if original_record['type'] == 'income' else '支出') or not matches(current, original_record):
                raise ValueError('表格中的账单已被修改，请核对后再同步')
            target = sheets[new_title]
            max_col = max(column_number(c.get('r')) for r in target['rows'] for c in r)
            if '账单ID' not in target['headers']:
                max_col += 1
                target['headers']['账单ID'] = max_col
                target['xml'] = target['xml'].replace('</row>', cell_xml(f'{column(max_col)}1', '账单ID') + '</row>', 1)
            old_number = row.get('r')
            source['xml'] = re.sub(r'<row\b(?=[^>]*\br="' + old_number + r'")[^>]*>.*?</row>', '', source['xml'], count=1, flags=re.S)
            number = max(int(r.get('r')) for r in target['rows']) + 1
            date_value = current['日期'] if record['date'] == original_record['date'] else record['date'] + ' 00:00:00'
            changes = {**current, '交易类型': new_title, '日期': date_value, '一级分类': record['category'],
                       '二级分类': record.get('subcategory') or '', '金额': record['amount'], '备注': record['note'], '账单ID': record['id']}
            old_cells = {column_number(c.get('r')): c for c in row}
            new_cells = []
            for header, col in sorted(target['headers'].items(), key=lambda pair: pair[1]):
                value = changes.get(header, '')
                if header == '日期' and record['date'] == original_record['date']:
                    original_cell = old_cells[source['headers']['日期']]
                    if original_cell.get('t') not in ('s', 'inlineStr'):
                        value = float(value)
                style = old_cells.get(col).get('s') if col in old_cells else None
                new_cells.append(cell_xml(f'{column(col)}{number}', value, style))
            target['xml'] = target['xml'].replace('</sheetData>', f'<row r="{number}">' + ''.join(new_cells) + '</row></sheetData>')
            updates = {}
            for info in (source, target):
                xml = sort_sheet(info['xml'], strings)
                count = len(ET.fromstring(xml).findall('s:sheetData/s:row', NS))
                width = max(info['headers'].values())
                xml = re.sub(r'<dimension\b[^>]*/>', f'<dimension ref="A1:{column(width)}{count}"/>', xml, count=1)
                updates[info['name']] = xml.encode()
            backups = path.parent / '.excel-backups'
            backups.mkdir(exist_ok=True)
            (backups / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '-before-edit.xlsx')).write_bytes(before)
            fd, temp = tempfile.mkstemp(suffix='.xlsx', dir=path.parent)
            os.close(fd)
            try:
                with ZipFile(temp, 'w') as output:
                    for entry in archive.infolist():
                        output.writestr(entry, updates.get(entry.filename, archive.read(entry.filename)))
                if path.read_bytes() != before:
                    raise ValueError('表格已更新，请重试')
                os.replace(temp, path)
            finally:
                if os.path.exists(temp): os.unlink(temp)
    return 'updated'


class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        origin = urlparse(self.headers.get('Origin', ''))
        return (origin.scheme == 'http' and origin.hostname in ('localhost', '127.0.0.1')
                and origin.port in (8081, 8082, 19006)
                and self.headers.get('Host') in ('127.0.0.1:8787', 'localhost:8787'))

    def respond(self, code, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        if self.allowed():
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
            self.send_header('Vary', 'Origin')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        if not self.allowed():
            return self.respond(403, {'error': '不允许的来源'})
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.respond(200 if self.path == '/health' else 404, {'service': 'jizhang-excel-sync'})

    def do_POST(self):
        if not self.allowed():
            return self.respond(403, {'error': '不允许的来源'})
        if self.path != '/records' or self.headers.get('Content-Type') != 'application/json':
            return self.respond(400, {'error': '请求格式不正确'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('请求过大或为空')
            record = json.loads(self.rfile.read(length))
            status = (update_record if record.get('excelOriginal') else append_record)(ROOT / 'history.xlsx', record)
            self.respond(200, {'id': record['id'], 'status': status})
        except (ValueError, KeyError) as error:
            self.respond(400, {'error': str(error)})
        except Exception:
            self.respond(500, {'error': '表格写入失败，请确认文件可写并关闭 Excel/WPS 后重试'})


if __name__ == '__main__':
    print('Excel sync listening on http://127.0.0.1:8787', flush=True)
    HTTPServer(('127.0.0.1', 8787), Handler).serve_forever()
