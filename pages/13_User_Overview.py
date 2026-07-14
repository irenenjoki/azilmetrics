import streamlit as st

from src.components import charts, styles
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import daily_count, filter_by_date_range, value_counts_df
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "User Overview",
    icon="👤",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

users = loaders.fetch_users(client)

# /users/ returns every account type (admin, staff, agent, user per AZIL's own schema) — split
# out customer-type accounts so "Total accounts" (everyone) and "Customers" (buyers) aren't conflated.
type_col = next((c for c in users.columns if c.endswith("profile_type")), None)
customer_count = int((users[type_col] == "user").sum()) if type_col else None

active_col = next((c for c in ("status", "active_status") if c in users.columns), None)
if active_col == "status":
    active_count = (users["status"] == "active").sum()
elif active_col == "active_status":
    active_count = (users["active_status"] == 1).sum()
else:
    active_count = None

new_in_range = filter_by_date_range(users, "created_at", filters["from"], filters["to"]).shape[0] if not users.empty else 0

kpi_cards_with_trend(
    [
        {"label": "Total accounts", "value": f"{len(users):,}", "icon": "👤"},
        {"label": "Customers", "value": f"{customer_count:,}" if customer_count is not None else "n/a", "icon": "👥"},
        {"label": "Active accounts", "value": f"{active_count:,}" if active_count is not None else "n/a", "icon": "✅"},
        {"label": "New signups in range", "value": f"{new_in_range:,}", "icon": "🆕"},
    ],
    key_prefix="uo",
)

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Signups over time")
    daily = daily_count(users, "created_at", "signups")
    if not daily.empty:
        st.plotly_chart(charts.line_chart(daily, "day", "signups"), use_container_width=True, key="signups_over_time")
    else:
        st.info("No signup dates available.")

with col2:
    st.subheader("Active vs inactive")
    if active_col:
        labels = users[active_col].map(lambda v: "active" if v in ("active", 1) else "inactive")
        counts = labels.value_counts().reset_index()
        counts.columns = ["state", "count"]
        st.plotly_chart(charts.pie_chart(counts, "state", "count"), use_container_width=True, key="active_vs_inactive")
    else:
        st.info("No active/inactive field available.")

st.subheader("User type mix")
type_col = next((c for c in users.columns if c.endswith("profile_type")), None)
if type_col:
    counts = value_counts_df(users, type_col, "type")
    st.plotly_chart(charts.bar_chart(counts, "type", "count"), use_container_width=True, key="user_type_mix")
else:
    st.info("No user profile-type field available.")
