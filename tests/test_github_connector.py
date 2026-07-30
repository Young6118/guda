from __future__ import annotations

import httpx

from guda.connectors.github import GitHubConnector


def test_github_connector_normalizes_repo_issue_and_release_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/search/repositories":
            return httpx.Response(200, json={"items": [{"id": 1, "full_name": "owner/repo", "html_url": "https://github.com/owner/repo", "description": "Agent framework", "stargazers_count": 42, "forks_count": 3, "open_issues_count": 5, "updated_at": "2026-07-30T00:00:00Z"}]})
        if request.url.path == "/search/issues":
            return httpx.Response(200, json={"items": [{"id": 2, "html_url": "https://github.com/owner/repo/issues/1", "title": "Deployment is painful", "body": "Agent deploy needs work", "state": "open", "comments": 2, "created_at": "2026-07-29T00:00:00Z", "repository_url": "https://api.github.com/repos/owner/repo", "user": {"login": "alice"}}]})
        if request.url.path == "/repos/owner/repo/releases":
            return httpx.Response(200, json=[{"id": 3, "html_url": "https://github.com/owner/repo/releases/tag/v1", "name": "v1", "body": "First release", "published_at": "2026-07-28T00:00:00Z", "author": {"login": "bob"}}])
        return httpx.Response(404)

    connector = GitHubConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.github.com"))

    raw_items = connector.fetch_raw("repo:owner/repo agent deploy", 10)
    evidence = [item for raw in raw_items for item in connector.normalize(raw)]

    assert [item.item_type for item in evidence] == ["repo", "issue", "release"]
    assert evidence[0].title == "owner/repo"
    assert "Deployment" in evidence[1].title
    assert evidence[2].url == "https://github.com/owner/repo/releases/tag/v1"
