from __future__ import annotations

from typing import Iterable

import pandas as pd


COMPANY_NAME_ALIASES = {
    "PPCBank": "JB캄보디아은행",
    "JB Cambodia Bank": "JB캄보디아은행",
    "JB CambodiaBank": "JB캄보디아은행",
    "JB Woori Capital": "JB우리캐피탈",
    "JB WooriCapital": "JB우리캐피탈",
    "JB Capital": "JB우리캐피탈",
}


def assert_required_columns(name: str, df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{name} dataframe is missing required columns: {missing}")


def normalize_company_names(df: pd.DataFrame, company_col: str = "company_name") -> pd.DataFrame:
    if company_col not in df.columns:
        return df

    normalized = df.copy()
    normalized[company_col] = (
        normalized[company_col]
        .astype(str)
        .str.strip()
        .replace(COMPANY_NAME_ALIASES)
    )
    return normalized


def standardize_string_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    normalized = df.copy()
    for column in columns:
        if column in normalized.columns:
            normalized[column] = normalized[column].astype(str).str.strip()
    return normalized


def validate_date_column(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    if date_col not in df.columns:
        return df

    normalized = df.copy()
    original_values = normalized[date_col]
    normalized[date_col] = pd.to_datetime(normalized[date_col], errors="coerce")
    invalid_mask = original_values.notna() & normalized[date_col].isna()
    if invalid_mask.any():
        invalid_samples = original_values[invalid_mask].astype(str).head(3).tolist()
        raise ValueError(f"Invalid {date_col} values detected: {invalid_samples}")
    return normalized.sort_values(date_col).reset_index(drop=True)


def coerce_numeric_columns(df: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame:
    normalized = df.copy()
    for column in numeric_columns:
        if column not in normalized.columns:
            continue
        raw = normalized[column]
        as_text = raw.astype(str).str.replace(",", "", regex=False).str.strip()
        coerced = pd.to_numeric(as_text.where(raw.notna()), errors="coerce")
        invalid_mask = raw.notna() & coerced.isna()
        if invalid_mask.any():
            invalid_samples = raw[invalid_mask].astype(str).head(3).tolist()
            raise ValueError(f"Invalid numeric values in {column}: {invalid_samples}")
        normalized[column] = coerced
    return normalized


def drop_duplicate_rows(df: pd.DataFrame, subset: Iterable[str] | None = None) -> pd.DataFrame:
    return df.drop_duplicates(subset=list(subset) if subset else None).reset_index(drop=True)


def validate_rate_ranges(
    df: pd.DataFrame,
    rate_columns: Iterable[str],
    min_value: float = 0.0,
    max_value: float = 100.0,
) -> pd.DataFrame:
    for column in rate_columns:
        if column not in df.columns:
            continue
        invalid_mask = df[column].notna() & ((df[column] < min_value) | (df[column] > max_value))
        if invalid_mask.any():
            invalid_samples = df.loc[invalid_mask, column].head(3).tolist()
            raise ValueError(
                f"Out-of-range rate values in {column}: {invalid_samples} (expected {min_value} to {max_value})"
            )
    return df


def ensure_non_negative(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            continue
        invalid_mask = df[column].notna() & (df[column] < 0)
        if invalid_mask.any():
            invalid_samples = df.loc[invalid_mask, column].head(3).tolist()
            raise ValueError(f"Negative values are not allowed in {column}: {invalid_samples}")
    return df


def prepare_dataframe(
    name: str,
    df: pd.DataFrame,
    required_columns: Iterable[str],
    numeric_columns: Iterable[str] | None = None,
    rate_columns: Iterable[str] | None = None,
    non_negative_columns: Iterable[str] | None = None,
    string_columns: Iterable[str] | None = None,
    duplicate_subset: Iterable[str] | None = None,
    company_col: str = "company_name",
    date_col: str = "date",
) -> pd.DataFrame:
    cleaned = df.copy()
    assert_required_columns(name, cleaned, required_columns)
    cleaned = standardize_string_columns(cleaned, string_columns or [])
    cleaned = normalize_company_names(cleaned, company_col=company_col)
    cleaned = validate_date_column(cleaned, date_col=date_col)
    cleaned = coerce_numeric_columns(cleaned, numeric_columns or [])
    cleaned = drop_duplicate_rows(cleaned, subset=duplicate_subset)
    cleaned = validate_rate_ranges(cleaned, rate_columns or [])
    cleaned = ensure_non_negative(cleaned, non_negative_columns or [])
    return cleaned
