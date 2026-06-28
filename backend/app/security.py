import hashlib
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app import models

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
    return f"pbkdf2$sha256${salt}${h.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    parts = hashed.split('$')
    if len(parts) != 4 or parts[0] != 'pbkdf2':
        return False
    _, algo, salt, stored = parts
    h = hashlib.pbkdf2_hmac(algo, plain.encode(), salt.encode(), 260000)
    return secrets.compare_digest(h.hex(), stored)


def create_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "role": role, "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise exc
    user = db.get(models.User, user_id)
    if not user or not user.is_active:
        raise exc
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")
    return user


def require_write(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role == models.UserRole.readonly:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения данных")
    return user
