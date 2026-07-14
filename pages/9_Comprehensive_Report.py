import streamlit as st

from src.components import styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Comprehensive Report",
    icon="🧾",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

cover_trends = loaders.fetch_cover_trends(client, filters)
income_trends = loaders.fetch_income_trends(client, filters)
agent_ranks = loaders.fetch_agent_ranks(client, filters)
product_sales = loaders.fetch_product_sales(client, filters)
underwriter_ranks = loaders.fetch_underwriter_ranks(client, filters)

cover_totals = cover_trends.get("totals", {}) or {}
income_totals = income_trends.get("totals", {}) or {}

kpi_cards_with_trend(
    [
        {"label": "Policies", "value": f"{cover_totals.get('count', 0):,}", "icon": "🛡️"},
        {"label": "Premium volume (KES)", "value": f"{cover_totals.get('amount', 0):,.0f}", "icon": "🪙"},
        {"label": "Azil Income (KES)", "value": f"{income_totals.get('income', 0):,.0f}", "icon": "📊"},
    ],
    key_prefix="cr",
)

st.caption("This report bundles the period's key tables into one downloadable workbook.")
tables.excel_download_button_multi(
    {
        "Agent Ranks": agent_ranks,
        "Product Sales": product_sales,
        "Underwriter Ranks": underwriter_ranks,
    },
    "comprehensive_report.xlsx",
)

st.divider()
st.subheader("Agent leaderboard")
if not agent_ranks.empty:
    tables.paginated_table(agent_ranks, key="report_agents")
else:
    st.info("No agent ranking data for this date range.")

st.subheader("Product sales")
if not product_sales.empty:
    tables.paginated_table(product_sales, key="report_products")
else:
    st.info("No product sales data for this date range.")

st.subheader("Underwriter rankings")
if not underwriter_ranks.empty:
    tables.paginated_table(underwriter_ranks, key="report_underwriters")
else:
    st.info("No underwriter ranking data for this date range.")
