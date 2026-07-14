import streamlit as st

from src.components import styles, tables
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.services import auth_api

client = auth_api.require_client()

styles.page_header("All Users", icon="🗂️")

users = loaders.fetch_users(client)

status_col = next((c for c in ("status", "active_status") if c in users.columns), None)
type_col = next((c for c in users.columns if c.endswith("profile_type")), None)

col1, col2, col3 = st.columns(3)
with col1:
    search = st.text_input("Search by name or email", placeholder="Type to filter...")
with col2:
    status_options = ["all"] + sorted(users[status_col].dropna().astype(str).unique().tolist()) if status_col else ["all"]
    status_filter = st.selectbox("Status", status_options)
with col3:
    type_options = ["all"] + sorted(users[type_col].dropna().astype(str).unique().tolist()) if type_col else ["all"]
    type_filter = st.selectbox("User type", type_options)

filtered = users
if search:
    name_col = "name" if "name" in filtered.columns else None
    email_col = "email" if "email" in filtered.columns else None
    mask = False
    if name_col is not None:
        mask = filtered[name_col].astype(str).str.contains(search, case=False, na=False)
    if email_col is not None:
        mask = mask | filtered[email_col].astype(str).str.contains(search, case=False, na=False)
    if name_col or email_col:
        filtered = filtered[mask]
if status_filter != "all" and status_col:
    filtered = filtered[filtered[status_col].astype(str) == status_filter]
if type_filter != "all" and type_col:
    filtered = filtered[filtered[type_col].astype(str) == type_filter]

kpi_cards_with_trend(
    [
        {"label": "Total users", "value": f"{len(users):,}", "icon": "👥"},
        {"label": "Matching filters", "value": f"{len(filtered):,}", "icon": "🔍"},
    ],
    key_prefix="au",
)

st.divider()
tables.paginated_table(filtered, key="all_users")
tables.excel_download_button(filtered, "all_users.xlsx")
