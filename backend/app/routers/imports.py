from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.security import require_write
from app.importers import veeam, bareos, tsm, commvault, netbackup, acronis, kiberbackup, backupexec, dataprotector, networker, vinchin
from app.importers.base import ImportError as ParseError, guess_lto_version, guess_date_from_text
from app.routers._shared import audit as _audit

router = APIRouter(prefix="/import", tags=["import"])

_PARSERS = {
    'veeam':          veeam.parse,
    'bareos':         bareos.parse,
    'tsm':            tsm.parse,
    'commvault':      commvault.parse,
    'netbackup':      netbackup.parse,
    'acronis':        acronis.parse,
    'kiberbackup':    kiberbackup.parse,
    'backupexec':     backupexec.parse,
    'dataprotector':  dataprotector.parse,
    'networker':      networker.parse,
    'vinchin':        vinchin.parse,
}


@router.post("/preview", response_model=schemas.ImportPreviewOut, dependencies=[Depends(require_write)])
async def preview(
    format: str = Form(...),
    file: UploadFile = File(...),
):
    parser = _PARSERS.get(format)
    if not parser:
        raise HTTPException(status_code=400, detail=f"Неизвестный формат: {format}")

    content = await file.read()
    try:
        parsed_sets = parser(file.filename or 'file.csv', content)
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e))

    warnings: list[str] = []
    sets: list[schemas.ImportedSet] = []
    for ps in parsed_sets:
        if not ps.tapes:
            warnings.append(f"Набор «{ps.name}» не содержит лент и будет пропущен")
            continue
        sets.append(schemas.ImportedSet(
            name=ps.name,
            tapes=[schemas.ImportedTape(
                label=t.label,
                status=t.status,
                lto_version=t.lto_version or guess_lto_version(t.label),
            ) for t in ps.tapes],
            recording_date=ps.recording_date or guess_date_from_text(ps.name),
            expires_at=ps.expires_at,
            notes=ps.notes,
        ))

    return schemas.ImportPreviewOut(sets=sets, warnings=warnings)


@router.post("/execute", response_model=schemas.ImportResultOut)
def execute(data: schemas.ImportExecuteIn, db: Session = Depends(get_db),
            actor: models.User = Depends(require_write)):
    created_sets = 0
    created_tapes = 0
    updated_sets = 0

    for s in data.sets:
        target_set: models.TapeSet | None = None

        if data.on_duplicate == 'merge_by_tapes':
            incoming_labels = {t.label for t in s.tapes}
            best_set = None
            best_overlap = 0
            for ts in db.query(models.TapeSet).all():
                existing = {t.label for t in ts.tapes}
                overlap = len(incoming_labels & existing)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_set = ts
            if best_set and best_overlap / max(len(incoming_labels), 1) >= 0.3:
                target_set = best_set
                updated_sets += 1

        if target_set is None:
            if s.retention_forever:
                retention_days = s.retention_days or 365
                expires_at = None
                status = models.SetStatus.in_storage
            else:
                retention_days, expires_at = _resolve_retention(s.recording_date, s.expires_at)
                if s.retention_days is not None:
                    retention_days = s.retention_days
                if expires_at is None and s.recording_date is not None:
                    expires_at = s.recording_date + timedelta(days=retention_days)
                status = _auto_status(expires_at)
            target_set = models.TapeSet(
                name=s.name,
                description=s.description,
                location_id=data.location_id,
                sent_date=s.sent_date,
                recording_date=s.recording_date,
                retention_days=retention_days,
                retention_forever=s.retention_forever,
                expires_at=expires_at,
                status=status,
                notes=s.notes,
            )
            db.add(target_set)
            db.flush()
            created_sets += 1
            if target_set.recording_date is not None:
                _audit(db, target_set.id, 'recording_date_set', actor.username,
                       recording_date=target_set.recording_date)

        existing_labels = {t.label for t in db.query(models.Tape).filter(models.Tape.set_id == target_set.id).all()}
        set_tapes_added = 0
        for t in s.tapes:
            if t.label in existing_labels:
                continue
            db.add(models.Tape(
                label=t.label,
                set_id=target_set.id,
                status=models.TapeStatus(t.status) if t.status in ('written', 'blank') else models.TapeStatus.written,
                lto_version=t.lto_version or None,
            ))
            created_tapes += 1
            set_tapes_added += 1

        _audit(db, target_set.id, 'imported', actor.username,
               tape_count=set_tapes_added, format=data.on_duplicate,
               recording_date=s.recording_date)

    db.commit()
    return schemas.ImportResultOut(
        created_sets=created_sets,
        created_tapes=created_tapes,
        updated_sets=updated_sets,
    )


def _resolve_retention(recording_date: date | None, expires_at: date | None) -> tuple[int, date | None]:
    if recording_date and expires_at:
        days = max(1, (expires_at - recording_date).days)
        return days, expires_at
    if expires_at:
        today = date.today()
        days = max(1, (expires_at - today).days)
        return days, expires_at
    return 365, None


def _auto_status(expires_at: date | None) -> models.SetStatus:
    if expires_at and expires_at < date.today():
        return models.SetStatus.expired
    return models.SetStatus.in_storage
