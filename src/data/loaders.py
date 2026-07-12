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


@st.cache_data(ttl=120, show_spinner="Loading expiration trends...")
def fetch_expiration_trends(_client: AzilClient, filters: dict) -> dict:
    return unwrap(_client.get("/dashboard/expiration-trends", params=filters)) or {}


@st.cache_data(ttl=120, show_spinner="Loading renewal trends...")
def fetch_renewal_trends(_client: AzilClient, filters: dict) -> dict:
    return unwrap(_client.get("/dashboard/renewal-trends", params=filters)) or {}


@st.cache_data(ttl=120, show_spinner="Loading underwriter rankings...")
def fetch_underwriter_ranks(_client: AzilClient, filters: dict) -> pd.DataFrame:
    # Unlike agent-ranks, this endpoint has no confirmed usage anywhere in AZIL-FRONTEND's
    # own code, so it may not be wired to real data on this backend — fail soft rather than
    # crash the page, since Underwriter Reports also derives rankings from underwriter-trends.
    try:
        return records_to_df(unwrap(_client.get("/dashboard/underwriter-ranks", params=filters)) or [])
    except ApiError:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner="Loading underwriter trends...")
def fetch_underwriter_trends(_client: AzilClient, filters: dict) -> dict:
    return unwrap(_client.get("/dashboard/underwriter-trends", params=filters)) or {}


@st.cache_data(ttl=180, show_spinner="Loading WhatsApp sessions...")
def fetch_whatsapp_sessions(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    try:
        return records_to_df(_client.get_all_pages("/whatsapp/sessions/", params=filters))
    except ApiError:
        return pd.DataFrame()


@st.cache_data(ttl=180, show_spinner="Loading WhatsApp session insights...")
def fetch_whatsapp_insights(_client: AzilClient, filters: dict) -> dict:
    try:
        return unwrap(_client.get("/whatsapp/sessions/insights", params=filters)) or {}
    except ApiError:
        return {}


@st.cache_data(ttl=180, show_spinner="Loading USSD sessions...")
def fetch_ussd_sessions(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    try:
        return records_to_df(_client.get_all_pages("/ussd/sessions/", params=filters))
    except ApiError:
        return pd.DataFrame()


@st.cache_data(ttl=180, show_spinner="Loading USSD session insights...")
def fetch_ussd_insights(_client: AzilClient, filters: dict) -> dict:
    try:
        return unwrap(_client.get("/ussd/sessions/insights", params=filters)) or {}
    except ApiError:
        return {}


@st.cache_data(ttl=300, show_spinner="Loading audit logs...")
def fetch_audit_logs(_client: AzilClient, filters: dict | None = None) -> pd.DataFrame:
    try:
        return records_to_df(_client.get_all_pages("/audit-logs/", params=filters))
    except ApiError:
        return pd.DataFrame()
