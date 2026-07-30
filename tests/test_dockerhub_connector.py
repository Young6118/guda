from __future__ import annotations

import httpx

from guda.connectors.dockerhub import DockerHubConnector


def test_dockerhub_connector_normalizes_repository_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"repo_name": "acme/agent", "short_description": "Agent runtime", "star_count": 7, "pull_count": 1000, "repo_owner": "acme"}]})

    connector = DockerHubConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://hub.docker.com"))

    raw = connector.fetch_raw("agent runtime", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert raw.url == "https://hub.docker.com/r/acme/agent"
    assert evidence.platform == "dockerhub"
    assert evidence.engagement["pulls"] == 1000
