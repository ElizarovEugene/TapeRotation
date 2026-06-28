from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models, schemas
from app.security import get_current_user

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[schemas.TapeSearchResult])
def search_tapes(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    like = f"%{q}%"
    tapes = (
        db.query(models.Tape)
        .options(joinedload(models.Tape.tape_set))
        .outerjoin(models.TapeSet, models.Tape.set_id == models.TapeSet.id)
        .filter(or_(
            models.Tape.label.ilike(like),
            models.Tape.notes.ilike(like),
            models.TapeSet.notes.ilike(like),
        ))
        .order_by(models.Tape.label)
        .limit(limit)
        .all()
    )
    return [
        schemas.TapeSearchResult(
            tape_id=t.id,
            tape_label=t.label,
            tape_lto_version=t.lto_version,
            tape_status=t.status,
            set_id=t.set_id,
            set_name=t.tape_set.name if t.tape_set else None,
            set_status=t.tape_set.status if t.tape_set else None,
            recording_date=t.tape_set.recording_date if t.tape_set else None,
            expires_at=t.tape_set.expires_at if t.tape_set else None,
        )
        for t in tapes
    ]
