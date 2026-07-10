"""Low-level HTTP client for the AZIL Insurance backend API."""
from __future__ import annotations

import requests
import streamlit as st


class ApiError(Exception):
    pass


@st.cache_resource(show_spinner=False)
def get_http_session() -> requests.Session:
    """Connection-pooled session, shared across users via @st.cache_resource.

    Holds no per-user auth state (the bearer token lives in st.session_state instead),
    so it's safe to share across concurrent Streamlit sessions.
    """
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


def _extract_items(body):
    """Pull the record list out of AZIL's `{data: [...]}` (occasionally double-wrapped) envelope."""
    data = body.get("data", body) if isinstance(body, dict) else body
    if isinstance(data, dict):
        return data.get("data", [])
    if isinstance(data, list):
        return data
    return []


def unwrap(body):
    """Pull the payload out of AZIL's `{data: ...}` envelope, whatever shape it holds."""
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


class AzilClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = get_http_session()

    def _headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, email: str, password: str) -> str:
        resp = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=30,
        )
        if not resp.ok:
            raise ApiError(f"Login failed ({resp.status_code}): {resp.text[:300]}")
        body = resp.json()
        token = body.get("token") or body.get("data", {}).get("token")
        if not token:
            raise ApiError("Login response did not contain a token")
        self.token = token
        return token

    def get(self, path: str, params: dict | None = None) -> dict:
        resp = self.session.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params={k: v for k, v in (params or {}).items() if v not in (None, "")},
            timeout=30,
        )
        if not resp.ok:
            raise ApiError(f"GET {path} failed ({resp.status_code}): {resp.text[:300]}")
        return resp.json()

    def get_all_pages(self, path: str, params: dict | None = None, limit: int = 100, max_pages: int = 500) -> list[dict]:
        """Fetch every page of a paginated list endpoint and return the combined records.

        Stops once a page returns fewer than `limit` records, so it works regardless of
        which pagination-meta key names (pagination/meta, total/total_items, ...) the
        backend happens to use for a given endpoint.
        """
        params = dict(params or {})
        params.setdefault("limit", limit)
        page = 1
        records: list[dict] = []
        while page <= max_pages:
            params["page"] = page
            body = self.get(path, params=params)
            items = _extract_items(body)
            if not items:
                break
            records.extend(items)
            if len(items) < limit:
                break
            page += 1
        return records
