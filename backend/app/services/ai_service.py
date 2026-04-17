import google.generativeai as genai
from app.core.config import get_gemini_api_key
import json
import re

REPORT_ANALYSIS_PROMPT = """你是一位专业的兽医化验单解读助手。请分析以下宠物化验单内容，并输出 JSON 格式的结果。

要求：
1. 提取所有检测指标（名称、数值、单位、参考范围）
2. 标记异常指标（偏高/偏低）
3. 给出整体健康评估
4. 提供 actionable 的建议

输出必须是有效的 JSON 格式：
{
  "indicators": [
    {
      "name": "指标名称",
      "value": "检测值",
      "unit": "单位",
      "reference_range": "参考范围",
      "status": "normal|high|low",
      "explanation": "简要说明"
    }
  ],
  "summary": "整体评估摘要",
  "recommendations": ["建议1", "建议2"]
}"""


def analyze_report(file_path: str, file_type: str) -> dict:
    """使用 Gemini 分析化验单"""
    api_key = get_gemini_api_key()
    if not api_key:
        return {"error": "Gemini API Key 未设置"}
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    try:
        # 读取文件
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # 根据文件类型设置 mime_type
        mime_type = "image/jpeg"
        if file_type in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif file_type == ".png":
            mime_type = "image/png"
        elif file_type == ".pdf":
            mime_type = "application/pdf"
        
        # 调用 Gemini
        response = model.generate_content([
            REPORT_ANALYSIS_PROMPT,
            {"mime_type": mime_type, "data": file_data}
        ])
        
        # 解析 JSON 响应
        text = response.text
        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError:
                pass
        
        # 如果无法解析 JSON，返回原始文本
        return {
            "summary": "AI 分析完成，但无法解析结构化数据",
            "raw_response": text,
            "indicators": [],
            "recommendations": []
        }
        
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}
