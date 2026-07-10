import streamlit as st

from src.components import charts, styles, tables
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import value_counts_df
from src.services import auth_api

client = auth_api.require_client()

styles.page_header("Products & Vehicle Mix", icon="🚗")

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
        ("Covers on file", f"{len(covers):,}"),
    ]
)

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Products by type")
    counts = value_counts_df(products, "product_type", "product_type")
    if not counts.empty:
        st.plotly_chart(charts.pie_chart(counts, "product_type", "count"), use_container_width=True)
    else:
        st.info("No product data available.")

with col2:
    st.subheader("Products by underwriter")
    counts = value_counts_df(products, "underwriter_name", "underwriter") if "underwriter_name" in products.columns else None
    if counts is not None and not counts.empty:
        st.plotly_chart(charts.bar_chart(counts, "count", "underwriter", orientation="h"), use_container_width=True)
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
    st.plotly_chart(charts.bar_chart(counts, "count", "make", orientation="h", title="Top vehicle makes"), use_container_width=True)
else:
    st.info("No vehicle make/model data available from either the vehicles endpoint or covers.")

with st.expander("Raw products"):
    tables.paginated_table(products, key="raw_products")
    tables.excel_download_button(products, "products.xlsx")
with st.expander("Raw underwriters"):
    tables.paginated_table(underwriters, key="raw_underwriters")
with st.expander("Raw vehicles"):
    tables.paginated_table(vehicles, key="raw_vehicles")
