import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_row
from src.data import loaders
from src.data.transforms import filter_by_date_range
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Policies by Month",
    icon="📆",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (widen it in the sidebar to see more months)",
)

status_col, payment_col = st.columns(2)
with status_col:
    policy_status = st.segmented_control("Policy status", ["All Policies", "Active Only", "Inactive Only"], default="All Policies")
with payment_col:
    payment_status = st.segmented_control("Payment status", ["All", "Paid Only", "Unpaid Only"], default="All")

covers = filter_by_date_range(loaders.fetch_covers(client), "created_at", filters["from"], filters["to"])
payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", filters["from"], filters["to"])

if policy_status == "Active Only" and "status" in covers.columns:
    covers = covers[covers["status"] == "active"]
elif policy_status == "Inactive Only" and "status" in covers.columns:
    covers = covers[covers["status"] != "active"]

if payment_status != "All" and "cover_id" in payments.columns and "id" in covers.columns:
    paid_cover_ids = set(payments.loc[payments.get("status") == "success", "cover_id"])
    covers = covers[covers["id"].isin(paid_cover_ids)] if payment_status == "Paid Only" else covers[~covers["id"].isin(paid_cover_ids)]

if covers.empty or "created_at" not in covers.columns:
    st.info("No policy data for this selection.")
    st.stop()

covers = covers.dropna(subset=["created_at"]).assign(month=lambda d: d["created_at"].dt.to_period("M"))
monthly = covers.groupby("month").size().reset_index(name="count").sort_values("month")
monthly["month_label"] = monthly["month"].astype(str)

total_policies = len(covers)
num_months = monthly["month"].nunique()
peak_row = monthly.loc[monthly["count"].idxmax()] if not monthly.empty else None

kpi_row(
    [
        ("Total Policies", f"{total_policies:,}"),
        ("Months", f"{num_months:,}"),
        ("Peak Month", peak_row["month_label"] if peak_row is not None else "n/a"),
    ],
    subtitles=["", "", f"{int(peak_row['count']):,} policies" if peak_row is not None else ""],
)

st.divider()

tab_overview, tab_single_month, tab_records = st.tabs(["Monthly Overview", "Single Month Breakdown", "Records by Month"])

with tab_overview:
    st.subheader("Policies Created per Month")
    st.plotly_chart(charts.bar_chart(monthly, "month_label", "count"), use_container_width=True, key="policies_per_month_chart")

    st.subheader("Records by month")
    table = monthly[["month_label", "count"]].rename(columns={"month_label": "Month", "count": "Count"})
    tables.paginated_table(table, key="policies_by_month_table")
    tables.excel_download_button(table, "policies_by_month.xlsx")

with tab_single_month:
    selected_month = st.selectbox("Select a month", monthly["month_label"].tolist()[::-1])
    month_covers = covers[covers["month"].astype(str) == selected_month]

    kpi_row(
        [
            ("Policies this month", f"{len(month_covers):,}"),
            ("Premium volume (KES)", f"{month_covers['amount'].sum():,.0f}" if "amount" in month_covers.columns else "n/a"),
        ]
    )

    if "channel" in month_covers.columns:
        st.subheader(f"Channel mix — {selected_month}")
        counts = month_covers["channel"].value_counts().reset_index()
        counts.columns = ["channel", "count"]
        if not counts.empty:
            st.plotly_chart(charts.pie_chart(counts, "channel", "count"), use_container_width=True, key="single_month_channel_mix")

    st.subheader(f"Policy records — {selected_month}")
    tables.paginated_table(month_covers, key="single_month_records")
    tables.excel_download_button(month_covers, f"policies_{selected_month}.xlsx")

with tab_records:
    st.subheader("All policy records in range")
    ordered = covers.sort_values("created_at", ascending=False)
    tables.paginated_table(ordered, key="records_by_month")
    tables.excel_download_button(ordered, "policy_records.xlsx")
