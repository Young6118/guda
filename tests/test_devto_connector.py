from __future__ import annotations

import httpx

from guda.connectors.devto import DevToConnector


def test_devto_connector_normalizes_articles() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": 1, "title": "Agent deployment", "description": "Deploying agents", "url": "https://dev.to/a/agent", "user": {"username": "alice"}, "published_at": "2026-07-30T00:00:00Z", "public_reactions_count": 4, "comments_count": 2, "tag_list": ["ai"]}])

    connector = DevToConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://dev.to"))

    raw = connector.fetch_raw("ai", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert evidence.platform == "devto"
    assert evidence.title == "Agent deployment"
    assert evidence.engagement["reactions"] == 4
