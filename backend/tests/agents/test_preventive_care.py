def test_vaccination_model_fields():
    from app.models.models import VaccinationRecord
    assert hasattr(VaccinationRecord, 'vaccine_type')
    assert hasattr(VaccinationRecord, 'next_due_at')

def test_deworming_model_fields():
    from app.models.models import DewormingRecord
    assert hasattr(DewormingRecord, 'product_name')
    assert hasattr(DewormingRecord, 'next_due_at')
