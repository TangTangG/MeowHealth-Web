from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import uuid

from app.core.database import get_db
from app.core.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from app.models.models import HealthRecord, HealthIndicator, ReportAttachment, AIChatMessage, Cat, WeightLog
from app.schemas.schemas import ReportCreate, ReportResponse, ChatMessageCreate, ChatMessageResponse
from app.ai.orchestrator import MedicalOrchestrator

router = APIRouter(prefix="/reports", tags=["reports"])

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf"
}


@router.post("/upload/{cat_id}", response_model=ReportResponse)
async def upload_and_analyze(
    cat_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传化验单文件并自动触发 AI 分析"""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"不支持的文件类型: {file.content_type}")
    
    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件大小超过10MB限制")
    
    # Save file
    file_id = str(uuid.uuid4())
    ext = ALLOWED_TYPES[file.content_type]
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Reuse analyze logic
    return await create_report_from_upload(
        cat_id=cat_id,
        file_path=str(file_path),
        file_name=file.filename or "unknown",
        mime_type=file.content_type,
        file_size=len(content),
        db=db
    )


@router.post("/analyze", response_model=ReportResponse)
async def create_report_from_upload(
    cat_id: str,
    file_path: str,
    file_name: str,
    mime_type: str,
    file_size: int,
    db: AsyncSession = Depends(get_db)
):
    """分析上传的文件并创建报告"""
    # 组装 cat_profile
    result = await db.execute(select(Cat).filter(Cat.id == cat_id))
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(404, "猫咪档案不存在")

    result = await db.execute(
        select(WeightLog).filter(WeightLog.cat_id == cat_id).order_by(WeightLog.date.desc())
    )
    latest_weight = result.scalars().first()
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

    # 查询该猫的历史化验记录（最近 5 次）
    history_stmt = (
        select(HealthRecord)
        .filter(HealthRecord.cat_id == cat_id, HealthRecord.type == "lab_report")
        .order_by(HealthRecord.date.desc())
        .limit(5)
    )
    history_result = await db.execute(history_stmt)
    history_records_db = history_result.scalars().all()

    history_records = []
    for rec in history_records_db:
        # Load indicators for each record
        ind_result = await db.execute(
            select(HealthIndicator).filter(HealthIndicator.record_id == rec.id)
        )
        indicators_data = []
        for ind in ind_result.scalars().all():
            indicators_data.append({
                "name": ind.name,
                "display_name": ind.display_name,
                "value": ind.value,
                "unit": ind.unit,
                "is_abnormal": ind.is_abnormal
            })
        history_records.append({
            "date": rec.date.isoformat(),
            "summary": rec.ai_summary,
            "indicators": indicators_data
        })

    orchestrator = MedicalOrchestrator()
    analysis_result = orchestrator.process_report(file_path, mime_type, cat_profile, history_records)
    
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
    
    await db.commit()
    
    # Reload with relationships
    result = await db.execute(
        select(HealthRecord)
        .where(HealthRecord.id == record.id)
        .options(selectinload(HealthRecord.indicators), selectinload(HealthRecord.attachments))
    )
    return result.scalars().first()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.id == report_id)
        .options(selectinload(HealthRecord.indicators), selectinload(HealthRecord.attachments))
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "报告不存在")
    return record


@router.get("/", response_model=List[ReportResponse])
async def list_reports(cat_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(HealthRecord).filter(HealthRecord.type == "lab_report").options(
        selectinload(HealthRecord.indicators), selectinload(HealthRecord.attachments)
    )
    if cat_id:
        stmt = stmt.filter(HealthRecord.cat_id == cat_id)
    result = await db.execute(stmt.order_by(HealthRecord.date.desc()))
    return result.scalars().all()


@router.post("/{report_id}/chat", response_model=ChatMessageResponse)
async def chat_with_report(
    report_id: str,
    message: ChatMessageCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.id == report_id)
        .options(selectinload(HealthRecord.indicators))
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "报告不存在")
    
    result = await db.execute(
        select(AIChatMessage).filter(AIChatMessage.record_id == report_id).order_by(AIChatMessage.created_at)
    )
    chat_history = result.scalars().all()
    
    history_list = [{"role": msg.role, "content": msg.content} for msg in chat_history]
    
    report_data = {
        "summary": record.ai_summary,
        "indicators": [
            {"name": i.name, "display_name": i.display_name, "is_abnormal": i.is_abnormal}
            for i in record.indicators
        ],
        "recommendations": record.actionable_advice or []
    }
    
    orchestrator = MedicalOrchestrator()
    ai_response = orchestrator.chat_about_report(report_data, message.content, history_list)
    
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
    
    await db.commit()
    
    return ai_msg


@router.get("/{report_id}/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AIChatMessage).filter(AIChatMessage.record_id == report_id).order_by(AIChatMessage.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.delete("/{report_id}")
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """删除报告"""
    result = await db.execute(select(HealthRecord).filter(HealthRecord.id == report_id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "报告不存在")
    
    # 级联删除关联的 indicators, attachments, chat_messages
    await db.execute(delete(HealthIndicator).where(HealthIndicator.record_id == report_id))
    await db.execute(delete(ReportAttachment).where(ReportAttachment.record_id == report_id))
    await db.execute(delete(AIChatMessage).where(AIChatMessage.record_id == report_id))
    
    await db.delete(record)
    await db.commit()
    
    return {"message": "Report deleted successfully"}
