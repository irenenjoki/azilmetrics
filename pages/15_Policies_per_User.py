import streamlit as st

from src.components import styles, tables
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import find_customer_id_column
from src.services import auth_api

client = auth_api.require_client()

styles.page_header("Policies per User", icon="🔍", subtitle="Look up a specific user's covers and payment history")

users = loaders.fetch_users(client)
covers = loaders.fetch_covers(client)
payments = loaders.fetch_payments(client)

if users.empty or "id" not in users.columns:
    st.info("No user data available to search.")
    st.stop()

name_col = next((c for c in ("name", "email") if c in users.columns), "id")
users = users.assign(_label=users[name_col].astype(str) + " (" + users["id"].astype(str) + ")")

selected_label = st.selectbox("Select a user", users["_label"].tolist())
selected_user = users[users["_label"] == selected_label].iloc[0]
user_id = selected_user["id"]
user_phone = next((selected_user.get(c) for c in ("msisdn", "phone_number") if c in users.columns and selected_user.get(c)), None)

# Covers embed the customer as a nested object (user/owner/client/customer) rather than a
# guaranteed flat `user_id` — try an ID column first, then fall back to matching by phone
# number if no covers matched by ID (covers embeds a phone as e.g. user_msisdn).
customer_col = find_customer_id_column(covers)
user_covers = covers[covers[customer_col].astype(str) == str(user_id)] if customer_col else covers.iloc[0:0]

if user_covers.empty and user_phone:
    phone_col = next(
        (c for c in covers.columns if c.endswith(("_msisdn", "_phone_number")) or c in ("msisdn", "phone_number")), None
    )
    if phone_col:
        user_covers = covers[covers[phone_col].astype(str) == str(user_phone)]

payment_user_col = next((c for c in payments.columns if c in ("user_id",)), None)
cover_id_col = "id" if "id" in user_covers.columns else None
if payment_user_col:
    user_payments = payments[payments[payment_user_col].astype(str) == str(user_id)]
elif cover_id_col and "cover_id" in payments.columns and not user_covers.empty:
    user_payments = payments[payments["cover_id"].isin(user_covers[cover_id_col])]
else:
    user_payments = payments.iloc[0:0]

kpi_cards_with_trend(
    [
        {"label": "Policies held", "value": f"{len(user_covers):,}", "icon": "🛡️"},
        {
            "label": "Total premium (KES)",
            "value": f"{user_covers['amount'].sum():,.0f}" if "amount" in user_covers.columns else "n/a",
            "icon": "🪙",
        },
        {"label": "Payments made", "value": f"{len(user_payments):,}", "icon": "💳"},
    ],
    key_prefix="ppu",
)

st.divider()
st.subheader(f"Policies for {selected_label}")
if not user_covers.empty:
    tables.paginated_table(user_covers, key="user_covers")
    tables.excel_download_button(user_covers, "user_policies.xlsx")
else:
    st.info(
        "No policies matched this user by ID or phone number — the covers endpoint's customer "
        "linkage field may use a different name than what this page checks for."
    )

st.subheader("Payment history")
if not user_payments.empty:
    tables.paginated_table(user_payments, key="user_payments")
else:
    st.info("No payments found for this user.")
