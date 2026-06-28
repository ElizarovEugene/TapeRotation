"""
Vinchin Backup & Recovery — экспорт носителей.

Источник: веб-консоль → Tape Library → Media → Export CSV/Excel.

Ожидаемые колонки (без учёта регистра):
  Метка      : Tape Barcode, Barcode, Tape ID, Label, Media Label, Name
  Пул        : Pool, Tape Pool, Media Pool, Pool Name, Group
  Дата записи: Last Write Time, Last Backup Time, Write Date, Backup Date, Date Written
  Истекает   : Expiry Date, Expiration Date, Retention Date, Expires, Valid Until
  Статус     : Status, Tape Status, Media Status
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['tape barcode', 'barcode', 'tape id', 'label', 'media label', 'name']
_POOL    = ['pool', 'tape pool', 'media pool', 'pool name', 'group']
_SENT    = ['last write time', 'last backup time', 'write date', 'backup date', 'date written']
_EXPIRES = ['expiry date', 'expiration date', 'retention date', 'expires', 'valid until']
_STATUS  = ['status', 'tape status', 'media status']

_BLANK_STATUSES = {'empty', 'blank', 'free', 'scratch', 'unused', 'available'}


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
