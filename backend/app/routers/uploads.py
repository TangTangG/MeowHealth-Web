from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf"
}

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """上传化验单文件，返回文件路径和ID"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"不支持的文件类型: {file.content_type}")
    
    file_id = str(uuid.uuid4())
    ext = ALLOWED_TYPES[file.content_type]
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "文件大小超过10MB限制")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "mime_type": file.content_type,
        "file_size": len(content)
    }
