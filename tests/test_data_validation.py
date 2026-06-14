import unittest

import pandas as pd

from services.data_validation import prepare_dataframe


class DataValidationServiceTest(unittest.TestCase):
    def test_prepare_dataframe_normalizes_alias_and_numeric_types(self):
        raw = pd.DataFrame(
            {
                "date": ["2026-06-01", "2026-06-01"],
                "company_name": ["PPCBank", "PPCBank"],
                "company_type": ["Overseas Bank", "Overseas Bank"],
                "delinquency_rate": ["1.25", "1.25"],
                "complaints": ["3", "3"],
                "abnormal_events": ["1", "1"],
                "exposure_real_estate": ["12.5", "12.5"],
                "exposure_sme": ["21.0", "21.0"],
            }
        )

        cleaned = prepare_dataframe(
            "metrics",
            raw,
            required_columns=[
                "date",
                "company_name",
                "company_type",
                "delinquency_rate",
                "complaints",
                "abnormal_events",
                "exposure_real_estate",
                "exposure_sme",
            ],
            numeric_columns=[
                "delinquency_rate",
                "complaints",
                "abnormal_events",
                "exposure_real_estate",
                "exposure_sme",
            ],
            rate_columns=["delinquency_rate", "exposure_real_estate", "exposure_sme"],
            non_negative_columns=[
                "delinquency_rate",
                "complaints",
                "abnormal_events",
                "exposure_real_estate",
                "exposure_sme",
            ],
            string_columns=["company_name", "company_type"],
            duplicate_subset=["date", "company_name"],
        )

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["company_name"], "JB캄보디아은행")
        self.assertAlmostEqual(cleaned.iloc[0]["delinquency_rate"], 1.25)

    def test_prepare_dataframe_rejects_invalid_rate_range(self):
        raw = pd.DataFrame(
            {
                "date": ["2026-06-01"],
                "company_name": ["JB우리캐피탈"],
                "company_type": ["Capital"],
                "delinquency_rate": [120.0],
                "complaints": [1],
                "abnormal_events": [0],
                "exposure_real_estate": [25.0],
                "exposure_sme": [18.0],
            }
        )

        with self.assertRaises(ValueError):
            prepare_dataframe(
                "metrics",
                raw,
                required_columns=[
                    "date",
                    "company_name",
                    "company_type",
                    "delinquency_rate",
                    "complaints",
                    "abnormal_events",
                    "exposure_real_estate",
                    "exposure_sme",
                ],
                numeric_columns=[
                    "delinquency_rate",
                    "complaints",
                    "abnormal_events",
                    "exposure_real_estate",
                    "exposure_sme",
                ],
                rate_columns=["delinquency_rate", "exposure_real_estate", "exposure_sme"],
                non_negative_columns=[
                    "delinquency_rate",
                    "complaints",
                    "abnormal_events",
                    "exposure_real_estate",
                    "exposure_sme",
                ],
                string_columns=["company_name", "company_type"],
                duplicate_subset=["date", "company_name"],
            )


if __name__ == "__main__":
    unittest.main()
