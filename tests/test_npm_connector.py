from __future__ import annotations

import httpx

from guda.connectors.npm_registry import NPMRegistryConnector


def test_npm_connector_normalizes_search_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"objects": [{"package": {"name": "agent-tool", "description": "Deploy AI agents", "version": "1.0.0", "links": {"npm": "https://www.npmjs.com/package/agent-tool", "repository": "https://github.com/acme/agent-tool"}, "publisher": {"username": "alice"}}, "score": {"final": 0.9}}]})

    connector = NPMRegistryConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://registry.npmjs.org"))

    raw = connector.fetch_raw("agent deploy", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert evidence.platform == "npm"
    assert evidence.title == "agent-tool"
    assert evidence.engagement["score"] == 0.9
