import json
from pathlib import Path

from constants import RISK_CONFIG_PATH

DEFAULT_RISK_CONFIG = {
    "severity_weights": {"High": 18, "Medium": 10, "Low": 4},
    "type_weights": {
        "Bank": 1.0,
        "Capital": 1.08,
        "Overseas Bank": 0.95,
        "Asset Management": 0.9,
    },
    "risk_level_thresholds": {"High": 75, "Medium": 45},
    "ui_defaults": {
        "default_company": "JB우리캐피탈",
        "default_focus_mode": "그룹 스캔",
        "default_severity_filter": ["High", "Medium"],
    },
}


def load_risk_config(path: Path | None = None) -> dict:
    config_path = path or RISK_CONFIG_PATH
    if not config_path.exists():
        return DEFAULT_RISK_CONFIG.copy()
    with config_path.open("r", encoding="utf-8") as fp:
        loaded = json.load(fp)
    merged = DEFAULT_RISK_CONFIG.copy()
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merged[key] | value
        else:
            merged[key] = value
    return merged
