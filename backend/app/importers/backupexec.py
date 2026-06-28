"""
Veritas Backup Exec — экспорт носителей.

Источники:
  1. Консоль → Storage → Media Vault → Export to CSV
  2. BEMCLI (PowerShell):
       Get-BEMedia | Select Label,MediaSet,LastWrittenDate,ExpirationDate,Status |
         Export-Csv -Encoding UTF8 media.csv

Ожидаемые колонки (без учёта регистра):
  Метка      : Label, Media Label, Barcode, Name
  Набор      : Media Set, Set, MediaSet, Pool
  Дата записи: Last Written Date, Last Written, Date Last Written, LastWrittenDate
  Истекает   : Expiration Date, Expiration, Overwrite Protected Until, ExpirationDate
  Статус     : Status, Media Status
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL   = ['label', 'media label', 'barcode', 'name']
_SET     = ['media set', 'mediaset', 'set', 'pool', 'set name']
_SENT    = ['last written date', 'last written', 'date last written', 'lastwrittendate', 'write date']
_EXPIRES = ['expiration date', 'expirationdate', 'expiration', 'overwrite protected until', 'retain until']
_STATUS  = ['status', 'media status']

# Recyclable/Overwritable = фактически свободен для перезаписи, но обычно содержит данные
_BLANK_STATUSES = {'scratch', 'blank', 'empty', 'available', 'unformatted'}


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    set_col     = find_col(rows[0], _SET)
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

        set_name = (row.get(set_col, '') if set_col else '').strip() or ''

        tape_status = 'written'
        if status_col and row.get(status_col, '').lower().strip() in _BLANK_STATUSES:
            tape_status = 'blank'

        if set_name not in sets:
            sets[set_name] = ParsedSet(
                name=set_name,
                recording_date=parse_date(row.get(sent_col, '') if sent_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[set_name].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного носителя в файле")

    return list(sets.values())
