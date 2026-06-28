"""
Veritas NetBackup — экспорт списка носителей.

Поддерживаемые форматы:
  1. CSV/Excel из NetBackup OpsCenter (Reports → Media)
  2. Вывод команды bpmedialist (текстовый, с фиксированными колонками или пробелами)

Ожидаемые колонки (без учёта регистра):
  Метка / ID  : Media ID, Media Label, Barcode, Media, Volume, ID
  Пул         : Volume Pool, Pool, Pool Name
  Дата записи : Allocation Date, Alloc Date, First Mount, First Mount Date, Alloc Time
  Истекает    : Expiration Date, Expiration, Expire Date, Expire Time, Expires
  Статус      : Status, Media Status, Frozen

bpmedialist: запустить как «bpmedialist -mlist -l» и сохранить вывод,
или экспортировать через OpsCenter в CSV/Excel.
"""

from datetime import datetime
from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['media id', 'media label', 'barcode', 'media', 'volume', 'id', 'mediaid']
_POOL    = ['volume pool', 'pool name', 'pool', 'volumepool']
_SENT    = ['allocation date', 'alloc date', 'first mount date', 'first mount', 'alloc time', 'alloctime']
_EXPIRES = ['expiration date', 'expiration', 'expire date', 'expire time', 'expires', 'expiretime']
_STATUS  = ['status', 'media status', 'frozen']

# Статусы, при которых лента считается незаписанной
_BLANK_STATUSES = {'scratch', 'unassigned', 'available', 'empty', 'blank'}
# Числовые коды NetBackup: 0 = Active/Full, 3 = Scratch/Unassigned
_BLANK_CODES = {'3', '4'}


def _try_parse_unix(s: str):
    """Пробует разобрать Unix timestamp (bpmedialist -mlist выдаёт секунды)."""
    try:
        ts = int(s)
        if ts > 0:
            return datetime.utcfromtimestamp(ts).date()
    except (ValueError, TypeError, OSError):
        pass
    return None


def _smart_date(s: str):
    if not s or not s.strip():
        return None
    s = s.strip()
    d = parse_date(s)
    if d:
        return d
    return _try_parse_unix(s)


def _read_bpmedialist(content: bytes) -> list[dict] | None:
    """
    Разбирает текстовый вывод bpmedialist.
    Ожидаемая структура: строки с пробельным разделением,
    первая непустая не-заголовочная строка — данные.
    Возвращает None если формат не опознан.
    """
    text = content.decode('utf-8-sig', errors='replace')
    lines = [l.rstrip() for l in text.splitlines()]

    # Ищем строку-заголовок: содержит 'media' и ('id' или 'pool')
    header_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if 'media' in low and ('id' in low or 'pool' in low):
            header_idx = i
            break

    if header_idx is None:
        return None

    header_line = lines[header_idx]
    # Пропускаем разделительную линию из дефисов если есть
    data_start = header_idx + 1
    if data_start < len(lines) and set(lines[data_start].strip()) <= {'-', ' '}:
        data_start += 1

    # Определяем позиции колонок по заголовку
    headers = header_line.split()
    if len(headers) < 2:
        return None

    rows = []
    for line in lines[data_start:]:
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        row = {headers[i].lower(): parts[i] for i in range(min(len(headers), len(parts)))}
        rows.append(row)

    return rows if rows else None


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    # Пробуем разобрать как bpmedialist если файл текстовый (не CSV/Excel)
    rows = None
    if not filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        rows = _read_bpmedialist(content)

    if not rows:
        rows = read_file(filename, content)

    # Если всё ещё не получилось — пробуем bpmedialist на любом расширении
    if not rows:
        rows = _read_bpmedialist(content)

    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    pool_col    = find_col(rows[0], _POOL)
    sent_col    = find_col(rows[0], _SENT)
    expires_col = find_col(rows[0], _EXPIRES)
    status_col  = find_col(rows[0], _STATUS)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка с идентификатором носителя.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    sets: dict[str, ParsedSet] = {}
    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a', '---'):
            continue

        pool = (row.get(pool_col, '') if pool_col else '').strip() or ''

        tape_status = 'written'
        if status_col:
            raw = row.get(status_col, '').lower().strip()
            if raw in _BLANK_STATUSES or raw in _BLANK_CODES:
                tape_status = 'blank'

        if pool not in sets:
            sets[pool] = ParsedSet(
                name=pool,
                recording_date=_smart_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=_smart_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[pool].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного носителя в файле")

    return list(sets.values())
