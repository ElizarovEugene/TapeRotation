"""
Bareos/Bacula — экспорт списка томов.

Поддерживаемые форматы:
  1. Вывод bconsole "list media" (pipe-таблица: | col | col | ...)
  2. CSV/Excel из прямого запроса к каталогу:
       SELECT VolumeName, Pool.Name AS Pool, LastWritten, VolRetention, VolStatus
       FROM Media JOIN Pool ON Media.PoolId = Pool.PoolId;

Ожидаемые колонки (без учёта регистра):
  Имя тома    : VolumeName, Volume Name, Name
  Пул         : Pool, Pool.Name, PoolName, Pool Name
  Дата записи : LastWritten, Last Written, FirstWritten
  Удержание   : VolRetention, Vol Retention, Retention (секунды)
  Статус      : VolStatus, Vol Status, Status
"""

from datetime import timedelta
from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col, parse_date

_LABEL     = ['volumename', 'volume name', 'volname', 'name']
_POOL      = ['pool.name', 'poolname', 'pool name', 'pool']
_WRITTEN   = ['lastwritten', 'last written', 'firstwritten', 'first written']
_RETENTION = ['volretention', 'vol retention', 'retention']
_STATUS    = ['volstatus', 'vol status', 'status']


def _read_pipe_table(content: bytes) -> list[dict]:
    text = content.decode('utf-8-sig')
    headers: list[str] = []
    rows: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('+'):
            continue
        if line.startswith('|'):
            cols = [c.strip() for c in line.strip('|').split('|')]
            if not headers:
                headers = cols
            else:
                if len(cols) >= len(headers):
                    rows.append(dict(zip(headers, cols)))
    return rows


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    # bconsole pipe-table starts with '|' or '+---'
    sample = content[:256].decode('utf-8-sig', errors='ignore').strip()
    rows = _read_pipe_table(content) if (sample.startswith('|') or sample.startswith('+')) else []
    if not rows:
        rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col     = find_col(rows[0], _LABEL)
    pool_col      = find_col(rows[0], _POOL)
    written_col   = find_col(rows[0], _WRITTEN)
    retention_col = find_col(rows[0], _RETENTION)
    status_col    = find_col(rows[0], _STATUS)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка с именем тома.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    # Collect per-pool data: accumulate tapes, track earliest expiry
    pool_data: dict[str, dict] = {}

    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a'):
            continue

        pool = (row.get(pool_col, '') if pool_col else '').strip() or ''

        tape_status = 'written'
        if status_col:
            if row.get(status_col, '').lower() in ('blank', 'scratch', 'purged', 'recycled'):
                tape_status = 'blank'

        recording_date = parse_date(row.get(written_col, '') if written_col else '')
        expires_at = None
        if recording_date and retention_col:
            try:
                secs = int(float(row.get(retention_col, 0)))
                expires_at = recording_date + timedelta(seconds=secs)
            except (ValueError, TypeError):
                pass

        if pool not in pool_data:
            pool_data[pool] = {'tapes': [], 'recording_date': recording_date, 'expires_at': expires_at}
        else:
            # Keep the earliest expiry date so we don't miss an expiring tape
            if expires_at and (pool_data[pool]['expires_at'] is None or expires_at < pool_data[pool]['expires_at']):
                pool_data[pool]['expires_at'] = expires_at

        pool_data[pool]['tapes'].append(ParsedTape(label=label, status=tape_status))

    if not pool_data:
        raise ImportError("Не найдено ни одного тома в файле")

    return [
        ParsedSet(
            name=pool,
            tapes=data['tapes'],
            recording_date=data['recording_date'],
            expires_at=data['expires_at'],
        )
        for pool, data in pool_data.items()
    ]
