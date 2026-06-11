import pandas as pd

from risk_engine import calculate_company_risk, detect_alerts, get_company_comparison


def load_dataframes(metrics_path, logs_path, drivers_path, segment_path):
    metrics = pd.read_csv(metrics_path, parse_dates=["date"])
    logs = pd.read_csv(logs_path, parse_dates=["date"])
    drivers = pd.read_csv(drivers_path, parse_dates=["date"])
    segments = pd.read_csv(segment_path, parse_dates=["date"])
    return metrics, logs, drivers, segments


def validate_required_columns(name: str, df: pd.DataFrame, required_columns: list[str]):
    return [col for col in required_columns if col not in df.columns]


def build_dashboard_data(metrics_df: pd.DataFrame, logs_df: pd.DataFrame, drivers_df: pd.DataFrame, segment_df: pd.DataFrame):
    risk = calculate_company_risk(metrics_df, logs_df, drivers_df)
    alerts = detect_alerts(metrics_df, logs_df)
    comparison = get_company_comparison(risk)
    return risk, alerts, comparison
