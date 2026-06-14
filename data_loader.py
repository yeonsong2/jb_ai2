import pandas as pd

from constants import PUBLIC_ANCHOR_PATH, REQUIRED_COLUMNS
from risk_engine import calculate_company_risk, detect_alerts, get_company_comparison
from services.data_validation import prepare_dataframe


DATASET_RULES = {
    "metrics": {
        "numeric_columns": [
            "delinquency_rate",
            "complaints",
            "abnormal_events",
            "exposure_real_estate",
            "exposure_sme",
        ],
        "rate_columns": ["delinquency_rate", "exposure_real_estate", "exposure_sme"],
        "non_negative_columns": [
            "delinquency_rate",
            "complaints",
            "abnormal_events",
            "exposure_real_estate",
            "exposure_sme",
        ],
        "string_columns": ["company_name", "company_type"],
        "duplicate_subset": ["date", "company_name"],
    },
    "logs": {
        "numeric_columns": [],
        "rate_columns": [],
        "non_negative_columns": [],
        "string_columns": ["company_name", "issue_type", "severity", "description"],
        "duplicate_subset": ["date", "company_name", "issue_type", "description"],
    },
    "drivers": {
        "numeric_columns": ["contribution_bps"],
        "rate_columns": [],
        "non_negative_columns": [],
        "string_columns": ["company_name", "driver_name", "direction", "description"],
        "duplicate_subset": ["date", "company_name", "driver_name", "description"],
    },
    "segments": {
        "numeric_columns": ["balance", "delinquency_rate", "customer_count"],
        "rate_columns": ["delinquency_rate"],
        "non_negative_columns": ["balance", "delinquency_rate", "customer_count"],
        "string_columns": [
            "company_name",
            "portfolio_group",
            "segment_name",
            "collateral_type",
            "industry",
        ],
        "duplicate_subset": ["date", "company_name", "segment_name"],
    },
}


PUBLIC_ANCHOR_COLUMNS = [
    "source_system",
    "metric_name",
    "observation_period",
    "anchor_value",
    "unit",
    "source_url",
    "usage_note",
]


def load_dataframe(dataset_name: str, csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    rules = DATASET_RULES[dataset_name]
    return prepare_dataframe(
        dataset_name,
        df,
        required_columns=REQUIRED_COLUMNS[dataset_name],
        numeric_columns=rules["numeric_columns"],
        rate_columns=rules["rate_columns"],
        non_negative_columns=rules["non_negative_columns"],
        string_columns=rules["string_columns"],
        duplicate_subset=rules["duplicate_subset"],
    )



def load_dataframes(metrics_path, logs_path, drivers_path, segment_path):
    metrics = load_dataframe("metrics", metrics_path)
    logs = load_dataframe("logs", logs_path)
    drivers = load_dataframe("drivers", drivers_path)
    segments = load_dataframe("segments", segment_path)
    return metrics, logs, drivers, segments



def load_public_anchor_metrics(anchor_path: str | None = None) -> pd.DataFrame:
    csv_path = anchor_path or str(PUBLIC_ANCHOR_PATH)
    anchors = pd.read_csv(csv_path)
    missing = [column for column in PUBLIC_ANCHOR_COLUMNS if column not in anchors.columns]
    if missing:
        raise ValueError(f"public anchor metrics are missing required columns: {missing}")

    anchors = anchors.copy()
    anchors["source_system"] = anchors["source_system"].astype(str).str.strip()
    anchors["metric_name"] = anchors["metric_name"].astype(str).str.strip()
    anchors["observation_period"] = anchors["observation_period"].astype(str).str.strip()
    anchors["unit"] = anchors["unit"].astype(str).str.strip()
    anchors["source_url"] = anchors["source_url"].astype(str).str.strip()
    anchors["usage_note"] = anchors["usage_note"].astype(str).str.strip()
    anchors["anchor_value"] = pd.to_numeric(anchors["anchor_value"], errors="raise")
    return anchors.drop_duplicates().reset_index(drop=True)



def validate_required_columns(name: str, df: pd.DataFrame, required_columns: list[str]):
    return [col for col in required_columns if col not in df.columns]



def build_dashboard_data(metrics_df: pd.DataFrame, logs_df: pd.DataFrame, drivers_df: pd.DataFrame, segment_df: pd.DataFrame):
    risk = calculate_company_risk(metrics_df, logs_df, drivers_df)
    alerts = detect_alerts(metrics_df, logs_df)
    comparison = get_company_comparison(risk)
    return risk, alerts, comparison
