import streamlit as st

from src.components import styles
from src.components.auth_forms import render_login_form
from src.config import get_settings
from src.services import auth_api

settings = get_settings()

styles.page_header(settings.app_name, icon="🔑", subtitle="Sign in to view the dashboard")

if auth_api.is_authenticated():
    with st.container(border=True):
        st.success("You're already logged in. Use the sidebar to open a dashboard page.")
        if st.button("Go to Overview"):
            st.switch_page("pages/1_Overview.py")
else:
    with st.container(border=True):
        render_login_form(settings)
