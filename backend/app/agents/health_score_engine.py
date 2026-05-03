"""HealthScoreEngine — 综合健康评分引擎

基于猫咪的多维度健康数据，计算 0-100 的综合健康评分。
与前端 HealthProfile.tsx 的评分规则保持一致。
"""

from datetime import datetime, timedelta
from typing import Any, Optional


class HealthScoreEngine:
    """综合健康评分引擎"""

    def calculate(
        self,
        weight_kg: Optional[float] = None,
        weight_history: Optional[list[dict[str, Any]]] = None,
        indicators: Optional[list[dict[str, Any]]] = None,
        symptom_logs: Optional[list[dict[str, Any]]] = None,
        records: Optional[list[dict[str, Any]]] = None,
        age_months: int = 0,
    ) -> dict[str, Any]:
        scores = {
            "base": 80,
            "weight_bonus": 0,
            "indicator_bonus": 0,
            "symptom_bonus": 0,
            "treatment_bonus": 0,
        }

        # 1. 体重加分（3-6kg 为正常范围）
        if weight_kg is not None and 3.0 <= weight_kg <= 6.0:
            scores["weight_bonus"] = 5
        elif weight_kg is not None:
            # 体重在 2.5-3kg 或 6-7kg 给 3 分
            if 2.5 <= weight_kg < 3.0 or 6.0 < weight_kg <= 7.0:
                scores["weight_bonus"] = 3

        # 2. 指标正常率加分
        if indicators:
            total = len(indicators)
            normal = sum(1 for i in indicators if not i.get("is_abnormal", True))
            if total > 0 and normal / total > 0.8:
                scores["indicator_bonus"] = 5

        # 3. 近期症状加分（30天内无症状 +5）
        if symptom_logs is not None:
            now = datetime.now()
            recent = [
                s for s in symptom_logs
                if s.get("created_at") and (now - datetime.fromisoformat(s["created_at"])).days <= 30
            ]
            if len(recent) == 0:
                scores["symptom_bonus"] = 5

        # 4. 诊疗完成度加分
        if records:
            if all(r.get("treatment_status") == "resolved" for r in records if r.get("treatment_status")):
                scores["treatment_bonus"] = 5

        total = sum(scores.values())
        total = max(40, min(100, total))

        return {
            "total_score": total,
            "breakdown": scores,
            "dimension_scores": {
                "weight": min(100, 60 + scores["weight_bonus"] * 4),
                "indicators": min(100, 60 + scores["indicator_bonus"] * 4),
                "symptoms": min(100, 60 + scores["symptom_bonus"] * 4),
                "treatment": min(100, 60 + scores["treatment_bonus"] * 4),
            },
            "grade": self._grade(total),
            "generated_at": datetime.now().isoformat(),
        }

    def _grade(self, score: int) -> str:
        if score >= 80:
            return "优秀"
        if score >= 60:
            return "良好"
        return "需关注"
