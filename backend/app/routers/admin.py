from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.security import require_admin
from app.services import email as email_svc
from app.config import settings
from app import models, schemas

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/log", response_model=list[schemas.AuditLogFullOut], dependencies=[Depends(require_admin)])
def get_log(db: Session = Depends(get_db), limit: int = Query(default=500, le=2000)):
    rows = (
        db.query(models.AuditLog, models.TapeSet.name)
        .outerjoin(models.TapeSet, models.AuditLog.set_id == models.TapeSet.id)
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.AuditLogFullOut(
            id=log.id,
            set_id=log.set_id,
            set_name=name,
            action=log.action,
            actor=log.actor,
            details=log.details,
            created_at=log.created_at,
        )
        for log, name in rows
    ]


@router.post("/notify/run", dependencies=[Depends(require_admin)])
def run_notify():
    """Принудительный запуск ежедневной проверки и отправки уведомлений."""
    db = SessionLocal()
    try:
        expired = email_svc.notify_expired(db)
        expiring = email_svc.notify_expiring_soon(db)
    finally:
        db.close()
    return {"expired": expired, "expiring_soon": expiring}


@router.post("/notify/test", dependencies=[Depends(require_admin)])
def send_test():
    """Отправить тестовое письмо на NOTIFY_EMAIL."""
    class _FakeSet:
        id = 0
        name = "Тестовый набор LTO-2024"
        location = type("L", (), {"name": "Серверная"})()
        expires_at = "2024-12-31"

    email_svc.send_notification(
        [_FakeSet()],  # type: ignore
        subject="[TapeRotation] Тестовое уведомление",
        heading="Это тестовое письмо",
        intro="",
    )
    return {"to": settings.notify_email, "host": settings.smtp_host}
