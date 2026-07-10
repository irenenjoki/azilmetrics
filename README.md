# Azil Metrics

Streamlit analytics dashboard for the AZIL Insurance backend API.

## Structure

```
app.py                  # Entry point — auth gate + navigation, routing/config only
pages/                  # One file per dashboard page
src/
  config.py             # Settings (pydantic-settings) + logger
  data/
    loaders.py          # API fetchers wrapped in @st.cache_data
    transforms.py       # Pure pandas transforms (no st.* calls) — unit tested
  services/
    api_client.py       # HTTP client + connection pooling via @st.cache_resource
    auth_api.py         # Login HTTP calls + session-state helpers
  components/
    auth_forms.py       # Login screen UI
    styles.py            # Global CSS injection
    charts.py             # Colour palette + plotly style builders
    metrics.py             # KPI card renderer
    filters.py             # Sidebar/page filter widgets
    tables.py               # Styled table + pagination + Excel export
    nav.py                   # Sidebar chrome + st.navigation wiring
  utils/
    formatting.py       # hex_rgba, Excel export helper
.streamlit/
  config.toml            # Theme/server settings (committed)
  secrets.toml            # Local only — gitignored
tests/
  test_transforms.py
  test_loaders.py
```

## Setup

```
pip install -r requirements.txt
copy .env.example .env   # then fill in AZIL_API_EMAIL / AZIL_API_PASSWORD
streamlit run app.py
```

## Tests

```
pytest
```

## Docker

```
docker build -t azil-metrics .
docker run -p 8501:8501 --env-file .env azil-metrics
```

## Pages

- **Overview** — top-level KPIs (policies, premium volume, income), revenue trend, top agents, product performance.
- **Business KPIs** — cover/income trends filterable by status and channel, agent leaderboard, product sales.
- **Payments & STK** — payment status/mode breakdown, revenue over time, M-Pesa STK push success rate and failure reasons.
- **Products & Vehicles** — product mix by type/underwriter, vehicle make breakdown.
- **User Growth** — signups over time, active/inactive split, user type mix.

Data is pulled live from the AZIL backend (`/dashboard/*` aggregation endpoints plus the raw `/covers`, `/payments`, `/stk-responses`, `/users`, `/products`, `/vehicles`, `/underwriters` list endpoints). Auth is the existing AZIL admin email/password login (`POST /auth/login`).
