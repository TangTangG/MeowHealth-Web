import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

DIETITIAN_PROMPT_TEMPLATE = """你是一位宠物临床营养师。请根据猫咪的病理诊断摘要、具体的异常指标，以及提供的饮食护理知识库，为用户输出可执行的建议列表。

【基础护理知识库】
{general_diet}

【特殊体型/阶段护理知识库 (必须优先遵守该库的规则，如超重不可断食等)】
{specific_diet}

【病理分析摘要】
{lab_summary}

【异常指标列表】
{abnormal_indicators}

任务要求：
1. 提取 actionable 的具体建议（不要泛泛而谈，要指出具体换什么粮、加什么补充剂、如何改变生活习惯）。
2. 如果存在冲突，以【特殊知识库】为准。
3. 输出纯 JSON 数组格式。

返回格式必须是绝对纯净的 JSON：
{
  "recommendations": [
    "建议1...",
    "建议2..."
  ]
}"""

class DietitianAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def prescribe(self, lab_result: Dict[str, Any], general_diet: str, specific_diet: str) -> List[str]:
        """根据异常情况和知识库开具处方/护理建议"""
        if "error" in lab_result:
            return []
            
        summary = lab_result.get("summary", "无结论")
        indicators = lab_result.get("indicators", [])
        abnormals = [i for i in indicators if i.get("status") in ["high", "low"]]
        
        abnormal_text = json.dumps(abnormals, ensure_ascii=False, indent=2) if abnormals else "无异常指标"

        prompt = DIETITIAN_PROMPT_TEMPLATE.format(
            general_diet=general_diet,
            specific_diet=specific_diet if specific_diet else "无特殊体型/阶段规则。",
            lab_summary=summary,
            abnormal_indicators=abnormal_text
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            try:
                result = clean_and_parse_json(text)
                if isinstance(result, dict):
                    return result.get("recommendations", [])
                elif isinstance(result, list):
                    return result
                return []
            except Exception:
                return []
        except Exception:
            return []
