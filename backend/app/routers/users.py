from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.security import hash_password, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.User).order_by(models.User.username).all()


@router.post("/", response_model=schemas.UserOut, status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    user = models.User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        language=data.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, data: schemas.UserUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.language is not None:
        user.language = data.language
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
