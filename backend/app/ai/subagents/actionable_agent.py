import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

ACTION_PROMPT = """你是一位将诊断转化为行动的兽医助手。根据化验结果，生成可执行的行动清单。

【病理摘要】
{summary}

【异常指标】
{abnormals}

【营养建议】
{recommendations}

【猫咪档案】
{cat_profile}

任务：
1. 生成复查提醒（指定多少天后需要复查哪些指标）。
2. 生成处方粮/补充剂购买清单（如果需要）。
3. 每个行动必须是具体的、可执行的。

返回 JSON：
{{
  "reminders": [
    {{"title": "复查肾功能", "description": "需复查 CREA、BUN、SDMA", "days_from_now": 30, "reminder_type": "vet_visit"}}
  ],
  "shopping_list": [
    {{"item": "肾脏处方粮", "reason": "CREA 偏高", "priority": "high"}}
  ]
}}"""


class ActionableAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_actions(
        self,
        summary: str,
        abnormals: List[Dict[str, Any]],
        recommendations: List[str],
        cat_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成可执行的行动清单"""
        if not abnormals and not recommendations:
            return {"reminders": [], "shopping_list": []}

        prompt = ACTION_PROMPT.format(
            summary=summary,
            abnormals=json.dumps(abnormals, ensure_ascii=False, indent=2),
            recommendations=json.dumps(recommendations, ensure_ascii=False),
            cat_profile=json.dumps(cat_profile, ensure_ascii=False)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"reminders": [], "shopping_list": []}
        except Exception:
            return {"reminders": [], "shopping_list": []}
