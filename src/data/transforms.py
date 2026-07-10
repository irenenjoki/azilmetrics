"""Pure pandas transforms — no Streamlit calls, so these are unit-testable in isolation."""
from __future__ import annotations

import pandas as pd

DATE_LIKE_SUFFIXES = ("_at", "_date")


def records_to_df(records: list[dict]) -> pd.DataFrame:
    """Flatten a list of (possibly nested) API records into a DataFrame with parsed date columns."""
    if not records:
        return pd.DataFrame()
    df = pd.json_normalize(records, sep="_")
    for col in df.columns:
        if col.endswith(DATE_LIKE_SUFFIXES):
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_localize(None)
    return df


def filter_by_date_range(df: pd.DataFrame, date_col: str, date_from: str, date_to: str) -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df
    return df[(df[date_col] >= date_from) & (df[date_col] <= f"{date_to} 23:59:59")]


def value_counts_df(df: pd.DataFrame, col: str, label_col: str = "label", count_col: str = "count") -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[label_col, count_col])
    counts = df[col].value_counts().reset_index()
    counts.columns = [label_col, count_col]
    return counts


def daily_count(df: pd.DataFrame, date_col: str, out_col: str = "count") -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=["day", out_col])
    daily = df.dropna(subset=[date_col]).assign(day=df[date_col].dt.date)
    return daily.groupby("day", as_index=False).size().rename(columns={"size": out_col})


def daily_sum(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    filter_col: str | None = None,
    filter_val=None,
) -> pd.DataFrame:
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=["day", value_col])
    subset = df if filter_col is None else df[df[filter_col] == filter_val]
    if subset.empty:
        return pd.DataFrame(columns=["day", value_col])
    daily = subset.dropna(subset=[date_col]).assign(day=subset[date_col].dt.date)
    return daily.groupby("day", as_index=False)[value_col].sum()


def success_rate(df: pd.DataFrame, col: str, success_value) -> float | None:
    if df.empty or col not in df.columns:
        return None
    return (df[col].astype(str) == str(success_value)).mean() * 100
