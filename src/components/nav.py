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

POLICIES_PAGES = [
    ("Overview", "pages/1_Overview.py", ":material/dashboard:"),
    ("Policies by Month", "pages/2_Policies_by_Month.py", ":material/calendar_month:"),
    ("Channel Analysis", "pages/3_Channel_Analysis.py", ":material/hub:"),
    ("Financial Metrics", "pages/4_Financial_Metrics.py", ":material/payments:"),
    ("Financial Trends", "pages/5_Financial_Trends.py", ":material/trending_up:"),
    ("Customer Analysis", "pages/6_Customer_Analysis.py", ":material/groups_2:"),
    ("Product Rankings", "pages/7_Product_Rankings.py", ":material/leaderboard:"),
    ("Product Monthly Analysis", "pages/8_Product_Monthly_Analysis.py", ":material/calendar_view_month:"),
    ("Comprehensive Report", "pages/9_Comprehensive_Report.py", ":material/summarize:"),
    ("Transaction Patterns", "pages/10_Transaction_Patterns.py", ":material/credit_card:"),
    ("Inactive & Paid Records", "pages/11_Inactive_Paid_Records.py", ":material/inventory_2:"),
    ("Underwriter Reports", "pages/12_Underwriter_Reports.py", ":material/verified:"),
]

USERS_PAGES = [
    ("User Overview", "pages/13_User_Overview.py", ":material/person:"),
    ("All Users", "pages/14_All_Users.py", ":material/groups:"),
    ("Policies per User", "pages/15_Policies_per_User.py", ":material/assignment_ind:"),
]


def build_pages() -> list[st.Page]:
    authenticated = auth_api.is_authenticated()
    pages = []
    if not authenticated:
        pages.append(st.Page("pages/0_Login.py", title="Login", icon=":material/login:", default=True))
    first = True
    for label, path, icon in POLICIES_PAGES + USERS_PAGES:
        pages.append(st.Page(path, title=label, icon=icon, default=authenticated and first))
        first = False
    return pages


def render() -> None:
    authenticated = auth_api.is_authenticated()
    pages = build_pages()
    page = st.navigation(pages, position="hidden")

    if authenticated:
        with st.sidebar:
            styles.sidebar_brand()

            def render_section(label: str, entries: list[tuple[str, str, str]], offset: int) -> None:
                st.markdown(f'<div class="azm-sidebar-section">{label}</div>', unsafe_allow_html=True)
                for i, (title, path, icon) in enumerate(entries):
                    is_active = page.url_path == next(p.url_path for p in pages if p.title == title)
                    # Key must stay stable across reruns regardless of active state — a key
                    # that changes (e.g. azmnavactive_N vs azmnavitem_N for the same slot)
                    # loses widget identity between pages and can blank the sidebar out.
                    # Active/inactive styling is done in CSS via the marker span below.
                    with st.container(key=f"azmnav_{offset + i}"):
                        if is_active:
                            st.markdown('<span class="azm-nav-active-marker"></span>', unsafe_allow_html=True)
                        st.page_link(path, label=title, icon=icon)

            render_section("Policies", POLICIES_PAGES, offset=0)
            render_section("Users", USERS_PAGES, offset=len(POLICIES_PAGES))

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

        # Navbar only makes sense once there's a dashboard behind it — keep the login
        # screen a clean, full hero layout with no app chrome. Modeled on the ibima
        # reference's Header: section label left, connection/identity/sign-out right.
        # Rendered as plain HTML (not st.columns) — see styles.topbar()'s docstring for
        # why mixing a fixed-position bar with Streamlit's column grid broke layout.
        styles.topbar(auth_api.current_user_display_name(), user.get("email"), connected=True)
        if st.button("Sign Out", key="azm_topbar_logout", icon=":material/logout:"):
            auth_api.logout()
            st.switch_page("pages/0_Login.py")

    page.run()
