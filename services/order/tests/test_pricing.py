import unittest
from unittest import mock

from app import pricing


def _with_flag(flag: str):
    return mock.patch.object(pricing.settings, "experiment_flag", flag)


class CalculateTotalTest(unittest.TestCase):
    def test_small_basket_without_flag(self):
        with _with_flag(""):
            self.assertEqual(pricing.calculate_total([(10.0, 2)]), 20.0)

    def test_bulk_discount_without_flag(self):
        with _with_flag(""):
            self.assertEqual(pricing.calculate_total([(10.0, 5)]), 45.0)

    def test_promo_v2_five_items_does_not_divide_by_zero(self):
        # Regression: total_qty == 5 used to raise ZeroDivisionError.
        with _with_flag("promo_v2"):
            self.assertEqual(pricing.calculate_total([(10.0, 5)]), 42.5)

    def test_promo_v2_totals_stay_positive(self):
        # Regression: baskets larger than 5 items used to get negative totals.
        with _with_flag("promo_v2"):
            for qty in range(1, 12):
                total = pricing.calculate_total([(10.0, qty)])
                self.assertGreater(total, 0.0)
                self.assertLess(total, 10.0 * qty)

    def test_promo_v2_mixed_basket(self):
        with _with_flag("promo_v2"):
            self.assertEqual(pricing.calculate_total([(199.25, 1), (50.0, 4)]), 339.36)

    def test_empty_basket_is_zero(self):
        with _with_flag("promo_v2"):
            self.assertEqual(pricing.calculate_total([]), 0.0)


if __name__ == "__main__":
    unittest.main()
