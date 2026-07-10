"""Custom sidebar chrome + st.navigation wiring — the only routing logic in the app.

st.navigation's automatic sidebar widget always pins itself to the top of the sidebar,
which fights the layout we actually want (brand wordmark, then nav, then identity card,
then logout, then filters). So navigation runs with position="hidden" and we render the
page list ourselves via st.page_link(), wrapped in st.container(key=...) so styles.py can
target the active vs. inactive rows with plain CSS instead of guessing at Streamlit's
internal class names. Visual reference: AZIL-FRONTEND's admin SideNav (dark navy,
brand-tinted active link) and Header (welcome + profile chip) for the navbar.
"""
from __future__ import annotations

import streamlit as st

from src.services import auth_api

from . import styles
from .filters import date_range_filter


def build_pages() -> list[st.Page]:
    authenticated = auth_api.is_authenticated()
    pages = []
    if not authenticated:
        pages.append(st.Page("pages/0_Login.py", title="Login", icon=":material/login:", default=True))
    pages.extend(
        [
            st.Page("pages/1_Overview.py", title="Overview", icon=":material/dashboard:", default=authenticated),
            st.Page("pages/2_Business_KPIs.py", title="Business KPIs", icon=":material/bar_chart:"),
            st.Page("pages/3_Payments_STK.py", title="Payments & STK", icon=":material/credit_card:"),
            st.Page("pages/4_Products_Vehicles.py", title="Products & Vehicles", icon=":material/directions_car:"),
            st.Page("pages/5_User_Growth.py", title="User Growth", icon=":material/groups:"),
        ]
    )
    return pages


def render() -> None:
    authenticated = auth_api.is_authenticated()
    pages = build_pages()
    page = st.navigation(pages, position="hidden")

    if authenticated:
        with st.sidebar:
            styles.sidebar_brand()

            for i, p in enumerate(pages):
                is_active = p.url_path == page.url_path
                key = f"azmnavactive_{i}" if is_active else f"azmnavitem_{i}"
                with st.container(key=key):
                    st.page_link(p, label=p.title, icon=p.icon)

            st.divider()

            user = auth_api.current_user() or {}
            styles.sidebar_user_card(auth_api.current_user_display_name(), user.get("email"))
            with st.container(key="azm_logout"):
                if st.button("Logout", icon=":material/logout:"):
                    auth_api.logout()
                    st.switch_page("pages/0_Login.py")

            st.divider()
            date_range_filter()
            st.caption("This range applies to the KPI cards and trend charts on every page.")

    styles.topbar(auth_api.current_user_display_name())
    page.run()
