"""
Micro Focus / OpenText Data Protector — экспорт носителей.

Источники:
  1. Встроенный CSV: omnimedium -list -csv > media.csv
  2. GUI: Media Management → Export

Формат omnimedium -list -csv:
  "Label";"Pool";"Location";"Created";"Valid Until";"Status";"Media ID"

Ожидаемые колонки (без учёта регистра):
  Метка      : Label, Medium Label, Media Label, Barcode, Name
  Пул        : Pool, Pool Name
  Локация    : Location (игнорируется, не нужна)
  Дата записи: Created, Creation Time, Write Date
  Истекает   : Valid Until, Expiration, Expiration Date, Expires
  Статус     : Status, Medium Status, Condition
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['label', 'medium label', 'media label', 'barcode', 'name']
_POOL    = ['pool', 'pool name']
_SENT    = ['created', 'creation time', 'write date', 'creation date']
_EXPIRES = ['valid until', 'expiration', 'expiration date', 'expires', 'expiry']
_STATUS  = ['status', 'medium status', 'condition']

_BLANK_STATUSES = {'blank', 'scratch', 'free', 'unformatted', 'poor'}


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    pool_col    = find_col(rows[0], _POOL)
    sent_col    = find_col(rows[0], _SENT)
    expires_col = find_col(rows[0], _EXPIRES)
    status_col  = find_col(rows[0], _STATUS)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка с меткой носителя.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    sets: dict[str, ParsedSet] = {}
    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a'):
            continue

        pool = (row.get(pool_col, '') if pool_col else '').strip() or ''

        tape_status = 'written'
        if status_col and row.get(status_col, '').lower().strip() in _BLANK_STATUSES:
            tape_status = 'blank'

        if pool not in sets:
            sets[pool] = ParsedSet(
                name=pool,
                recording_date=parse_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[pool].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного носителя в файле")

    return list(sets.values())
