"""Login screen UI."""
from __future__ import annotations

import streamlit as st

from src.config import Settings
from src.services import auth_api
from src.services.api_client import ApiError


def render_login_form(settings: Settings) -> None:
    st.subheader("Sign in to Continue")
    with st.form("login_form"):
        email = st.text_input("Email", value=settings.azil_api_email)
        password = st.text_input("Password", value=settings.azil_api_password, type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        try:
            auth_api.login(settings.azil_api_base_url, email, password)
            st.switch_page("pages/1_Overview.py")
        except ApiError as e:
            st.error(str(e))
