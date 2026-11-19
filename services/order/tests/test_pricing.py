from app import pricing


def test_calculate_total_default():
    assert pricing.calculate_total([(10.0, 1)]) == 10.0
    assert pricing.calculate_total([(10.0, 5)]) == 45.0


def test_calculate_total_promo_v2_never_divides_by_zero(monkeypatch):
    monkeypatch.setattr(pricing.settings, "experiment_flag", "promo_v2", raising=False)
    for qty in (1, 2, 4, 5, 6, 10, 50):
        total = pricing.calculate_total([(10.0, qty)])
        assert total > 0, f"non-positive total for qty={qty}: {total}"
