from dataclasses import replace
import json
from pathlib import Path
import unittest

from gon_stock02.risk import EntryState, assess_entry


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((Path(__file__).parents[1] / "config/paper.json").read_text())
        self.policy["order_submission_enabled"] = True
        self.state = EntryState("10000000", "10000000", "10000000", "10000000", "0", "0", 0, 0, 1.0, True, "0")

    def assess(self, state=None, **kwargs):
        args = dict(symbol="005930", venue="KRX", entry="100000", stop="99000", cost_per_share="200")
        args.update(kwargs)
        return assess_entry(self.policy, state or self.state, **args)

    def test_quantity_includes_cost_and_does_not_enable_submission(self):
        self.policy["order_submission_enabled"] = False
        result = self.assess()
        self.assertTrue(result["risk_passed"])
        self.assertFalse(result["allowed"])
        self.assertEqual(result["quantity"], 20)
        self.assertEqual(result["planned_loss_krw"], "24000")
        self.assertEqual(result["reason"], "execution_gate_closed")

    def test_quantity_fits_remaining_daily_loss_budget(self):
        state = replace(self.state, equity="9926000")
        self.assertEqual(self.assess(state)["reason"], "minimum_lot_exceeds_limit")
        result = self.assess(state, stop="99500", cost_per_share="0")
        self.assertEqual(result["quantity"], 2)

    def test_market_verification_requires_boolean_true(self):
        self.assertFalse(self.assess(replace(self.state, venue_verified="false"))["allowed"])
        self.assertFalse(self.assess(replace(self.state, quote_age_seconds=True))["allowed"])

    def test_existing_and_pending_risk_reserves_reduce_budget(self):
        state = replace(self.state, reserved_loss_krw="74000")
        self.assertEqual(self.assess(state)["reason"], "minimum_lot_exceeds_limit")
        self.assertEqual(self.assess(state, stop="99500", cost_per_share="0")["quantity"], 2)
        self.assertFalse(self.assess(replace(state, reserved_loss_krw="-1"))["allowed"])

    def test_intraday_gain_cannot_increase_prior_close_budget(self):
        state = replace(self.state, equity="9900000", day_open_equity="9800000")
        self.assertEqual(self.assess(state, entry="10000", stop="9900", cost_per_share="0")["quantity"], 245)

    def test_enable_flag_does_not_bypass_risk_checks(self):
        self.policy["order_submission_enabled"] = True
        self.assertTrue(self.assess()["allowed"])
        self.assertFalse(self.assess(replace(self.state, quote_age_seconds=None))["allowed"])

    def test_unknown_or_stale_quote_never_passes(self):
        for age in (None, -1, 6, float("nan")):
            self.assertFalse(self.assess(replace(self.state, quote_age_seconds=age))["allowed"])
        self.assertFalse(self.assess(replace(self.state, venue_verified=False))["allowed"])

    def test_nxt_or_real_environment_cannot_pass(self):
        self.assertFalse(self.assess(venue="NXT")["allowed"])
        self.policy["environment"] = "real"
        self.assertFalse(self.assess()["allowed"])

    def test_loss_thresholds_include_equality(self):
        for equity, day, peak in (("9925000", "10000000", "10000000"), ("9700000", "9700000", "10000000"), ("10670000", "10670000", "11000000")):
            result = self.assess(replace(self.state, equity=equity, day_open_equity=day, peak_equity=peak))
            self.assertEqual(result["reason"], "loss_limit")

    def test_position_entry_and_gross_limits(self):
        self.assertEqual(self.assess(replace(self.state, positions=2, gross_exposure="4000000"))["reason"], "position_limit")
        self.assertEqual(self.assess(replace(self.state, entries_today=2))["reason"], "entry_limit")
        self.assertEqual(self.assess(replace(self.state, positions=1, gross_exposure="5000000", symbol_exposure="1000000"))["reason"], "minimum_lot_exceeds_limit")

    def test_no_single_share_can_exceed_risk_budget(self):
        self.assertEqual(self.assess(entry="1000000", stop="900000")["reason"], "minimum_lot_exceeds_limit")

    def test_nonfinite_numbers_invalid_stops_and_negative_costs(self):
        for values in ({"entry": "NaN"}, {"stop": "101000"}, {"cost_per_share": "-1"}):
            self.assertFalse(self.assess(**values)["allowed"])
        self.assertFalse(self.assess(replace(self.state, equity="Infinity"))["allowed"])
        self.policy["max_positions"] = float("nan")
        self.assertFalse(self.assess()["allowed"])


if __name__ == "__main__":
    unittest.main()
