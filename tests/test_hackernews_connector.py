from __future__ import annotations

import httpx

from guda.connectors.hackernews import HackerNewsConnector


def test_hackernews_connector_normalizes_algolia_hits() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/search"
        return httpx.Response(200, json={"hits": [{"objectID": "123", "title": "Ask HN: Agent deployment pain", "url": "https://example.com", "story_text": "How do you deploy agents?", "author": "alice", "created_at": "2026-07-30T00:00:00Z", "points": 10, "num_comments": 4}]})

    connector = HackerNewsConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://hn.algolia.com"))

    raw_items = connector.fetch_raw("agent deployment", 5)
    evidence = connector.normalize(raw_items[0])

    assert raw_items[0].url == "https://news.ycombinator.com/item?id=123"
    assert evidence[0].item_type == "story"
    assert evidence[0].title == "Ask HN: Agent deployment pain"
    assert evidence[0].engagement["points"] == 10
