import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import channel_select, current_date_filters, status_select
from src.components.metrics import kpi_row
from src.data import loaders
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Business KPIs", icon="📈", subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)"
)

status = status_select(["active", "pending", "inactive", "canceled", "expired"])
channel = channel_select(["web", "ussd", "agent", "whatsapp", "ios", "android"])

trend_filters = dict(filters)
if status != "all":
    trend_filters["status"] = status
if channel != "all":
    trend_filters["channel"] = channel

cover_trends = loaders.fetch_cover_trends(client, trend_filters)
income_trends = loaders.fetch_income_trends(client, trend_filters)
agent_ranks = loaders.fetch_agent_ranks(client, trend_filters)
product_sales = loaders.fetch_product_sales(client, trend_filters)

cover_totals = cover_trends.get("totals", {}) or {}
income_totals = income_trends.get("totals", {}) or {}

kpi_row(
    [
        ("Covers", f"{cover_totals.get('count', 0):,}"),
        ("Premium volume (KES)", f"{cover_totals.get('amount', 0):,.0f}"),
        ("Income (KES)", f"{income_totals.get('income', 0):,.0f}"),
    ]
)

st.divider()
cover_rows = cover_trends.get("trends") or []
income_rows = income_trends.get("trends") or []

col1, col2 = st.columns(2)
with col1:
    st.subheader("Covers sold over time")
    if cover_rows:
        cdf = pd.DataFrame(cover_rows)
        date_col = "date" if "date" in cdf.columns else cdf.columns[0]
        value_col = next((c for c in ("count", "total_count") if c in cdf.columns), None)
        if value_col:
            cdf[date_col] = pd.to_datetime(cdf[date_col], errors="coerce")
            cdf = cdf.sort_values(date_col)
            st.plotly_chart(charts.bar_chart(cdf, date_col, value_col), use_container_width=True)
    else:
        st.info("No cover trend data for this selection.")

with col2:
    st.subheader("Income over time")
    if income_rows:
        idf = pd.DataFrame(income_rows)
        date_col = "date" if "date" in idf.columns else idf.columns[0]
        value_col = next((c for c in ("income", "total", "amount") if c in idf.columns), None)
        if value_col:
            idf[date_col] = pd.to_datetime(idf[date_col], errors="coerce")
            idf = idf.sort_values(date_col)
            st.plotly_chart(charts.line_chart(idf, date_col, value_col), use_container_width=True)
    else:
        st.info("No income trend data for this selection.")

st.divider()
st.subheader("Agent leaderboard")
if not agent_ranks.empty:
    show_cols = [c for c in ("name", "count", "premium") if c in agent_ranks.columns]
    tables.paginated_table(agent_ranks[show_cols].sort_values("premium", ascending=False), key="agent_ranks")
else:
    st.info("No agent ranking data for this selection.")

st.subheader("Product sales")
if not product_sales.empty:
    tables.paginated_table(product_sales, key="product_sales")
    tables.excel_download_button(product_sales, "product_sales.xlsx")
    if {"name", "amount"}.issubset(product_sales.columns):
        top_products = product_sales.sort_values("amount", ascending=False).head(10)
        st.plotly_chart(
            charts.bar_chart(top_products, "amount", "name", orientation="h", title="Top products by amount"),
            use_container_width=True,
        )
else:
    st.info("No product sales data for this selection.")
