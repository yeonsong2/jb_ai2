import unittest

from app_config import load_risk_config
from constants import REQUIRED_COLUMNS
from data_loader import load_dataframes, validate_required_columns


class ConfigAndLoaderTest(unittest.TestCase):
    def test_config_has_required_sections(self):
        config = load_risk_config()
        self.assertIn("severity_weights", config)
        self.assertIn("type_weights", config)
        self.assertIn("risk_level_thresholds", config)
        self.assertEqual(config["ui_defaults"]["default_company"], "JB우리캐피탈")

    def test_sample_data_matches_required_columns(self):
        metrics, logs, drivers, segments = load_dataframes(
            "data/sample_risk_metrics.csv",
            "data/sample_risk_logs.csv",
            "data/sample_delinquency_drivers.csv",
            "data/sample_segment_metrics.csv",
        )
        self.assertEqual(validate_required_columns("metrics", metrics, REQUIRED_COLUMNS["metrics"]), [])
        self.assertEqual(validate_required_columns("logs", logs, REQUIRED_COLUMNS["logs"]), [])
        self.assertEqual(validate_required_columns("drivers", drivers, REQUIRED_COLUMNS["drivers"]), [])
        self.assertEqual(validate_required_columns("segments", segments, REQUIRED_COLUMNS["segments"]), [])


if __name__ == "__main__":
    unittest.main()
