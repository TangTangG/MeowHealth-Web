from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import shutil
import uuid

from app.core.database import get_db
from app.core.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.models.models import ReportAttachment, HealthRecord, HealthIndicator
from app.schemas.schemas import ReportAttachmentResponse

from app.services.ai_service import analyze_report
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])


from app.core.config import set_gemini_api_key, get_gemini_api_key
from pydantic import BaseModel

class ApiKeyRequest(BaseModel):
    api_key: str

@router.post("/settings/api-key")
def set_api_key(request: ApiKeyRequest):
    """设置 Gemini API Key"""
    if not request.api_key or len(request.api_key) < 10:
        raise HTTPException(400, detail="无效的 API Key")
    set_gemini_api_key(request.api_key)
    return {"message": "API Key 设置成功"}

@router.get("/settings/api-key/status")
def get_api_key_status():
    """检查 API Key 是否已设置"""
    key = get_gemini_api_key()
    return {"configured": bool(key), "masked": key[:4] + "****" if key else None}


@router.post("/{report_id}/analyze")
def analyze_report_endpoint(
    report_id: str,
    db: Session = Depends(get_db)
):
    """分析化验单"""
    report = db.query(ReportAttachment).filter(ReportAttachment.id == report_id).first()
    if not report:
        raise HTTPException(404, detail="Report not found")
    
    # 调用 AI 分析
    result = analyze_report(report.file_path, report.file_type)
    
    if "error" in result:
        raise HTTPException(400, detail=result["error"])
    
    # 创建健康记录
    health_record = HealthRecord(
        cat_id=report.cat_id,
        date=datetime.utcnow(),
        type="checkup",
        title=f"化验单分析: {report.file_name}",
        note=result.get("raw_response", "")[:500] if "raw_response" in result else None,
        ai_summary=result.get("summary", ""),
        actionable_advice=result.get("recommendations", [])
    )
    db.add(health_record)
    db.commit()
    db.refresh(health_record)
    
    # 添加指标
    for ind in result.get("indicators", []):
        try:
            indicator = HealthIndicator(
                record_id=health_record.id,
                name=ind.get("name", ""),
                display_name=ind.get("name", ""),
                value=float(ind["value"]) if ind.get("value") and str(ind["value"]).replace(".", "").isdigit() else None,
                unit=ind.get("unit", ""),
                reference_min=float(ind["reference_range"].split("-")[0]) if ind.get("reference_range") and "-" in str(ind["reference_range"]) else None,
                reference_max=float(ind["reference_range"].split("-")[1]) if ind.get("reference_range") and "-" in str(ind["reference_range"]) and len(ind["reference_range"].split("-")) > 1 else None,
                is_abnormal=ind.get("status") in ["high", "low"],
                explanation=ind.get("explanation", "")
            )
            db.add(indicator)
        except:
            pass  # 跳过无法解析的指标
    
    db.commit()
    
    return {
        "record_id": health_record.id,
        "analysis": result
    }


@router.post("/upload/{cat_id}", response_model=ReportAttachmentResponse)
async def upload_report(
    cat_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传化验单文件"""
    # 验证文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"不支持的文件格式: {ext}")
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(500, detail=f"文件保存失败: {str(e)}")
    
    # 创建数据库记录
    attachment = ReportAttachment(
        id=file_id,
        cat_id=cat_id,
        file_name=file.filename,
        file_path=str(file_path),
        file_type=ext,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    return attachment


@router.get("/cat/{cat_id}", response_model=List[ReportAttachmentResponse])
def get_cat_reports(
    cat_id: str,
    db: Session = Depends(get_db)
):
    """获取猫咪的所有化验单"""
    reports = db.query(ReportAttachment).filter(
        ReportAttachment.cat_id == cat_id
    ).order_by(ReportAttachment.created_at.desc()).all()
    return reports


@router.get("/{report_id}", response_model=ReportAttachmentResponse)
def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """获取单个化验单详情"""
    report = db.query(ReportAttachment).filter(ReportAttachment.id == report_id).first()
    if not report:
        raise HTTPException(404, detail="Report not found")
    return report


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """删除化验单"""
    report = db.query(ReportAttachment).filter(ReportAttachment.id == report_id).first()
    if not report:
        raise HTTPException(404, detail="Report not found")
    
    # 删除文件
    try:
        Path(report.file_path).unlink(missing_ok=True)
    except:
        pass
    
    # 删除数据库记录
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted successfully"}
