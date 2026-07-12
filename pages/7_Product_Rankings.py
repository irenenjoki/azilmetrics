import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import value_counts_df
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Product Rankings",
    icon="🏆",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

product_sales = loaders.fetch_product_sales(client, filters)
products = loaders.fetch_products(client)
underwriters = loaders.fetch_underwriters(client)
vehicles = loaders.fetch_vehicles(client)
covers = loaders.fetch_covers(client)

if not products.empty and not underwriters.empty and "underwriter_id" in products.columns and "id" in underwriters.columns:
    uw_lookup = underwriters.set_index("id")["name"]
    products["underwriter_name"] = products["underwriter_id"].map(uw_lookup)

kpi_row(
    [
        ("Products", f"{len(products):,}"),
        ("Underwriters", f"{len(underwriters):,}"),
        ("Products with sales this range", f"{len(product_sales):,}"),
    ]
)

st.divider()
st.subheader("Top products by amount")
if not product_sales.empty and {"name", "amount"}.issubset(product_sales.columns):
    top_products = product_sales.sort_values("amount", ascending=False).head(10)
    st.plotly_chart(charts.bar_chart(top_products, "amount", "name", orientation="h"), use_container_width=True, key="top_products")
    tables.paginated_table(product_sales.sort_values("amount", ascending=False), key="product_rankings")
    tables.excel_download_button(product_sales, "product_rankings.xlsx")
else:
    st.info("No product sales data for this date range.")

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Products by type")
    counts = value_counts_df(products, "product_type", "product_type")
    if not counts.empty:
        st.plotly_chart(charts.pie_chart(counts, "product_type", "count"), use_container_width=True, key="products_by_type")
    else:
        st.info("No product data available.")

with col2:
    st.subheader("Products by underwriter")
    counts = value_counts_df(products, "underwriter_name", "underwriter") if "underwriter_name" in products.columns else None
    if counts is not None and not counts.empty:
        st.plotly_chart(charts.bar_chart(counts, "count", "underwriter", orientation="h"), use_container_width=True, key="products_by_underwriter")
    else:
        st.info("No underwriter linkage available.")

st.divider()
st.subheader("Vehicle mix")
make_col = next((c for c in vehicles.columns if "make" in c.lower()), None) if not vehicles.empty else None
if make_col:
    source_df, label = vehicles, "vehicles endpoint"
else:
    make_col = next((c for c in covers.columns if "make" in c.lower()), None) if not covers.empty else None
    source_df, label = covers, "vehicle details embedded in covers"

if make_col:
    st.caption(f"Source: {label}")
    counts = value_counts_df(source_df.dropna(subset=[make_col]), make_col, "make").head(15)
    st.plotly_chart(charts.bar_chart(counts, "count", "make", orientation="h", title="Top vehicle makes"), use_container_width=True, key="vehicle_mix")
else:
    st.info("No vehicle make/model data available from either the vehicles endpoint or covers.")
