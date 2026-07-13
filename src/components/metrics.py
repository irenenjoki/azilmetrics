"""KPI card renderer — cards are custom HTML/CSS (see styles.py) rather than st.metric,
so we get full control over layout (gradients, spacing, subtext) instead of the default
Streamlit metric widget look.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.utils.formatting import hex_rgba

from . import charts
from .styles import ACCENT_MUTED, BRAND_100, ERROR, SUCCESS, TEAL_300, _render_html

_GRADIENTS = [BRAND_100, hex_rgba(SUCCESS, 0.12), ACCENT_MUTED, hex_rgba(TEAL_300, 0.3), hex_rgba(ERROR, 0.1)]
# KPI icon circles: blue / green / orange / cyan, one per card.
_ICON_COLORS = [hex_rgba("#2563EB", 0.14), hex_rgba("#16A34A", 0.14), hex_rgba("#EA580C", 0.14), hex_rgba("#0891B2", 0.16)]


def kpi_row(items: list[tuple[str, str]], subtitles: list[str] | None = None) -> None:
    """Render a row of KPI cards. items is a list of (label, formatted_value)."""
    subtitles = subtitles or [""] * len(items)
    cols = st.columns(len(items))
    for i, (col, (label, value), sub) in enumerate(zip(cols, items, subtitles)):
        gradient = _GRADIENTS[i % len(_GRADIENTS)]
        sub_html = f'<div class="azm-kpi-sub">{sub}</div>' if sub else ""
        with col:
            _render_html(
                f"""
                <div class="azm-kpi-card" style="--azm-grad-from: {gradient};">
                    <div class="azm-kpi-label">{label}</div>
                    <div class="azm-kpi-value">{value}</div>
                    {sub_html}
                </div>
                """
            )


def kpi_cards_with_trend(cards: list[dict], key_prefix: str) -> None:
    """Icon-badged KPI cards with a "+/-X% vs previous period" indicator and a small
    trend sparkline underneath — each card dict: {label, value, icon, pct_change,
    trend_df, trend_col, period_label}. pct_change/trend_df are optional (None/empty
    skips that part of the card cleanly).

    Split across two renders (HTML header, then a real st.plotly_chart) inside the same
    st.container(key=...) so the sparkline visually sits inside the card — the container
    itself carries the card's border/background via the azmkpiv2_ CSS below, since a
    live Plotly chart can't be embedded inside a raw HTML string.
    """
    cols = st.columns(len(cards))
    for i, (col, card) in enumerate(zip(cols, cards)):
        icon_bg = _ICON_COLORS[i % len(_ICON_COLORS)]
        pct = card.get("pct_change")
        if pct is None:
            trend_html = ""
        else:
            up = pct >= 0
            color = SUCCESS if up else ERROR
            arrow = "▲" if up else "▼"
            period_label = card.get("period_label", "vs previous period")
            trend_html = (
                f'<div class="azm-kpi-trend"><span style="color:{color};">{arrow} {abs(pct):.1f}%</span> '
                f'<span class="azm-kpi-trend-label">{period_label}</span></div>'
            )
        with col:
            with st.container(key=f"azmkpiv2_{key_prefix}_{i}"):
                _render_html(
                    f"""
                    <div class="azm-kpi-icon" style="background:{icon_bg};">{card['icon']}</div>
                    <div class="azm-kpi-label">{card['label']}</div>
                    <div class="azm-kpi-value">{card['value']}</div>
                    {trend_html}
                    """
                )
                trend_df: pd.DataFrame | None = card.get("trend_df")
                trend_col = card.get("trend_col", "value")
                if trend_df is not None and not trend_df.empty:
                    st.plotly_chart(
                        charts.sparkline(trend_df, "period", trend_col),
                        use_container_width=True,
                        key=f"azmkpiv2_{key_prefix}_{i}_spark",
                        config={"displayModeBar": False},
                    )
