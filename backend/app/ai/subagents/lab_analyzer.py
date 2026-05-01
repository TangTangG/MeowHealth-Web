import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

LAB_ANALYSIS_PROMPT_TEMPLATE = """你是一位资深兽医病理学家。请根据提取的化验数据和所提供的医学知识库，判定指标的异常状态，并给出专业的医学解释和总评。

【基础知识库】
{general_knowledge}

【品种/特性知识库 (必须优先遵守该库的放大警告规则)】
{specific_knowledge}

【历史趋势上下文】
{historical_context}

【原始提取数据】
{vision_data}

任务要求：
1. 遍历所有 indicator，比对 value 和 reference_range。
2. 判定 status (可选值: normal, high, low)。
3. 如果 status 为 high 或 low，请结合知识库给出简短的 explanation (解释该异常意味着什么)。
4. 综合所有异常，给出一句话的 summary (整体健康评估)。

返回格式必须是绝对纯净的 JSON，格式如下：
{
  "summary": "发现多项指标偏高，提示可能存在肝脏损伤...",
  "indicators": [
    {
      "name": "CREA",
      "display_name": "肌酐",
      "value": 123.5,
      "unit": "umol/L",
      "reference_range": "71-212",
      "status": "normal",
      "explanation": ""
    }
  ]
}"""

class LabAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze(self, vision_data: Dict[str, Any], general_knowledge: str, specific_knowledge: str, historical_context: str = "") -> Dict[str, Any]:
        """结合知识库进行数值比对和病理分析"""
        if "error" in vision_data:
            return vision_data
            
        prompt = LAB_ANALYSIS_PROMPT_TEMPLATE.format(
            general_knowledge=general_knowledge,
            specific_knowledge=specific_knowledge if specific_knowledge else "无特殊品种警示。",
            historical_context=historical_context if historical_context else "无历史记录",
            vision_data=json.dumps(vision_data, ensure_ascii=False, indent=2)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            try:
                result = clean_and_parse_json(text)
                if isinstance(result, dict):
                    return result
                return {"error": "返回的 JSON 不是字典结构", "raw": text}
            except Exception as e:
                return {"error": f"JSON 提取失败: {str(e)}", "raw": text}
        except Exception as e:
            return {"error": f"病理分析失败: {str(e)}"}
