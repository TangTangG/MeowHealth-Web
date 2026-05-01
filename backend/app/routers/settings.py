from fastapi import APIRouter
from app.core.config import set_gemini_api_key, get_gemini_api_key
from app.schemas.schemas import ApiKeySetting, ApiKeyStatus

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/api-key/status", response_model=ApiKeyStatus)
async def api_key_status():
    key = get_gemini_api_key()
    if key:
        masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
        return ApiKeyStatus(is_set=True, masked_key=masked)
    return ApiKeyStatus(is_set=False)

@router.post("/api-key")
async def set_api_key(setting: ApiKeySetting):
    set_gemini_api_key(setting.api_key)
    return {"message": "API Key updated successfully"}
