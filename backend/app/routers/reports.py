from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.models import HealthRecord, HealthIndicator, ReportAttachment, AIChatMessage, Cat, WeightLog
from app.schemas.schemas import ReportCreate, ReportResponse, ChatMessageCreate, ChatMessageResponse
from app.services.ai_service import chat_about_report
from app.ai.orchestrator import MedicalOrchestrator

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/analyze", response_model=ReportResponse)
async def create_report_from_upload(
    cat_id: str,
    file_path: str,
    file_name: str,
    mime_type: str,
    file_size: int,
    db: Session = Depends(get_db)
):
    """分析上传的文件并创建报告"""
    # 组装 cat_profile
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(404, "猫咪档案不存在")

    latest_weight = db.query(WeightLog).filter(WeightLog.cat_id == cat_id).order_by(WeightLog.date.desc()).first()
    current_weight = latest_weight.value if latest_weight else None

    weight_status = "normal"
    if current_weight and cat.target_weight_min and cat.target_weight_max:
        if current_weight > cat.target_weight_max:
            weight_status = "overweight"
        elif current_weight < cat.target_weight_min:
            weight_status = "underweight"

    cat_profile = {
        "breed": cat.breed,
        "weight_status": weight_status,
        "current_weight": current_weight
    }

    orchestrator = MedicalOrchestrator()
    analysis_result = orchestrator.process_report(file_path, mime_type, cat_profile)
    
    if "error" in analysis_result:
        raise HTTPException(400, analysis_result["error"])
    
    record = HealthRecord(
        id=str(uuid.uuid4()),
        cat_id=cat_id,
        date=datetime.now(),
        type="lab_report",
        title=f"化验单分析 - {file_name}",
        ai_summary=analysis_result.get("summary", ""),
        actionable_advice=analysis_result.get("recommendations", [])
    )
    db.add(record)
    
    for indicator_data in analysis_result.get("indicators", []):
        indicator = HealthIndicator(
            id=str(uuid.uuid4()),
            record_id=record.id,
            name=indicator_data.get("name", ""),
            display_name=indicator_data.get("display_name", indicator_data.get("name", "")),
            value=indicator_data.get("value"),
            unit=indicator_data.get("unit", ""),
            reference_min=indicator_data.get("reference_min"),
            reference_max=indicator_data.get("reference_max"),
            is_abnormal=indicator_data.get("is_abnormal", False),
            explanation=indicator_data.get("explanation", "")
        )
        db.add(indicator)
    
    attachment = ReportAttachment(
        id=str(uuid.uuid4()),
        cat_id=cat_id,
        record_id=record.id,
        file_path=file_path,
        file_name=file_name,
        file_type="pdf",
        mime_type=mime_type,
        file_size=file_size
    )
    db.add(attachment)
    
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    record = db.query(HealthRecord).filter(HealthRecord.id == report_id).first()
    if not record:
        raise HTTPException(404, "报告不存在")
    return record


@router.get("/", response_model=List[ReportResponse])
def list_reports(cat_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(HealthRecord).filter(HealthRecord.type == "lab_report")
    if cat_id:
        query = query.filter(HealthRecord.cat_id == cat_id)
    return query.order_by(HealthRecord.date.desc()).all()


@router.post("/{report_id}/chat", response_model=ChatMessageResponse)
def chat_with_report(
    report_id: str,
    message: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(HealthRecord.id == report_id).first()
    if not record:
        raise HTTPException(404, "报告不存在")
    
    chat_history = db.query(AIChatMessage).filter(
        AIChatMessage.record_id == report_id
    ).order_by(AIChatMessage.created_at).all()
    
    history_list = [{"role": msg.role, "content": msg.content} for msg in chat_history]
    
    report_data = {
        "summary": record.ai_summary,
        "indicators": [
            {"name": i.name, "display_name": i.display_name, "is_abnormal": i.is_abnormal}
            for i in record.indicators
        ],
        "recommendations": record.actionable_advice or []
    }
    
    ai_response = chat_about_report(report_data, message.content, history_list)
    
    user_msg = AIChatMessage(
        id=str(uuid.uuid4()),
        record_id=report_id,
        role="user",
        content=message.content,
        model_name="gemini-2.0-flash"
    )
    db.add(user_msg)
    
    ai_msg = AIChatMessage(
        id=str(uuid.uuid4()),
        record_id=report_id,
        role="model",
        content=ai_response,
        model_name="gemini-2.0-flash"
    )
    db.add(ai_msg)
    
    db.commit()
    
    return ai_msg


@router.get("/{report_id}/chat/history", response_model=List[ChatMessageResponse])
def get_chat_history(report_id: str, db: Session = Depends(get_db)):
    messages = db.query(AIChatMessage).filter(
        AIChatMessage.record_id == report_id
    ).order_by(AIChatMessage.created_at).all()
    return messages


@router.delete("/{report_id}")
def delete_report(report_id: str, db: Session = Depends(get_db)):
    """删除报告"""
    record = db.query(HealthRecord).filter(HealthRecord.id == report_id).first()
    if not record:
        raise HTTPException(404, "报告不存在")
    
    # 级联删除关联的 indicators, attachments, chat_messages
    db.query(HealthIndicator).filter(HealthIndicator.record_id == report_id).delete()
    db.query(ReportAttachment).filter(ReportAttachment.record_id == report_id).delete()
    db.query(AIChatMessage).filter(AIChatMessage.record_id == report_id).delete()
    
    db.delete(record)
    db.commit()
    
    return {"message": "Report deleted successfully"}
