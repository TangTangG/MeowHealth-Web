import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.core.config import get_gemini_api_key

from .subagents.vision_agent import VisionAgent
from .subagents.lab_analyzer import LabAnalyzer
from .subagents.dietitian_agent import DietitianAgent
from .subagents.critic_agent import CriticAgent
from .subagents.research_agent import ResearchAgent
from .subagents.history_agent import HistoryAnalystAgent


def parse_reference_range(ref_range: str) -> tuple[Optional[float], Optional[float]]:
    """解析参考范围字符串，返回 (min, max)，兼容旧有 API 契约"""
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


class MedicalOrchestrator:
    def __init__(self):
        self.api_key = get_gemini_api_key()
        if self.api_key:
            self.vision = VisionAgent(self.api_key)
            self.analyzer = LabAnalyzer(self.api_key)
            self.dietitian = DietitianAgent(self.api_key)
            self.critic = CriticAgent(self.api_key)
            self.history_analyst = HistoryAnalystAgent(self.api_key)
            self.researcher = ResearchAgent(self.api_key)
        self.base_dir = Path(__file__).parent

    def _load_skill(self, category: str, name: str) -> str:
        """根据类别和名称动态加载 Markdown 技能库"""
        if not name:
            return ""
        # 简单将名称规范化，如 "Maine Coon" -> "maine_coon"
        name_clean = name.lower().replace(" ", "_")
        skill_path = self.base_dir / "skills" / category / f"{name_clean}.md"
        if skill_path.exists():
            with open(skill_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def chat_about_report(self, report_data: dict, message: str, chat_history: List[Dict]) -> str:
        """基于化验单数据进行对话"""
        if not self.api_key:
            return "API Key 未设置"

        genai.configure(api_key=self.api_key)
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

    def process_report(self, file_path: str, mime_type: str, cat_profile: Dict[str, Any], history_records: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """完整化验单处理流水线"""
        if not self.api_key:
            return {"error": "Gemini API Key 未设置"}

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            return {"error": f"无法读取文件: {str(e)}"}

        # 1. Vision 提取 (纯数据)
        vision_result = self.vision.extract(file_data, mime_type)
        if "error" in vision_result:
            return vision_result
        
        # 1.5 历史趋势分析
        history_result = self.history_analyst.analyze(cat_profile, history_records or [], vision_result)

        # 2. 动态挂载 Context/Skills
        general_lab = self._load_skill("common", "general_lab")
        general_diet = self._load_skill("common", "general_diet")
        
        breed = cat_profile.get("breed", "")
        weight_status = cat_profile.get("weight_status", "")
        
        breed_skill = self._load_skill("breeds", breed)
        weight_skill = self._load_skill("weights", weight_status)

        # 3. Lab 病理分析 (结合通用指标、品种特异性和历史趋势)
        lab_result = self.analyzer.analyze(vision_result, general_lab, breed_skill, history_result.get("historical_context", ""))
        if "error" in lab_result:
            return lab_result
        
        # 3.5 Research 补充（知识库未覆盖的指标）
        abnormals = [i for i in lab_result.get("indicators", []) if i.get("status") in ["high", "low"]]
        unmatched = [i for i in abnormals if not i.get("explanation") or len(i.get("explanation", "")) < 10]
        if unmatched:
            research_result = self.researcher.research(unmatched, breed_skill)
            for finding in research_result.get("supplementary_findings", []):
                for ind in lab_result.get("indicators", []):
                    if ind.get("name") == finding.get("indicator") and not ind.get("explanation"):
                        ind["explanation"] = finding.get("finding", "")
        
        # 4. Dietitian 营养学建议 (结合异常情况和体型特异性)
        recommendations = self.dietitian.prescribe(lab_result, general_diet, weight_skill)

        # 4.5 Critic 审查
        critic_result = self.critic.review(lab_result, recommendations, cat_profile)
        if not critic_result.get("approved", True):
            lab_result["summary"] = critic_result.get("revised_summary", lab_result.get("summary"))
            recommendations = critic_result.get("revised_recommendations", recommendations)
            lab_result["critic_flags"] = critic_result.get("flags", [])

        # 5. 格式化组装与规范化 (对齐原前端 API 契约)
        final_indicators = []
        for ind in lab_result.get("indicators", []):
            ref_range = ind.get("reference_range", "")
            ref_min, ref_max = parse_reference_range(ref_range)
            ind["reference_min"] = ref_min
            ind["reference_max"] = ref_max
            status = ind.get("status", "normal")
            ind["is_abnormal"] = status in ["high", "low"]
            final_indicators.append(ind)
        
        return {
            "indicators": final_indicators,
            "summary": lab_result.get("summary", "分析完成"),
            "recommendations": recommendations,
            "historical_context": history_result.get("historical_context", ""),
            "critic_flags": lab_result.get("critic_flags", [])
        }
