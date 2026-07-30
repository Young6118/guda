from __future__ import annotations

import httpx

from guda.connectors.v2ex import V2EXConnector


def test_v2ex_connector_fetches_topics_and_replies_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/nodes/go/topics":
            return httpx.Response(
                200,
                json={
                    "result": [
                        {
                            "id": 101,
                            "title": "Go agents are painful to deploy",
                            "content": "I need a better workflow",
                            "url": "https://www.v2ex.com/t/101",
                            "member": {"username": "alice"},
                            "node": {"name": "go"},
                            "replies": 1,
                            "created": 1785369600,
                        }
                    ]
                },
            )
        if request.url.path == "/api/v2/topics/101/replies":
            return httpx.Response(
                200,
                json={
                    "result": [
                        {
                            "id": 201,
                            "content": "Same here, deployment is still too manual.",
                            "member": {"username": "bob"},
                            "created": 1785369700,
                        }
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.v2ex.com")
    connector = V2EXConnector(client=client, token="test-token")

    raw_items = connector.fetch_raw("node:go agent deploy", 5)
    evidence = [item for raw in raw_items for item in connector.normalize(raw)]

    assert len(raw_items) == 2
    assert [item.item_type for item in evidence] == ["topic", "reply"]
    assert evidence[0].title == "Go agents are painful to deploy"
    assert "deployment" in evidence[1].text
