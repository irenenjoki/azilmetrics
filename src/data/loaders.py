"""API fetchers wrapped in @st.cache_data. Thin — normalization logic lives in transforms.py."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.api_client import ApiError, AzilClient, unwrap

from .transforms import records_to_df


@st.cache_data(ttl=180, show_spinner="Loading covers...")
def fetch_covers(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    return records_to_df(_client.get_all_pages("/covers/", params=filters))


@st.cache_data(ttl=180, show_spinner="Loading payments...")
def fetch_payments(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    return records_to_df(_client.get_all_pages("/payments/", params=filters))


@st.cache_data(ttl=180, show_spinner="Loading STK (M-Pesa) responses...")
def fetch_stk_responses(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    return records_to_df(_client.get_all_pages("/stk-responses/", params=filters))


@st.cache_data(ttl=300, show_spinner="Loading users...")
def fetch_users(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    return records_to_df(_client.get_all_pages("/users/", params=filters))


@st.cache_data(ttl=300, show_spinner="Loading products...")
def fetch_products(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    return records_to_df(_client.get_all_pages("/products/", params=filters))


@st.cache_data(ttl=300, show_spinner="Loading vehicles...")
def fetch_vehicles(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    try:
        return records_to_df(_client.get_all_pages("/vehicles/", params=filters))
    except ApiError:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner="Loading underwriters...")
def fetch_underwriters(_client: AzilClient) -> pd.DataFrame:
    payload = unwrap(_client.get("/underwriters/"))
    return records_to_df(payload if isinstance(payload, list) else [])


@st.cache_data(ttl=120, show_spinner="Loading cover trends...")
def fetch_cover_trends(_client: AzilClient, filters: dict) -> dict:
    return unwrap(_client.get("/dashboard/cover-trends", params=filters)) or {}


@st.cache_data(ttl=120, show_spinner="Loading income trends...")
def fetch_income_trends(_client: AzilClient, filters: dict) -> dict:
    return unwrap(_client.get("/dashboard/income-trends", params=filters)) or {}


@st.cache_data(ttl=120, show_spinner="Loading agent rankings...")
def fetch_agent_ranks(_client: AzilClient, filters: dict) -> pd.DataFrame:
    return records_to_df(unwrap(_client.get("/dashboard/agent-ranks", params=filters)) or [])


@st.cache_data(ttl=120, show_spinner="Loading product sales...")
def fetch_product_sales(_client: AzilClient, filters: dict) -> pd.DataFrame:
    return records_to_df(unwrap(_client.get("/dashboard/product-sales", params=filters)) or [])
