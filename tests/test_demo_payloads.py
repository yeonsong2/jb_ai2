import json
import unittest
from pathlib import Path


class DemoPayloadsTest(unittest.TestCase):
    def test_demo_payloads_json_is_valid_and_has_default_keys(self):
        payload_path = Path("data/demo_llm_payloads.json")
        self.assertTrue(payload_path.exists())
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        self.assertIn("__default__", payload)
        default_payload = payload["__default__"]
        for key in [
            "orchestrator_brief",
            "pf_agent_note",
            "collateral_agent_note",
            "early_warning_note",
            "scenario_agent_note",
            "reason_report",
            "executive_report",
            "qa_answers",
        ]:
            self.assertIn(key, default_payload)
        self.assertIn("__default__", default_payload["qa_answers"])


if __name__ == "__main__":
    unittest.main()
