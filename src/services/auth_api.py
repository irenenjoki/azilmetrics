"""AZIL staff login HTTP calls, plus the session-state helpers that depend on them."""
from __future__ import annotations

import streamlit as st

from .api_client import ApiError, AzilClient, unwrap


def login(base_url: str, email: str, password: str) -> None:
    """Authenticate against POST /auth/login, then GET /auth/me for the display name."""
    client = AzilClient(base_url)
    token = client.login(email, password)
    st.session_state["azil_base_url"] = base_url
    st.session_state["azil_token"] = token

    try:
        me = unwrap(client.get("/auth/me"))
        if isinstance(me, dict) and isinstance(me.get("data"), dict):
            me = me["data"]  # some AZIL endpoints double-wrap: {data: {data: {...user...}}}
        st.session_state["azil_user"] = me if isinstance(me, dict) else None
    except ApiError:
        st.session_state["azil_user"] = None


def logout() -> None:
    for key in ("azil_base_url", "azil_token", "azil_user"):
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("azil_token"))


def current_user() -> dict | None:
    return st.session_state.get("azil_user")


def current_user_display_name() -> str | None:
    user = current_user()
    if not user:
        return None
    return user.get("name") or user.get("email")


def require_client() -> AzilClient:
    """Call at the top of every page. Stops the page if the user isn't logged in yet."""
    if not is_authenticated():
        st.warning("Please log in first.")
        st.page_link("pages/0_Login.py", label="Go to Login", icon="🔑")
        st.stop()
    return AzilClient(st.session_state["azil_base_url"], st.session_state["azil_token"])
