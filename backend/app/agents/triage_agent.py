from typing import Dict, List, Optional


class TriageAgent:
    """前台分诊 Agent — 基于规则引擎判断症状紧急程度"""

    def __init__(self):
        # 定义分诊规则：级别 -> 关键词列表
        self.rules = {
            "emergency": {
                "keywords": [
                    "呼吸困难",
                    "昏迷",
                    "大出血",
                    "出血",
                    "带血",
                    "抽搐",
                    "休克",
                    "无法站立",
                    "窒息",
                ],
                "vital_thresholds": {
                    "temperature_celsius": lambda t: t > 40.5 or t < 35.5,
                    "heart_rate": lambda h: h < 100 or h > 250,
                    "respiratory_rate": lambda r: r > 60,
                },
            },
            "urgent": {
                "keywords": [
                    "持续呕吐",
                    "腹泻带血",
                    "拒食",
                    "尿频尿血",
                    "精神萎靡",
                    "明显脱水",
                ],
                "vital_thresholds": {
                    "temperature_celsius": lambda t: 39.5 <= t <= 40.5 or 35.5 <= t < 37,
                    "heart_rate": lambda h: 100 <= h < 120 or 220 < h <= 250,
                    "weight_loss_1w_pct": lambda p: p > 10,
                },
            },
            "routine": {
                "keywords": [
                    "轻度呕吐",
                    "软便",
                    "食欲下降",
                    "打喷嚏",
                    "流泪",
                    "轻度抓挠",
                ],
                "vital_thresholds": {
                    "temperature_celsius": lambda t: 38.5 <= t < 39.5,
                    "weight_loss_1m_pct": lambda p: p > 5,
                },
            },
            "non_urgent": {
                "keywords": [
                    "行为问题",
                    "挑食",
                    "换粮不适",
                    "偶尔吐毛球",
                    "轻度掉毛增加",
                    "踩奶频繁",
                ],
                "vital_thresholds": {},
            },
        }

        # 优先级顺序（高 -> 低）
        self.priority = ["emergency", "urgent", "routine", "non_urgent"]

        # 科室映射辅助：症状 -> 科室
        self.department_keywords = {
            "消化内科": ["轻度呕吐", "软便", "食欲下降", "持续呕吐", "腹泻带血", "拒食", "偶尔吐毛球", "换粮不适", "挑食"],
            "皮肤科": ["轻度抓挠", "流泪", "轻度掉毛增加"],
            "呼吸内科": ["打喷嚏", "呼吸困难", "窒息"],
            "泌尿内科": ["尿频尿血"],
            "行为科": ["行为问题", "踩奶频繁"],
            "营养科": ["挑食", "换粮不适", "食欲下降", "拒食"],
        }

    def _match_symptoms(self, symptom_description: str, keywords: List[str]) -> List[str]:
        """返回命中的关键词列表"""
        matched = []
        for kw in keywords:
            if kw in symptom_description:
                matched.append(kw)
        return matched

    def _match_vitals(self, vital_signs: Dict, thresholds: Dict) -> List[str]:
        """返回命中的体征规则名称列表"""
        matched = []
        if not vital_signs:
            return matched
        for key, check in thresholds.items():
            val = vital_signs.get(key)
            if val is not None and check(val):
                matched.append(key)
        return matched

    def _determine_department(self, triage_level: str, matched_keywords: List[str]) -> str:
        """推荐科室/Agent"""
        if triage_level in ("emergency", "urgent"):
            return "建议立即联系兽医急诊"

        # 按命中关键词匹配科室
        best_dept = None
        best_count = 0
        for dept, keywords in self.department_keywords.items():
            count = sum(1 for kw in matched_keywords if kw in keywords)
            if count > best_count:
                best_count = count
                best_dept = dept

        if best_dept:
            return best_dept
        return "综合内科"

    def _get_advice(self, triage_level: str) -> str:
        """按级别给出即时建议"""
        advice_map = {
            "emergency": "请立即前往最近的宠物医院急诊！",
            "urgent": "建议尽快（今天内）带猫咪就医。",
            "routine": "可预约 3 天内的门诊检查。",
            "non_urgent": "症状较轻，可先观察或在线咨询。",
        }
        return advice_map.get(triage_level, "建议咨询兽医。")

    def triage(self, symptom_description: str, vital_signs: Optional[Dict] = None) -> Dict:
        """
        输入:
          - symptom_description: str, 症状描述（用户自然语言）
          - vital_signs: dict, 可选体征数据 {temperature_celsius, heart_rate, ...}
        输出:
          dict: {
            "triage_level": "emergency" | "urgent" | "routine" | "non_urgent",
            "confidence": float,  # 0.0-1.0
            "matched_rules": list[str],  # 命中了哪些规则
            "recommended_department": str,  # 推荐科室/Agent
            "advice": str,  # 给用户的即时建议
            "disclaimer": "仅供参考，不构成医疗建议"
          }
        """
        result_level = None
        all_matched = []
        max_confidence = 0.0

        for level in self.priority:
            config = self.rules[level]
            kw_matched = self._match_symptoms(symptom_description, config["keywords"])
            vital_matched = self._match_vitals(vital_signs or {}, config["vital_thresholds"])
            combined = kw_matched + vital_matched

            if combined:
                total_checks = len(config["keywords"]) + len(config["vital_thresholds"])
                confidence = len(combined) / total_checks if total_checks else 1.0
                if result_level is None:
                    result_level = level
                    all_matched = combined
                    max_confidence = confidence
                # 保持最高优先级，不覆盖
                break

        if result_level is None:
            result_level = "non_urgent"
            all_matched = []
            max_confidence = 1.0

        department = self._determine_department(result_level, all_matched)
        advice = self._get_advice(result_level)

        return {
            "triage_level": result_level,
            "confidence": round(max_confidence, 2),
            "matched_rules": all_matched,
            "recommended_department": department,
            "advice": advice,
            "disclaimer": "仅供参考，不构成医疗建议",
        }


if __name__ == "__main__":
    agent = TriageAgent()

    # Test cases
    print(agent.triage("我家猫呼吸困难，体温 41 度", {"temperature_celsius": 41}))
    print(agent.triage("猫咪持续呕吐两天，不吃东西"))
    print(agent.triage("猫有点软便，但精神还行"))
    print(agent.triage("猫最近不爱吃新换的粮"))
