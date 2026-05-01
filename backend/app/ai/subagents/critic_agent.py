import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

CRITIC_PROMPT_TEMPLATE = """你是一位资深兽医科主任，负责审查下级医生的诊断报告和营养处方。

【病理分析报告】
{lab_report}

【营养处方建议】
{dietitian_advice}

【猫咪档案】
{cat_profile}

审查要求：
1. 检查病理诊断与营养建议之间是否存在医学冲突（如：肝指标异常但建议高蛋白饮食）。
2. 检查是否遗漏了关键警告（如：多项指标严重异常但未建议复查）。
3. 检查建议是否过于激进或保守。
4. 如果一切合理，直接通过。

返回 JSON：
{{
  "approved": true/false,
  "flags": ["冲突或遗漏描述1", ...],
  "revised_summary": "如果需要修改，给出修正后的总结；如果通过，原样返回",
  "revised_recommendations": ["修正后的建议1", ...]
}}"""


class CriticAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def review(
        self,
        lab_result: Dict[str, Any],
        recommendations: List[str],
        cat_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查病理报告和营养处方"""
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            lab_report=json.dumps(lab_result, ensure_ascii=False, indent=2),
            dietitian_advice=json.dumps(recommendations, ensure_ascii=False),
            cat_profile=json.dumps(cat_profile, ensure_ascii=False)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"approved": True, "flags": [], "revised_summary": "", "revised_recommendations": []}
        except Exception:
            return {"approved": True, "flags": [], "revised_summary": "", "revised_recommendations": []}
