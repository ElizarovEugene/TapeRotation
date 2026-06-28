from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.security import get_current_user, require_write

router = APIRouter(prefix="/locations", tags=["locations"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[schemas.LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return db.query(models.Location).order_by(models.Location.name).all()


@router.get("/{location_id}", response_model=schemas.LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(models.Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.post("/", response_model=schemas.LocationOut, status_code=201, dependencies=[Depends(require_write)])
def create_location(data: schemas.LocationCreate, db: Session = Depends(get_db)):
    loc = models.Location(**data.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.put("/{location_id}", response_model=schemas.LocationOut, dependencies=[Depends(require_write)])
def update_location(location_id: int, data: schemas.LocationUpdate, db: Session = Depends(get_db)):
    loc = db.get(models.Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    for k, v in data.model_dump().items():
        setattr(loc, k, v)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}", status_code=204, dependencies=[Depends(require_write)])
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(models.Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(loc)
    db.commit()
