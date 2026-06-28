"""
Dell EMC NetWorker — экспорт носителей.

Источники:
  1. mminfo с выводом в CSV:
       mminfo -r "volume,pool,created,expires,capacity,used,volretent" \\
              -q "volume=*" -xc > media.csv
  2. NMC (NetWorker Management Console) → Reports → Media → Export

Ожидаемые колонки (без учёта регистра):
  Метка      : volume, Volume Name, Name, Label, Barcode
  Пул        : pool, Pool Name, Group
  Дата записи: created, Creation Date, Write Date, Date Written
  Истекает   : expires, Expiration, Expiration Date, volretent, Retention Date
  Статус     : volume flags, Flags, Status, recyclable
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['volume', 'volume name', 'name', 'label', 'barcode']
_POOL    = ['pool', 'pool name', 'group']
_SENT    = ['created', 'creation date', 'write date', 'date written']
_EXPIRES = ['expires', 'expiration', 'expiration date', 'volretent', 'retention date', 'retain until']
_STATUS  = ['volume flags', 'flags', 'status', 'recyclable', 'vol flags']

_BLANK_FLAGS = {'recyclable', 'full recyclable', 'scratch', 'manual recyclable', 'appendable recyclable'}


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
            f"Не найдена колонка с именем тома.\n"
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
        if status_col and row.get(status_col, '').lower().strip() in _BLANK_FLAGS:
            tape_status = 'blank'

        if pool not in sets:
            sets[pool] = ParsedSet(
                name=pool,
                recording_date=parse_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[pool].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного тома в файле")

    return list(sets.values())
