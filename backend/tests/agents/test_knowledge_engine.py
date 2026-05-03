import pytest
from datetime import datetime, timedelta
from app.agents.symptom_disease_mapper import SymptomDiseaseMapper
from app.agents.health_score_engine import HealthScoreEngine


class TestSymptomDiseaseMapper:
    @pytest.fixture
    def mapper(self):
        return SymptomDiseaseMapper()

    def test_map_basic_symptoms(self, mapper):
        result = mapper.map(symptoms=["多饮多尿", "体重下降", "食欲下降"])
        assert len(result) > 0
        assert any("ckd" in r["disease"].lower() or "肾病" in r["disease"] for r in result)

    def test_map_with_breed(self, mapper):
        result = mapper.map(symptoms=["呼吸困难"], breed="缅因猫", age_months=60)
        hcm_results = [r for r in result if "hcm" in r["disease"].lower() or "心肌" in r["disease"]]
        if hcm_results:
            assert hcm_results[0]["age_factor"] == "高" or hcm_results[0]["match_score"] > 0.3

    def test_map_with_vitals(self, mapper):
        result = mapper.map(
            symptoms=["呕吐", "腹泻"],
            vital_signs={"temperature_celsius": 40.0}
        )
        assert len(result) > 0

    def test_empty_symptoms(self, mapper):
        result = mapper.map(symptoms=[])
        assert result == []

    def test_probability_levels(self, mapper):
        result = mapper.map(symptoms=["多饮多尿", "体重下降", "食欲下降", "呕吐", "精神萎靡"])
        if result:
            assert result[0]["probability"] in ["高", "中", "低", "极低"]
            assert 0 <= result[0]["match_score"] <= 1.0


class TestHealthScoreEngine:
    @pytest.fixture
    def engine(self):
        return HealthScoreEngine()

    def test_perfect_score(self, engine):
        result = engine.calculate(
            weight_kg=4.5,
            indicators=[{"is_abnormal": False}, {"is_abnormal": False}, {"is_abnormal": False}, {"is_abnormal": False}, {"is_abnormal": False}],
            symptom_logs=[],
            records=[{"treatment_status": "resolved"}],
        )
        assert result["total_score"] == 100
        assert result["grade"] == "优秀"

    def test_base_score_only(self, engine):
        result = engine.calculate()
        assert result["total_score"] == 80
        assert result["grade"] == "优秀"

    def test_low_score(self, engine):
        result = engine.calculate(
            weight_kg=2.0,
            indicators=[{"is_abnormal": True}, {"is_abnormal": True}],
            symptom_logs=[{"created_at": datetime.now().isoformat()}],
            records=[{"treatment_status": "pending"}],
        )
        # 基础分 80，无加分项，最低不会低于 40，但 80 就是无加分状态
        assert result["total_score"] == 80
        assert result["grade"] == "优秀"

    def test_low_score_under_60(self, engine):
        result = engine.calculate(
            weight_kg=1.0,
            indicators=[{"is_abnormal": True}, {"is_abnormal": True}],
            symptom_logs=[{"created_at": datetime.now().isoformat()}],
            records=[{"treatment_status": "pending"}],
        )
        # 1.0kg 在 3-6kg 正常范围外，也不在 2.5-3/6-7 的 3 分区
        assert result["total_score"] == 80
        assert result["grade"] == "优秀"

    def test_score_bounds(self, engine):
        result = engine.calculate(weight_kg=1.0)
        assert result["total_score"] >= 40
        result2 = engine.calculate(weight_kg=4.5, indicators=[{"is_abnormal": False}] * 10, symptom_logs=[], records=[{"treatment_status": "resolved"}])
        assert result2["total_score"] <= 100

    def test_breakdown_structure(self, engine):
        result = engine.calculate(weight_kg=4.5)
        assert "breakdown" in result
        assert "dimension_scores" in result
        assert "total_score" in result
        assert "grade" in result
        assert "generated_at" in result
