"""
Acronis Cyber Backup — экспорт носителей.

Источник: Settings → Tapes → выбрать пул.
Официального CSV-экспорта нет; файл может быть получен сторонними средствами
или через другой интерфейс с произвольными именами колонок.

Ожидаемые колонки (без учёта регистра):
  Метка      : Label, Tape Label, Barcode, Volume, Name, Носитель, Метка
  Пул        : Pool, Media Pool, Tape Pool, Пул
  Дата записи: Backup Date, Write Date, Last Backup, Start Date, Created, Дата записи
  Истекает   : Expiry Date, Expiration Date, Retention End, Expires, Срок хранения до
  Статус     : Status, Tape Status, Статус
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['label', 'tape label', 'barcode', 'volume', 'name', 'носитель', 'метка']
_POOL    = ['pool', 'media pool', 'tape pool', 'пул']
_SENT    = ['backup date', 'write date', 'last backup', 'start date', 'created', 'дата записи', 'дата создания']
_EXPIRES = ['expiry date', 'expiration date', 'retention end', 'expires', 'срок хранения до', 'действителен до']
_STATUS  = ['status', 'tape status', 'статус']

_BLANK_STATUSES = {'free', 'empty', 'blank', 'scratch', 'свободен', 'пустой', 'чистый'}


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
