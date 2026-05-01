import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

HISTORY_ANALYSIS_PROMPT = """你是一位擅长纵向分析的兽医。请对比猫咪的历史化验数据与当前数据，识别趋势和早期预警信号。

【猫咪档案】
{cat_profile}

【历史化验记录（按时间倒序）】
{history_records}

【当前化验数据】
{current_data}

分析要求：
1. 对比关键指标的历史变化趋势（如：肌酐从 3 个月前的 120 升至现在的 180）。
2. 识别慢性病早期信号（如：肾功能指标持续上升）。
3. 给出基于趋势的预警。

返回 JSON：
{{
  "trends": [
    {{"indicator": "CREA", "values": [120, 145, 180], "dates": ["2026-02", "2026-03", "2026-04"], "direction": "rising", "concern": "high"}}
  ],
  "warnings": ["肌酐持续升高，提示肾功能可能进行性下降"],
  "historical_context": "该猫近 3 个月肾功能指标呈上升趋势，建议密切关注"
}}"""


class HistoryAnalystAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze(
        self,
        cat_profile: Dict[str, Any],
        history_records: List[Dict[str, Any]],
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """纵向分析历史趋势"""
        if not history_records:
            return {"trends": [], "warnings": [], "historical_context": "无历史记录，首次分析"}

        prompt = HISTORY_ANALYSIS_PROMPT.format(
            cat_profile=json.dumps(cat_profile, ensure_ascii=False),
            history_records=json.dumps(history_records, ensure_ascii=False, indent=2),
            current_data=json.dumps(current_data, ensure_ascii=False, indent=2)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"trends": [], "warnings": [], "historical_context": "历史分析解析失败"}
        except Exception:
            return {"trends": [], "warnings": [], "historical_context": "历史分析不可用"}
