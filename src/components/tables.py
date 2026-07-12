"""Styled table + pagination + Excel-export components."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src.utils.formatting import to_excel_bytes, to_excel_bytes_multi


def paginated_table(df: pd.DataFrame, page_size: int = 25, key: str = "table") -> None:
    """Render a DataFrame with simple page-number pagination."""
    if df.empty:
        st.info("No data available.")
        return

    total_pages = max(1, math.ceil(len(df) / page_size))
    page = st.number_input(
        "Page", min_value=1, max_value=total_pages, value=1, step=1, key=f"{key}_page"
    )
    start = (page - 1) * page_size
    st.dataframe(df.iloc[start : start + page_size], use_container_width=True)
    st.caption(f"Page {page} of {total_pages} ({len(df):,} rows)")


def styled_table(df: pd.DataFrame) -> None:
    """A small, non-paginated table with a dark navy header row (see styles.py's
    stTable CSS). Uses st.table (real HTML) rather than st.dataframe, since
    st.dataframe's grid is canvas-rendered and can't be styled via CSS at all — reserve
    this for short summary tables, not large paginated record dumps."""
    if df.empty:
        st.info("No data available.")
        return
    st.table(df.reset_index(drop=True))


def excel_download_button(df: pd.DataFrame, filename: str, label: str = "Download as Excel", key: str | None = None) -> None:
    if df.empty:
        return
    st.download_button(
        label=label,
        data=to_excel_bytes(df),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
    )


def excel_download_button_multi(sheets: dict[str, pd.DataFrame], filename: str, label: str = "Download full report as Excel") -> None:
    """Like excel_download_button, but bundles several DataFrames into one workbook (one sheet each)."""
    if not any(not df.empty for df in sheets.values()):
        return
    st.download_button(
        label=label,
        data=to_excel_bytes_multi(sheets),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
