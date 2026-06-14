from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_CSV = BASE_DIR / "data" / "public_anchor_metrics.csv"
OUTPUT_JSON = BASE_DIR / "data" / "public_anchor_params.json"


def build_anchor_payload(source_csv: Path = SOURCE_CSV) -> dict:
    df = pd.read_csv(source_csv)
    records = []
    for row in df.to_dict(orient="records"):
        records.append(
            {
                "source_system": row["source_system"],
                "metric_name": row["metric_name"],
                "observation_period": str(row["observation_period"]),
                "anchor_value": float(row["anchor_value"]),
                "unit": row["unit"],
                "source_url": row["source_url"],
                "usage_note": row["usage_note"],
            }
        )

    grouped = {}
    for record in records:
        grouped.setdefault(record["metric_name"], []).append(record)

    return {
        "version": "demo-public-anchor-v1",
        "source_csv": str(source_csv.relative_to(BASE_DIR)),
        "metric_count": len(records),
        "metrics": grouped,
    }


def main() -> None:
    payload = build_anchor_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
