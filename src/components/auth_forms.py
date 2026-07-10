"""Login screen UI."""
from __future__ import annotations

import streamlit as st

from src.config import Settings
from src.services import auth_api
from src.services.api_client import ApiError


def render_login_form(settings: Settings) -> None:
    """The functional email/password form, matching AZIL-FRONTEND's real client login
    (src/modules/client/dashboard/login/index.tsx) — same field labels, icons, and
    "Access Dashboard" button text. The heading above it comes from
    styles.login_form_header() so this only renders the fields + submit."""
    with st.form("login_form", border=False):
        email = st.text_input(
            "Email", value=settings.azil_api_email, placeholder="Enter email", icon=":material/mail:"
        )
        password = st.text_input(
            "Password",
            value=settings.azil_api_password,
            type="password",
            placeholder="Enter your password",
            icon=":material/lock:",
        )
        submitted = st.form_submit_button("Access Dashboard", use_container_width=True, type="primary")

    if submitted:
        try:
            auth_api.login(settings.azil_api_base_url, email, password)
            st.switch_page("pages/1_Overview.py")
        except ApiError as e:
            st.error(str(e))
