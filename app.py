"""Entry point — navigation only. Page content (including Login) lives under pages/."""
import streamlit as st

from src.components import nav, styles
from src.config import get_logger, get_settings
from src.services import auth_api

settings = get_settings()
logger = get_logger(__name__)

authenticated = auth_api.is_authenticated()

st.set_page_config(
    page_title=settings.app_name,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" if authenticated else "collapsed",
)
styles.inject_global_css(login_mode=not authenticated)

nav.render()
