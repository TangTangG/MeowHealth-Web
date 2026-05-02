"""
Health Advisor Agent — 基于猫咪档案数据给出日常护理建议

⚠️ 免责声明：本 Agent 提供的所有建议均为日常护理参考，不构成医疗诊断或治疗建议。
如有健康疑虑，请务必咨询专业兽医。
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class HealthAdvisorAgent:
    """健康顾问 Agent — 基于猫咪档案数据给出日常护理建议（纯规则引擎，无 LLM 依赖）"""

    def __init__(self):
        # 护理建议规则库
        self.care_rules = {
            "disclaimer": "本建议仅供参考，不构成医疗建议。如有疑虑请咨询兽医。",
            "weight": {
                "kitten_weekly_gain_g": {"0-6": 100, "6-12": 50},
                "adult_fluctuation_pct": 5,
                "adult_decline_alert_pct": 5,
                "adult_decline_weeks": 2,
                "adult_obesity_alert_pct": 10,
                "senior_monthly_decline_alert_pct": 3,
            },
            "diet": {
                "kitten_high_protein": True,
                "indoor_calorie_control": True,
                "senior_digestible": True,
            },
            "vaccine": {
                "core_first_dose_weeks": 8,
                "core_second_dose_weeks": 12,
                "core_third_dose_weeks": 16,
                "booster_months": 12,
            },
            "deworming": {
                "internal_months": 3,
                "external_months": 1,
                "internal_overdue_alert_months": 4,
                "external_overdue_alert_months": 2,
            },
        }

    def generate_report(
        self,
        cat: Dict[str, Any],
        weight_history: List[Dict[str, Any]],
        feeding_history: List[Dict[str, Any]],
        recent_vitals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        输入:
          - cat: dict, 猫咪档案 {age_months, breed, gender, weight_kg, ...}
          - weight_history: list[dict], 最近体重记录 [{weight_kg/value, log_date/date}, ...]
          - feeding_history: list[dict], 最近喂食记录 [{type/meal_type, amount/amount_grams, timestamp/log_time}, ...]
          - recent_vitals: list[dict], 最近体征记录 [{weight_kg, temperature_celsius, appetite_score, water_intake_ml, ...}]
        输出:
          dict: {
            "overall_status": str,
            "weight_assessment": dict,
            "diet_recommendation": dict,
            "vaccine_reminders": list[dict],
            "deworming_reminders": list[dict],
            "daily_care_tips": list[str],
            "risk_alerts": list[str],
            "next_checkup_suggestion": str,
            "generated_at": str,
          }
        """
        report = {
            "overall_status": "健康良好",
            "weight_assessment": {},
            "diet_recommendation": {},
            "vaccine_reminders": [],
            "deworming_reminders": [],
            "daily_care_tips": [],
            "risk_alerts": [],
            "next_checkup_suggestion": "",
            "generated_at": datetime.now().isoformat(),
        }

        # 1. 体重评估
        weight_assessment = self.assess_weight_trend(
            weight_history,
            cat.get("weight_kg"),
            cat.get("age_months", 12),
        )
        report["weight_assessment"] = weight_assessment
        if weight_assessment.get("status") == "alert":
            report["overall_status"] = "需关注"

        # 2. 饮食建议
        diet = self.recommend_diet(
            cat, weight_assessment.get("trend", "stable"), feeding_history
        )
        report["diet_recommendation"] = diet
        if diet.get("status") == "alert":
            report["overall_status"] = "需关注"

        # 3. 疫苗提醒
        vaccines = self.check_vaccine_status(
            cat.get("age_months", 12), cat.get("breed", "")
        )
        report["vaccine_reminders"] = vaccines
        if any(v.get("urgency") == "urgent" for v in vaccines):
            report["overall_status"] = "需关注"

        # 4. 驱虫提醒（简化：没有上次驱虫日期则按年龄推断）
        last_deworming = cat.get("last_deworming_date")
        deworming = self.check_deworming_status(last_deworming)
        report["deworming_reminders"] = deworming
        if any(d.get("urgency") == "urgent" for d in deworming):
            report["overall_status"] = "需关注"

        # 5. 日常护理
        report["daily_care_tips"] = self._get_daily_care_tips(
            cat.get("age_months", 12)
        )

        # 6. 风险预警（基于品种和体征）
        report["risk_alerts"] = self._get_breed_risks(
            cat.get("breed", ""),
            cat.get("age_months", 12),
            recent_vitals,
        )
        if report["risk_alerts"]:
            report["overall_status"] = (
                "建议就医"
                if report["overall_status"] == "建议就医"
                else "需关注"
            )

        # 7. 下次体检建议
        report["next_checkup_suggestion"] = self._get_checkup_suggestion(
            cat.get("age_months", 12)
        )

        return report

    def check_vaccine_status(self, age_months: int, breed: str) -> List[Dict[str, Any]]:
        """检查疫苗接种状态并生成提醒"""
        reminders = []
        age_weeks = age_months * 4.33  # 近似周数
        rules = self.care_rules["vaccine"]

        # 核心疫苗（猫三联）
        if age_weeks < rules["core_first_dose_weeks"]:
            reminders.append(
                {
                    "vaccine": "猫三联（核心疫苗）",
                    "due_at_weeks": rules["core_first_dose_weeks"],
                    "urgency": "info",
                    "note": f"预计 {int(rules['core_first_dose_weeks'] - age_weeks)} 周后接种第一针",
                }
            )
        elif age_weeks < rules["core_second_dose_weeks"]:
            reminders.append(
                {
                    "vaccine": "猫三联（第二针）",
                    "due_at_weeks": rules["core_second_dose_weeks"],
                    "urgency": "info",
                    "note": f"预计 {int(rules['core_second_dose_weeks'] - age_weeks)} 周后接种第二针",
                }
            )
        elif age_weeks < rules["core_third_dose_weeks"]:
            reminders.append(
                {
                    "vaccine": "猫三联（第三针）",
                    "due_at_weeks": rules["core_third_dose_weeks"],
                    "urgency": "info",
                    "note": f"预计 {int(rules['core_third_dose_weeks'] - age_weeks)} 周后接种第三针",
                }
            )
        else:
            # 已成年，需每年加强
            reminders.append(
                {
                    "vaccine": "猫三联（年度加强）",
                    "due_at_weeks": None,
                    "urgency": "info",
                    "note": "建议每年加强一次（请确认上次接种时间）",
                }
            )

        # 狂犬疫苗
        if age_weeks >= 12:
            reminders.append(
                {
                    "vaccine": "狂犬疫苗",
                    "due_at_weeks": None,
                    "urgency": "info",
                    "note": "12 周龄以上可接种，之后每年或每 3 年加强（根据疫苗类型）",
                }
            )

        return reminders

    def check_deworming_status(
        self, last_deworming_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """检查驱虫状态并生成提醒"""
        reminders = []
        rules = self.care_rules["deworming"]
        now = datetime.now()

        if last_deworming_date:
            try:
                last_date = datetime.fromisoformat(
                    last_deworming_date.replace("Z", "+00:00")
                )
                months_since = (now - last_date).days / 30.0
            except (ValueError, TypeError):
                months_since = 999  # 解析失败视为已过期
        else:
            months_since = 999  # 无记录视为已过期

        # 体内驱虫
        if months_since >= rules["internal_overdue_alert_months"]:
            reminders.append(
                {
                    "type": "体内驱虫",
                    "frequency": f"每 {rules['internal_months']} 个月一次",
                    "urgency": "urgent",
                    "note": f"已超过 {int(months_since)} 个月未体内驱虫，建议尽快安排",
                }
            )
        elif months_since >= rules["internal_months"]:
            reminders.append(
                {
                    "type": "体内驱虫",
                    "frequency": f"每 {rules['internal_months']} 个月一次",
                    "urgency": "warning",
                    "note": "体内驱虫即将到期，请安排",
                }
            )
        else:
            next_due = last_date + timedelta(days=rules["internal_months"] * 30) if last_deworming_date else None
            reminders.append(
                {
                    "type": "体内驱虫",
                    "frequency": f"每 {rules['internal_months']} 个月一次",
                    "urgency": "ok",
                    "note": f"下次预计时间: {next_due.strftime('%Y-%m-%d') if next_due else '请记录上次驱虫日期'}",
                }
            )

        # 体外驱虫（独立计算，通常每月一次）
        # 简化：若无记录，也视为 urgent
        external_months_since = months_since  # 简化使用同一日期
        if external_months_since >= rules["external_overdue_alert_months"]:
            reminders.append(
                {
                    "type": "体外驱虫",
                    "frequency": f"每 {rules['external_months']} 个月一次",
                    "urgency": "urgent",
                    "note": f"已超过 {int(external_months_since)} 个月未体外驱虫，建议尽快安排",
                }
            )
        elif external_months_since >= rules["external_months"]:
            reminders.append(
                {
                    "type": "体外驱虫",
                    "frequency": f"每 {rules['external_months']} 个月一次",
                    "urgency": "warning",
                    "note": "体外驱虫即将到期，请安排",
                }
            )
        else:
            next_external = (
                last_date + timedelta(days=rules["external_months"] * 30)
                if last_deworming_date
                else None
            )
            reminders.append(
                {
                    "type": "体外驱虫",
                    "frequency": f"每 {rules['external_months']} 个月一次",
                    "urgency": "ok",
                    "note": f"下次预计时间: {next_external.strftime('%Y-%m-%d') if next_external else '请记录上次驱虫日期'}",
                }
            )

        return reminders

    def assess_weight_trend(
        self,
        weight_history: List[Dict[str, Any]],
        current_weight: Optional[float],
        age_months: int,
    ) -> Dict[str, Any]:
        """评估体重趋势并给出建议"""
        if not weight_history or current_weight is None:
            return {
                "status": "unknown",
                "trend": "stable",
                "message": "体重数据不足，无法评估",
                "recommendation": "建议定期记录体重",
            }

        # 统一提取体重数值（兼容 weight_kg/value 两种键名）
        weights = []
        for entry in weight_history:
            w = entry.get("weight_kg")
            if w is None:
                w = entry.get("value")
            if w is not None:
                weights.append(float(w))

        if len(weights) < 2:
            return {
                "status": "info",
                "trend": "stable",
                "message": "体重记录较少，建议持续监测",
                "recommendation": "建议每周称重一次",
            }

        first_weight = weights[0]
        latest_weight = weights[-1]
        pct_change = (
            ((latest_weight - first_weight) / first_weight * 100)
            if first_weight != 0
            else 0
        )

        # 幼猫（0-12 月）
        if age_months <= 12:
            if pct_change < -10:
                return {
                    "status": "alert",
                    "trend": "declining",
                    "message": f"体重下降 {abs(pct_change):.1f}%，超过幼猫安全阈值（10%）",
                    "recommendation": "建议尽快就医检查，幼猫体重下降需高度重视",
                }
            # 简单估算周增重（假设记录间隔均匀）
            weeks = max(len(weights), 1)
            weekly_gain = (latest_weight - first_weight) * 1000 / weeks  # 转为克
            expected_gain = (
                100 if age_months <= 6 else 50
            )  # 0-6月每周100g，6-12月每周50g
            if weekly_gain > expected_gain * 2:
                return {
                    "status": "warning",
                    "trend": "rapid_gain",
                    "message": f"体重增长过快（每周约 {weekly_gain:.0f}g）",
                    "recommendation": "建议咨询兽医评估生长速度",
                }
            return {
                "status": "ok",
                "trend": "growing",
                "message": f"幼猫体重增长中（变化 {pct_change:+.1f}%）",
                "recommendation": "持续监测，确保营养均衡",
            }

        # 成猫（1-7 岁）
        if age_months < 84:
            if pct_change < -5:
                return {
                    "status": "alert",
                    "trend": "declining",
                    "message": f"体重下降 {abs(pct_change):.1f}%，超过成猫警戒阈值（5%）",
                    "recommendation": "建议连续监测 2 周，如持续下降请就医",
                }
            if pct_change > 10:
                return {
                    "status": "warning",
                    "trend": "increasing",
                    "message": f"体重增加 {pct_change:.1f}%，存在肥胖风险",
                    "recommendation": "建议控制饮食、增加运动",
                }
            if abs(pct_change) <= 5:
                return {
                    "status": "ok",
                    "trend": "stable",
                    "message": f"体重在正常波动范围内（{pct_change:+.1f}%）",
                    "recommendation": "保持当前饮食和运动习惯",
                }
            return {
                "status": "info",
                "trend": "stable",
                "message": f"体重变化 {pct_change:+.1f}%",
                "recommendation": "继续观察",
            }

        # 老年猫（7 岁+）
        if pct_change < -3:
            return {
                "status": "alert",
                "trend": "declining",
                "message": f"体重下降 {abs(pct_change):.1f}%，老年猫需警惕肌肉流失",
                "recommendation": "建议尽快就医，排查肾病、甲亢等老年疾病",
            }
        if pct_change > 10:
            return {
                "status": "warning",
                "trend": "increasing",
                "message": f"体重增加 {pct_change:.1f}%",
                "recommendation": "老年猫肥胖加重关节负担，建议调整饮食",
            }
        return {
            "status": "ok",
            "trend": "stable",
            "message": f"老年猫体重相对稳定（{pct_change:+.1f}%）",
            "recommendation": "继续定期监测，关注肌肉量",
        }

    def recommend_diet(
        self, cat: Dict[str, Any], weight_trend: str, recent_feeding: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """根据体重趋势和品种推荐饮食"""
        age_months = cat.get("age_months", 12)
        breed = cat.get("breed", "")
        breed_lower = breed.lower() if breed else ""

        advice = []
        status = "ok"

        # 基于年龄
        if age_months < 6:
            advice.append("幼猫期：选择高蛋白、高钙幼猫粮，每日 3-4 餐")
            advice.append("确保食物易咀嚼，可适当泡软")
        elif age_months < 12:
            advice.append("成长期：继续幼猫粮或过渡至幼猫粮，保证充足蛋白质")
            advice.append("每日 2-3 餐，根据活动量调整")
        elif age_months < 84:
            advice.append("成猫期：选择优质成猫粮，根据活动量调整热量")
            advice.append("室内猫注意控制卡路里，避免肥胖")
        else:
            advice.append("老年期：选择易消化、含关节保健成分的老年猫粮")
            advice.append("关注饮水量，可适当增加湿粮比例")

        # 基于体重趋势
        if weight_trend == "declining":
            advice.append("体重下降：建议高热量粮，少量多餐，排查健康问题")
            status = "alert"
        elif weight_trend == "rapid_gain" or weight_trend == "increasing":
            advice.append("体重增长：建议减重粮，控制食量，增加互动运动")
            status = "warning"

        # 基于品种
        if any(k in breed_lower for k in ["英短", "美短", "布偶"]):
            advice.append("品种注意：该品种易肥胖，需严格控制体重")
        if "缅因" in breed_lower or "布偶" in breed_lower:
            advice.append("大型猫：食量相对较大，但需避免过度喂养")
        if any(k in breed_lower for k in ["暹罗", "阿比"]):
            advice.append("活泼品种：新陈代谢较快，可选择高蛋白配方")

        # 基于最近喂食记录
        if recent_feeding:
            total_amount = sum(
                f.get("amount_grams", f.get("amount", 0)) for f in recent_feeding
            )
            avg_amount = total_amount / len(recent_feeding)
            if avg_amount > 100:
                advice.append(f"近期平均每餐 {avg_amount:.0f}g，建议根据体重目标评估是否适量")

        return {
            "status": status,
            "main_advice": advice[0] if advice else "请根据猫咪具体情况选择合适猫粮",
            "tips": advice[1:] if len(advice) > 1 else [],
            "feeding_frequency": (
                "每日 3-4 餐" if age_months < 6
                else "每日 2-3 餐" if age_months < 84
                else "每日 2-3 餐（少量多餐更佳）"
            ),
            "disclaimer": "饮食建议仅供参考，特殊健康状况请遵医嘱",
        }

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _get_daily_care_tips(self, age_months: int) -> List[str]:
        """根据年龄生成日常护理建议"""
        if age_months < 6:
            return [
                "建议每日刷牙习惯养成",
                "提供磨爪玩具",
                "注意社交化训练",
                "确保充足睡眠（幼猫需 16-20 小时/天）",
            ]
        elif age_months < 12:
            return [
                "继续刷牙习惯",
                "提供攀爬空间（猫爬架）",
                "保持疫苗接种进度",
                "适量运动，避免过度疲劳",
            ]
        elif age_months < 84:  # 7 年
            return [
                "建议每日刷牙",
                "提供丰富环境（玩具、猫爬架、窗边观景台）",
                "定期修剪指甲（每 2-4 周）",
                "控制体重，预防肥胖",
            ]
        else:
            return [
                "注意关节保暖，提供软垫休息区",
                "提供低门槛猫砂盆，方便进出",
                "定期体检（每年 1-2 次）",
                "关注饮水量，预防肾病",
                "选择易消化饮食，可适当补充关节保健品",
            ]

    def _get_breed_risks(
        self, breed: str, age_months: int, recent_vitals: List[Dict[str, Any]]
    ) -> List[str]:
        """基于品种和体征生成风险预警"""
        risks = []
        breed_lower = breed.lower() if breed else ""

        # 品种相关风险
        if any(k in breed_lower for k in ["英短", "美短"]):
            risks.append("肥厚型心肌病（HCM）风险，建议定期心超检查")
        if "布偶" in breed_lower:
            risks.append("肥厚型心肌病（HCM）风险较高，建议定期心超检查")
        if "折耳" in breed_lower:
            risks.append("软骨发育异常风险，避免剧烈运动和肥胖")
        if "暹罗" in breed_lower:
            risks.append("呼吸道敏感，注意环境清洁，避免粉尘和烟雾")
        if "缅因" in breed_lower:
            risks.append("髋关节发育不良风险，注意控制体重")
        if "波斯" in breed_lower or "加菲" in breed_lower:
            risks.append("短鼻品种：注意呼吸问题，避免高温环境")
        if "德文" in breed_lower or "斯芬克斯" in breed_lower:
            risks.append("无毛/短毛品种：注意皮肤护理和保暖")

        # 基于年龄和体征的风险
        if age_months >= 84 and recent_vitals:
            latest = recent_vitals[0]
            water = latest.get("water_intake_ml", 0)
            appetite = latest.get("appetite_score", 5)
            temp = latest.get("temperature_celsius")

            if water > 300:
                risks.append("老年猫多饮，建议检查肾功能和血糖")
            if appetite <= 2:
                risks.append("食欲显著下降，需排查甲亢、肾病或口腔疾病")
            if temp and (temp < 37.5 or temp > 39.2):
                risks.append(f"体温异常（{temp}°C），建议就医检查")
            if latest.get("spirit_status") == "萎靡":
                risks.append("精神状态萎靡，建议尽快就医")

        return risks

    def _get_checkup_suggestion(self, age_months: int) -> str:
        """生成下次体检建议"""
        if age_months < 6:
            return "建议每月体检一次（幼猫发育监测）"
        elif age_months < 12:
            return "建议每 2-3 个月体检一次"
        elif age_months < 84:
            return "建议每年体检一次（基础项目：血常规、生化、尿检）"
        else:
            return "建议每 6 个月体检一次（老年猫重点：肾功、甲功、心超、血压）"


# ----------------------------------------------------------------------
# Self-test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    agent = HealthAdvisorAgent()

    # 测试：成年英短
    report = agent.generate_report(
        cat={
            "age_months": 36,
            "breed": "英短",
            "gender": "male",
            "weight_kg": 5.2,
        },
        weight_history=[
            {"weight_kg": 5.0, "log_date": "2025-01-01"},
            {"weight_kg": 5.2, "log_date": "2025-04-01"},
        ],
        feeding_history=[{"meal_type": "干粮", "amount_grams": 60}],
        recent_vitals=[
            {
                "weight_kg": 5.2,
                "appetite_score": 4,
                "water_intake_ml": 200,
            }
        ],
    )
    print(f"Status: {report['overall_status']}")
    print(f"Weight: {report['weight_assessment']['status']}")
    print(f"Diet: {report['diet_recommendation']['main_advice']}")
    print(f"Vaccines: {len(report['vaccine_reminders'])} reminders")
    print(f"Risks: {report['risk_alerts']}")
    print(f"Checkup: {report['next_checkup_suggestion']}")
