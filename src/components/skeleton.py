"""Shimmering placeholder blocks shown in an st.empty() slot while a page's slower data
calls (API fetches that miss @st.cache_data) are still running, then swapped out for the
real content once it's ready — see pages/1_Overview.py for the st.empty() placeholder
pattern this is meant to be used with.
"""
from __future__ import annotations

import streamlit as st

from .styles import _render_html


def kpi_row(n: int = 4) -> None:
    """n shimmering blocks shaped like metrics.kpi_cards_with_trend()'s cards."""
    cols = st.columns(n)
    for col in cols:
        with col:
            _render_html(
                """
                <div class="azm-skeleton-card">
                    <div class="azm-skeleton azm-skeleton-circle"></div>
                    <div class="azm-skeleton azm-skeleton-line" style="width: 60%; margin-top: 0.6rem;"></div>
                    <div class="azm-skeleton azm-skeleton-line" style="width: 40%; height: 1.5rem; margin-top: 0.4rem;"></div>
                    <div class="azm-skeleton azm-skeleton-line" style="width: 50%; margin-top: 0.4rem;"></div>
                </div>
                """
            )


def chart(height: int = 260) -> None:
    """A single shimmering block shaped like a chart panel."""
    _render_html(f'<div class="azm-skeleton azm-skeleton-block" style="height: {height}px;"></div>')


def table(rows: int = 5) -> None:
    """A stack of shimmering row bars shaped like a table/list."""
    rows_html = "".join('<div class="azm-skeleton azm-skeleton-line" style="margin-top: 0.6rem;"></div>' for _ in range(rows))
    _render_html(f'<div class="azm-skeleton-table">{rows_html}</div>')
