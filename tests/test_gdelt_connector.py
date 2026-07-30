from __future__ import annotations

import httpx

from guda.connectors.gdelt import GDELTConnector


def test_gdelt_connector_normalizes_articles() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"articles": [{"url": "https://news.example/a", "title": "Chip supply chain shifts", "seendate": "20260730T010000Z", "domain": "news.example", "sourcecountry": "US", "language": "English"}]})

    connector = GDELTConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.gdeltproject.org"))

    raw = connector.fetch_raw("semiconductor supply chain", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert evidence.platform == "gdelt"
    assert evidence.title == "Chip supply chain shifts"
    assert evidence.engagement["domain"] == "news.example"
