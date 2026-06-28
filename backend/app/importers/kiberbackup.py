"""
Кибербекап (Киберпротект) — CSV-выгрузка скриптом scrape_web_tapes.py.
https://github.com/Kenny856/Cyber_Backup_Tape_Export

Разделитель: точка с запятой (`;`), кодировка: UTF-8 BOM.

Ожидаемые колонки:
  barcode   — метка ленты (штрихкод)
  poolName  — название пула (имя набора)
  state     — статус: Free → blank, остальные → written
  tapeSet   — набор резервных копий (используется как примечание)
"""

from .base import ParsedSet, ParsedTape, ImportError, read_file, find_col

_LABEL    = ['barcode', 'label', 'метка', 'штрихкод']
_POOL     = ['poolname', 'pool_name', 'pool', 'пул']
_STATE    = ['state', 'статус', 'status']
_TAPESET  = ['tapeset', 'tape_set', 'набор']

_FREE_STATES = {'free', 'empty', 'blank', 'scratch', 'свободен', 'пустой', 'чистый'}


def parse(filename: str, content: bytes) -> list[ParsedSet]:
    rows = read_file(filename, content)
    if not rows:
        raise ImportError("Файл пустой или не удалось прочитать")

    label_col   = find_col(rows[0], _LABEL)
    pool_col    = find_col(rows[0], _POOL)
    state_col   = find_col(rows[0], _STATE)
    tapeset_col = find_col(rows[0], _TAPESET)

    if not label_col:
        raise ImportError(
            f"Не найдена колонка со штрихкодом ленты.\n"
            f"Ожидается одна из: {', '.join(_LABEL)}.\n"
            f"В файле: {', '.join(rows[0].keys())}"
        )

    sets: dict[str, ParsedSet] = {}
    for row in rows:
        label = row.get(label_col, '').strip()
        if not label or label.lower() in ('none', 'null', '-', 'n/a', ''):
            continue

        pool = (row.get(pool_col, '') if pool_col else '').strip() or 'Без пула'

        state_val = (row.get(state_col, '') if state_col else '').lower().strip()
        tape_status = 'blank' if state_val in _FREE_STATES else 'written'

        notes = (row.get(tapeset_col, '') if tapeset_col else '').strip() or None

        if pool not in sets:
            sets[pool] = ParsedSet(name=pool, notes=notes)

        sets[pool].tapes.append(ParsedTape(label=label, status=tape_status))

    if not sets:
        raise ImportError("Не найдено ни одного носителя в файле")

    return list(sets.values())
