import google.generativeai as genai
from app.core.config import get_gemini_api_key
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

REPORT_ANALYSIS_PROMPT = """你是一位专业的兽医化验单解读助手。请分析以下宠物化验单内容，并输出 JSON 格式的结果。

要求：
1. 提取所有检测指标（名称、数值、单位、参考范围）
2. 标记异常指标（偏高/偏低）
3. 给出整体健康评估（一句话核心结论）
4. 提供 actionable 的建议

输出必须是有效的 JSON 格式：
{
  "indicators": [
    {
      "name": "指标英文代码（如 CREA, WBC, ALT）",
      "display_name": "指标中文名称（如 肌酐, 白细胞, 谷丙转氨酶）",
      "value": 123.5,
      "unit": "单位",
      "reference_min": 100.0,
      "reference_max": 150.0,
      "status": "normal|high|low",
      "explanation": "简要说明该指标的意义"
    }
  ],
  "summary": "整体评估摘要，一句话核心结论",
  "recommendations": ["建议1", "建议2", "建议3"]
}"""


def parse_reference_range(ref_range: str) -> tuple[Optional[float], Optional[float]]:
    """解析参考范围字符串，返回 (min, max)"""
    if not ref_range:
        return None, None
    
    patterns = [
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',  # 100-150
        r'<\s*(\d+(?:\.\d+)?)',  # <150
        r'>\s*(\d+(?:\.\d+)?)',  # >100
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ref_range)
        if match:
            if '-' in ref_range:
                return float(match.group(1)), float(match.group(2))
            elif '<' in ref_range:
                return None, float(match.group(1))
            elif '>' in ref_range:
                return float(match.group(1)), None
    
    return None, None


def analyze_report(file_path: str, mime_type: str) -> dict:
    """使用 Gemini 分析化验单，返回结构化数据"""
    api_key = get_gemini_api_key()
    if not api_key:
        return {"error": "Gemini API Key 未设置"}
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        response = model.generate_content([
            REPORT_ANALYSIS_PROMPT,
            {"mime_type": mime_type, "data": file_data}
        ])
        
        text = response.text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                for indicator in result.get("indicators", []):
                    ref_range = indicator.get("reference_range", "")
                    ref_min, ref_max = parse_reference_range(ref_range)
                    indicator["reference_min"] = ref_min
                    indicator["reference_max"] = ref_max
                    status = indicator.get("status", "normal")
                    indicator["is_abnormal"] = status in ["high", "low"]
                
                return result
            except json.JSONDecodeError as e:
                return {"error": f"JSON 解析失败: {str(e)}", "raw_response": text}
        
        return {"error": "无法解析 AI 响应", "raw_response": text}
        
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}


def chat_about_report(report_data: dict, message: str, chat_history: List[Dict]) -> str:
    """基于化验单数据进行对话"""
    api_key = get_gemini_api_key()
    if not api_key:
        return "API Key 未设置"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    context = f"""你是一位专业的兽医助手。用户正在查看一份宠物化验单，以下是化验单数据：

核心结论：{report_data.get('summary', '无')}
异常指标：{', '.join([i['display_name'] for i in report_data.get('indicators', []) if i.get('is_abnormal')]) or '无'}
建议：{', '.join(report_data.get('recommendations', []))}

请基于以上信息回答用户的问题。"""
    
    messages = [{"role": "system", "parts": [context]}]
    for msg in chat_history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [msg["content"]]})
    messages.append({"role": "user", "parts": [message]})
    
    try:
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        return f"抱歉，处理问题时出错: {str(e)}"
