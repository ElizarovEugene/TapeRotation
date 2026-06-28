from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.routers import locations, tapes, sets, auth, users, imports, search, admin
from app import scheduler
from app.config import settings


def migrate_db():
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE tape_sets ADD COLUMN retention_forever INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN language VARCHAR(5) NOT NULL DEFAULT 'ru'",
        "ALTER TABLE tape_sets ADD COLUMN recording_date DATE",
    ]
    with engine.connect() as conn:
        for stmt in stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass


def migrate_tape_sets_autoincrement():
    """Пересобрать tape_sets с настоящим AUTOINCREMENT, чтобы ID удалённых
    наборов никогда не переиспользовались — иначе история/лог нового набора
    мог унаследовать записи от старого набора с тем же ID."""
    from sqlalchemy import text
    with engine.connect() as check_conn:
        row = check_conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='tape_sets'")
        ).fetchone()
    if row is None or 'AUTOINCREMENT' in row[0].upper():
        return
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(tape_sets)")).fetchall()
        col_names = [c[1] for c in cols]
        col_defs = []
        for _cid, name, ctype, notnull, dflt, pk in cols:
            if pk:
                col_defs.append(f"{name} INTEGER PRIMARY KEY AUTOINCREMENT")
                continue
            parts = [name, ctype or "TEXT"]
            if notnull:
                parts.append("NOT NULL")
            if dflt is not None:
                parts.append(f"DEFAULT {dflt}")
            col_defs.append(" ".join(parts))
        col_defs.append("FOREIGN KEY(location_id) REFERENCES locations (id)")
        conn.execute(text(f"CREATE TABLE tape_sets_new ({', '.join(col_defs)})"))
        cols_csv = ", ".join(col_names)
        conn.execute(text(f"INSERT INTO tape_sets_new ({cols_csv}) SELECT {cols_csv} FROM tape_sets"))
        conn.execute(text("DROP TABLE tape_sets"))
        conn.execute(text("ALTER TABLE tape_sets_new RENAME TO tape_sets"))
        max_id = conn.execute(text(
            "SELECT MAX(v) FROM ("
            "SELECT COALESCE(MAX(id), 0) AS v FROM tape_sets "
            "UNION ALL SELECT COALESCE(MAX(set_id), 0) FROM audit_logs)"
        )).scalar() or 0
        conn.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('tape_sets', 'tape_sets_new')"))
        conn.execute(text("INSERT INTO sqlite_sequence (name, seq) VALUES ('tape_sets', :seq)"), {"seq": max_id})
    print(f"[taperotation] tape_sets переведена на AUTOINCREMENT (seq={max_id})")


def seed_admin():
    from app import models
    from app.security import hash_password
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            admin = models.User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role=models.UserRole.admin,
                language=settings.admin_language,
            )
            db.add(admin)
            db.commit()
            print(f"[taperotation] Создан администратор: {settings.admin_username}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_db()
    migrate_tape_sets_autoincrement()
    seed_admin()
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="TapeRotation", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(locations.router)
app.include_router(tapes.router)
app.include_router(sets.router)
app.include_router(imports.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
