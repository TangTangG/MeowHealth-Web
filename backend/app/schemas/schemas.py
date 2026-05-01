from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ReportAttachment schemas
class ReportAttachmentBase(BaseModel):
    file_path: str
    file_name: str
    mime_type: str
    file_size: Optional[int] = None

class ReportAttachmentResponse(ReportAttachmentBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Report schemas
class ReportBase(BaseModel):
    cat_id: str
    title: str
    note: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportResponse(BaseModel):
    id: str
    cat_id: str
    date: datetime
    type: str
    title: str
    note: Optional[str] = None
    ai_summary: Optional[str] = None
    actionable_advice: Optional[List[str]] = None
    indicators: List[HealthIndicatorResponse] = []
    attachments: List[ReportAttachmentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Chat schemas
class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    record_id: Optional[str] = None
    role: str
    content: str
    model_name: Optional[str] = None
    token_usage: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Settings schemas
class ApiKeySetting(BaseModel):
    api_key: str

class ApiKeyStatus(BaseModel):
    is_set: bool
    masked_key: Optional[str] = None

