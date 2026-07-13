"""Colour palette + plotly style builders, so every page's charts look consistent."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.formatting import hex_rgba

from .styles import ACCENT, BRAND_400, BRAND_600, ERROR, SUCCESS, WARNING

PRIMARY = BRAND_600
PALETTE = [BRAND_600, ACCENT, SUCCESS, WARNING, ERROR, BRAND_400]


def _apply_theme(fig: go.Figure, title: str | None = None, show_legend: bool = False) -> go.Figure:
    layout_kwargs = dict(
        colorway=PALETTE,
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    # Only set `title` when there is one — passing title=None explicitly serializes as a
    # null title in the JSON spec sent to the browser, which some Plotly.js versions
    # render as the literal text "undefined" instead of no title at all.
    if title:
        layout_kwargs["title"] = title
    fig.update_layout(**layout_kwargs)
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, title: str | None = None) -> go.Figure:
    # Single-series chart with no color/group column, so px.line sets no trace name —
    # forcing a legend here would render as a literal "undefined" label. Keep it off.
    fig = px.line(df, x=x, y=y, markers=True)
    fig.update_traces(line_color=PRIMARY, fillcolor=hex_rgba(PRIMARY, 0.15), fill="tozeroy")
    return _apply_theme(fig, title, show_legend=False)


def bar_chart(
    df: pd.DataFrame, x: str, y: str, orientation: str = "v", title: str | None = None, show_values: bool = False
) -> go.Figure:
    # Same single-series reasoning as line_chart — no legend needed or safe to show.
    fig = px.bar(df, x=x, y=y, orientation=orientation)
    if orientation == "h":
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    if show_values:
        value_col = x if orientation == "h" else y
        fig.update_traces(text=df[value_col], texttemplate="%{text:,}", textposition="outside")
    return _apply_theme(fig, title, show_legend=False)


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str | None = None, donut: bool = False) -> go.Figure:
    # Pie slices get real category names from the `names` column, so the legend is safe here.
    fig = px.pie(df, names=names, values=values, color_discrete_sequence=PALETTE, hole=0.55 if donut else 0)
    if donut:
        fig.update_traces(textinfo="percent", textposition="inside")
    return _apply_theme(fig, title, show_legend=True)


def stacked_bar_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str | None = None) -> go.Figure:
    """Multi-series bar chart (e.g. count-per-month split by channel) — real category
    names come from the `color` column, so the legend is safe here, unlike bar_chart()."""
    fig = px.bar(df, x=x, y=y, color=color, color_discrete_sequence=PALETTE, barmode="stack")
    return _apply_theme(fig, title, show_legend=True)


def sparkline(df: pd.DataFrame, x: str, y: str, color: str | None = None) -> go.Figure:
    """Tiny axis-less trend line for KPI cards — no theme/legend/margin, just the shape."""
    fig = px.line(df, x=x, y=y)
    fig.update_traces(line_color=color or PRIMARY, line_width=2)
    fig.update_xaxes(visible=False, showgrid=False)
    fig.update_yaxes(visible=False, showgrid=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=42,
    )
    return fig


def donut_with_center(df: pd.DataFrame, names: str, values: str, center_label: str, center_value: str) -> go.Figure:
    """Donut chart with a total annotated in the middle — used for "Top agents by
    premium" style breakdowns where the whole ring represents one grand total."""
    fig = pie_chart(df, names, values, donut=True)
    # No on-slice text or built-in legend — a custom legend (with %-of-total) sits
    # alongside this chart instead, so both would just be redundant here.
    fig.update_traces(textinfo="none")
    fig.update_layout(showlegend=False)
    fig.add_annotation(
        text=f"<b>{center_value}</b><br><span style='font-size:11px;color:#7C7A8A'>{center_label}</span>",
        showarrow=False,
        font=dict(size=18),
    )
    return fig
