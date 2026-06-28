"""
IBM Spectrum Protect (TSM) — экспорт отчёта по томам.

Источник: dsmadmc «query volume * f=d» с перенаправлением в файл,
или экспорт из Operations Center в CSV/Excel.

Ожидаемые колонки (без учёта регистра):
  Имя тома       : Volume Name, VolumeName, Volume
  Пул хранения   : Storage Pool Name, Storage Pool, Pool Name, Pool
  Дата записи    : Approx. Date Last Written, Last Use Date, Last Use, Last Access, Last Write
  Дата истечения : Expiration Date, Expiration, Expires
  Статус         : Status, Volume Status, Vol Status
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL     = ['volume name', 'volumename', 'volume', 'name']
_POOL      = ['storage pool name', 'storage pool', 'pool name', 'pool']
_RECORDING = ['approx. date last written', 'date last written', 'last use date', 'last use', 'last access', 'last write', 'lastuse']
_EXPIRES   = ['expiration date', 'expiration', 'expires', 'expiry date']
_STATUS    = ['status', 'volume status', 'vol status', 'access']


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col      = find_col(rows[0], _LABEL)
    pool_col       = find_col(rows[0], _POOL)
    recording_col  = find_col(rows[0], _RECORDING)
    expires_col    = find_col(rows[0], _EXPIRES)
    status_col     = find_col(rows[0], _STATUS)

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
        if status_col:
            if row.get(status_col, '').lower() in ('scratch', 'empty', 'blank'):
                tape_status = 'blank'

        if pool not in sets:
            sets[pool] = ParsedSet(
                name=pool,
                recording_date=parse_date(row.get(recording_col, '') if recording_col else ''),
                expires_at=parse_date(row.get(expires_col, '') if expires_col else ''),
            )

        sets[pool].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного тома в файле")

    return list(sets.values())
