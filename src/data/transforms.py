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


def extract_trend_df(payload: dict, value_candidates: tuple[str, ...] = ("count", "amount", "income", "total")) -> pd.DataFrame:
    """Turn a /dashboard/*-trends endpoint's `trends` list into a (period, value) DataFrame,
    auto-detecting the date and value field names since they vary slightly by endpoint."""
    rows = payload.get("trends") or []
    if not rows:
        return pd.DataFrame(columns=["period", "value"])
    df = pd.DataFrame(rows)
    date_col = next((c for c in ("date", "period", "day") if c in df.columns), df.columns[0])
    value_col = next((c for c in value_candidates if c in df.columns), None)
    if value_col is None:
        return pd.DataFrame(columns=["period", "value"])
    df["period"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["period"]).sort_values("period")
    return df[["period", value_col]].rename(columns={value_col: "value"})


def resample_period(df: pd.DataFrame, granularity: str = "month") -> pd.DataFrame:
    """Aggregate an (period, value) trend DataFrame (see extract_trend_df) up to day/week/month/year buckets."""
    if df.empty or "period" not in df.columns:
        return df
    freq = {"day": "D", "week": "W-MON", "month": "MS", "year": "YS"}.get(granularity, "MS")
    return df.set_index("period").resample(freq)["value"].sum().reset_index()


def previous_period(date_from: str, date_to: str) -> dict[str, str]:
    """The date range immediately preceding [date_from, date_to], of the same length —
    e.g. for a 31-day range, the 31 days right before it. Used to compute "vs previous
    period" KPI trend percentages."""
    d_from = pd.Timestamp(date_from)
    d_to = pd.Timestamp(date_to)
    span = (d_to - d_from).days + 1
    prev_to = d_from - pd.Timedelta(days=1)
    prev_from = prev_to - pd.Timedelta(days=span - 1)
    return {"from": prev_from.strftime("%Y-%m-%d"), "to": prev_to.strftime("%Y-%m-%d")}


def pct_change(current: float, previous: float) -> float | None:
    """Percentage change from `previous` to `current`, or None if `previous` is 0/falsy
    (a percentage change from zero is undefined, not infinite or zero)."""
    if not previous:
        return None
    return (current - previous) / previous * 100


def flatten_underwriter_trends(payload: dict) -> pd.DataFrame:
    """/dashboard/underwriter-trends nests a per-underwriter breakdown inside each period,
    unlike the flat trends[] arrays cover-trends/income-trends use:
        {trends: [{date, underwriters: [{underwriterId, underwriterName, totalAmount,
                                          coverCount, underwriterIncome}, ...]}, ...]}
    Flatten it into one row per (period, underwriter) — same shape AZIL-FRONTEND's own
    admin reports page builds via trends.flatMap(period => period.underwriters.map(...)).
    """
    periods = payload.get("trends") or []
    rows = []
    for period in periods:
        period_date = period.get("date")
        for u in period.get("underwriters") or []:
            rows.append(
                {
                    "period": period_date,
                    "underwriter_id": u.get("underwriterId"),
                    "underwriter_name": u.get("underwriterName"),
                    "amount": u.get("totalAmount"),
                    "count": u.get("coverCount"),
                    "income": u.get("underwriterIncome"),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["period", "underwriter_id", "underwriter_name", "amount", "count", "income"])
    df = pd.DataFrame(rows)
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    return df.dropna(subset=["period"]).sort_values("period")


CUSTOMER_ID_CANDIDATES = ("user_id", "owner_id", "customer_id", "client_id", "user_user_id", "vehicle_owner_id")


def find_customer_id_column(df: pd.DataFrame) -> str | None:
    """Find whichever column links a cover to its customer. Covers embed the customer as a
    nested object (`user`, `owner`, `client`, or `customer` depending on the endpoint/context
    per AZIL-FRONTEND's own code), which json_normalize flattens to `<prefix>_id` — but the
    exact prefix isn't guaranteed, so try the common ones rather than assuming `user_id`."""
    return next((c for c in CUSTOMER_ID_CANDIDATES if c in df.columns), None)


def find_customer_name_column(df: pd.DataFrame) -> str | None:
    """Fallback display identifier when there's no clean customer ID column to group by."""
    for prefix in ("user", "owner", "client", "customer"):
        first, last = f"{prefix}_first_name", f"{prefix}_last_name"
        if first in df.columns:
            df[f"{prefix}_full_name"] = (df[first].fillna("") + " " + df.get(last, "").fillna("")).str.strip()
            return f"{prefix}_full_name"
        for candidate in (f"{prefix}_name", f"{prefix}_msisdn", f"{prefix}_phone_number"):
            if candidate in df.columns:
                return candidate
    return None


def link_customers_via_vehicles(covers: pd.DataFrame, vehicles: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Bridge covers to the user who purchased them when covers don't carry a direct
    customer-id field. AZIL's own API docs show the real chain is User -> owns Vehicle ->
    Vehicle has Cover: `GET /vehicles/` takes `user_id` ("Filter by owner") and `GET /covers/`
    takes `vehicle_id` ("Filter by vehicle ID") — the customer link lives on the vehicle, not
    the cover. Merge vehicles' owner id onto covers via vehicle_id so a customer is always
    "a user who purchased a policy" even when the cover record itself is silent on who bought it.
    """
    if covers.empty or vehicles.empty:
        return covers, None
    if "id" not in vehicles.columns or "vehicle_id" not in covers.columns:
        return covers, None
    owner_col = next((c for c in CUSTOMER_ID_CANDIDATES if c in vehicles.columns), None)
    if not owner_col:
        return covers, None
    bridge = vehicles[["id", owner_col]].rename(columns={"id": "vehicle_id", owner_col: "customer_id"})
    merged = covers.merge(bridge, on="vehicle_id", how="left")
    return merged, "customer_id"
