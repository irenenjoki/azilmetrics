import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.data import loaders
from src.data.transforms import filter_by_date_range, value_counts_df
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Channel Analysis",
    icon="🔀",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
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
    paid_ids = set(payments.loc[payments.get("status") == "success", "cover_id"])
    covers = covers[covers["id"].isin(paid_ids)] if payment_status == "Paid Only" else covers[~covers["id"].isin(paid_ids)]

channel_col = "channel" if "channel" in covers.columns else None
status_field = "status" if "status" in covers.columns else None


def _channel_view(df, title: str, key_prefix: str) -> None:
    if not channel_col or df.empty:
        st.info("No channel data for this selection.")
        return
    counts = value_counts_df(df, channel_col, "channel")
    if counts.empty:
        st.info("No channel data for this selection.")
        return
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{title}**")
        st.plotly_chart(charts.pie_chart(counts, "channel", "count", donut=True), use_container_width=True, key=f"{key_prefix}_pie")
    with right:
        st.markdown("**Count by Channel**")
        st.plotly_chart(
            charts.bar_chart(counts.sort_values("count"), "count", "channel", orientation="h", show_values=True),
            use_container_width=True,
            key=f"{key_prefix}_bar",
        )
    st.divider()
    tables.styled_table(counts.sort_values("count", ascending=False).rename(columns={"channel": "Channel", "count": "Count"}))
    tables.excel_download_button(counts, f"channel_breakdown_{key_prefix}.xlsx", key=f"{key_prefix}_dl")


tab_active, tab_inactive, tab_monthly, tab_detail = st.tabs(
    ["Active by Channel", "Inactive by Channel", "Channel per Month", "Monthly Detail"]
)

with tab_active:
    active_covers = covers[covers[status_field] == "active"] if status_field else covers
    _channel_view(active_covers, "Active Policies by Channel", key_prefix="active")

with tab_inactive:
    inactive_covers = covers[covers[status_field] != "active"] if status_field else covers.iloc[0:0]
    _channel_view(inactive_covers, "Inactive Policies by Channel", key_prefix="inactive")

with tab_monthly:
    if channel_col and "created_at" in covers.columns and not covers.empty:
        monthly_channel = (
            covers.dropna(subset=["created_at"])
            .assign(month=lambda d: d["created_at"].dt.to_period("M").astype(str))
            .groupby(["month", channel_col])
            .size()
            .reset_index(name="count")
            .sort_values("month")
        )
        if not monthly_channel.empty:
            st.plotly_chart(charts.stacked_bar_chart(monthly_channel, "month", "count", channel_col), use_container_width=True)
        else:
            st.info("No channel-by-month data for this selection.")
    else:
        st.info("No channel/date data for this selection.")

with tab_detail:
    if channel_col and "created_at" in covers.columns and not covers.empty:
        detail = (
            covers.dropna(subset=["created_at"])
            .assign(month=lambda d: d["created_at"].dt.to_period("M").astype(str))
            .groupby(["month", channel_col])
            .size()
            .reset_index(name="count")
            .sort_values(["month", "count"], ascending=[True, False])
            .rename(columns={"month": "Month", channel_col: "Channel", "count": "Count"})
        )
        tables.paginated_table(detail, key="channel_monthly_detail")
        tables.excel_download_button(detail, "channel_monthly_detail.xlsx")
    else:
        st.info("No channel/date data for this selection.")
