from __future__ import annotations
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class ParsedTape:
    label: str
    status: str = 'written'
    lto_version: str | None = None


@dataclass
class ParsedSet:
    name: str
    tapes: list[ParsedTape] = field(default_factory=list)
    recording_date: date | None = None
    expires_at: date | None = None
    notes: str | None = None


class ImportError(Exception):
    pass


_LTO_RE = re.compile(r'(?:LTO|ULTRIUM)[-_\s]?([1-9][0-9]?)', re.IGNORECASE)


def guess_lto_version(label: str) -> str | None:
    if not label:
        return None
    # Explicit pattern anywhere in the label: LTO-7, LTO-10, ULTRIUM-8, etc.
    m = _LTO_RE.search(label)
    if m:
        return f'LTO-{m.group(1)}'
    # Standard LTO barcode suffix: e.g. ABC001L7 (LTO-7), ABC001LA (LTO-10)
    if len(label) >= 2 and label[-2].upper() == 'L':
        ch = label[-1].upper()
        if ch.isdigit() and ch != '0':
            return f'LTO-{ch}'
        if ch == 'A':
            return 'LTO-10'
    return None


_DATE_FORMATS = ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d')


def parse_date(s: str) -> date | None:
    if not s:
        return None
    s = s.strip().split(' ')[0].split('T')[0]
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


_NAME_DATE_PATTERNS = (
    re.compile(r'(?<!\d)(\d{4})[-_.](\d{2})[-_.](\d{2})(?!\d)'),  # 2026-06-19 / 2026_06_19 / 2026.06.19
    re.compile(r'(?<!\d)(\d{2})[-_.](\d{2})[-_.](\d{4})(?!\d)'),  # 19-06-2026 / 19.06.2026
    re.compile(r'(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)'),            # 20260619
)


def guess_date_from_text(text: str) -> date | None:
    if not text:
        return None
    for pat in _NAME_DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        g = m.groups()
        year, month, day = (g[0], g[1], g[2]) if len(g[0]) == 4 else (g[2], g[1], g[0])
        if not (1990 <= int(year) <= 2099):
            continue
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            continue
    return None


def find_col(row: dict, aliases: list[str]) -> str | None:
    lower_keys = {k.lower().strip(): k for k in row}
    for alias in aliases:
        if alias.lower() in lower_keys:
            return lower_keys[alias.lower()]
    return None


def read_file(filename: str, content: bytes) -> list[dict]:
    if filename.lower().endswith(('.xlsx', '.xls')):
        return _read_excel(content)
    return _read_csv(content)


def _read_csv(content: bytes) -> list[dict]:
    text = content.decode('utf-8-sig')
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    lines = text.splitlines()
    header_idx = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        cols = next(csv.reader([line], dialect=dialect))
        if sum(1 for c in cols if c.strip()) >= 2:
            header_idx = i
            break
    reader = csv.DictReader(io.StringIO('\n'.join(lines[header_idx:])), dialect=dialect)
    return [{k.strip(): (v or '').strip() for k, v in row.items() if k} for row in reader]


def _read_excel(content: bytes) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    # Some export tools (e.g. TSM Operations Center) prepend a one-cell
    # title row ("Export Table 'console' / ...") before the real header.
    header_idx = 0
    for i, row in enumerate(rows):
        if sum(1 for v in row if v not in (None, '')) >= 2:
            header_idx = i
            break
    headers = [str(h).strip() if h is not None else f'_col{i}' for i, h in enumerate(rows[header_idx])]
    result = []
    for row in rows[header_idx + 1:]:
        d: dict[str, str] = {}
        for i, v in enumerate(row):
            if i >= len(headers) or not headers[i] or headers[i].startswith('_col'):
                continue
            if hasattr(v, 'strftime'):
                d[headers[i]] = v.strftime('%Y-%m-%d')
            else:
                d[headers[i]] = str(v).strip() if v is not None else ''
        if any(d.values()):
            result.append(d)
    return result
