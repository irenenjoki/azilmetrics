"""KPI card renderer — cards are custom HTML/CSS (see styles.py) rather than st.metric,
so we get full control over layout (gradients, spacing, subtext) instead of the default
Streamlit metric widget look.
"""
from __future__ import annotations

import streamlit as st

from src.utils.formatting import hex_rgba

from .styles import ACCENT_MUTED, BRAND_100, ERROR, SUCCESS, TEAL_300

_GRADIENTS = [BRAND_100, hex_rgba(SUCCESS, 0.12), ACCENT_MUTED, hex_rgba(TEAL_300, 0.3), hex_rgba(ERROR, 0.1)]


def kpi_row(items: list[tuple[str, str]], subtitles: list[str] | None = None) -> None:
    """Render a row of KPI cards. items is a list of (label, formatted_value)."""
    subtitles = subtitles or [""] * len(items)
    cols = st.columns(len(items))
    for i, (col, (label, value), sub) in enumerate(zip(cols, items, subtitles)):
        gradient = _GRADIENTS[i % len(_GRADIENTS)]
        sub_html = f'<div class="azm-kpi-sub">{sub}</div>' if sub else ""
        with col:
            st.markdown(
                f"""
                <div class="azm-kpi-card" style="--azm-grad-from: {gradient};">
                    <div class="azm-kpi-label">{label}</div>
                    <div class="azm-kpi-value">{value}</div>
                    {sub_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
