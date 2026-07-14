import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import extract_trend_df, filter_by_date_range, resample_period
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Financial Metrics",
    icon="💰",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

col1, col2, col3 = st.columns(3)
with col1:
    policy_status = st.segmented_control(
        "Policy status", ["All Policies", "Active Only", "Inactive Only"], default="All Policies"
    )
with col2:
    view_by = st.segmented_control("View by", ["Monthly", "Yearly"], default="Monthly")
with col3:
    payment_status = st.segmented_control("Payment status", ["All", "Paid Only", "Unpaid Only"], default="All")

granularity = "month" if view_by == "Monthly" else "year"

covers = filter_by_date_range(loaders.fetch_covers(client), "created_at", filters["from"], filters["to"])
payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", filters["from"], filters["to"])

if policy_status == "Active Only" and "status" in covers.columns:
    covers = covers[covers["status"] == "active"]
elif policy_status == "Inactive Only" and "status" in covers.columns:
    covers = covers[covers["status"] != "active"]

paid_cover_ids = set(payments.loc[payments.get("status") == "success", "cover_id"]) if "cover_id" in payments.columns else set()
if payment_status != "All" and "id" in covers.columns:
    covers = covers[covers["id"].isin(paid_cover_ids)] if payment_status == "Paid Only" else covers[~covers["id"].isin(paid_cover_ids)]


def _monthly_breakdown(df, value_col: str, value_label: str):
    """(month_label, policies, value) rows, plus (total_value, total_policies, peak_month, peak_value)."""
    if df.empty or "created_at" not in df.columns:
        return None
    working = df.dropna(subset=["created_at"]).assign(month=lambda d: d["created_at"].dt.to_period("M"))
    agg = {"id": "count"}
    if value_col in working.columns:
        agg[value_col] = "sum"
    monthly = working.groupby("month", as_index=False).agg(agg).rename(columns={"id": "Policies", value_col: value_label})
    monthly["Month"] = monthly["month"].astype(str)
    monthly = monthly.sort_values("month")
    if value_label not in monthly.columns:
        monthly[value_label] = 0
    total_value = monthly[value_label].sum()
    total_policies = monthly["Policies"].sum()
    peak = monthly.loc[monthly[value_label].idxmax()] if not monthly.empty else None
    return monthly, total_value, total_policies, peak


def _render_channel_breakdown(df, value_col: str, kpi_prefix: str, chart_key: str) -> None:
    """Stacked bar + pivoted table of `value_col` by channel per month, matching the
    reference site's "<Metric> by Channel per Month" section."""
    if df.empty or "created_at" not in df.columns or "channel" not in df.columns or value_col not in df.columns:
        return
    st.subheader(f"{kpi_prefix} by Channel per Month")
    working = df.dropna(subset=["created_at"]).assign(month=lambda d: d["created_at"].dt.to_period("M").astype(str))
    by_channel = working.groupby(["month", "channel"], as_index=False)[value_col].sum().sort_values("month")
    if by_channel.empty:
        st.info("No channel data for this selection.")
        return
    st.plotly_chart(charts.stacked_bar_chart(by_channel, "month", value_col, "channel"), use_container_width=True, key=f"{chart_key}_channel")

    pivot = by_channel.pivot_table(index="month", columns="channel", values=value_col, aggfunc="sum", fill_value=0)
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.reset_index().rename(columns={"month": "Period"})
    tables.styled_table(pivot)
    tables.excel_download_button(pivot, f"{kpi_prefix.lower().replace(' ', '_')}_by_channel.xlsx", key=f"{chart_key}_channel_dl")


def _render_metric_tab(df, value_col: str, value_label: str, kpi_prefix: str, chart_key: str):
    monthly_result = _monthly_breakdown(df, value_col, value_label)
    if monthly_result is None:
        st.info("No data for this selection.")
        return
    monthly, total_value, total_policies, peak = monthly_result
    kpi_cards_with_trend(
        [
            {"label": f"Total {kpi_prefix} (KES)", "value": f"{total_value:,.0f}", "icon": "🪙"},
            {"label": "Total Policies", "value": f"{total_policies:,}", "icon": "🛡️"},
            {
                "label": "Peak Month",
                "value": peak["Month"] if peak is not None else "n/a",
                "icon": "📈",
                "subtitle": f"KES {peak[value_label]:,.0f}" if peak is not None else "",
            },
        ],
        key_prefix=chart_key,
    )
    st.divider()
    st.subheader(f"{kpi_prefix} per Month")
    st.plotly_chart(charts.bar_chart(monthly, "Month", value_label), use_container_width=True, key=chart_key)
    st.divider()
    tables.styled_table(monthly[["Month", "Policies", value_label]])
    tables.excel_download_button(monthly[["Month", "Policies", value_label]], f"{kpi_prefix.lower().replace(' ', '_')}.xlsx", key=f"{chart_key}_dl")
    st.divider()
    _render_channel_breakdown(df, value_col, kpi_prefix, chart_key)


tab_payable, tab_underwriter, tab_income, tab_paid, tab_records = st.tabs(
    ["Payable Premium", "Underwriter Premium", "Azil Income", "Paid Summary", "Records"]
)

with tab_payable:
    _render_metric_tab(covers, "amount", "Payable Premium", "Payable Premium", "payable_premium_chart")

with tab_underwriter:
    premium_col = "premium" if "premium" in covers.columns else "amount"
    _render_metric_tab(covers, premium_col, "Underwriter Premium", "Underwriter Premium", "underwriter_premium_chart")

with tab_income:
    trend_filters = dict(filters)
    if policy_status == "Active Only":
        trend_filters["status"] = "active"
    income_trends = loaders.fetch_income_trends(client, trend_filters)
    income_totals = income_trends.get("totals", {}) or {}
    kpi_cards_with_trend(
        [{"label": "Total Azil Income (KES)", "value": f"{income_totals.get('income', 0):,.0f}", "icon": "📊"}],
        key_prefix="fm_income",
    )
    st.divider()
    st.subheader(f"Azil Income — {view_by.lower()} trend")
    income_df = extract_trend_df(income_trends, value_candidates=("income", "total", "amount"))
    if not income_df.empty:
        bucketed = resample_period(income_df, granularity)
        bucketed["label"] = bucketed["period"].dt.strftime("%b %Y" if granularity == "month" else "%Y")
        st.plotly_chart(charts.line_chart(bucketed, "label", "value"), use_container_width=True, key="income_chart")
    else:
        st.info("No income trend data for this selection.")

with tab_paid:
    is_paid = covers["id"].isin(paid_cover_ids) if "id" in covers.columns else covers.index < 0
    paid_covers = covers[is_paid]
    unpaid_covers = covers[~is_paid]
    kpi_cards_with_trend(
        [
            {"label": "Paid policies", "value": f"{len(paid_covers):,}", "icon": "✅"},
            {"label": "Unpaid policies", "value": f"{len(unpaid_covers):,}", "icon": "⏳"},
            {
                "label": "Paid amount (KES)",
                "value": f"{paid_covers['amount'].sum():,.0f}" if "amount" in paid_covers.columns else "n/a",
                "icon": "🪙",
            },
            {
                "label": "Unpaid amount (KES)",
                "value": f"{unpaid_covers['amount'].sum():,.0f}" if "amount" in unpaid_covers.columns else "n/a",
                "icon": "🪙",
            },
        ],
        key_prefix="fm_paid",
    )
    st.divider()
    breakdown = None
    if "amount" in covers.columns:
        breakdown = pd.DataFrame(
            {
                "Status": ["Paid", "Unpaid"],
                "Policies": [len(paid_covers), len(unpaid_covers)],
                "Amount": [paid_covers["amount"].sum(), unpaid_covers["amount"].sum()],
            }
        )
    if breakdown is not None:
        st.plotly_chart(charts.pie_chart(breakdown, "Status", "Amount", donut=True), use_container_width=True, key="paid_summary_chart")
        tables.styled_table(breakdown)
    else:
        st.info("No amount field available to summarize.")

with tab_records:
    st.subheader("Policy records")
    ordered = covers.sort_values("created_at", ascending=False) if "created_at" in covers.columns else covers
    tables.paginated_table(ordered, key="financial_records")
    tables.excel_download_button(ordered, "financial_metrics_records.xlsx", key="records_dl")
