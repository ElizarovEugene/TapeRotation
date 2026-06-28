"""
Commvault — экспорт отчёта по носителям.

Источник: CommCell Console → Reports → Media → экспорт в CSV/Excel.

Ожидаемые колонки (без учёта регистра):
  Штрихкод / метка : Barcode, Media Label, Label, Name, Volume
  Группа / набор   : Media Group, Storage Policy, Pool, Group, Set
  Дата записи      : Start Time, Data Written, Write Date, Last Write
  Дата истечения   : Expiration Date, Expiration, Retain Until, Expires
  Статус           : Status, Media Status
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['barcode', 'media label', 'label', 'name', 'volume']
_GROUP   = ['media group', 'storage policy', 'pool', 'group', 'set', 'media set']
_SENT    = ['start time', 'data written', 'write date', 'last write', 'written']
_EXPIRES = ['expiration date', 'expiration', 'retain until', 'expires', 'expiry']
_STATUS  = ['status', 'media status']


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    group_col   = find_col(rows[0], _GROUP)
    sent_col    = find_col(rows[0], _SENT)
    expires_col = find_col(rows[0], _EXPIRES)
    status_col  = find_col(rows[0], _STATUS)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка со штрихкодом / меткой носителя.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    sets: dict[str, ParsedSet] = {}
    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a'):
            continue

        group = (row.get(group_col, '') if group_col else '').strip() or ''

        tape_status = 'written'
        if status_col:
            if row.get(status_col, '').lower() in ('scratch', 'blank', 'free', 'empty'):
                tape_status = 'blank'

        if group not in sets:
            sets[group] = ParsedSet(
                name=group,
                recording_date=parse_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[group].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного носителя в файле")

    return list(sets.values())
