import pandas as pd
import streamlit as st

from src.components import charts, styles
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import extract_trend_df, resample_period
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Financial Trends",
    icon="📉",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

view_by = st.segmented_control("View by", ["Monthly", "Yearly"], default="Monthly")
granularity = "month" if view_by == "Monthly" else "year"

cover_trends = loaders.fetch_cover_trends(client, filters)
income_trends = loaders.fetch_income_trends(client, filters)
expiration_trends = loaders.fetch_expiration_trends(client, {**filters, "granularity": granularity})
renewal_trends = loaders.fetch_renewal_trends(client, {**filters, "granularity": granularity})

cover_totals = cover_trends.get("totals", {}) or {}
income_totals = income_trends.get("totals", {}) or {}

kpi_row(
    [
        ("Premium volume (KES)", f"{cover_totals.get('amount', 0):,.0f}"),
        ("Azil Income (KES)", f"{income_totals.get('income', 0):,.0f}"),
        ("Expiring covers", f"{(expiration_trends.get('totals', {}) or {}).get('count', 0):,}"),
        ("Renewed covers", f"{(renewal_trends.get('totals', {}) or {}).get('count', 0):,}"),
    ]
)

st.divider()
st.subheader("Premium vs. Azil Income")

premium_df = extract_trend_df(cover_trends, value_candidates=("amount",))
income_df = extract_trend_df(income_trends, value_candidates=("income", "total", "amount"))

if not premium_df.empty or not income_df.empty:
    premium_b = resample_period(premium_df, granularity).rename(columns={"value": "Premium"})
    income_b = resample_period(income_df, granularity).rename(columns={"value": "Income"})
    merged = pd.merge(premium_b, income_b, on="period", how="outer").sort_values("period").fillna(0)
    merged["label"] = merged["period"].dt.strftime("%b %Y" if granularity == "month" else "%Y")
    fig = charts.line_chart(merged, "label", "Premium")
    fig.data[0].name = "Premium"
    fig.add_scatter(x=merged["label"], y=merged["Income"], mode="lines+markers", name="Azil Income", line=dict(color=charts.ACCENT))
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True, key="premium_income_chart")
else:
    st.info("No premium/income trend data for this date range.")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Covers expiring")
    exp_df = extract_trend_df(expiration_trends, value_candidates=("count", "total_count"))
    if not exp_df.empty:
        bucketed = resample_period(exp_df, granularity)
        bucketed["label"] = bucketed["period"].dt.strftime("%b %Y" if granularity == "month" else "%Y")
        st.plotly_chart(charts.bar_chart(bucketed, "label", "value"), use_container_width=True, key="expiring_chart")
    else:
        st.info("No expiration trend data for this date range.")

with col2:
    st.subheader("Covers renewed")
    ren_df = extract_trend_df(renewal_trends, value_candidates=("count", "total_count"))
    if not ren_df.empty:
        bucketed = resample_period(ren_df, granularity)
        bucketed["label"] = bucketed["period"].dt.strftime("%b %Y" if granularity == "month" else "%Y")
        st.plotly_chart(charts.bar_chart(bucketed, "label", "value"), use_container_width=True, key="renewed_chart")
    else:
        st.info("No renewal trend data for this date range.")
