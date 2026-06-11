import importlib.util
import unittest

import pandas as pd

from pdf_export import build_company_report_pdf, build_group_brief_pdf


@unittest.skipUnless(importlib.util.find_spec("reportlab") is not None, "reportlab not installed")
class PdfExportTest(unittest.TestCase):
    def test_company_pdf_bytes(self):
        action_df = pd.DataFrame([
            {"시점": "오늘", "소관 Agent": "Early Warning Agent", "액션 아이템": "PF 만기집중 점검", "목적": "즉시 대응"}
        ])
        pdf_bytes = build_company_report_pdf(
            "JB우리캐피탈",
            "2026-06",
            {"current_rate": 2.21, "mom_change_pp": 0.47, "vs_3m_avg_pp": 0.55},
            {"pf_share": 34.5, "secured_share": 80.8, "largest_balance_segment": "부동산PF 브릿지론", "worst_segment": "부동산PF 브릿지론"},
            "테스트 보고서 본문",
            action_df,
        )
        self.assertGreater(len(pdf_bytes), 500)

    def test_group_pdf_bytes(self):
        comparison_df = pd.DataFrame([{"계열사": "JB우리캐피탈", "현재 연체율": 2.21}])
        alerts_df = pd.DataFrame([{"company_name": "JB우리캐피탈", "alert_type": "PF 만기집중 경보", "severity": "High", "detail": "테스트"}])
        pdf_bytes = build_group_brief_pdf("2026-06", "그룹 브리프 테스트", comparison_df, alerts_df)
        self.assertGreater(len(pdf_bytes), 500)


if __name__ == "__main__":
    unittest.main()
