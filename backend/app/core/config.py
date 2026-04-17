import os
from pathlib import Path

# 上传配置
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Gemini API Key（优先从环境变量读取，也可通过 API 设置）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def set_gemini_api_key(key: str):
    """设置 Gemini API Key"""
    global GEMINI_API_KEY
    GEMINI_API_KEY = key

def get_gemini_api_key() -> str:
    """获取 Gemini API Key"""
    return GEMINI_API_KEY
