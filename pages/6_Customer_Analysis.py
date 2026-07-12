import pandas as pd
import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import filter_by_date_range, find_customer_id_column, link_customers_via_vehicles
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Customer Analysis",
    icon="🧑‍🤝‍🧑",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar) — users who have paid for a policy (switch Payment status below to include pending/unpaid)",
)

status_col, payment_col = st.columns(2)
with status_col:
    policy_status = st.segmented_control("Policy status", ["All Policies", "Active Only", "Inactive Only"], default="All Policies")
with payment_col:
    payment_status = st.segmented_control("Payment status", ["Paid Only", "All", "Unpaid Only"], default="Paid Only")

covers = filter_by_date_range(loaders.fetch_covers(client), "created_at", filters["from"], filters["to"])
payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", filters["from"], filters["to"])

if policy_status == "Active Only" and "status" in covers.columns:
    covers = covers[covers["status"] == "active"]
elif policy_status == "Inactive Only" and "status" in covers.columns:
    covers = covers[covers["status"] != "active"]

paid_cover_ids = set(payments.loc[payments.get("status") == "success", "cover_id"]) if "cover_id" in payments.columns else set()
if payment_status != "All" and "id" in covers.columns:
    covers = covers[covers["id"].isin(paid_cover_ids)] if payment_status == "Paid Only" else covers[~covers["id"].isin(paid_cover_ids)]

if payment_status != "All" and "status" in payments.columns:
    payments = payments[payments["status"] == "success"] if payment_status == "Paid Only" else payments[payments["status"] != "success"]

# "Customer" = a user who has purchased a policy. Try a direct customer-linking field on
# payments/covers first; if the API doesn't expose one there, bridge via vehicles instead —
# AZIL's docs show the real chain is User -> owns Vehicle -> Vehicle has Cover (`GET /vehicles/`
# filters by `user_id` = owner; `GET /covers/` filters by `vehicle_id`), so the purchasing
# user's id lives on the vehicle even when it's absent from the cover/payment record itself.
customer_col, source_df, source_name = None, None, None
for label, df in (("payments", payments), ("covers", covers)):
    col = find_customer_id_column(df)
    if col:
        customer_col, source_df, source_name = col, df, label
        break

vehicles = pd.DataFrame()
if not customer_col:
    vehicles = loaders.fetch_vehicles(client)
    bridged, col = link_customers_via_vehicles(covers, vehicles)
    if col:
        customer_col, source_df, source_name = col, bridged, "covers (via vehicles)"

if not customer_col:
    st.warning(
        "Could not find a way to link policies back to the users who purchased them — neither a "
        "direct customer field on payments/covers, nor a vehicle_id/user_id bridge via vehicles. "
        "Expand below to see the actual fields returned by each endpoint."
    )
    with st.expander("Available columns", expanded=True):
        st.write("Payments:", sorted(payments.columns.tolist()) if not payments.empty else "no payments in range")
        st.write("Covers:", sorted(covers.columns.tolist()) if not covers.empty else "no covers in range")
        st.write("Vehicles:", sorted(vehicles.columns.tolist()) if not vehicles.empty else "no vehicles returned")
    st.stop()

st.caption(f"Customer identity resolved from **{source_name}.{customer_col}**")

users = loaders.fetch_users(client)
if not users.empty and "id" in users.columns:
    display_col = next((c for c in ("name", "full_name", "first_name") if c in users.columns), None)
    if display_col:
        name_lookup = users.set_index("id")[display_col].to_dict()
        source_df = source_df.assign(customer_name=source_df[customer_col].map(name_lookup))

date_col = "created_at"
first_purchase = (
    source_df.dropna(subset=[date_col, customer_col])
    .groupby(customer_col)[date_col]
    .min()
    .reset_index()
    .rename(columns={date_col: "first_purchase"})
)
first_purchase["month"] = first_purchase["first_purchase"].dt.to_period("M").astype(str)
purchase_counts = source_df.groupby(customer_col).size().reset_index(name="purchase_count")
customers = first_purchase.merge(purchase_counts, on=customer_col)
customers["segment"] = customers["purchase_count"].apply(lambda c: "Repeat" if c > 1 else "New")

if "customer_name" in source_df.columns:
    names = source_df[[customer_col, "customer_name"]].dropna(subset=[customer_col]).drop_duplicates(customer_col)
    customers = customers.merge(names, on=customer_col, how="left")

monthly_new = customers.groupby("month", as_index=False).size().rename(columns={"size": "New Customers"}).sort_values("month")

total_customers = len(customers)
new_customers = int((customers["segment"] == "New").sum())
repeat_customers = int((customers["segment"] == "Repeat").sum())
peak = monthly_new.loc[monthly_new["New Customers"].idxmax()] if not monthly_new.empty else None

kpi_row(
    [
        ("Total Customers", f"{total_customers:,}"),
        ("New Customers", f"{new_customers:,}"),
        ("Repeat Customers", f"{repeat_customers:,}"),
        ("Peak Month", peak["month"] if peak is not None else "n/a"),
    ],
    subtitles=["", "", "", f"{int(peak['New Customers']):,} new" if peak is not None else ""],
)

st.divider()

tab_monthly, tab_new_repeat, tab_drill, tab_new_records, tab_repeat_records = st.tabs(
    ["New Customers by Month", "New vs Repeat", "Drill Down", "New Customer Records", "Repeat Customer Records"]
)

with tab_monthly:
    st.subheader("New Customers by Month")
    st.plotly_chart(charts.bar_chart(monthly_new, "month", "New Customers"), use_container_width=True, key="new_customers_chart")
    st.divider()
    tables.styled_table(monthly_new.rename(columns={"month": "Month"}))
    tables.excel_download_button(monthly_new, "new_customers_by_month.xlsx", key="new_customers_dl")

with tab_new_repeat:
    counts = customers["segment"].value_counts().reset_index()
    counts.columns = ["Segment", "Customers"]
    st.plotly_chart(charts.pie_chart(counts, "Segment", "Customers", donut=True), use_container_width=True, key="new_vs_repeat_chart")
    tables.styled_table(counts)

with tab_drill:
    selected_month = st.selectbox("Select a month", monthly_new["month"].tolist()[::-1])
    month_customers = customers[customers["month"] == selected_month]
    kpi_row(
        [
            ("New customers this month", f"{len(month_customers):,}"),
            ("Of which repeat by range-end", f"{(month_customers['segment'] == 'Repeat').sum():,}"),
        ]
    )
    tables.paginated_table(month_customers, key="drill_down_table")

with tab_new_records:
    tables.paginated_table(customers[customers["segment"] == "New"], key="new_customer_records")
    tables.excel_download_button(customers[customers["segment"] == "New"], "new_customer_records.xlsx", key="new_records_dl")

with tab_repeat_records:
    tables.paginated_table(customers[customers["segment"] == "Repeat"], key="repeat_customer_records")
    tables.excel_download_button(customers[customers["segment"] == "Repeat"], "repeat_customer_records.xlsx", key="repeat_records_dl")
