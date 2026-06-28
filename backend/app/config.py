from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_project_root = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{_project_root}/taperotation.db"
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    notify_email: str = ""
    notify_days_before: int = 7
    cors_origins: str = "http://localhost:5174"
    app_url: str = "http://localhost:5174"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 480
    admin_username: str = "admin"
    admin_password: str = "admin"
    admin_language: str = "en"

    model_config = SettingsConfigDict(env_file=str(_project_root / ".env"))


settings = Settings()
