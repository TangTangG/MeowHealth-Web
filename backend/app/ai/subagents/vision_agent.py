import google.generativeai as genai
import json
from typing import Dict, Any
from app.ai.utils import clean_and_parse_json

VISION_EXTRACTION_PROMPT = """你是一个高精度的医疗 OCR 提取器。你的唯一任务是从化验单图片中提取所有检测指标的字面数值，不要做任何医学评估。

提取要求：
1. name: 指标英文代码或缩写（如 WBC, RBC, CREA）
2. display_name: 指标的中文名称
3. value: 测量的具体数值（必须转为浮点数，如无法提取则填 null）
4. unit: 计量单位（如 g/L, mmol/L）
5. reference_range: 图片上标注的参考范围原始字符串（如 "100-150", "<50"）

返回格式必须是绝对纯净的 JSON，格式如下：
{
  "indicators": [
    {
      "name": "CREA",
      "display_name": "肌酐",
      "value": 123.5,
      "unit": "umol/L",
      "reference_range": "71-212"
    }
  ]
}"""

class VisionAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Vision 需要使用多模态模型
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def extract(self, file_data: bytes, mime_type: str) -> Dict[str, Any]:
        """仅提取，不做分析"""
        try:
            response = self.model.generate_content([
                VISION_EXTRACTION_PROMPT,
                {"mime_type": mime_type, "data": file_data}
            ])
            
            text = response.text
            try:
                result = clean_and_parse_json(text)
                if isinstance(result, dict):
                    return result
                return {"error": "返回的 JSON 不是字典结构", "raw": text}
            except Exception as e:
                return {"error": f"JSON 提取失败: {str(e)}", "raw": text}
        except Exception as e:
            return {"error": f"OCR 提取失败: {str(e)}"}
