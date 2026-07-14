"""KPI card renderer — cards are custom HTML/CSS (see styles.py) rather than st.metric,
so we get full control over layout (gradients, spacing, subtext) instead of the default
Streamlit metric widget look.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.utils.formatting import hex_rgba

from . import charts
from .styles import ERROR, SUCCESS, _render_html

# KPI icon circles: blue / green / orange / cyan, one per card.
_ICON_COLORS = [hex_rgba("#2563EB", 0.14), hex_rgba("#16A34A", 0.14), hex_rgba("#EA580C", 0.14), hex_rgba("#0891B2", 0.16)]


def kpi_cards_with_trend(cards: list[dict], key_prefix: str) -> None:
    """Icon-badged KPI cards — the visual standard every page's KPIs should use, per the
    Overview page. Each card dict: {label, value, icon, pct_change, trend_df, trend_col,
    period_label, subtitle}. All but label/value/icon are optional:
    - pct_change/trend_df: a real "+/-X% vs previous period" indicator + sparkline
      (Overview's covers/premium/income/users cards use this — needs a genuine previous-
      period comparison and daily-granularity data, which not every page has).
    - subtitle: a plain caption line (no arrow/color) shown instead, for pages that just
      want icon+color visual consistency without a trend computation — e.g. "3 policies"
      under a "Peak Month" card. Ignored if pct_change is also given.

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
            subtitle = card.get("subtitle")
            trend_html = f'<div class="azm-kpi-trend-label">{subtitle}</div>' if subtitle else ""
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
