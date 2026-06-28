from __future__ import annotations
import json
from sqlalchemy.orm import Session
from app import models


def audit(db: Session, set_id: int | None, action: str, actor: str, **details):
    db.add(models.AuditLog(
        set_id=set_id,
        action=action,
        actor=actor,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
    ))
