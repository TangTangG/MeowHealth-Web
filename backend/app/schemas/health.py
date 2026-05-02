from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Literal
from app.schemas.schemas import HealthIndicatorResponse, ReportAttachmentResponse

# Enums (str constraints)
ConsultationType = Literal["routine", "symptom", "emergency", "followup"]
TriageLevel = Literal["emergency", "urgent", "routine", "non_urgent"]
TreatmentStatus = Literal["pending", "diagnosed", "treating", "resolved"]
SpiritStatus = Literal["normal", "lethargic", "agitated"]
StoolStatus = Literal["normal", "diarrhea", "constipation", "none"]


# ─── SymptomLog schemas ───

class SymptomLogBase(BaseModel):
    cat_id: str
    record_id: Optional[str] = None
    symptom_description: str
    severity: int  # 1-5
    onset_time: datetime
    duration_hours: Optional[int] = None
    is_ongoing: bool = True
    photo_urls: Optional[List[str]] = None
    triggers: Optional[str] = None


class SymptomLogCreate(BaseModel):
    symptom_description: str
    severity: int
    onset_time: datetime
    duration_hours: Optional[int] = None
    is_ongoing: bool = True
    photo_urls: Optional[List[str]] = None
    triggers: Optional[str] = None


class SymptomLogResponse(SymptomLogBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── VitalSign schemas ───

class VitalSignBase(BaseModel):
    cat_id: str
    record_id: Optional[str] = None
    weight_kg: float
    temperature_celsius: Optional[float] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spirit_status: Optional[str] = None
    appetite_score: Optional[int] = None  # 1-5
    water_intake_ml: Optional[int] = None
    stool_status: Optional[str] = None
    measured_at: datetime


class VitalSignCreate(BaseModel):
    weight_kg: float
    temperature_celsius: Optional[float] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spirit_status: Optional[str] = None
    appetite_score: Optional[int] = None
    water_intake_ml: Optional[int] = None
    stool_status: Optional[str] = None
    measured_at: datetime


class VitalSignResponse(VitalSignBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── HealthRecordWithDetails ───

class HealthRecordWithDetails(BaseModel):
    # Copied from HealthRecordResponse (avoid circular import)
    id: str
    cat_id: str
    date: datetime
    type: str
    title: str
    note: Optional[str] = None
    ai_summary: Optional[str] = None
    actionable_advice: Optional[List[str]] = None

    # New fields
    consultation_type: str
    triage_level: Optional[str] = None
    treatment_status: str
    next_followup_at: Optional[datetime] = None

    symptom_logs: List[SymptomLogResponse] = []
    vital_signs: List[VitalSignResponse] = []
    indicators: List[HealthIndicatorResponse] = []
    attachments: List[ReportAttachmentResponse] = []

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── TreatmentStatusUpdate ───

class TreatmentStatusUpdate(BaseModel):
    treatment_status: str
    next_followup_at: Optional[datetime] = None


# ------------------------------------------------------------------
# 诊疗流水线 Schemas
# ------------------------------------------------------------------
class ConsultationStartRequest(BaseModel):
    """启动诊疗请求"""
    cat_id: str
    initial_symptoms: str


class ConsultationContinueRequest(BaseModel):
    """继续诊疗请求"""
    user_input: dict = Field(default_factory=dict, description="用户对上一轮问题的回答")


class ConsultationResponse(BaseModel):
    """诊疗流程响应"""
    session_id: str
    status: str
    triage_level: Optional[str] = None
    triage_advice: Optional[str] = None
    questions: Optional[list[str]] = None
    is_sufficient: Optional[bool] = None
    next_action: Optional[str] = None
    health_record_id: Optional[str] = None
    diagnosis: Optional[dict] = None
    current_round: Optional[int] = None
    collected_summary: Optional[str] = None
    error: Optional[str] = None


class ConsultationStatusResponse(BaseModel):
    """诊疗状态查询响应"""
    session_id: str
    status: str
    current_round: int
    triage_result: Optional[dict] = None
    collected_summary: Optional[dict] = None
    error: Optional[str] = None
