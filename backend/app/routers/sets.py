from __future__ import annotations
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models, schemas
from app.config import settings
from app.security import get_current_user, require_write
from app.routers._shared import audit as _audit

router = APIRouter(prefix="/sets", tags=["sets"], dependencies=[Depends(get_current_user)])


def _compute_expires(recording_date: date | None, retention_days: int, retention_forever: bool = False) -> date | None:
    if retention_forever or recording_date is None:
        return None
    return recording_date + timedelta(days=retention_days)


def _auto_status(expires_at: date | None, current_status: models.SetStatus, retention_forever: bool = False) -> models.SetStatus:
    if current_status == models.SetStatus.returned:
        return models.SetStatus.returned
    if retention_forever:
        return models.SetStatus.in_storage
    if expires_at and expires_at < date.today():
        return models.SetStatus.expired
    return models.SetStatus.in_storage


def _set_query(db: Session):
    return db.query(models.TapeSet).options(
        joinedload(models.TapeSet.tapes),
        joinedload(models.TapeSet.location),
    )


@router.get("/", response_model=list[schemas.TapeSetOut])
def list_sets(
    status: models.SetStatus | None = None,
    location_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = _set_query(db)
    if status:
        q = q.filter(models.TapeSet.status == status)
    if location_id:
        q = q.filter(models.TapeSet.location_id == location_id)
    return q.order_by(models.TapeSet.name).all()


@router.get("/expired", response_model=list[schemas.TapeSetOut])
def list_expired(db: Session = Depends(get_db)):
    today = date.today()
    return (
        _set_query(db)
        .filter(models.TapeSet.expires_at <= today, models.TapeSet.status != models.SetStatus.returned)
        .order_by(models.TapeSet.expires_at)
        .all()
    )


@router.get("/expiring", response_model=list[schemas.TapeSetOut])
def list_expiring(days: int = Query(default=7, ge=1), db: Session = Depends(get_db)):
    today = date.today()
    deadline = today + timedelta(days=days)
    return (
        _set_query(db)
        .filter(models.TapeSet.expires_at > today, models.TapeSet.expires_at <= deadline,
                models.TapeSet.status == models.SetStatus.in_storage)
        .order_by(models.TapeSet.expires_at)
        .all()
    )


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    today = date.today()
    deadline = today + timedelta(days=settings.notify_days_before)
    total = db.query(models.TapeSet).count()
    in_storage = db.query(models.TapeSet).filter(models.TapeSet.status == models.SetStatus.in_storage).count()
    expired = db.query(models.TapeSet).filter(models.TapeSet.status == models.SetStatus.expired).count()
    returned = db.query(models.TapeSet).filter(models.TapeSet.status == models.SetStatus.returned).count()
    expiring_soon = (
        db.query(models.TapeSet)
        .filter(models.TapeSet.expires_at > today, models.TapeSet.expires_at <= deadline,
                models.TapeSet.status == models.SetStatus.in_storage)
        .count()
    )
    return schemas.StatsOut(total_sets=total, in_storage=in_storage, expired=expired,
                            returned=returned, expiring_soon=expiring_soon)



_SET_PAGE_HISTORY_ACTIONS = ('set_created', 'set_moved', 'imported', 'set_returned', 'recording_date_set')


@router.get("/{set_id}/history", response_model=list[schemas.AuditLogOut])
def get_history(set_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.set_id == set_id,
                models.AuditLog.action.in_(_SET_PAGE_HISTORY_ACTIONS))
        .order_by(models.AuditLog.created_at.desc())
        .all()
    )


@router.get("/{set_id}", response_model=schemas.TapeSetOut)
def get_set(set_id: int, db: Session = Depends(get_db)):
    ts = _set_query(db).filter(models.TapeSet.id == set_id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="TapeSet not found")
    return ts


@router.post("/", response_model=schemas.TapeSetOut, status_code=201)
def create_set(data: schemas.TapeSetCreate, db: Session = Depends(get_db),
               actor: models.User = Depends(require_write)):
    payload = data.model_dump()
    retention_forever = payload.get("retention_forever", False)
    expires_at = _compute_expires(payload.get("recording_date"), payload.get("retention_days", 365), retention_forever)
    ts = models.TapeSet(**payload, expires_at=expires_at)
    ts.status = _auto_status(expires_at, ts.status, retention_forever)
    db.add(ts)
    db.flush()
    _audit(db, ts.id, 'set_created', actor.username, name=ts.name)
    if ts.recording_date is not None:
        _audit(db, ts.id, 'recording_date_set', actor.username, recording_date=ts.recording_date)
    db.commit()
    db.refresh(ts)
    return ts


@router.put("/{set_id}", response_model=schemas.TapeSetOut)
def update_set(set_id: int, data: schemas.TapeSetUpdate, db: Session = Depends(get_db),
               actor: models.User = Depends(require_write)):
    ts = db.get(models.TapeSet, set_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TapeSet not found")
    payload = data.model_dump()
    old_location_id = ts.location_id
    changed = [k for k, v in payload.items() if getattr(ts, k, None) != v]
    for k, v in payload.items():
        setattr(ts, k, v)
    ts.expires_at = _compute_expires(ts.recording_date, ts.retention_days, ts.retention_forever)
    ts.status = _auto_status(ts.expires_at, ts.status, ts.retention_forever)
    generic_changed = [k for k in changed if k not in ('location_id', 'recording_date')]
    if generic_changed:
        _audit(db, ts.id, 'set_updated', actor.username, changed=generic_changed)
    if 'recording_date' in changed and ts.recording_date is not None:
        _audit(db, ts.id, 'recording_date_set', actor.username, recording_date=ts.recording_date)
    if ts.location_id != old_location_id:
        old_location = db.get(models.Location, old_location_id) if old_location_id else None
        new_location = db.get(models.Location, ts.location_id) if ts.location_id else None
        _audit(db, ts.id, 'set_moved', actor.username,
               from_location=old_location.name if old_location else None,
               to_location=new_location.name if new_location else None)
    db.commit()
    db.refresh(ts)
    return ts


@router.patch("/{set_id}/return", response_model=schemas.TapeSetOut)
def mark_returned(set_id: int, db: Session = Depends(get_db),
                  actor: models.User = Depends(require_write)):
    ts = db.get(models.TapeSet, set_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TapeSet not found")
    ts.status = models.SetStatus.returned
    _audit(db, ts.id, 'set_returned', actor.username)
    db.commit()
    db.refresh(ts)
    return ts


@router.delete("/{set_id}", status_code=204)
def delete_set(set_id: int, db: Session = Depends(get_db),
               actor: models.User = Depends(require_write)):
    ts = db.get(models.TapeSet, set_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TapeSet not found")
    _audit(db, ts.id, 'set_deleted', actor.username, name=ts.name)
    db.commit()
    db.delete(ts)
    db.commit()
