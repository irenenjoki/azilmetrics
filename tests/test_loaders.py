from src.data import loaders


class StubClient:
    """Minimal stand-in for AzilClient so loaders can be tested without hitting the network."""

    def __init__(self, pages_by_path=None, bodies_by_path=None):
        self.pages_by_path = pages_by_path or {}
        self.bodies_by_path = bodies_by_path or {}

    def get_all_pages(self, path, params=None):
        return self.pages_by_path.get(path, [])

    def get(self, path, params=None):
        return self.bodies_by_path.get(path, {})


def test_fetch_covers_returns_dataframe():
    client = StubClient(pages_by_path={"/covers/": [{"id": "1", "status": "active"}]})
    df = loaders.fetch_covers(client)
    assert list(df["status"]) == ["active"]


def test_fetch_payments_empty():
    client = StubClient()
    df = loaders.fetch_payments(client)
    assert df.empty


def test_fetch_cover_trends_unwraps_data_envelope():
    client = StubClient(bodies_by_path={"/dashboard/cover-trends": {"data": {"totals": {"count": 5, "amount": 1000}}}})
    result = loaders.fetch_cover_trends(client, {"from": "2026-01-01", "to": "2026-01-31"})
    assert result["totals"]["count"] == 5


def test_fetch_agent_ranks_returns_dataframe():
    client = StubClient(bodies_by_path={"/dashboard/agent-ranks": {"data": [{"name": "Jane", "count": 3, "premium": 900}]}})
    df = loaders.fetch_agent_ranks(client, {"from": "2026-01-01", "to": "2026-01-31"})
    assert df.iloc[0]["name"] == "Jane"
