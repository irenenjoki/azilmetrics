import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Overview", icon="📊", subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)"
)

cover_trends = loaders.fetch_cover_trends(client, filters)
income_trends = loaders.fetch_income_trends(client, filters)
agent_ranks = loaders.fetch_agent_ranks(client, filters)
product_sales = loaders.fetch_product_sales(client, filters)

cover_totals = cover_trends.get("totals", {}) or {}
income_totals = income_trends.get("totals", {}) or {}

kpi_row(
    [
        ("Policies (covers)", f"{cover_totals.get('count', 0):,}"),
        ("Premium volume (KES)", f"{cover_totals.get('amount', 0):,.0f}"),
        ("Income (KES)", f"{income_totals.get('income', 0):,.0f}"),
    ]
)

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Revenue trend")
    trend_rows = income_trends.get("trends") or []
    if trend_rows:
        tdf = pd.DataFrame(trend_rows)
        date_col = "date" if "date" in tdf.columns else tdf.columns[0]
        value_col = next((c for c in ("income", "total", "amount") if c in tdf.columns), None)
        if value_col:
            tdf[date_col] = pd.to_datetime(tdf[date_col], errors="coerce")
            tdf = tdf.sort_values(date_col)
            st.plotly_chart(charts.line_chart(tdf, date_col, value_col), use_container_width=True)
    else:
        st.info("No income trend data for this date range.")

with right:
    st.subheader("Top agents by premium")
    if not agent_ranks.empty and "premium" in agent_ranks.columns:
        top_agents = agent_ranks.sort_values("premium", ascending=False).head(10)
        st.plotly_chart(charts.bar_chart(top_agents, "premium", "name", orientation="h"), use_container_width=True)
    else:
        st.info("No agent ranking data for this date range.")

st.subheader("Product performance")
if not product_sales.empty:
    tables.paginated_table(product_sales, key="overview_products")
    tables.excel_download_button(product_sales, "product_sales.xlsx")
else:
    st.info("No product sales data for this date range.")
