import pandas as pd
import pytest

from src.data.transforms import (
    daily_count,
    daily_sum,
    filter_by_date_range,
    records_to_df,
    success_rate,
    value_counts_df,
)


def test_records_to_df_empty():
    assert records_to_df([]).empty


def test_records_to_df_flattens_nested_fields_and_parses_dates():
    records = [
        {"id": "1", "amount": 100, "created_at": "2026-01-01T10:00:00Z", "cover": {"status": "active"}},
        {"id": "2", "amount": 200, "created_at": "2026-01-02T10:00:00Z", "cover": {"status": "pending"}},
    ]
    df = records_to_df(records)
    assert list(df["cover_status"]) == ["active", "pending"]
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])


def test_filter_by_date_range():
    df = records_to_df(
        [
            {"id": "1", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "2", "created_at": "2026-02-01T00:00:00Z"},
        ]
    )
    filtered = filter_by_date_range(df, "created_at", "2026-01-01", "2026-01-31")
    assert list(filtered["id"]) == ["1"]


def test_filter_by_date_range_missing_column_returns_input():
    df = pd.DataFrame({"id": [1, 2]})
    assert filter_by_date_range(df, "created_at", "2026-01-01", "2026-01-31") is df


def test_value_counts_df():
    df = pd.DataFrame({"status": ["success", "success", "failed"]})
    counts = value_counts_df(df, "status", "status")
    assert counts.set_index("status")["count"].to_dict() == {"success": 2, "failed": 1}


def test_daily_count():
    df = records_to_df(
        [
            {"id": "1", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "2", "created_at": "2026-01-01T12:00:00Z"},
            {"id": "3", "created_at": "2026-01-02T00:00:00Z"},
        ]
    )
    daily = daily_count(df, "created_at")
    counts = dict(zip(daily["day"].astype(str), daily["count"]))
    assert counts["2026-01-01"] == 2
    assert counts["2026-01-02"] == 1


def test_daily_sum_with_filter():
    df = records_to_df(
        [
            {"id": "1", "created_at": "2026-01-01T00:00:00Z", "amount": 100, "status": "success"},
            {"id": "2", "created_at": "2026-01-01T00:00:00Z", "amount": 50, "status": "failed"},
        ]
    )
    daily = daily_sum(df, "created_at", "amount", filter_col="status", filter_val="success")
    assert daily["amount"].iloc[0] == 100


def test_success_rate():
    df = pd.DataFrame({"ResultCode": ["0", "0", "1"]})
    assert success_rate(df, "ResultCode", "0") == pytest.approx(66.6667, abs=0.01)


def test_success_rate_missing_column_returns_none():
    df = pd.DataFrame({"other": [1, 2]})
    assert success_rate(df, "ResultCode", "0") is None
