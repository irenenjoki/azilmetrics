import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import daily_sum, filter_by_date_range, success_rate, value_counts_df
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Transaction Patterns",
    icon="💳",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar) — payments & M-Pesa STK",
)

payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", filters["from"], filters["to"])
stk = filter_by_date_range(loaders.fetch_stk_responses(client), "created_at", filters["from"], filters["to"])

success_amount = payments.loc[payments.get("status") == "success", "amount"].sum() if not payments.empty else 0
stk_rate = success_rate(stk, "ResultCode", "0")

kpi_row(
    [
        ("Payments", f"{len(payments):,}"),
        ("Successful amount (KES)", f"{success_amount:,.0f}"),
        ("STK success rate", f"{stk_rate:.1f}%" if stk_rate is not None else "n/a"),
    ]
)

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Payments by status")
    counts = value_counts_df(payments, "status", "status")
    if not counts.empty:
        st.plotly_chart(charts.pie_chart(counts, "status", "count"), use_container_width=True, key="payments_by_status")
    else:
        st.info("No payment data available.")

with col2:
    st.subheader("Payments by mode")
    counts = value_counts_df(payments, "mode", "mode")
    if not counts.empty:
        st.plotly_chart(charts.pie_chart(counts, "mode", "count"), use_container_width=True, key="payments_by_mode")
    else:
        st.info("No payment data available.")

st.subheader("Revenue over time (successful payments)")
daily = daily_sum(payments, "created_at", "amount", filter_col="status", filter_val="success")
if not daily.empty:
    st.plotly_chart(charts.bar_chart(daily, "day", "amount"), use_container_width=True, key="revenue_over_time")
else:
    st.info("No successful payments in this range.")

st.divider()
st.subheader("STK push outcomes")
result_counts = value_counts_df(stk, "ResultDesc", "result").head(10)
if not result_counts.empty:
    st.plotly_chart(
        charts.bar_chart(result_counts, "count", "result", orientation="h", title="Top STK result reasons"),
        use_container_width=True,
        key="stk_outcomes",
    )
else:
    st.info("No STK response data available.")

with st.expander("Raw payments"):
    tables.paginated_table(payments, key="raw_payments")
    tables.excel_download_button(payments, "payments.xlsx")
with st.expander("Raw STK responses"):
    tables.paginated_table(stk, key="raw_stk")
    tables.excel_download_button(stk, "stk_responses.xlsx")
