from __future__ import annotations

import httpx

from guda.connectors.stackexchange import StackExchangeConnector


def test_stackexchange_connector_normalizes_questions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [{"question_id": 123, "title": "How to deploy agents?", "body": "Deployment is manual", "link": "https://stackoverflow.com/q/123", "owner": {"display_name": "alice"}, "creation_date": 1785369600, "score": 5, "answer_count": 2, "tags": ["python", "ai"]}]})

    connector = StackExchangeConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.stackexchange.com"))

    raw = connector.fetch_raw("agent deployment", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert raw.platform_item_id == "123"
    assert evidence.platform == "stackexchange"
    assert evidence.title == "How to deploy agents?"
    assert evidence.engagement["score"] == 5
