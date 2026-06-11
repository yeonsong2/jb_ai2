import unittest
import pandas as pd

from risk_engine import (
    calculate_company_risk,
    detect_alerts,
    get_delinquency_snapshot,
    get_enterprise_portfolio_summary,
    simulate_what_if_scenario,
)


class RiskEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = pd.read_csv("data/sample_risk_metrics.csv", parse_dates=["date"])
        cls.logs = pd.read_csv("data/sample_risk_logs.csv", parse_dates=["date"])
        cls.drivers = pd.read_csv("data/sample_delinquency_drivers.csv", parse_dates=["date"])
        cls.segments = pd.read_csv("data/sample_segment_metrics.csv", parse_dates=["date"])
        cls.risk = calculate_company_risk(cls.metrics, cls.logs, cls.drivers)

    def test_jb_capital_is_high_risk(self):
        top = self.risk.iloc[0]
        self.assertEqual(top["company_name"], "JB우리캐피탈")
        self.assertEqual(top["risk_level"], "High")
        self.assertGreaterEqual(top["risk_score"], 75)

    def test_portfolio_summary_matches_expected_shape(self):
        summary = get_enterprise_portfolio_summary(self.segments, "JB우리캐피탈")
        self.assertAlmostEqual(summary["pf_share"], 34.5, places=1)
        self.assertAlmostEqual(summary["secured_share"], 80.8, places=1)
        self.assertEqual(summary["largest_balance_segment"], "부동산PF 브릿지론")

    def test_snapshot_has_expected_change(self):
        snapshot = get_delinquency_snapshot(self.risk, "JB우리캐피탈")
        self.assertAlmostEqual(snapshot["current_rate"], 2.21, places=2)
        self.assertAlmostEqual(snapshot["mom_change_pp"], 0.47, places=2)
        self.assertAlmostEqual(snapshot["vs_3m_avg_pp"], 0.55, places=2)

    def test_alerts_include_pf_high_alert(self):
        alerts = detect_alerts(self.metrics, self.logs)
        matched = alerts[(alerts["company_name"] == "JB우리캐피탈") & (alerts["severity"] == "High")]
        self.assertGreaterEqual(len(matched), 1)

    def test_what_if_increases_projected_rate(self):
        result = simulate_what_if_scenario("JB우리캐피탈", self.risk, self.segments, 0.3, 0.2, 0.15)
        self.assertGreater(result["projected_rate"], result["base_rate"])
        self.assertIn(result["projected_risk_level"], {"High", "Medium", "Low"})


if __name__ == "__main__":
    unittest.main()
