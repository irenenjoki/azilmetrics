"""AZIL staff login HTTP calls, plus the session-state helpers that depend on them."""
from __future__ import annotations

import streamlit as st

from src.components import styles

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
    """Call at the top of every page. Stops the page if the user isn't logged in yet.

    Also (re-)injects the global CSS unconditionally. Streamlit only applies our custom
    st.navigation()-based sidebar/theme once app.py has actually run for a given session —
    if a page ever gets hit directly (e.g. a browser tab deep-linked to a sub-page
    reconnects to a freshly restarted server before hitting the root URL), Streamlit falls
    back to its plain default multipage view. Calling this here too means at least the
    fonts/colors/cards always render correctly even in that edge case, since every
    protected page calls require_client() as its first line regardless of how it was
    reached. (st.markdown-injected <style> tags are harmless to add more than once.)
    """
    styles.inject_global_css()
    if not is_authenticated():
        _render_orphaned_page_notice()
        st.stop()
    return AzilClient(st.session_state["azil_base_url"], st.session_state["azil_token"])


def _render_orphaned_page_notice() -> None:
    """Styled stand-in for st.warning(), used when a page is reached without a valid
    session — looks intentional instead of like Streamlit's raw default fallback.

    Uses a plain HTML anchor (not st.page_link) on purpose: st.page_link looks the
    target page up in Streamlit's internal navigation registry, which only exists once
    app.py has run st.navigation() for this session — exactly what's missing here, so
    st.page_link itself raises a KeyError in this state. A raw `<a href="/">` forces a
    real full-page reload of the root URL instead, which is the actual fix (it makes
    app.py run first), and doesn't depend on that registry at all.
    """
    # A soft st.rerun() can't fix this — the current run is already "stuck" treating this
    # sub-page as the active script, independent of app.py, so rerunning it just repeats
    # the same broken state. Only a real browser navigation to "/" forces app.py to run
    # from scratch. <meta refresh> triggers that automatically after a short delay, so
    # the user doesn't have to click — the link below is just the immediate fallback.
    st.markdown('<meta http-equiv="refresh" content="1; url=/">', unsafe_allow_html=True)
    styles.page_header("Sign in required", icon="🔒", subtitle="Your session isn't active on this page yet.")
    st.info("Reloading from the start automatically — click below if it doesn't happen within a second.")
    st.markdown(
        '<a href="/" target="_self" style="display:inline-block; padding:0.5rem 1.25rem; '
        f'border-radius:0.5rem; background:{styles.BRAND_600}; color:#ffffff; font-weight:600; '
        'text-decoration:none;">🔑 Reload app from the start</a>',
        unsafe_allow_html=True,
    )
