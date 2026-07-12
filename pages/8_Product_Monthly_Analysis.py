from datetime import date

import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.data import loaders
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Product Monthly Analysis",
    icon="📦",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

# /dashboard/product-sales returns one aggregate per product for a date range, with no
# built-in monthly breakdown — so build the monthly view ourselves by calling it once
# per calendar month in the selected range (capped so a huge range can't trigger dozens
# of API calls).
from_date = pd.to_datetime(filters["from"]).date()
to_date = pd.to_datetime(filters["to"]).date()
months = pd.period_range(from_date, to_date, freq="M")[:12]

rows = []
for period in months:
    month_from = max(period.start_time.date(), from_date)
    month_to = min(period.end_time.date(), to_date)
    sales = loaders.fetch_product_sales(client, {"from": month_from.isoformat(), "to": month_to.isoformat()})
    if not sales.empty and {"name", "amount"}.issubset(sales.columns):
        for _, row in sales.iterrows():
            rows.append({"month": period.strftime("%b %Y"), "product": row["name"], "amount": row.get("amount", 0)})

monthly_df = pd.DataFrame(rows)

if monthly_df.empty:
    st.info("No product sales data across this date range.")
else:
    top_products = monthly_df.groupby("product")["amount"].sum().sort_values(ascending=False).head(5).index.tolist()
    st.subheader("Top 5 products — monthly amount")
    pivot = monthly_df[monthly_df["product"].isin(top_products)]
    fig = charts.line_chart(pivot[pivot["product"] == top_products[0]], "month", "amount")
    fig.data[0].name = top_products[0]
    for product in top_products[1:]:
        series = pivot[pivot["product"] == product]
        fig.add_scatter(x=series["month"], y=series["amount"], mode="lines+markers", name=product)
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Monthly product sales table")
    tables.paginated_table(monthly_df.sort_values(["month", "amount"], ascending=[True, False]), key="product_monthly")
    tables.excel_download_button(monthly_df, "product_monthly_analysis.xlsx")
