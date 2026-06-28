"""
Veeam Backup & Replication — экспорт инвентаря лент из консоли.
Поддерживаемый формат: Tape Library Inventory (CSV/Excel).

Ожидаемые колонки (без учёта регистра):
  Метка ленты : Name, Barcode, Media Label, Label
  Набор       : Media Set, Media Pool, Pool, Set
  Дата записи : Last Write Time, Start Time, Modified, Write Date
  Истекает    : Expiration Date, Expiration, Expires, Retention Date
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['name', 'barcode', 'media label', 'label', 'tape label']
_SET     = ['media set', 'media pool', 'pool', 'set name', 'set']
_EXPIRES = ['expiration date', 'expiration', 'expires', 'expire date', 'retention date']
_SENT    = ['last write time', 'start time', 'modified', 'write date', 'last modified']


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    set_col     = find_col(rows[0], _SET)
    expires_col = find_col(rows[0], _EXPIRES)
    sent_col    = find_col(rows[0], _SENT)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка с меткой ленты.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    sets: dict[str, ParsedSet] = {}
    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a'):
            continue

        set_name = (row.get(set_col, '') if set_col else '').strip() or ''

        if set_name not in sets:
            sets[set_name] = ParsedSet(
                name=set_name,
                recording_date=parse_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[set_name].tapes.append(ParsedTape(label=label))

    if not sets:
        raise ImportError("Не найдено ни одной ленты в файле")

    return list(sets.values())
