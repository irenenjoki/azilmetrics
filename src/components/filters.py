"""Sidebar/page filter widgets. Widgets write their selection into st.session_state."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st


def date_range_filter() -> dict:
    """Sidebar date-range picker shared across every page. Returns {"from": iso, "to": iso}."""
    st.subheader("Date range")
    default_from = date.today() - timedelta(days=30)
    from_date = st.date_input("From", value=st.session_state.get("date_from_obj", default_from))
    to_date = st.date_input("To", value=st.session_state.get("date_to_obj", date.today()))
    st.session_state["date_from_obj"] = from_date
    st.session_state["date_to_obj"] = to_date
    st.session_state["date_from"] = from_date.isoformat()
    st.session_state["date_to"] = to_date.isoformat()
    return {"from": st.session_state["date_from"], "to": st.session_state["date_to"]}


def current_date_filters() -> dict:
    """Read the date range chosen in the sidebar, defaulting to the last 30 days."""
    default_from = (date.today() - timedelta(days=30)).isoformat()
    return {
        "from": st.session_state.get("date_from", default_from),
        "to": st.session_state.get("date_to", date.today().isoformat()),
    }


def status_select(options: list[str], label: str = "Cover status") -> str:
    return st.selectbox(label, ["all", *options], index=0)


def channel_select(options: list[str], label: str = "Channel") -> str:
    return st.selectbox(label, ["all", *options], index=0)
