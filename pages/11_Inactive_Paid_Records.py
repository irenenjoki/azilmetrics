import streamlit as st

from src.components import styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import filter_by_date_range
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Inactive & Paid Records",
    icon="📋",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar) — covers that were paid for but are no longer active",
)

covers = filter_by_date_range(loaders.fetch_covers(client), "created_at", filters["from"], filters["to"])
payments = filter_by_date_range(loaders.fetch_payments(client), "created_at", filters["from"], filters["to"])

inactive_statuses = {"inactive", "expired", "canceled", "cancelled"}
status_col = "status" if "status" in covers.columns else None

if status_col and not covers.empty:
    inactive_covers = covers[covers[status_col].isin(inactive_statuses)]
else:
    inactive_covers = covers.iloc[0:0]

paid_cover_ids = set(payments.loc[payments.get("status") == "success", "cover_id"]) if "cover_id" in payments.columns else set()
id_col = "id" if "id" in inactive_covers.columns else None

if id_col and paid_cover_ids:
    inactive_and_paid = inactive_covers[inactive_covers[id_col].isin(paid_cover_ids)]
else:
    inactive_and_paid = inactive_covers.iloc[0:0]

kpi_cards_with_trend(
    [
        {"label": "Inactive covers in range", "value": f"{len(inactive_covers):,}", "icon": "⛔"},
        {"label": "Inactive but paid", "value": f"{len(inactive_and_paid):,}", "icon": "⚠️"},
        {
            "label": "Premium tied up (KES)",
            "value": f"{inactive_and_paid['amount'].sum():,.0f}" if "amount" in inactive_and_paid.columns and not inactive_and_paid.empty else "0",
            "icon": "🪙",
        },
    ],
    key_prefix="ipr",
)

st.divider()
st.caption(
    "These are covers marked inactive/expired/cancelled that still have a successful payment on record "
    "— worth reviewing for reconciliation or reactivation."
)
if not inactive_and_paid.empty:
    tables.paginated_table(inactive_and_paid, key="inactive_paid")
    tables.excel_download_button(inactive_and_paid, "inactive_paid_records.xlsx")
else:
    st.info("No inactive-but-paid records found for this date range — either everything reconciles, or the "
            "cover/payment records don't share a matching cover_id field to join on.")

with st.expander("All inactive covers in range (not just paid)"):
    tables.paginated_table(inactive_covers, key="inactive_all")
