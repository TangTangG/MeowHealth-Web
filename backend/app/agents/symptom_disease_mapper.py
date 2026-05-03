"""SymptomDiseaseMapper — 症状-疾病关联引擎（纯规则引擎，无 LLM 依赖）

基于结构化症状数据，结合品种/年龄/体征，输出可能疾病的排序列表。
兼容 DiagnosticReasonerAgent 的疾病知识库。
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class SymptomDiseaseMapper:
    """症状-疾病关联引擎"""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path(__file__).parent.parent / "ai" / "skills"
        self.disease_knowledge: list[dict[str, Any]] = []
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        """加载疾病知识库（外部 skills + 内置 fallback）"""
        diseases_dir = self.skills_dir / "diseases"
        if diseases_dir.exists():
            for md_file in diseases_dir.glob("*.md"):
                disease = self._parse_disease_markdown(md_file)
                if disease:
                    self.disease_knowledge.append(disease)
        if not self.disease_knowledge:
            self.disease_knowledge = self._built_in_knowledge()

    def _parse_disease_markdown(self, path: Path) -> Optional[dict[str, Any]]:
        content = path.read_text(encoding="utf-8")
        name = path.stem
        disease = {"name": name, "file": str(path), "category": "未知"}
        symptoms = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("-") and not line.startswith("-"):
                pass
            if line.startswith("-") and "**" not in line and len(line) < 60:
                symptom = line.lstrip("- ").strip()
                if symptom:
                    symptoms.append(symptom)
        disease["key_symptoms"] = symptoms[:6]
        disease["related_symptoms"] = symptoms[6:12]
        disease["risk_factors"] = self._extract_risk_factors(content)
        disease["suggested_exams"] = self._extract_exams(content)
        disease["category"] = self._extract_category(content)
        return disease

    def _extract_risk_factors(self, content: str) -> list[str]:
        factors = []
        in_risk = False
        for line in content.splitlines():
            if "## 风险因素" in line or "## 风险" in line:
                in_risk = True
                continue
            if in_risk and line.startswith("##"):
                break
            if in_risk and line.startswith("-"):
                factors.append(line.lstrip("- ").strip())
        return factors[:6]

    def _extract_exams(self, content: str) -> list[str]:
        exams = []
        in_exam = False
        for line in content.splitlines():
            if "## 建议检查" in line or "## 检查" in line or "## 诊断" in line:
                in_exam = True
                continue
            if in_exam and line.startswith("##"):
                break
            if in_exam and line.startswith("-"):
                exams.append(line.lstrip("- ").strip().split("：")[0])
        return exams[:4]

    def _extract_category(self, content: str) -> str:
        for line in content.splitlines():
            if "## 概述" in line:
                continue
            if line.startswith("##"):
                continue
            if "肾" in line or "泌尿" in line:
                return "泌尿系统"
            if "心脏" in line or "心肌" in line:
                return "心血管"
            if "内分泌" in line or "甲状腺" in line or "糖尿病" in line:
                return "内分泌/代谢"
            if "消化" in line or "肠胃" in line or "胰腺" in line or "肝脏" in line:
                return "消化系统"
            if "呼吸" in line or "鼻" in line:
                return "呼吸系统"
            if "皮肤" in line:
                return "皮肤"
            if "肿瘤" in line or "癌" in line or "淋巴瘤" in line:
                return "肿瘤"
            if "传染" in line or "病毒" in line or "冠状" in line:
                return "传染病"
        return "其他"

    def map(
        self,
        symptoms: list[str],
        breed: str = "",
        age_months: int = 0,
        vital_signs: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        if not symptoms:
            return []
        vital_signs = vital_signs or {}
        scored: list[tuple[float, dict[str, Any]]] = []
        for disease in self.disease_knowledge:
            score = self._calculate_match_score(disease, symptoms, vital_signs, {"age_months": age_months, "breed": breed})
            scored.append((score, disease))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:5]
        result = []
        for score, disease in top:
            if score <= 0:
                continue
            matched = self._get_matched_symptoms(disease, symptoms)
            probability = self._score_to_probability(score)
            age_factor = self._get_age_factor(disease, age_months)
            result.append({
                "disease": disease["name"],
                "match_score": round(score, 2),
                "probability": probability,
                "age_factor": age_factor,
                "matched_symptoms": matched,
                "suggested_exams": disease.get("suggested_exams", []),
                "category": disease.get("category", "其他"),
            })
        return result

    def _calculate_match_score(
        self, disease: dict[str, Any], symptoms: list[str],
        vital_signs: dict[str, Any], history: dict[str, Any]
    ) -> float:
        score = 0.0
        key_symptoms = [s.strip() for s in disease.get("key_symptoms", [])]
        related_symptoms = [s.strip() for s in disease.get("related_symptoms", [])]
        symptom_lower = [s.lower() for s in symptoms]
        for ks in key_symptoms:
            if any(ks.lower() in sl or sl in ks.lower() for sl in symptom_lower):
                score += 0.3
        for rs in related_symptoms:
            if any(rs.lower() in sl or sl in rs.lower() for sl in symptom_lower):
                score += 0.1
        # 品种因素
        breed = history.get("breed", "").lower()
        for risk in disease.get("risk_factors", []):
            risk_lower = risk.lower()
            if breed and any(b in risk_lower for b in breed.split() if len(b) > 1):
                score += 0.15
        # 年龄因素
        age_months = history.get("age_months", 0)
        for risk in disease.get("risk_factors", []):
            if "幼猫" in risk and age_months < 12:
                score += 0.15
            if "老年猫" in risk and age_months > 84:
                score += 0.15
            if "7岁" in risk or "8岁" in risk:
                if age_months > 84:
                    score += 0.15
        # 体征加成
        score += self._apply_vital_bonus(disease, vital_signs)
        return min(score, 1.0)

    def _get_matched_symptoms(self, disease: dict[str, Any], symptoms: list[str]) -> list[str]:
        all_disease_symptoms = disease.get("key_symptoms", []) + disease.get("related_symptoms", [])
        matched = []
        symptom_lower = [s.lower() for s in symptoms]
        for ds in all_disease_symptoms:
            ds_lower = ds.lower()
            if any(ds_lower in sl or sl in ds_lower for sl in symptom_lower):
                matched.append(ds)
        return matched

    def _score_to_probability(self, score: float) -> str:
        if score >= 0.7:
            return "高"
        if score >= 0.4:
            return "中"
        if score >= 0.2:
            return "低"
        return "极低"

    def _get_age_factor(self, disease: dict[str, Any], age_months: int) -> str:
        for risk in disease.get("risk_factors", []):
            if "幼猫" in risk and age_months < 12:
                return "高"
            if "老年猫" in risk and age_months > 84:
                return "高"
        return "中"

    def _apply_vital_bonus(self, disease: dict[str, Any], vital_signs: dict[str, Any]) -> float:
        bonus = 0.0
        temp = vital_signs.get("temperature_celsius")
        if temp and temp > 39.5:
            if any(k in disease.get("name", "") for k in ["瘟", "感染", "传腹", "鼻支"]):
                bonus += 0.1
        hr = vital_signs.get("heart_rate")
        if hr and hr > 220:
            if any(k in disease.get("name", "") for k in ["甲亢", "心脏", "心肌"]):
                bonus += 0.1
        rr = vital_signs.get("respiratory_rate")
        if rr and rr > 40:
            if any(k in disease.get("name", "") for k in ["心脏", "呼吸", "哮喘", "胸"]):
                bonus += 0.1
        return bonus

    def _built_in_knowledge(self) -> list[dict[str, Any]]:
        # 内置精简版知识库 fallback
        return [
            {"name": "ckd", "category": "泌尿系统", "key_symptoms": ["多饮多尿", "体重下降", "食欲下降", "呕吐"], "related_symptoms": ["精神萎靡", "口臭", "贫血", "脱水"], "risk_factors": ["老年猫", "7岁以上"], "suggested_exams": ["生化", "SDMA", "尿常规"]},
            {"name": "hyperthyroid", "category": "内分泌/代谢", "key_symptoms": ["多饮多尿", "体重下降", "食欲亢进", "亢奋"], "related_symptoms": ["呕吐", "腹泻", "心跳加快", "多动"], "risk_factors": ["老年猫", "8岁以上"], "suggested_exams": ["T4", "生化", "心电图"]},
            {"name": "diabetes", "category": "内分泌/代谢", "key_symptoms": ["多饮多尿", "体重下降", "食欲增加但消瘦"], "related_symptoms": ["精神萎靡", "呕吐", "脱水"], "risk_factors": ["肥胖", "老年猫"], "suggested_exams": ["血糖", "果糖胺", "尿糖"]},
            {"name": "fip", "category": "传染病", "key_symptoms": ["发热", "精神萎靡", "食欲下降", "腹水"], "related_symptoms": ["体重下降", "腹泻", "胸水", "眼部病变"], "risk_factors": ["幼猫", "多猫环境"], "suggested_exams": ["生化", "血常规", "B超"]},
            {"name": "fpv", "category": "传染病", "key_symptoms": ["呕吐", "腹泻", "精神萎靡", "拒食"], "related_symptoms": ["发热", "脱水", "白细胞低"], "risk_factors": ["未接种疫苗", "幼猫"], "suggested_exams": ["猫瘟抗原", "血常规", "生化"]},
            {"name": "fhv", "category": "呼吸系统", "key_symptoms": ["打喷嚏", "流鼻涕", "流泪", "发热"], "related_symptoms": ["咳嗽", "食欲不振", "口腔溃疡"], "risk_factors": ["未接种疫苗", "多猫环境"], "suggested_exams": ["PCR", "血常规"]},
            {"name": "hcm", "category": "心血管", "key_symptoms": ["呼吸困难", "活动耐受下降", "后肢瘫痪"], "related_symptoms": ["精神萎靡", "食欲下降", "猝死"], "risk_factors": ["缅因猫", "布偶猫"], "suggested_exams": ["心脏超声", "NT-proBNP", "心电图"]},
            {"name": "flutd", "category": "泌尿系统", "key_symptoms": ["尿频", "尿血", "排尿困难", "乱尿"], "related_symptoms": ["精神萎靡", "舔生殖器", "腹部不适"], "risk_factors": ["公猫"], "suggested_exams": ["尿常规", "B超", "生化"]},
            {"name": "pancreatitis", "category": "消化系统", "key_symptoms": ["食欲下降", "呕吐", "腹痛"], "related_symptoms": ["弓背", "精神萎靡", "脱水"], "risk_factors": ["肥胖猫", "脂肪肝并发"], "suggested_exams": ["fPL", "超声", "生化"]},
            {"name": "fatty_liver", "category": "消化系统", "key_symptoms": ["拒食", "黄疸", "精神萎靡", "体重快速下降"], "related_symptoms": ["呕吐", "脱水", "虚弱"], "risk_factors": ["肥胖猫", "应激后绝食"], "suggested_exams": ["生化", "B超", "胆红素"]},
        ]
