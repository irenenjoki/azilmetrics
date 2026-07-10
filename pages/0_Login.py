import streamlit as st

from src.components import styles
from src.components.auth_forms import render_login_form
from src.config import get_settings
from src.services import auth_api

settings = get_settings()

if auth_api.is_authenticated():
    styles.page_header(settings.app_name, icon="🔑", subtitle="Sign in to view the dashboard")
    with st.container(border=True):
        st.success("You're already logged in. Use the sidebar to open a dashboard page.")
        if st.button("Go to Overview"):
            st.switch_page("pages/1_Overview.py")
else:
    left, center, right = st.columns([0.5, 2, 0.5])
    with center:
        with st.container(key="azm_login_card", border=True):
            styles.login_form_header()
            render_login_form(settings)
