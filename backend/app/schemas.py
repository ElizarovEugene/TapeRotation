from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel
from app.models import SetStatus, TapeStatus, UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    is_active: bool
    language: str = 'ru'
    created_at: datetime
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user
    language: str = 'ru'


class UserUpdate(BaseModel):
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    language: str | None = None


class LocationBase(BaseModel):
    name: str
    address: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(LocationBase):
    pass


class LocationOut(LocationBase):
    id: int
    model_config = {"from_attributes": True}


class TapeBase(BaseModel):
    label: str
    set_id: int | None = None
    status: TapeStatus = TapeStatus.written
    lto_version: str | None = None
    notes: str | None = None


class TapeCreate(TapeBase):
    pass


class TapeUpdate(TapeBase):
    pass


class TapeOut(TapeBase):
    id: int
    model_config = {"from_attributes": True}


class TapeSetBase(BaseModel):
    name: str
    description: str | None = None
    location_id: int | None = None
    sent_date: date | None = None
    recording_date: date | None = None
    retention_days: int = 365
    retention_forever: bool = False
    status: SetStatus = SetStatus.in_storage
    notes: str | None = None


class TapeSetCreate(TapeSetBase):
    pass


class TapeSetUpdate(TapeSetBase):
    pass


class TapeSetOut(TapeSetBase):
    id: int
    retention_forever: bool
    recording_date: date | None
    expires_at: date | None
    created_at: datetime
    tapes: list[TapeOut] = []
    location: LocationOut | None = None
    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total_sets: int
    in_storage: int
    expired: int
    returned: int
    expiring_soon: int


class ImportedTape(BaseModel):
    label: str
    status: str = 'written'
    lto_version: str | None = None


class ImportedSet(BaseModel):
    name: str
    tapes: list[ImportedTape]
    description: str | None = None
    sent_date: date | None = None
    recording_date: date | None = None
    retention_days: int | None = None
    retention_forever: bool = False
    expires_at: date | None = None
    notes: str | None = None


class ImportPreviewOut(BaseModel):
    sets: list[ImportedSet]
    warnings: list[str] = []


class ImportExecuteIn(BaseModel):
    sets: list[ImportedSet]
    location_id: int | None = None
    on_duplicate: str = 'create_new'  # create_new | merge_by_tapes


class ImportResultOut(BaseModel):
    created_sets: int
    created_tapes: int
    updated_sets: int


class AuditLogOut(BaseModel):
    id: int
    set_id: int | None
    action: str
    actor: str | None
    details: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class AuditLogFullOut(BaseModel):
    id: int
    set_id: int | None
    set_name: str | None
    action: str
    actor: str | None
    details: str | None
    created_at: datetime


class TapeSearchResult(BaseModel):
    tape_id: int
    tape_label: str
    tape_lto_version: str | None
    tape_status: TapeStatus
    set_id: int | None
    set_name: str | None
    set_status: SetStatus | None
    recording_date: date | None
    expires_at: date | None
