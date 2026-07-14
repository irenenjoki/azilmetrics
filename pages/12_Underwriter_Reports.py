import streamlit as st

from src.components import charts, styles, tables
from src.components.filters import current_date_filters
from src.components.metrics import kpi_cards_with_trend
from src.data import loaders
from src.data.transforms import flatten_underwriter_trends, resample_period
from src.services import auth_api

client = auth_api.require_client()
filters = current_date_filters()

styles.page_header(
    "Underwriter Reports",
    icon="🛡️",
    subtitle=f"Date range: {filters['from']} → {filters['to']} (change it in the sidebar)",
)

view_by = st.segmented_control("View by", ["Monthly", "Yearly"], default="Monthly")
granularity = "month" if view_by == "Monthly" else "year"

underwriters = loaders.fetch_underwriters(client)
underwriter_trends = loaders.fetch_underwriter_trends(client, filters)
flat = flatten_underwriter_trends(underwriter_trends)

# /dashboard/underwriter-ranks has no confirmed usage anywhere in AZIL-FRONTEND's own
# frontend, so it may not be backed by real data on this API — try it, but derive rankings
# from underwriter-trends (confirmed real, used by their own admin reports page) either way.
ranks_from_api = loaders.fetch_underwriter_ranks(client, filters)
if not ranks_from_api.empty:
    rankings = ranks_from_api
else:
    rankings = (
        flat.groupby(["underwriter_id", "underwriter_name"], as_index=False)
        .agg(amount=("amount", "sum"), count=("count", "sum"), income=("income", "sum"))
        .sort_values("amount", ascending=False)
        if not flat.empty
        else flat
    )

kpi_cards_with_trend(
    [
        {"label": "Underwriters", "value": f"{len(underwriters):,}", "icon": "🏢"},
        {"label": "Total premium (KES)", "value": f"{flat['amount'].sum():,.0f}" if not flat.empty else "0", "icon": "🪙"},
        {"label": "Total income (KES)", "value": f"{flat['income'].sum():,.0f}" if not flat.empty else "0", "icon": "📊"},
    ],
    key_prefix="uw",
)

st.divider()
st.subheader("Underwriter rankings")
if not rankings.empty:
    name_col = next((c for c in ("underwriter_name", "name") if c in rankings.columns), None)
    amount_col = next((c for c in ("amount", "total_amount") if c in rankings.columns), None)
    if name_col and amount_col:
        top = rankings.sort_values(amount_col, ascending=False).head(10)
        st.plotly_chart(charts.bar_chart(top, amount_col, name_col, orientation="h"), use_container_width=True, key="underwriter_rankings_chart")
    tables.paginated_table(rankings, key="underwriter_ranks")
    tables.excel_download_button(rankings, "underwriter_rankings.xlsx")
else:
    st.info("No underwriter ranking data for this date range.")

st.divider()
st.subheader(f"Underwriter trend — {view_by.lower()}")
if not flat.empty:
    # Resample per underwriter separately so each gets its own monthly/yearly bucket.
    top_underwriters = flat.groupby("underwriter_name")["amount"].sum().sort_values(ascending=False).head(5).index.tolist()
    fig = None
    for uw in top_underwriters:
        series = flat[flat["underwriter_name"] == uw][["period", "amount"]].rename(columns={"amount": "value"})
        series = resample_period(series, granularity)
        series["label"] = series["period"].dt.strftime("%b %Y" if granularity == "month" else "%Y")
        if fig is None:
            fig = charts.line_chart(series, "label", "value")
            fig.data[0].name = uw
        else:
            fig.add_scatter(x=series["label"], y=series["value"], mode="lines+markers", name=uw)
    if fig is not None:
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig, use_container_width=True, key="underwriter_trend_chart")
else:
    st.info("No underwriter trend data for this date range.")
