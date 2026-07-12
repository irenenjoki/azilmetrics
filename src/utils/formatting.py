"""Small formatting helpers shared by the components layer."""
from __future__ import annotations

import io

import pandas as pd


def hex_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#RRGGBB' to an 'rgba(r, g, b, a)' string for plotly fills/backgrounds."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """Serialize a DataFrame to an in-memory .xlsx file for st.download_button."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


def to_excel_bytes_multi(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Serialize multiple DataFrames into one .xlsx file, one sheet per entry."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            (df if not df.empty else pd.DataFrame({"note": ["no data"]})).to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()
