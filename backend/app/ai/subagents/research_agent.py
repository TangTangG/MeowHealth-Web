import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

RESEARCH_PROMPT = """你是一位兽医文献检索专家。当遇到疑难指标或知识库未覆盖的情况时，你需要基于已有医学常识提供补充信息。

【未覆盖的异常指标】
{unmatched_indicators}

【品种特异性上下文】
{breed_context}

任务：
1. 针对每个未匹配的异常指标，给出可能的临床意义。
2. 提供需要关注的并发症。
3. 给出建议的复查项目。

返回 JSON：
{{
  "supplementary_findings": [
    {{"indicator": "指标名", "finding": "临床意义", "follow_up": "建议复查项目"}}
  ],
  "literature_notes": ["相关医学知识要点"]
}}"""


class ResearchAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def research(
        self,
        unmatched_indicators: List[Dict[str, Any]],
        breed_context: str = ""
    ) -> Dict[str, Any]:
        """对知识库未覆盖的指标进行补充研究"""
        if not unmatched_indicators:
            return {"supplementary_findings": [], "literature_notes": []}

        prompt = RESEARCH_PROMPT.format(
            unmatched_indicators=json.dumps(unmatched_indicators, ensure_ascii=False, indent=2),
            breed_context=breed_context or "无特殊品种上下文"
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"supplementary_findings": [], "literature_notes": []}
        except Exception:
            return {"supplementary_findings": [], "literature_notes": []}
