from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# Cat schemas
class CatBase(BaseModel):
    name: str
    breed: str
    birthday: datetime
    gender: str
    is_neutered: bool = False
    photo_path: Optional[str] = None
    target_weight_min: Optional[float] = None
    target_weight_max: Optional[float] = None

class CatCreate(CatBase):
    pass

class CatResponse(CatBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# WeightLog schemas
class WeightLogBase(BaseModel):
    date: datetime
    value: float
    note: Optional[str] = None

class WeightLogCreate(WeightLogBase):
    pass

class WeightLogResponse(WeightLogBase):
    id: str
    cat_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# HealthRecord schemas
class HealthRecordBase(BaseModel):
    date: datetime
    type: str
    title: str
    note: Optional[str] = None
    ai_summary: Optional[str] = None
    actionable_advice: Optional[List[str]] = None

class HealthRecordCreate(HealthRecordBase):
    cat_id: str

class HealthRecordResponse(HealthRecordBase):
    id: str
    cat_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# HealthIndicator schemas
class HealthIndicatorBase(BaseModel):
    name: str
    display_name: str
    value: Optional[float] = None
    unit: str
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    is_abnormal: bool = False
    explanation: Optional[str] = None

class HealthIndicatorCreate(HealthIndicatorBase):
    pass

class HealthIndicatorResponse(HealthIndicatorBase):
    id: str
    record_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Reminder schemas
class ReminderBase(BaseModel):
    title: str
    description: Optional[str] = None
    reminder_type: str
    due_date: datetime
    is_completed: bool = False

class ReminderCreate(ReminderBase):
    cat_id: Optional[str] = None

class ReminderResponse(ReminderBase):
    id: str
    cat_id: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ReportAttachment schemas
class ReportAttachmentBase(BaseModel):
    file_name: str
    file_type: str
    mime_type: str = ""
    file_size: Optional[int] = None

class ReportAttachmentCreate(ReportAttachmentBase):
    cat_id: str

class ReportAttachmentResponse(ReportAttachmentBase):
    id: str
    cat_id: str
    file_path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Dashboard summary schema
class DashboardSummary(BaseModel):
    cat_id: str
    cat_name: str
    latest_weight: Optional[float]
    weight_trend: List[WeightLogResponse]
    upcoming_reminders: List[ReminderResponse]
    recent_records: List[HealthRecordResponse]