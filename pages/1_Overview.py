import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import (
    daily_count,
    daily_sum,
    extract_trend_df,
    filter_by_date_range,
    pct_change,
    previous_period,
    resample_period,
)
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()
styles.page_header("Azil · Motor Policies · Standard Overview", color=styles.TEAL_400)

header_col, filter_col = st.columns([2, 1.3])
with header_col:
    styles.page_header(
        "Overview", icon=styles.logo_icon_html(), subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)"
    )
with filter_col:
    user_status = st.segmented_control("User status", ["All Users", "Active Only", "Inactive Only"], default="All Users")

policy_col, payment_col = st.columns(2)
with policy_col:
    policy_status = st.segmented_control("Policy status", ["All Policies", "Active Only", "Inactive Only"], default="All Policies")
with payment_col:
    payment_status = st.segmented_control("Payment status", ["All", "Paid Only", "Unpaid Only"], default="All")


def _filtered_covers(date_from: str, date_to: str) -> pd.DataFrame:
    """Covers + payments for one date range, with the page's Policy/Payment status
    filters applied — same pattern as Financial Metrics, reused here for both the
    current and previous period so "vs previous period" compares like with like."""
    covers = filter_by_date_range(loaders.fetch_covers(client), "created_at", date_from, date_to)
    payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", date_from, date_to)

    if policy_status == "Active Only" and "status" in covers.columns:
        covers = covers[covers["status"] == "active"]
    elif policy_status == "Inactive Only" and "status" in covers.columns:
        covers = covers[covers["status"] != "active"]

    paid_cover_ids = set(payments.loc[payments.get("status") == "success", "cover_id"]) if "cover_id" in payments.columns else set()
    if payment_status != "All" and "id" in covers.columns:
        covers = covers[covers["id"].isin(paid_cover_ids)] if payment_status == "Paid Only" else covers[~covers["id"].isin(paid_cover_ids)]
    return covers


cover_trends = loaders.fetch_cover_trends(client, filters)
income_trends = loaders.fetch_income_trends(client, filters)
agent_ranks = loaders.fetch_agent_ranks(client, filters)
product_sales = loaders.fetch_product_sales(client, filters)
users = loaders.fetch_users(client)
covers = _filtered_covers(filters["from"], filters["to"])

active_col = next((c for c in ("status", "active_status") if c in users.columns), None)
if user_status == "Active Only" and active_col:
    users = users[users[active_col].isin(["active", 1])]
elif user_status == "Inactive Only" and active_col:
    users = users[~users[active_col].isin(["active", 1])]

income_totals = income_trends.get("totals", {}) or {}
policies_count = len(covers)
premium_amount = covers["amount"].sum() if "amount" in covers.columns else 0

# ---- "vs previous period" comparisons: same-length date range immediately before this one,
# with the same Policy/Payment status filters applied ----
prev_filters = previous_period(filters["from"], filters["to"])
prev_covers = _filtered_covers(prev_filters["from"], prev_filters["to"])
prev_income_trends = loaders.fetch_income_trends(client, prev_filters)
prev_income_totals = prev_income_trends.get("totals", {}) or {}
prev_policies_count = len(prev_covers)
prev_premium_amount = prev_covers["amount"].sum() if "amount" in prev_covers.columns else 0

users_current_count = int((users["created_at"] <= filters["to"]).sum()) if "created_at" in users.columns else len(users)
users_prev_count = int((users["created_at"] <= prev_filters["to"]).sum()) if "created_at" in users.columns else None

policies_count_df = daily_count(covers, "created_at", "value").rename(columns={"day": "period"})
premium_amount_df = daily_sum(covers, "created_at", "amount").rename(columns={"day": "period", "amount": "value"})
income_df = resample_period(extract_trend_df(income_trends, value_candidates=("income", "total", "amount")), "day")
users_daily_df = daily_count(users, "created_at", "value") if "created_at" in users.columns else pd.DataFrame()
if not users_daily_df.empty:
    users_daily_df = users_daily_df.rename(columns={"day": "period"})

kpi_cards_with_trend(
    [
        {
            "label": "Policies (covers)",
            "value": f"{policies_count:,}",
            "icon": "🛡️",
            "pct_change": pct_change(policies_count, prev_policies_count),
            "trend_df": policies_count_df,
        },
        {
            "label": "Premium volume (KES)",
            "value": f"{premium_amount:,.0f}",
            "icon": "🪙",
            "pct_change": pct_change(premium_amount, prev_premium_amount),
            "trend_df": premium_amount_df,
        },
        {
            "label": "Azil Income (KES)",
            "value": f"{income_totals.get('income', 0):,.0f}",
            "icon": "📊",
            "pct_change": pct_change(income_totals.get("income", 0), prev_income_totals.get("income", 0)),
            "trend_df": income_df,
        },
        {
            "label": "Users",
            "value": f"{len(users):,}",
            "icon": "👥",
            "pct_change": pct_change(users_current_count, users_prev_count) if users_prev_count is not None else None,
            "trend_df": users_daily_df,
        },
    ],
    key_prefix="ov",
)

st.divider()
left, right = st.columns(2)

with left:
    header_col, granularity_col = st.columns([3, 1])
    with header_col:
        st.subheader("Revenue trend")
    with granularity_col:
        granularity_label = st.selectbox("View by", ["Daily", "Weekly", "Monthly"], label_visibility="collapsed", key="ov_revenue_granularity")
    granularity = {"Daily": "day", "Weekly": "week", "Monthly": "month"}[granularity_label]
    income_trend_df = extract_trend_df(income_trends, value_candidates=("income", "total", "amount"))
    if not income_trend_df.empty:
        bucketed = resample_period(income_trend_df, granularity)
        st.plotly_chart(charts.line_chart(bucketed, "period", "value"), use_container_width=True, key="revenue_trend")
    else:
        st.info("No income trend data for this date range.")

with right:
    st.subheader("Top agents by premium")
    if not agent_ranks.empty and "premium" in agent_ranks.columns:
        name_col = next((c for c in ("name", "agent_name") if c in agent_ranks.columns), agent_ranks.columns[0])
        ranked = agent_ranks.sort_values("premium", ascending=False).reset_index(drop=True)
        top = ranked.head(4)
        others_total = ranked["premium"].iloc[4:].sum()
        legend_df = top[[name_col, "premium"]].rename(columns={name_col: "name"})
        if others_total > 0:
            legend_df = pd.concat([legend_df, pd.DataFrame([{"name": "Other Agents", "premium": others_total}])], ignore_index=True)
        grand_total = legend_df["premium"].sum()

        st.plotly_chart(
            charts.donut_with_center(legend_df, "name", "premium", "Total (KES)", f"{grand_total:,.0f}"),
            use_container_width=True,
            key="top_agents_donut",
        )
        legend_rows = "".join(
            f'<div class="azm-legend-row"><span class="azm-legend-dot" style="background:{charts.PALETTE[i % len(charts.PALETTE)]};"></span>'
            f'<span class="azm-legend-name">{row["name"]}</span>'
            f'<span class="azm-legend-value">{row["premium"]:,.0f} '
            f'<span class="azm-legend-pct">({row["premium"] / grand_total * 100:,.1f}%)</span></span></div>'
            for i, row in legend_df.iterrows()
        )
        st.markdown(f'<div class="azm-legend-list">{legend_rows}</div>', unsafe_allow_html=True)
    else:
        st.info("No agent ranking data for this date range.")

st.subheader("Product performance")
if not product_sales.empty:
    tables.paginated_table(product_sales, key="overview_products")
    tables.excel_download_button(product_sales, "product_sales.xlsx")
else:
    st.info("No product sales data for this date range.")
