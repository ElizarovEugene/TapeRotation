from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database import Base



class UserRole(str, enum.Enum):
    readonly = "readonly"
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    language: Mapped[str] = mapped_column(String(5), default='ru')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SetStatus(str, enum.Enum):
    in_storage = "in_storage"
    expired = "expired"
    returned = "returned"


class TapeStatus(str, enum.Enum):
    blank = "blank"
    written = "written"


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)

    sets: Mapped[list["TapeSet"]] = relationship("TapeSet", back_populates="location")


class TapeSet(Base):
    __tablename__ = "tape_sets"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    sent_date: Mapped[date | None] = mapped_column(Date)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    retention_forever: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[SetStatus] = mapped_column(
        Enum(SetStatus), default=SetStatus.in_storage, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    recording_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    location: Mapped["Location | None"] = relationship("Location", back_populates="sets")
    tapes: Mapped[list["Tape"]] = relationship("Tape", back_populates="tape_set", cascade="all, delete-orphan")


class Tape(Base):
    __tablename__ = "tapes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    set_id: Mapped[int | None] = mapped_column(ForeignKey("tape_sets.id"), nullable=True)
    status: Mapped[TapeStatus] = mapped_column(
        Enum(TapeStatus), default=TapeStatus.written, nullable=False
    )
    lto_version: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    tape_set: Mapped["TapeSet | None"] = relationship("TapeSet", back_populates="tapes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    set_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tape_sets.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(50))
    actor: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
