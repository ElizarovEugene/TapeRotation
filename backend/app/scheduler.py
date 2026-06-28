from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.services.email import notify_expired, notify_expiring_soon

scheduler = BackgroundScheduler()


def _daily_check():
    db = SessionLocal()
    try:
        notify_expired(db)
        notify_expiring_soon(db)
    finally:
        db.close()


def start():
    scheduler.add_job(_daily_check, "cron", hour=8, minute=0, id="daily_check", replace_existing=True)
    scheduler.start()


def stop():
    scheduler.shutdown()
