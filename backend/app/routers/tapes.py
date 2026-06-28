from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.security import get_current_user, require_write
from app.routers._shared import audit as _audit

router = APIRouter(prefix="/tapes", tags=["tapes"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[schemas.TapeOut])
def list_tapes(set_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Tape)
    if set_id is not None:
        q = q.filter(models.Tape.set_id == set_id)
    return q.order_by(models.Tape.label).all()


@router.get("/{tape_id}", response_model=schemas.TapeOut)
def get_tape(tape_id: int, db: Session = Depends(get_db)):
    tape = db.get(models.Tape, tape_id)
    if not tape:
        raise HTTPException(status_code=404, detail="Tape not found")
    return tape


@router.post("/", response_model=schemas.TapeOut, status_code=201)
def create_tape(data: schemas.TapeCreate, db: Session = Depends(get_db),
                actor: models.User = Depends(require_write)):
    tape = models.Tape(**data.model_dump())
    db.add(tape)
    db.flush()
    _audit(db, tape.set_id, 'tape_added', actor.username,
           label=tape.label, lto_version=tape.lto_version)
    db.commit()
    db.refresh(tape)
    return tape


@router.put("/{tape_id}", response_model=schemas.TapeOut)
def update_tape(tape_id: int, data: schemas.TapeUpdate, db: Session = Depends(get_db),
                actor: models.User = Depends(require_write)):
    tape = db.get(models.Tape, tape_id)
    if not tape:
        raise HTTPException(status_code=404, detail="Tape not found")
    old_label = tape.label
    for k, v in data.model_dump().items():
        setattr(tape, k, v)
    _audit(db, tape.set_id, 'tape_updated', actor.username,
           label=tape.label, old_label=old_label, lto_version=tape.lto_version)
    db.commit()
    db.refresh(tape)
    return tape


@router.delete("/{tape_id}", status_code=204)
def delete_tape(tape_id: int, db: Session = Depends(get_db),
                actor: models.User = Depends(require_write)):
    tape = db.get(models.Tape, tape_id)
    if not tape:
        raise HTTPException(status_code=404, detail="Tape not found")
    _audit(db, tape.set_id, 'tape_deleted', actor.username, label=tape.label)
    db.commit()
    db.delete(tape)
    db.commit()
