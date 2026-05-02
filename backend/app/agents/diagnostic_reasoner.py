"""DiagnosticReasonerAgent — 推理诊断 Agent（纯规则引擎，无 LLM 依赖）

基于结构化症状和体征数据，通过规则匹配输出可能疾病的 Top 3 列表。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DiagnosticReasonerAgent:
    """推理诊断 Agent — 基于症状和体征匹配可能疾病"""

    def __init__(self):
        # 疾病知识库（初期硬编码，后续 Phase 10 升级为 JSON/YAML）
        self.disease_knowledge: list[dict[str, Any]] = [
            # ==========================================================
            # 消化系统
            # ==========================================================
            {
                "name": "急性肠胃炎",
                "category": "消化系统",
                "key_symptoms": ["呕吐", "腹泻", "食欲下降"],
                "related_symptoms": ["精神萎靡", "腹部不适", "发热", "软便"],
                "risk_factors": [],
                "suggested_exams": ["血常规", "粪检", "腹部触诊"],
                "typical_visit_level": "routine",
                "notes": "常见于饮食不当、细菌或病毒感染",
            },
            {
                "name": "猫瘟 (FPV)",
                "category": "消化系统",
                "key_symptoms": ["呕吐", "腹泻", "精神萎靡", "拒食"],
                "related_symptoms": ["发热", "脱水", "白细胞低", "软便"],
                "risk_factors": ["未接种疫苗", "幼猫"],
                "suggested_exams": ["猫瘟抗原检测", "血常规", "生化"],
                "typical_visit_level": "urgent",
                "notes": "猫泛白细胞减少症，传染性强，幼猫致死率高",
            },
            {
                "name": "毛球症",
                "category": "消化系统",
                "key_symptoms": ["呕吐", "吐毛球", "干呕"],
                "related_symptoms": ["食欲下降", "便秘", "精神萎靡"],
                "risk_factors": [],
                "suggested_exams": ["腹部X光", "触诊"],
                "typical_visit_level": "non_urgent",
                "notes": "长毛猫常见，可通过化毛膏/猫草缓解",
            },
            {
                "name": "便秘",
                "category": "消化系统",
                "key_symptoms": ["便秘", "排便困难", "几天不排便"],
                "related_symptoms": ["食欲下降", "腹部胀", "精神萎靡"],
                "risk_factors": [],
                "suggested_exams": ["腹部触诊", "X光"],
                "typical_visit_level": "routine",
                "notes": "老年猫或饮水不足时常见",
            },
            {
                "name": "肠道异物",
                "category": "消化系统",
                "key_symptoms": ["呕吐", "拒食", "腹部疼痛"],
                "related_symptoms": ["精神萎靡", "便秘", "腹泻", "干呕"],
                "risk_factors": ["吞食异物史", "好奇心强"],
                "suggested_exams": ["腹部X光", "B超", "造影"],
                "typical_visit_level": "urgent",
                "notes": "需尽快排除肠梗阻风险，可能需要手术",
            },
            # ==========================================================
            # 呼吸系统
            # ==========================================================
            {
                "name": "猫鼻支 (FHV)",
                "category": "呼吸系统",
                "key_symptoms": ["打喷嚏", "流鼻涕", "流泪", "发热"],
                "related_symptoms": ["咳嗽", "食欲不振", "口腔溃疡", "精神萎靡"],
                "risk_factors": ["未接种疫苗", "多猫环境"],
                "suggested_exams": ["PCR检测", "血常规", "眼部检查"],
                "typical_visit_level": "routine",
                "notes": "猫疱疹病毒感染，终身潜伏，应激可复发",
            },
            {
                "name": "上呼吸道感染",
                "category": "呼吸系统",
                "key_symptoms": ["打喷嚏", "咳嗽", "流鼻涕"],
                "related_symptoms": ["精神萎靡", "低烧", "流泪", "鼻塞"],
                "risk_factors": [],
                "suggested_exams": ["血常规", "胸片"],
                "typical_visit_level": "routine",
                "notes": "细菌或病毒引起的鼻腔/咽喉感染",
            },
            {
                "name": "哮喘/过敏",
                "category": "呼吸系统",
                "key_symptoms": ["呼吸困难", "咳嗽", "呼吸急促"],
                "related_symptoms": ["精神萎靡", "食欲下降", "张口呼吸"],
                "risk_factors": [],
                "suggested_exams": ["胸片", "过敏原检测"],
                "typical_visit_level": "urgent",
                "notes": "若出现严重呼吸困难需视为急诊",
            },
            # ==========================================================
            # 泌尿系统
            # ==========================================================
            {
                "name": "膀胱炎/尿道炎",
                "category": "泌尿系统",
                "key_symptoms": ["尿频", "尿血", "排尿困难", "乱尿"],
                "related_symptoms": ["精神萎靡", "舔生殖器", "腹部不适"],
                "risk_factors": [],
                "suggested_exams": ["尿常规", "B超", "血常规"],
                "typical_visit_level": "routine",
                "notes": "细菌感染或特发性膀胱炎，母猫更常见",
            },
            {
                "name": "尿闭 (FIC/FLUTD)",
                "category": "泌尿系统",
                "key_symptoms": ["排尿困难", "尿少", "频繁蹲猫砂盆", "腹部疼痛"],
                "related_symptoms": ["呕吐", "精神萎靡", "拒食", "舔生殖器"],
                "risk_factors": ["公猫"],
                "suggested_exams": ["B超", "尿常规", "生化", "电解质"],
                "typical_visit_level": "emergency",
                "notes": "公猫尿道阻塞可致急性肾衰，24h 内可致命",
            },
            {
                "name": "慢性肾病 (CKD)",
                "category": "泌尿系统",
                "key_symptoms": ["多饮多尿", "体重下降", "食欲下降", "呕吐"],
                "related_symptoms": ["精神萎靡", "口臭", "贫血", "脱水"],
                "risk_factors": ["老年猫", "7岁以上"],
                "suggested_exams": ["生化", "SDMA", "尿常规", "血压", "B超"],
                "typical_visit_level": "routine",
                "notes": "中老年猫常见病，不可逆但可管理",
            },
            # ==========================================================
            # 内分泌/代谢
            # ==========================================================
            {
                "name": "糖尿病",
                "category": "内分泌/代谢",
                "key_symptoms": ["多饮多尿", "体重下降", "食欲增加但消瘦"],
                "related_symptoms": ["精神萎靡", "呕吐", "脱水"],
                "risk_factors": ["肥胖", "老年猫"],
                "suggested_exams": ["血糖", "果糖胺", "尿糖", "生化"],
                "typical_visit_level": "routine",
                "notes": "常见于肥胖老年猫，需胰岛素治疗",
            },
            {
                "name": "甲状腺功能亢进",
                "category": "内分泌/代谢",
                "key_symptoms": ["多饮多尿", "体重下降", "食欲亢进", "亢奋"],
                "related_symptoms": ["呕吐", "腹泻", "心跳加快", "多动"],
                "risk_factors": ["老年猫", "8岁以上"],
                "suggested_exams": ["T4检测", "生化", "心电图"],
                "typical_visit_level": "routine",
                "notes": "老年猫常见病，甲状腺激素分泌过多",
            },
            {
                "name": "脂肪肝 (HL)",
                "category": "内分泌/代谢",
                "key_symptoms": ["拒食", "精神萎靡", "黄疸", "体重快速下降"],
                "related_symptoms": ["呕吐", "脱水", "腹部不适", "虚弱"],
                "risk_factors": ["肥胖猫", "应激后绝食"],
                "suggested_exams": ["生化", "B超", "胆红素"],
                "typical_visit_level": "urgent",
                "notes": "继发于厌食，肝内脂肪沉积，需强制饲喂",
            },
            # ==========================================================
            # 其他
            # ==========================================================
            {
                "name": "猫传腹 (FIP)",
                "category": "其他",
                "key_symptoms": ["发热", "精神萎靡", "食欲下降", "腹水"],
                "related_symptoms": ["体重下降", "腹泻", "胸水", "眼部病变", "黄疸"],
                "risk_factors": ["幼猫", "多猫环境", "冠状病毒感染史"],
                "suggested_exams": ["生化", "血常规", "B超/胸片", "FIP抗体"],
                "typical_visit_level": "urgent",
                "notes": "猫冠状病毒变异所致，湿性/干性两种表现",
            },
            {
                "name": "耳螨/耳炎",
                "category": "其他",
                "key_symptoms": ["耳垢", "抓耳朵", "甩头", "耳朵异味"],
                "related_symptoms": ["红肿", "疼痛", "脱毛"],
                "risk_factors": [],
                "suggested_exams": ["耳镜检查", "分泌物镜检"],
                "typical_visit_level": "routine",
                "notes": "耳螨为寄生虫，耳炎多为细菌/真菌感染",
            },
            {
                "name": "皮肤真菌 (猫癣)",
                "category": "其他",
                "key_symptoms": ["掉毛", "皮屑", "红疹", "圆形脱毛"],
                "related_symptoms": ["抓挠", "结痂", "瘙痒"],
                "risk_factors": [],
                "suggested_exams": ["伍德氏灯", "真菌培养", "皮肤刮片"],
                "typical_visit_level": "routine",
                "notes": "人畜共患，需隔离治疗",
            },
            {
                "name": "中毒",
                "category": "其他",
                "key_symptoms": ["呕吐", "腹泻", "精神萎靡", "抽搐", "流口水"],
                "related_symptoms": ["拒食", "呼吸困难", "瞳孔异常", "共济失调"],
                "risk_factors": ["接触毒物", "散养", "好奇心强"],
                "suggested_exams": ["血常规", "生化", "毒物筛查"],
                "typical_visit_level": "emergency",
                "notes": "需尽快明确毒物种类以便针对性治疗",
            },
            {
                "name": "外伤",
                "category": "其他",
                "key_symptoms": ["出血", "跛行", "疼痛", "肿胀"],
                "related_symptoms": ["精神萎靡", "拒食", "舔舐伤口"],
                "risk_factors": ["散养", "多猫打架"],
                "suggested_exams": ["X光", "血常规", "伤口检查"],
                "typical_visit_level": "urgent",
                "notes": "需排除骨折、内出血等严重损伤",
            },
        ]

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def diagnose(
        self,
        symptoms: list[str],
        vital_signs: dict[str, Any] | None = None,
        history: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        输入:
          - symptoms: list[str], 结构化症状关键词列表
          - vital_signs: dict, 体征数据 {temperature_celsius, heart_rate, ...}
          - history: dict, 病史（可选）{age_months, breed, previous_conditions}
        输出:
          dict: {
            "possible_diseases": [...],
            "differential_diagnosis_note": str,
            "disclaimer": str,
            "timestamp": str,
          }
        """
        vital_signs = vital_signs or {}
        history = history or {}

        # 1. 计算每种疾病的匹配得分
        scored_diseases: list[tuple[float, dict[str, Any]]] = []
        for disease in self.disease_knowledge:
            score = self._calculate_match_score(disease, symptoms, vital_signs, history)
            scored_diseases.append((score, disease))

        # 2. 排序取 Top 3
        scored_diseases.sort(key=lambda x: x[0], reverse=True)
        top_diseases = scored_diseases[:3]

        # 3. 构建输出结构
        possible_diseases = []
        for score, disease in top_diseases:
            if score <= 0:
                continue  # 完全没匹配的不输出
            matched = self._get_matched_symptoms(disease, symptoms)
            probability = self._score_to_probability(score)
            visit_level = self._determine_visit_level(disease, score)
            possible_diseases.append(
                {
                    "disease": disease["name"],
                    "probability": probability,
                    "confidence_score": round(min(score, 1.0), 2),
                    "matched_symptoms": matched,
                    "suggested_exams": disease["suggested_exams"],
                    "recommended_visit_level": visit_level,
                }
            )

        # 4. 鉴别诊断说明
        note = self._generate_differential_note(possible_diseases, symptoms, vital_signs)

        return {
            "possible_diseases": possible_diseases,
            "differential_diagnosis_note": note,
            "disclaimer": "仅供参考，不构成医疗建议",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # 匹配算法
    # ------------------------------------------------------------------
    def _calculate_match_score(
        self,
        disease: dict[str, Any],
        symptoms: list[str],
        vital_signs: dict[str, Any],
        history: dict[str, Any],
    ) -> float:
        """
        计算匹配得分:
        - key_symptoms 命中: 每个 +0.3
        - related_symptoms 命中: 每个 +0.1
        - 风险因素匹配: 额外 +0.1-0.2
        - 体征加成: 按规则额外加分

        总分上限 1.0（超过截断）
        """
        score = 0.0

        # 症状匹配
        key_symptoms = disease.get("key_symptoms", [])
        related_symptoms = disease.get("related_symptoms", [])

        for symptom in symptoms:
            if symptom in key_symptoms:
                score += 0.3
            elif symptom in related_symptoms:
                score += 0.1

        # 风险因素匹配
        risk_factors = disease.get("risk_factors", [])
        if risk_factors and history:
            # 未接种疫苗 → 猫瘟/猫鼻支风险提升
            if "vaccinated" in history and not history["vaccinated"]:
                if "未接种疫苗" in risk_factors:
                    score += 0.2
            # 幼猫
            age_months = history.get("age_months")
            if age_months is not None and age_months < 6:
                if "幼猫" in risk_factors:
                    score += 0.15
            # 老年猫
            if age_months is not None and age_months > 84:  # 7岁+
                if "老年猫" in risk_factors or "8岁以上" in risk_factors or "7岁以上" in risk_factors:
                    score += 0.15
            # 公猫
            sex = history.get("sex")
            if sex == "公" or sex == "male":
                if "公猫" in risk_factors:
                    score += 0.2
            # 肥胖
            if history.get("overweight"):
                if "肥胖" in risk_factors or "肥胖猫" in risk_factors:
                    score += 0.1

        # 体征加成
        score = self._apply_vital_bonus(score, disease, vital_signs, symptoms)

        return min(score, 1.0)

    def _apply_vital_bonus(
        self,
        score: float,
        disease: dict[str, Any],
        vital_signs: dict[str, Any],
        symptoms: list[str],
    ) -> float:
        """根据体征数据对匹配得分进行加成"""
        temp = vital_signs.get("temperature_celsius")
        hr = vital_signs.get("heart_rate")
        rr = vital_signs.get("respiratory_rate")

        # 体温异常 + 消化症状 → 肠胃炎/猫瘟概率提升
        if temp is not None and (temp > 39.5 or temp < 37.5):
            if disease["category"] == "消化系统":
                if any(s in symptoms for s in ["呕吐", "腹泻", "拒食"]):
                    score += 0.15

        # 呼吸困难 + 呼吸道症状 → 哮喘/过敏/感染概率提升
        if rr is not None and rr > 40:
            if disease["category"] == "呼吸系统":
                if any(s in symptoms for s in ["呼吸困难", "咳嗽", "呼吸急促"]):
                    score += 0.2

        # 心跳异常 + 内分泌症状 → 甲亢概率提升
        if hr is not None and hr > 200:
            if disease["name"] == "甲状腺功能亢进":
                score += 0.15

        # 尿血 + 排尿困难 → 膀胱炎/尿闭概率提升
        if "尿血" in symptoms and "排尿困难" in symptoms:
            if disease["category"] == "泌尿系统":
                score += 0.15

        # 黄疸 + 拒食 → 脂肪肝概率提升
        if "黄疸" in symptoms and "拒食" in symptoms:
            if disease["name"] == "脂肪肝 (HL)":
                score += 0.2

        # 多饮多尿 + 体重下降 → 糖尿病/甲亢/肾病概率提升
        if "多饮多尿" in symptoms and "体重下降" in symptoms:
            if disease["name"] in ["糖尿病", "甲状腺功能亢进", "慢性肾病 (CKD)"]:
                score += 0.15

        # 体温过低 + 精神萎靡 → 猫瘟/传腹概率提升
        if temp is not None and temp < 37.5:
            if disease["name"] in ["猫瘟 (FPV)", "猫传腹 (FIP)"]:
                if "精神萎靡" in symptoms:
                    score += 0.15

        return score

    def _get_matched_symptoms(self, disease: dict[str, Any], symptoms: list[str]) -> list[str]:
        """返回用户症状中命中该疾病的症状列表"""
        all_disease_symptoms = set(disease.get("key_symptoms", []) + disease.get("related_symptoms", []))
        return [s for s in symptoms if s in all_disease_symptoms]

    def _score_to_probability(self, score: float) -> str:
        """将得分转换为概率等级"""
        if score >= 0.7:
            return "高"
        elif score >= 0.4:
            return "中"
        else:
            return "低"

    def _determine_visit_level(self, disease: dict[str, Any], score: float) -> str:
        """确定建议就医级别"""
        base_level = disease.get("typical_visit_level", "routine")
        # 如果得分高且涉及急症，保持急症级别
        if score >= 0.5 and base_level == "emergency":
            return "emergency"
        if score >= 0.5 and base_level == "urgent":
            return "urgent"
        return base_level

    def _generate_differential_note(
        self,
        possible_diseases: list[dict[str, Any]],
        symptoms: list[str],
        vital_signs: dict[str, Any],
    ) -> str:
        """根据 Top 3 结果生成鉴别诊断说明"""
        if not possible_diseases:
            return "根据当前症状无法给出明确倾向，建议进一步检查。"

        diseases = [d["disease"] for d in possible_diseases]
        notes: list[str] = []

        # 如果多个疾病共享症状，生成鉴别建议
        if len(possible_diseases) >= 2:
            top1, top2 = possible_diseases[0], possible_diseases[1]
            # 检查是否有共同症状
            shared = set(top1["matched_symptoms"]) & set(top2["matched_symptoms"])
            if shared:
                notes.append(
                    f"主要需鉴别 {top1['disease']} 与 {top2['disease']}，"
                    f"建议通过 {', '.join(top1['suggested_exams'][:2])} 区分。"
                )

        # 检查是否涉及传染病
        infectious = [d for d in possible_diseases if any(x in d["disease"] for x in ["猫瘟", "猫鼻支", "猫传腹", "猫癣"])]
        if infectious:
            notes.append(
                f"建议优先排查 {infectious[0]['disease']}，因其具有传染性且需要隔离治疗。"
            )

        # 检查是否涉及急症
        emergency_diseases = [d for d in possible_diseases if d["recommended_visit_level"] == "emergency"]
        if emergency_diseases:
            notes.append(
                f"请注意 {emergency_diseases[0]['disease']} 可能危及生命，建议尽快就医。"
            )

        # 如果用户提供了体征数据但不够完整
        if not vital_signs:
            notes.append("建议补充体温、心率等基础体征数据以提高诊断准确性。")

        if not notes:
            return "建议根据猫咪整体状态综合评估，如有恶化请及时就医。"

        return " ".join(notes)


# ------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = DiagnosticReasonerAgent()

    # 测试 1: 呕吐+腹泻+精神差（疑似猫瘟/肠胃炎）
    result = agent.diagnose(
        symptoms=["呕吐", "腹泻", "精神萎靡", "拒食"],
        vital_signs={"temperature_celsius": 39.8, "heart_rate": 150},
        history={"age_months": 6, "breed": "英短", "vaccinated": False},
    )
    print("=== 测试 1: 呕吐+腹泻+精神差 ===")
    print(f"Top 3: {[d['disease'] + '(' + d['probability'] + ')' for d in result['possible_diseases']]}")
    print(f"Note: {result['differential_diagnosis_note']}")
    print()

    # 测试 2: 多饮多尿+体重下降（疑似糖尿病/甲亢/肾病）
    result2 = agent.diagnose(
        symptoms=["多饮多尿", "体重下降", "食欲增加但消瘦"],
        vital_signs={"temperature_celsius": 38.5, "heart_rate": 220},
        history={"age_months": 120, "breed": "橘猫", "overweight": True},
    )
    print("=== 测试 2: 多饮多尿+体重下降 ===")
    print(f"Top 3: {[d['disease'] + '(' + d['probability'] + ')' for d in result2['possible_diseases']]}")
    print(f"Note: {result2['differential_diagnosis_note']}")
    print()

    # 测试 3: 呼吸困难+咳嗽（疑似哮喘/上呼吸道感染）
    result3 = agent.diagnose(
        symptoms=["呼吸困难", "咳嗽", "呼吸急促"],
        vital_signs={"respiratory_rate": 55},
        history={"age_months": 36},
    )
    print("=== 测试 3: 呼吸困难+咳嗽 ===")
    print(f"Top 3: {[d['disease'] + '(' + d['probability'] + ')' for d in result3['possible_diseases']]}")
    print(f"Note: {result3['differential_diagnosis_note']}")
    print()

    # 测试 4: 排尿困难+尿血（疑似尿闭/膀胱炎）
    result4 = agent.diagnose(
        symptoms=["排尿困难", "尿血", "频繁蹲猫砂盆", "腹部疼痛"],
        vital_signs={"temperature_celsius": 38.8},
        history={"age_months": 24, "sex": "公"},
    )
    print("=== 测试 4: 排尿困难+尿血 ===")
    print(f"Top 3: {[d['disease'] + '(' + d['probability'] + ')' for d in result4['possible_diseases']]}")
    print(f"Note: {result4['differential_diagnosis_note']}")
    print()

    # 测试 5: 黄疸+拒食（疑似脂肪肝）
    result5 = agent.diagnose(
        symptoms=["黄疸", "拒食", "精神萎靡", "体重快速下降"],
        vital_signs={},
        history={"age_months": 60, "overweight": True},
    )
    print("=== 测试 5: 黄疸+拒食 ===")
    print(f"Top 3: {[d['disease'] + '(' + d['probability'] + ')' for d in result5['possible_diseases']]}")
    print(f"Note: {result5['differential_diagnosis_note']}")
